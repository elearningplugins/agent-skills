# GitHub PR Mockup Agent Skill

Local GitHub-style pull request preview: title, rendered description, and full unified diff in an HTML page — before anything reaches GitHub.

Especially useful for open-source contributions where you want a private review pass first.

## Contents

```text
github-pr-mockup/
├── SKILL.md
├── README.md
├── references/
│   ├── examples.md
│   └── script.md
└── scripts/
    └── build_pr_mockup.py
```

## Install

Copy this directory into an Agent Skills location, e.g.:

```text
~/.cursor/skills/github-pr-mockup/
~/.claude/skills/github-pr-mockup/
<repo>/.cursor/skills/github-pr-mockup/
```

Or install the whole repo:

```bash
npx skills add elearningplugins/brians-agent-skills
```

## Quick use

From any git repository with local changes:

```bash
python3 /path/to/github-pr-mockup/scripts/build_pr_mockup.py \
  --title "Area: Describe the change" \
  --body-file /tmp/pr-body.md \
  --out /tmp/pr-mockup.html \
  --open
```

## Suggested prompts

```text
/github-pr-mockup
```

```text
Build a GitHub-style PR mockup for my current branch so I can review it before opening a PR.
```

Pair with `pr-quality` when you need evidence-backed PR bodies, then render with this skill.
