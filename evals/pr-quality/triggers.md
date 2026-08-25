# pr-quality trigger evals

Thin trigger checks for description routing. Not a substitute for task-level behavioral evals.

## Positive (should activate)

- Review this PR before I merge it.
- Prepare a PR body for this branch.
- Does this implementation have too much blast radius?
- Tell me if this is the right solution, not just whether it works.
- Draft a pull request with exact LOC accounting and testing evidence.
- Challenge whether this shared-package change is safe for downstream consumers.

## Negative (should not activate)

- Fix this TypeScript compile error.
- Write a README for this library.
- Explain what this function does.
- Add unit tests for this helper only (prefer `qa-unit-testing`).
- Rename this variable across the repo.
- What is the weather today?
