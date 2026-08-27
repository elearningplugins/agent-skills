#!/usr/bin/env python3
"""Build a GitHub-style PR review HTML mockup from a local git diff.

Intended for reviewing title, description, and full file diffs before a PR
ever reaches GitHub — especially useful on open-source forks.
"""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
import webbrowser
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


def git(repo: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode:
        print(proc.stderr.strip() or proc.stdout.strip(), file=sys.stderr)
        raise SystemExit(proc.returncode)
    return proc.stdout


def detect_base(repo: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    for candidate in ("origin/main", "origin/master", "main", "master"):
        proc = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--verify", candidate],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if proc.returncode == 0:
            return candidate
    print("Could not detect base branch; pass --base", file=sys.stderr)
    raise SystemExit(2)


def detect_remote_slug(repo: Path) -> str:
    url = git(repo, "remote", "get-url", "origin", check=False).strip()
    if not url:
        return "owner/repo"
    # git@github.com:owner/repo.git | https://github.com/owner/repo.git
    m = re.search(r"github\.com[:/](?P<slug>[^/]+/[^/]+?)(?:\.git)?$", url)
    if m:
        return m.group("slug")
    return "owner/repo"


@dataclass
class FileStat:
    path: str
    added: int
    deleted: int


@dataclass
class DiffFile:
    path: str
    lines: list[str] = field(default_factory=list)
    is_new: bool = False
    is_deleted: bool = False


def parse_unified_diff(patch: str) -> list[DiffFile]:
    files: list[DiffFile] = []
    current: DiffFile | None = None
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            if current:
                files.append(current)
            m = re.search(r" b/(.+)$", line)
            path = m.group(1) if m else line
            current = DiffFile(path=path)
        elif current is not None:
            if line.startswith("new file mode"):
                current.is_new = True
            elif line.startswith("deleted file mode"):
                current.is_deleted = True
            current.lines.append(line)
    if current:
        files.append(current)
    return files


def parse_numstat(text: str) -> list[FileStat]:
    rows: list[FileStat] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        if added == "-" or deleted == "-":
            continue
        rows.append(FileStat(path=path, added=int(added), deleted=int(deleted)))
    return rows


def collect_working_tree_diff(repo: Path) -> tuple[str, list[FileStat]]:
    """Include tracked modifications and untracked files (via intent-to-add)."""
    status = git(repo, "status", "--porcelain", "-uall")
    untracked: list[str] = []
    for line in status.splitlines():
        if not line:
            continue
        # ?? path | A  path (rare) | M  path etc. Untracked is "?? "
        if line.startswith("?? "):
            path = line[3:]
            if path.endswith("/"):
                # directory — expand via git ls-files --others
                continue
            untracked.append(path)

    # Expand untracked directories
    others = git(repo, "ls-files", "--others", "--exclude-standard")
    for path in others.splitlines():
        if path and path not in untracked:
            untracked.append(path)

    added_n: list[str] = []
    try:
        for path in untracked:
            # Skip obviously huge/binary paths if needed — git will still list them
            git(repo, "add", "-N", "--", path)
            added_n.append(path)
        patch = git(repo, "diff", "HEAD")
        numstat = parse_numstat(git(repo, "diff", "--numstat", "HEAD"))
        return patch, numstat
    finally:
        if added_n:
            # Restore untracked presentation without leaving the index dirty
            git(repo, "reset", "HEAD", "--", *added_n, check=False)


def collect_range_diff(repo: Path, base: str) -> tuple[str, list[FileStat]]:
    patch = git(repo, "diff", f"{base}...HEAD")
    numstat = parse_numstat(git(repo, "diff", "--numstat", f"{base}...HEAD"))
    return patch, numstat


def light_markdown_to_html(md: str) -> str:
    """Small Markdown subset for PR bodies: headings, lists, code, links, tasks, hr."""
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    in_ul = False
    in_ol = False
    in_code = False
    code_lang = ""
    code_buf: list[str] = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def inline(text: str) -> str:
        text = html.escape(text)
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        text = re.sub(
            r"\[([^\]]+)\]\((https?://[^)]+|#[^)]+)\)",
            r'<a href="\2">\1</a>',
            text,
        )
        text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
        return text

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            if in_code:
                out.append(
                    f'<pre class="md-code"><code>{html.escape(chr(10).join(code_buf))}</code></pre>'
                )
                code_buf = []
                in_code = False
            else:
                close_lists()
                in_code = True
                code_lang = line[3:].strip()
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if line.strip() == "---":
            close_lists()
            out.append("<hr>")
            i += 1
            continue

        heading = re.match(r"^(#{1,3})\s+(.*)$", line)
        if heading:
            close_lists()
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        task = re.match(r"^[-*]\s+\[([ xX])\]\s+(.*)$", line)
        if task:
            if not in_ul:
                close_lists()
                out.append('<ul class="task-list">')
                in_ul = True
            checked = " checked" if task.group(1).lower() == "x" else ""
            out.append(
                f'<li class="task-list-item"><input type="checkbox" disabled{checked}> '
                f"{inline(task.group(2))}</li>"
            )
            i += 1
            continue

        bullet = re.match(r"^[-*]\s+(.*)$", line)
        if bullet:
            if not in_ul:
                close_lists()
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline(bullet.group(1))}</li>")
            i += 1
            continue

        numbered = re.match(r"^\d+\.\s+(.*)$", line)
        if numbered:
            if not in_ol:
                close_lists()
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{inline(numbered.group(1))}</li>")
            i += 1
            continue

        if not line.strip():
            close_lists()
            i += 1
            continue

        close_lists()
        # Treat **Label** alone-ish paragraphs from PR templates as strong lead-ins
        out.append(f"<p>{inline(line)}</p>")
        i += 1

    close_lists()
    if in_code:
        out.append(
            f'<pre class="md-code"><code>{html.escape(chr(10).join(code_buf))}</code></pre>'
        )
    _ = code_lang  # reserved for future highlighting
    return "\n".join(out)


def fid_for(path: str) -> str:
    return "file-" + re.sub(r"[^a-zA-Z0-9_-]", "-", path)


def render_diff_rows(fd: DiffFile) -> str:
    rows: list[str] = []
    old_ln: int | None = None
    new_ln: int | None = None
    in_hunk = False
    for line in fd.lines:
        if line.startswith("@@"):
            in_hunk = True
            m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@(.*)$", line)
            if m:
                old_ln = int(m.group(1))
                new_ln = int(m.group(2))
            rows.append(
                '<tr class="hunk"><td class="blob-num"></td><td class="blob-num"></td>'
                f'<td class="blob-code hunk-code">{html.escape(line)}</td></tr>'
            )
            continue
        if not in_hunk:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            content = html.escape(line[1:])
            rows.append(
                f'<tr class="add"><td class="blob-num"></td>'
                f'<td class="blob-num blob-num-addition">{new_ln}</td>'
                f'<td class="blob-code blob-code-addition"><span class="x">+</span>{content}</td></tr>'
            )
            if new_ln is not None:
                new_ln += 1
        elif line.startswith("-") and not line.startswith("---"):
            content = html.escape(line[1:])
            rows.append(
                f'<tr class="del"><td class="blob-num blob-num-deletion">{old_ln}</td>'
                f'<td class="blob-num"></td>'
                f'<td class="blob-code blob-code-deletion"><span class="x">-</span>{content}</td></tr>'
            )
            if old_ln is not None:
                old_ln += 1
        elif line.startswith("\\"):
            rows.append(
                f'<tr class="meta"><td class="blob-num"></td><td class="blob-num"></td>'
                f'<td class="blob-code">{html.escape(line)}</td></tr>'
            )
        else:
            content = html.escape(line[1:] if line.startswith(" ") else line)
            rows.append(
                f'<tr class="ctx"><td class="blob-num">{old_ln if old_ln is not None else ""}</td>'
                f'<td class="blob-num">{new_ln if new_ln is not None else ""}</td>'
                f'<td class="blob-code"><span class="x"> </span>{content}</td></tr>'
            )
            if old_ln is not None:
                old_ln += 1
            if new_ln is not None:
                new_ln += 1
    return "".join(rows)


def render_file_block(fd: DiffFile, stats: dict[str, FileStat]) -> str:
    st = stats.get(fd.path)
    add = st.added if st else 0
    dele = st.deleted if st else 0
    badge = ""
    if fd.is_new:
        badge = '<span class="file-badge new">added</span>'
    elif fd.is_deleted:
        badge = '<span class="file-badge deleted">deleted</span>'
    fid = fid_for(fd.path)
    green = min(5, max(1 if add else 0, add and 1 + add // max(1, (add + dele) // 5)))
    red = min(5, max(0, dele and 1 + dele // max(1, (add + dele) // 5)))
    bars = ('<span class="diffstat-block add"></span>' * green) + (
        '<span class="diffstat-block del"></span>' * red
    )
    return f'''
    <div class="file" id="{fid}">
      <div class="file-header">
        <div class="file-info">
          <span class="disclosure">▾</span>
          <a href="#{fid}" class="file-path">{html.escape(fd.path)}</a>
          {badge}
        </div>
        <div class="file-stats">
          <span class="diffstat">
            <span class="diffstat-add">+{add}</span>
            <span class="diffstat-del">−{dele}</span>
            <span class="diffstat-bar">{bars}</span>
          </span>
        </div>
      </div>
      <div class="data highlight">
        <table class="diff-table"><tbody>{render_diff_rows(fd)}</tbody></table>
      </div>
    </div>
    '''


CSS = r"""
:root {
  --bg: #0d1117; --canvas: #010409; --border: #30363d; --border-muted: #21262d;
  --fg: #e6edf3; --fg-muted: #8b949e; --link: #2f81f7; --accent: #238636;
  --btn: #21262d; --btn-border: #30363d; --file-header: #161b22;
  --green-bg: rgba(46,160,67,0.15); --red-bg: rgba(248,81,73,0.15);
  --hunk-bg: rgba(56,139,253,0.1); --hunk-fg: #8b949e; --num: #8b949e;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
  font-size: 14px; line-height: 1.5; color: var(--fg); background: var(--canvas);
}
a { color: var(--link); text-decoration: none; }
a:hover { text-decoration: underline; }
code, .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; }
.topbar {
  background: #010409; border-bottom: 1px solid var(--border);
  padding: 12px 24px; display: flex; align-items: center; gap: 12px;
}
.topbar .mark { width: 32px; height: 32px; fill: var(--fg); }
.topbar .repo { font-weight: 600; }
.topbar .repo span { color: var(--fg-muted); font-weight: 400; }
.banner {
  background: #1f6feb33; border-bottom: 1px solid #1f6feb66;
  padding: 8px 24px; font-size: 13px;
}
.wrap { max-width: 1280px; margin: 0 auto; padding: 16px 24px 64px; }
.pr-title-row { display: flex; gap: 12px; align-items: flex-start; justify-content: space-between; }
.pr-title { font-size: 32px; font-weight: 400; margin: 0 0 8px; line-height: 1.25; }
.pr-title .num { color: var(--fg-muted); font-weight: 300; }
.pr-meta {
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
  margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid var(--border);
  color: var(--fg-muted);
}
.state {
  display: inline-flex; align-items: center; gap: 4px; background: var(--accent);
  color: #fff; border-radius: 2em; padding: 0 10px; height: 24px; font-size: 12px; font-weight: 600;
}
.branch {
  background: rgba(31,111,235,0.2); color: #2f81f7; border-radius: 2em;
  padding: 0 8px; font-size: 12px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
.labels { display: flex; gap: 6px; flex-wrap: wrap; margin: 0 0 12px; }
.label {
  border-radius: 2em; padding: 0 10px; font-size: 12px; font-weight: 500;
  line-height: 22px; border: 1px solid #9e6a03; background: #3d2c00; color: #d29922;
}
.tabs {
  display: flex; border-bottom: 1px solid var(--border); margin-bottom: 16px; overflow-x: auto;
}
.tab {
  appearance: none; background: transparent; border: 0; color: var(--fg-muted);
  padding: 8px 16px; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px;
  font-size: 14px; display: inline-flex; align-items: center; gap: 6px;
}
.tab:hover { color: var(--fg); }
.tab.active { color: var(--fg); border-bottom-color: #f78166; font-weight: 600; }
.tab .counter {
  background: var(--btn); border: 1px solid var(--border); border-radius: 2em;
  padding: 0 6px; font-size: 12px; min-width: 20px; text-align: center;
}
.panel { display: none; }
.panel.active { display: block; }
.timeline { display: grid; grid-template-columns: 40px 1fr; gap: 8px 12px; }
.avatar {
  width: 40px; height: 40px; border-radius: 50%;
  background: linear-gradient(135deg, #238636, #1f6feb);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 700; font-size: 14px;
}
.comment {
  border: 1px solid var(--border); border-radius: 6px; background: var(--bg); overflow: hidden;
}
.comment-header {
  background: var(--file-header); border-bottom: 1px solid var(--border);
  padding: 8px 16px; color: var(--fg-muted); font-size: 13px;
}
.comment-header strong { color: var(--fg); }
.comment-body { padding: 16px; }
.comment-body p { margin: 0 0 12px; }
.comment-body ul, .comment-body ol { margin: 0 0 12px; padding-left: 24px; }
.comment-body h1, .comment-body h2, .comment-body h3 { margin: 16px 0 8px; }
.comment-body code {
  background: rgba(110,118,129,0.2); padding: 0.2em 0.4em; border-radius: 6px; font-size: 85%;
}
.comment-body hr { border: 0; border-top: 1px solid var(--border); margin: 16px 0; }
.md-code {
  background: #161b22; border: 1px solid var(--border); border-radius: 6px;
  padding: 12px; overflow: auto; margin: 0 0 12px;
}
.task-list { list-style: none; padding-left: 0; }
.task-list-item { display: flex; gap: 8px; align-items: flex-start; margin: 6px 0; }
.task-list-item input { margin-top: 4px; }
.note {
  margin-top: 16px; border: 1px solid var(--border); border-radius: 6px;
  padding: 12px 16px; color: var(--fg-muted); font-size: 12px; background: var(--bg);
}
.files-layout { display: grid; grid-template-columns: 280px 1fr; gap: 16px; }
@media (max-width: 900px) { .files-layout { grid-template-columns: 1fr; } }
.toc {
  border: 1px solid var(--border); border-radius: 6px; background: var(--bg);
  position: sticky; top: 12px; max-height: calc(100vh - 24px); overflow: auto;
}
.toc h3 {
  margin: 0; padding: 12px 16px; font-size: 12px; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--fg-muted); border-bottom: 1px solid var(--border);
}
.toc ul { list-style: none; margin: 0; padding: 8px 0; }
.toc li a {
  display: flex; justify-content: space-between; gap: 8px; padding: 6px 12px;
  color: var(--fg); font-size: 12px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
.toc li a:hover { background: var(--border-muted); text-decoration: none; }
.fl-path { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fl-stat { flex-shrink: 0; }
.c-add { color: #3fb950; }
.c-del { color: #f85149; }
.diffstat-summary { margin-bottom: 16px; color: var(--fg-muted); }
.diffstat-summary strong { color: var(--fg); }
.file {
  border: 1px solid var(--border); border-radius: 6px; margin-bottom: 16px;
  background: var(--bg); overflow: hidden;
}
.file-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 16px; background: var(--file-header); border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 2;
}
.file-info { display: flex; align-items: center; gap: 8px; min-width: 0; }
.file-path {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px; color: var(--fg); font-weight: 600;
}
.disclosure { color: var(--fg-muted); }
.file-badge {
  font-size: 12px; border-radius: 2em; padding: 0 8px;
  border: 1px solid var(--border); color: var(--fg-muted);
}
.file-badge.new { color: #3fb950; border-color: rgba(63,185,80,0.4); }
.file-badge.deleted { color: #f85149; border-color: rgba(248,81,73,0.4); }
.diffstat { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; }
.diffstat-add { color: #3fb950; }
.diffstat-del { color: #f85149; }
.diffstat-bar { display: inline-flex; gap: 1px; }
.diffstat-block { width: 8px; height: 8px; border-radius: 1px; background: var(--border); }
.diffstat-block.add { background: #3fb950; }
.diffstat-block.del { background: #f85149; }
.data { overflow-x: auto; }
.diff-table {
  width: 100%; border-collapse: collapse;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px; table-layout: fixed;
}
.blob-num {
  width: 1%; min-width: 50px; padding: 0 8px; text-align: right; color: var(--num);
  user-select: none; vertical-align: top; border-right: 1px solid var(--border-muted);
  white-space: nowrap;
}
.blob-code { padding: 0 12px 0 8px; white-space: pre; vertical-align: top; color: var(--fg); width: 100%; }
.blob-code .x { user-select: none; margin-right: 4px; color: transparent; }
tr.add .blob-code .x, tr.del .blob-code .x { color: inherit; }
tr.add td { background: var(--green-bg); }
tr.del td { background: var(--red-bg); }
.blob-num-addition { background: rgba(46,160,67,0.2); }
.blob-num-deletion { background: rgba(248,81,73,0.2); }
tr.hunk td { background: var(--hunk-bg); }
.hunk-code { color: var(--hunk-fg); }
.btn {
  background: var(--btn); color: var(--fg); border: 1px solid var(--btn-border);
  border-radius: 6px; padding: 5px 12px; font-size: 14px; font-weight: 500;
}
.btn-primary { background: var(--accent); border-color: rgba(240,246,252,0.1); color: #fff; }
.btns { display: flex; gap: 8px; }
"""


def build_html(
    *,
    title: str,
    body_html: str,
    slug: str,
    base_branch: str,
    head_branch: str,
    author: str,
    pr_number: str,
    issue_url: str | None,
    mode: str,
    files: list[DiffFile],
    stats: list[FileStat],
    commit_subject: str | None,
    evidence_note: str,
) -> str:
    owner, _, repo_name = slug.partition("/")
    if not repo_name:
        owner, repo_name = "owner", slug
    stats_map = {s.path: s for s in stats}
    total_add = sum(s.added for s in stats)
    total_del = sum(s.deleted for s in stats)
    today = date.today().strftime("%b %-d, %Y")
    initials = "".join(p[0] for p in author.replace("_", " ").split()[:2]).upper() or "YO"

    toc = []
    for s in stats:
        toc.append(
            f'<li><a href="#{fid_for(s.path)}"><span class="fl-path">{html.escape(s.path)}</span>'
            f'<span class="fl-stat"><span class="c-add">+{s.added}</span> '
            f'<span class="c-del">−{s.deleted}</span></span></a></li>'
        )

    diff_blocks = "\n".join(render_file_block(fd, stats_map) for fd in files)
    issue_bit = (
        f' Related issue: <a href="{html.escape(issue_url)}">{html.escape(issue_url)}</a>.'
        if issue_url
        else ""
    )
    commit_line = html.escape(commit_subject or title)

    return f"""<!DOCTYPE html>
<html lang="en" data-color-mode="dark">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{html.escape(title)} · Pull Request mockup · {html.escape(slug)}</title>
<style>{CSS}</style>
</head>
<body>
  <div class="topbar">
    <svg class="mark" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
    <div class="repo"><span>{html.escape(owner)}</span> / <strong>{html.escape(repo_name)}</strong></div>
  </div>
  <div class="banner">Local review mockup — not a real GitHub PR. Diff source: <code>{html.escape(mode)}</code>.{issue_bit}</div>
  <div class="wrap">
    <div class="pr-title-row">
      <h1 class="pr-title">{html.escape(title)} <span class="num">#{html.escape(pr_number)}</span></h1>
      <div class="btns">
        <button class="btn" type="button" disabled>Edit</button>
        <button class="btn btn-primary" type="button" disabled>Merge pull request</button>
      </div>
    </div>
    <div class="pr-meta">
      <span class="state">Open</span>
      <span><strong style="color:var(--fg)">{html.escape(author)}</strong> wants to merge into
        <span class="branch">{html.escape(base_branch)}</span> from
        <span class="branch">{html.escape(head_branch)}</span></span>
      <span>· drafted {today}</span>
    </div>
    <div class="labels"><span class="label">review mockup</span></div>
    <div class="tabs" role="tablist">
      <button class="tab active" data-tab="conversation" type="button">Conversation <span class="counter">1</span></button>
      <button class="tab" data-tab="commits" type="button">Commits <span class="counter">1</span></button>
      <button class="tab" data-tab="files" type="button">Files changed <span class="counter">{len(stats)}</span></button>
    </div>

    <div id="panel-conversation" class="panel active">
      <div class="timeline">
        <div class="avatar">{html.escape(initials)}</div>
        <div class="comment">
          <div class="comment-header"><strong>{html.escape(author)}</strong> commented {today} · PR description preview</div>
          <div class="comment-body">{body_html}</div>
        </div>
      </div>
      <div class="note">{html.escape(evidence_note)}</div>
    </div>

    <div id="panel-commits" class="panel">
      <div class="comment">
        <div class="comment-header"><strong>Commits</strong></div>
        <div class="comment-body">
          <p class="mono"><span style="color:#3fb950">●</span> {commit_line}</p>
        </div>
      </div>
    </div>

    <div id="panel-files" class="panel">
      <div class="diffstat-summary">
        Showing <strong>{len(stats)} changed files</strong> with
        <strong class="c-add">{total_add} additions</strong> and
        <strong class="c-del">{total_del} deletions</strong>.
      </div>
      <div class="files-layout">
        <nav class="toc"><h3>Files</h3><ul>{"".join(toc)}</ul></nav>
        <div class="diff-files">{diff_blocks}</div>
      </div>
    </div>
  </div>
<script>
document.querySelectorAll('.tab').forEach(tab => {{
  tab.addEventListener('click', () => {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
  }});
}});
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Git repository root")
    parser.add_argument(
        "--mode",
        choices=("working-tree", "range"),
        default="working-tree",
        help="working-tree: uncommitted+untracked vs HEAD; range: base...HEAD commits",
    )
    parser.add_argument("--base", default=None, help="Base ref for --mode range (default: origin/main)")
    parser.add_argument("--title", required=True, help="PR title")
    parser.add_argument("--body-file", type=Path, help="Markdown file for PR description")
    parser.add_argument("--body", default="", help="PR description Markdown (alternative to --body-file)")
    parser.add_argument("--out", type=Path, required=True, help="Output HTML path")
    parser.add_argument("--author", default="you")
    parser.add_argument("--slug", default=None, help="owner/repo (default: from origin)")
    parser.add_argument("--base-branch", default=None, help="Display name for base branch")
    parser.add_argument("--head-branch", default=None, help="Display name for head branch")
    parser.add_argument("--pr-number", default="XXXXX")
    parser.add_argument("--issue-url", default=None, help="Optional linked issue URL for banner")
    parser.add_argument("--commit-subject", default=None)
    parser.add_argument("--evidence", default="", help="Footer evidence note (plain text)")
    parser.add_argument("--open", action="store_true", help="Open the HTML in the default browser")
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not (repo / ".git").exists() and not (repo / ".git").is_file():
        # worktrees use .git file
        print(f"Not a git repo: {repo}", file=sys.stderr)
        raise SystemExit(2)

    base = detect_base(repo, args.base) if args.mode == "range" else (args.base or "HEAD")
    if args.mode == "working-tree":
        patch, stats = collect_working_tree_diff(repo)
        mode_label = "working tree (including untracked) vs HEAD"
    else:
        patch, stats = collect_range_diff(repo, base)
        mode_label = f"{base}...HEAD"

    if not patch.strip() and not stats:
        print("No changes found for this mode.", file=sys.stderr)
        raise SystemExit(1)

    files = parse_unified_diff(patch)
    # Ensure stats cover every parsed file (order by numstat, then extras)
    seen = {s.path for s in stats}
    for fd in files:
        if fd.path not in seen:
            # Count from hunks roughly
            add = sum(1 for ln in fd.lines if ln.startswith("+") and not ln.startswith("+++"))
            dele = sum(1 for ln in fd.lines if ln.startswith("-") and not ln.startswith("---"))
            stats.append(FileStat(fd.path, add, dele))

    body_md = args.body
    if args.body_file:
        body_md = args.body_file.read_text()
    if not body_md.strip():
        body_md = (
            "**What is this feature?**\n\n"
            "_Add PR description Markdown via --body-file or --body._\n"
        )

    slug = args.slug or detect_remote_slug(repo)
    head = args.head_branch or git(repo, "branch", "--show-current").strip() or "HEAD"
    base_branch = args.base_branch or (
        args.base.split("/")[-1] if args.base else ("main" if args.mode == "working-tree" else base.split("/")[-1])
    )

    evidence = args.evidence or (
        f"+{sum(s.added for s in stats)} / −{sum(s.deleted for s in stats)} across {len(stats)} files · {mode_label}"
    )

    doc = build_html(
        title=args.title,
        body_html=light_markdown_to_html(body_md),
        slug=slug,
        base_branch=base_branch,
        head_branch=head,
        author=args.author,
        pr_number=args.pr_number,
        issue_url=args.issue_url,
        mode=mode_label,
        files=files,
        stats=stats,
        commit_subject=args.commit_subject,
        evidence_note=evidence,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(doc)
    print(f"Wrote {args.out} ({len(stats)} files, +{sum(s.added for s in stats)}/−{sum(s.deleted for s in stats)})")
    if args.open:
        webbrowser.open(args.out.resolve().as_uri())


if __name__ == "__main__":
    main()
