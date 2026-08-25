# Testing Evidence for PRs

The PR should describe what the tests prove, not only that a command exited successfully.

## Example-based tests

Report the command and result. Use exact assertions where exact behavior matters. For bug fixes, preserve a regression case that would fail if the fix were reverted.

## Property-based tests

Report the invariant, not merely `fast-check added`.

Strong examples include conservation, subset/permutation guarantees, ordering, exact boundaries, idempotence, round trips, bounds/sign constraints, and non-contamination of unrelated input.

When a property finds an important counterexample:

1. record/replay it;
2. understand the minimized failure;
3. fix the implementation if it is a defect;
4. add a deterministic regression for the important case;
5. keep the property exploring broader input space.

## Mutation testing

Mutation testing asks: **If the implementation were subtly wrong, would the tests notice?**

For the changed/high-value scope, report:

- files mutated;
- killed/survived counts or score;
- meaningful survivors;
- equivalent survivors and reasoning;
- tooling/unreachable survivors;
- whether it ran locally/on-demand or in CI.

Do not write implementation-coupled tests only to inflate mutation score.

## Assertion traps that commonly leave survivors

Check applicable cases:

- both branches of `if`;
- exact boundary for `>=`, `<=`, `<`, `>`;
- non-trivial arithmetic values, not only `0` and `1`;
- exact string/boolean assertions;
- both sides of meaningful `&&` / `||`;
- null/undefined behavior around optional chains;
- exact collection contents when membership/order is the contract.

## Integration / visual / runtime evidence

Unit tests cannot prove actual browser pointer/touch behavior, layout, video/canvas behavior, network integration, production dependency compatibility, or live consumer propagation. Use the right level of test and state exactly what was and was not verified.

## Completion summary pattern

A strong testing summary reports tests added/changed, property invariants, mutation scope, survivor status, defects discovered, equivalent/tooling mutants and why, local-only versus CI-gated status, and browser/integration/manual verification where relevant.
