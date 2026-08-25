# Brian's Agent Skills · [Brian's Job Search](https://briansjobsearch.com)

**One job: teaching AI coding agents how Brian's Job Search gets built.**
Reusable [Agent Skills](https://agentskills.io) for Cursor, Claude Code, Codex,
and other hosts that speak `SKILL.md`.

These are the same workflows used on [briansjobsearch.com](https://briansjobsearch.com)
and the [Chrome autofill extension](https://github.com/elearningplugins/briansjobsearch-chrome-extension-autofill) —
PR evidence, tests that catch real defects, and ATS payload truth before shipping parsers.

## Skills

| Skill | When to use it |
|---|---|
| [`pr-quality`](pr-quality/) | Preparing or reviewing a PR — exact diff accounting, evidence-backed testing, blast-radius and solution review |
| [`qa-unit-testing`](qa-unit-testing/) | Strengthening TypeScript unit tests with examples, fast-check properties, and Stryker mutation analysis |

Each skill is a folder with a `SKILL.md` (required `name` + `description` frontmatter)
plus optional `scripts/`, `references/`, and `assets/`.

## Install

### Cursor

```bash
npx skills add elearningplugins/brians-agent-skills
```

Or copy a skill folder into `.cursor/skills/<name>/` (project) or `~/.cursor/skills/<name>/` (personal).

### Claude Code

```bash
npx skills add elearningplugins/brians-agent-skills -a claude-code
```

Or copy into `.claude/skills/<name>/` or `~/.claude/skills/<name>/`.

### GitHub CLI

```bash
gh skill install elearningplugins/brians-agent-skills pr-quality
gh skill install elearningplugins/brians-agent-skills qa-unit-testing
```

### Manual

Clone and point your agent at the skill directory:

```bash
git clone https://github.com/elearningplugins/brians-agent-skills.git
```

## Suggested use

```text
/pr-quality
Prepare a PR for my current branch using the pr-quality skill.
```

```text
/qa-unit-testing
Strengthen unit tests for this module with properties and mutation analysis.
```

## Related

- Site: [briansjobsearch.com](https://briansjobsearch.com)
- Extension: [briansjobsearch-chrome-extension-autofill](https://github.com/elearningplugins/briansjobsearch-chrome-extension-autofill)
- Spec: [agentskills.io](https://agentskills.io)

---

Created by [Brian Batt](https://www.linkedin.com/posts/brianbatt_jobsearch-activity-7432771497389121536-Zt2q) · part of [Brian's Job Search](https://briansjobsearch.com)
