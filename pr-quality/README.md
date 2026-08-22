# PR Quality Agent Skill

Portable Agent Skill for exact production-vs-test diff accounting, evidence-backed testing, seven PR review questions, downstream blast-radius analysis, and staff-level solution review.

## Contents

```text
pr-quality/
├── SKILL.md
├── README.md
├── assets/
│   └── pr-body-template.md
├── references/
│   ├── examples.md
│   ├── review-checklist.md
│   └── testing-evidence.md
└── scripts/
    └── loc_breakdown.py
```

## Claude Code

Project-level:

```text
<repo>/.claude/skills/pr-quality/
```

Personal/global:

```text
~/.claude/skills/pr-quality/
```

Copy the entire `pr-quality` directory there.

## Cursor

Project-level:

```text
<repo>/.cursor/skills/pr-quality/
<repo>/.agents/skills/pr-quality/
```

Personal/global:

```text
~/.cursor/skills/pr-quality/
~/.agents/skills/pr-quality/
```

Cursor also loads Claude-compatible `.claude/skills/` directories. If you use Cursor and Claude Code on the same repository, a practical single-copy setup is:

```text
<repo>/.claude/skills/pr-quality/
```

## Other Agent-Skills-compatible tools

The package follows the open Agent Skills structure: a directory with `SKILL.md`, required `name` and `description` YAML frontmatter, and optional scripts/references/assets. Install the directory in the location supported by that agent.

## Suggested use

Where slash invocation is supported:

```text
/pr-quality
```

Then ask:

```text
Prepare a PR for my current branch using the pr-quality skill.
```

or:

```text
Review this PR using the pr-quality skill. Challenge whether the approach is the right solution, not just whether it works.
```

## LOC helper

From inside a git repository:

```bash
python /path/to/pr-quality/scripts/loc_breakdown.py --base origin/main
```

The script produces a draft Markdown LOC table. Its classification is intentionally conservative and must be reviewed before using it in a PR.
