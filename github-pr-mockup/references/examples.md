# Example prompts

## Open-source pre-flight

```text
Use the github-pr-mockup skill. Draft a PR description for this branch against
upstream main using the repo template, then generate a GitHub-style HTML mockup
I can review locally before I open anything.
```

## Working tree (uncommitted)

```text
Build a GitHub PR mockup for my current uncommitted changes. Title:
"Build: Soft-gate typecheck for e2e-playwright". Body should follow Grafana's
PR template and mention Fixes #129355. Open the HTML when done.
```

## After commits, before push

```text
Generate a PR mockup from origin/main...HEAD with the description in /tmp/pr-body.md.
Write the HTML next to the clone, not inside it.
```

## Pair with pr-quality

```text
Run pr-quality to draft the PR body with exact LOC and test evidence, then
render it with github-pr-mockup so I can review the full diff like GitHub.
```
