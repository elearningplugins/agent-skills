---
name: github-pr-mockup
description: >-
  Builds a local GitHub-style pull request HTML mockup (title, rendered description,
  Conversation/Files changed tabs, full unified diff) from the working tree or a
  commit range before anything is pushed. Use when the user wants a PR preview,
  GitHub mockup, pre-PR review page, local diff review UI, or to review an
  open-source contribution without opening a real PR yet.
---

# GitHub PR Mockup

Produce a **local HTML page that looks like a GitHub pull request** so the user can review title, description, and the full diff **before** the change reaches GitHub.

Especially useful for open-source forks: CLA, signed commits, maintainer norms, and first impressions matter — catch description and diff issues privately.

This skill renders a preview. It does **not** open a PR, push, or comment on GitHub unless the user separately asks.

## When to use

- User asks for a GitHub-like PR mockup / preview / review HTML
- Pre-flight review of an OSS contribution still on a local branch
- Validate PR title + body + full file list before `gh pr create`
- Pair with `pr-quality` after the body is drafted

## Workflow

### 1. Gather context

In the target git repo:

1. Detect base branch (`origin/main` / `origin/master` / local fallback).
2. Prefer **working-tree** mode when changes are uncommitted or include untracked files (typical pre-PR state).
3. Use **range** mode (`base...HEAD`) when commits already exist and the working tree is clean.
4. Read the repo’s PR template (`.github/PULL_REQUEST_TEMPLATE.md` etc.) and title conventions (`Area: Summary`, Conventional Commits, etc.).
5. Draft the PR **title** and **Markdown body** honestly. Prefer the `pr-quality` skill for evidence-backed bodies when preparing a real contribution. Never invent issue numbers or test results.

### 2. Write the body to a temp file

```bash
cat > /tmp/pr-body.md <<'EOF'
**What is this feature?**

…

**Which issue(s) does this PR fix?**:

Fixes #12345
EOF
```

### 3. Generate the mockup

Run this skill’s script (resolve the path to this skill’s `scripts/` directory):

```bash
python3 /path/to/github-pr-mockup/scripts/build_pr_mockup.py \
  --repo /path/to/target-repo \
  --mode working-tree \
  --title "Area: Short accurate title" \
  --body-file /tmp/pr-body.md \
  --out /tmp/pr-mockup.html \
  --issue-url "https://github.com/org/repo/issues/12345" \
  --evidence "+N / −M across K files · only commands you actually ran" \
  --open
```

Range mode after commits exist:

```bash
python3 /path/to/github-pr-mockup/scripts/build_pr_mockup.py \
  --repo /path/to/target-repo \
  --mode range \
  --base origin/main \
  --title "Area: Short accurate title" \
  --body-file /tmp/pr-body.md \
  --out /tmp/pr-mockup.html \
  --open
```

### 4. Deliver to the user

1. Open the HTML (script `--open`, or `open` / `xdg-open`).
2. Tell them the output path.
3. Point them at **Conversation** (description) and **Files changed** (full diff).
4. Do **not** create the real GitHub PR unless they ask.

## Output location rules

- Prefer a path **outside** the target repo (parent directory, `/tmp`, or Documents) so the mockup does not dirty `git status`.
- If writing inside the repo is unavoidable, gitignore or delete it after review — never commit the mockup unless the user explicitly wants that.

## Script behavior (do not reimplement)

`scripts/build_pr_mockup.py` already:

- collects unified diff + numstat (working tree includes untracked via temporary `git add -N`, then resets);
- renders GitHub-dark UI with Conversation / Commits / Files changed tabs;
- converts a Markdown subset (headings, lists, task lists, links, inline code, hr) for the description;
- detects `owner/repo` from `origin` when `--slug` is omitted.

Do not regenerate a one-off HTML builder in chat when this script can run.

## Quality bar

- Full diff of every file in scope — not a summary-only page.
- Description must match what would be pasted into GitHub (template sections filled).
- Banner must make clear this is a **local mockup**, not a real PR.
- Evidence footer: only commands/results actually run.

## Pairing

| Skill | Role |
| --- | --- |
| `pr-quality` | Decide readiness; exact LOC; evidence; solution review; draft the Markdown body |
| `github-pr-mockup` | Render that body + full diff as a GitHub-like page for human review |

Typical OSS sequence: implement → verify → `pr-quality` body → **this mockup** → user reviews → signed commit / CLA / `gh pr create` when they ask.

## Additional resources

- Script flags: [references/script.md](references/script.md)
- Example prompts: [references/examples.md](references/examples.md)
