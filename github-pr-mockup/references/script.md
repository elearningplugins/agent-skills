# Script reference: `build_pr_mockup.py`

```bash
python3 scripts/build_pr_mockup.py --help
```

## Required

| Flag | Meaning |
| --- | --- |
| `--title` | PR title string |
| `--out` | Output `.html` path |

## Description

Provide exactly one of:

| Flag | Meaning |
| --- | --- |
| `--body-file PATH` | Markdown PR description |
| `--body "..."` | Inline Markdown (fine for short bodies) |

## Diff source

| Flag | Default | Meaning |
| --- | --- | --- |
| `--mode working-tree` | yes | Diff `HEAD` including unstaged + untracked |
| `--mode range` | | Diff `base...HEAD` (committed only) |
| `--base REF` | auto for range | e.g. `origin/main` |
| `--repo PATH` | cwd | Target repository root |

Working-tree mode uses temporary `git add -N` for untracked files, then `git reset` so the index is not left dirty.

## Display metadata

| Flag | Meaning |
| --- | --- |
| `--author` | Display name (default `you`) |
| `--slug owner/repo` | Override remote detection |
| `--base-branch` / `--head-branch` | Branch pills in the header |
| `--pr-number` | Fake PR number (default `XXXXX`) |
| `--issue-url` | Linked in the mockup banner |
| `--commit-subject` | Commits tab line |
| `--evidence` | Plain-text footer note |
| `--open` | Open the HTML in the default browser |

## Exit codes

- `0` — wrote HTML
- `1` — no changes for the chosen mode
- `2` — not a git repo / could not detect base
