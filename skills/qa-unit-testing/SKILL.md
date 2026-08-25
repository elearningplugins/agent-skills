---
name: qa-unit-testing
description: Builds and strengthens TypeScript unit tests with example-based tests, fast-check property testing, and Stryker mutation analysis. Use when adding or reviewing unit tests, fixing logic bugs, testing pure functions, bootstrapping tests in an under-tested repository, or determining whether existing coverage actually detects defects.
license: MIT
compatibility: >
  Designed for TypeScript/JavaScript repositories. Mutation testing
  requires Node.js and a Stryker-compatible test runner. Property-based
  testing uses fast-check.
metadata:
  author: Brian Batt
---

# QA Unit Testing

## Overview

Use three complementary layers to test behavior, not just execution:

1. **Example-based tests** — does the code do what we expect for inputs we can reason about?
2. **fast-check properties** — does the behavior hold for inputs we did not think to hand-write?
3. **Stryker mutation testing** — would the tests actually fail if the implementation were subtly wrong?

Coverage is evidence that code ran. It is not proof that assertions are strong enough to catch defects.

## When to Use

Use this skill when:

- adding or changing TypeScript/JavaScript logic;
- fixing a bug and adding a regression guard;
- reviewing whether a test suite is meaningful rather than merely high-coverage;
- testing pure helpers, parsers, selectors, grouping logic, filtering logic, URL builders, reducers, calculations, or policy functions;
- bootstrapping unit tests in a repository with little or no coverage;
- a Stryker report has surviving mutants;
- a fast-check property has found a surprising counterexample;
- CI runs tests but may not actually fail when the tests fail.

Do **not** use mutation score as a universal quality gate. Do not treat unit tests as proof of visual, browser, integration, distributed-system, or end-to-end behavior that they cannot observe.

## Discover the Repository First

Before changing tests or configuration, inspect the repository and use its conventions.

Determine:

- package manager and Node version;
- existing test runner: Jest, Vitest, `node:test`, or another runner;
- test file naming and placement;
- current test scripts and focused-test commands;
- CI command that is supposed to gate merges;
- whether fast-check is already installed;
- whether Stryker is already configured;
- TypeScript config used by tests and by Stryker;
- existing mocks, setup files, aliases, and test environment;
- generated files or expensive integration code that should not be mutated.

Do not replace a working runner just to force Jest. The method is portable: use the repository's runner and adapt fast-check/Stryker around it.

## Core Workflow

### 1. Identify the behavioral contract

Read the production code before writing tests. Identify:

- branches and conditions;
- exact boundaries;
- input/output invariants;
- nullish behavior;
- ordering, grouping, filtering, and conservation rules;
- arithmetic and normalization rules;
- externally observable side effects;
- failure and fallback behavior.

Prefer testing public behavior. Extract pure logic when doing so makes the behavior easier to specify and test without changing semantics.

### 2. Add deterministic example and regression tests

For new behavior, write examples that make the contract obvious.

For a bug fix, create a regression guard that would fail if the fix were reverted. Do not keep tests whose only purpose is to assert the known-broken behavior.

Use exact assertions whenever exact behavior matters:

```ts
expect(result.label).toBe("Expected Label");
expect(result.enabled).toBe(true);
expect(result.items).toEqual(["a", "b"]);
```

Avoid assertions that let meaningful mutations survive:

```ts
expect(result.label).toBeTruthy();
expect(result.enabled).toBeTruthy();
expect(result.items.length).toBeGreaterThan(0);
```

### 3. Add fast-check properties for pure logic

Every meaningful pure function should have at least one property test when a useful invariant can be stated.

Prefer properties such as:

- conservation: nothing lost, nothing duplicated;
- output is a subset/permutation of valid input;
- length or cardinality relationships;
- ordering guarantees;
- bounds and sign constraints;
- total-function / never-throws guarantees for valid input domains;
- idempotence;
- round-trip identity;
- monotonicity;
- type/shape guarantees;
- policy invariants across a whole numeric/status range;
- non-contamination: unrelated input survives unchanged.

Read `references/property-testing.md` when designing arbitraries or debugging a property failure.

### 4. Let fast-check shrink failures, then pin important discoveries

When a property fails:

1. capture the counterexample, seed, and path from the failure output;
2. reproduce the failure;
3. understand the smallest counterexample produced by shrinking;
4. fix the implementation if it is a real defect;
5. add a deterministic regression test for the important edge case;
6. keep the property so the broader invariant continues exploring new inputs.

Do not routinely pin a fixed seed for the entire property suite. A permanently fixed seed collapses exploration to the same cases. Use seed/path for replay, then preserve important discoveries as deterministic tests.

Prototype-sensitive string keys deserve explicit regression cases when objects are used as maps:

```ts
for (const key of ["__proto__", "constructor", "toString"]) {
  expect(() => fn(key)).not.toThrow();
}
```

### 5. Run Stryker and treat survivors as test-design prompts

After the ordinary tests and properties pass, mutation-test the changed or high-value pure logic.

Preferred progression:

```text
single changed file
      ↓
changed source files
      ↓
one high-value directory / concern
      ↓
default mutation scope
      ↓
full repository only when justified
```

Use the bundled `scripts/mutation.mjs` for single-file or changed-source-file runs when the repository uses compatible npm scripts.

For each survivor, ask:

> What observable behavior did this mutation change that the current tests failed to prove?

Then write the smallest focused test that distinguishes the original behavior from the mutant.

Read `references/mutation-testing.md` for survivor patterns and the Stryker configuration template.

### 6. Re-run until important changed-code survivors are gone

The default objective is:

```text
changed source files → no meaningful surviving mutants
```

Do **not** chase a score mechanically. Classify survivors:

- **real assertion gap** → add/strengthen a test;
- **equivalent mutant** → document why behavior is equivalent;
- **unreachable/dead code** → consider removing/refactoring it;
- **tooling/configuration issue** → fix the test discovery/mutation setup;
- **out-of-scope expensive code** → narrow the mutation scope deliberately and explain why.

## Starting From Zero

When a repository has little or no test infrastructure, do not try to blanket-test the whole codebase.

1. **Map the logic.** Identify high-value pure functions and critical branches. A scoped Stryker run may initially report mostly `NoCoverage`; that is useful as a map.
2. **Bootstrap smoke properties for pure functions.** Start with valid-input "does not throw" and basic shape/bounds invariants where appropriate.
3. **Add deterministic examples around known requirements and boundaries.** For bug fixes, add the regression guard before or alongside the fix.
4. **Turn fast-check discoveries into deterministic regressions.** Preserve the surprising concrete case.
5. **Run Stryker to expose assertion gaps.** Once code is covered, survivors reveal what the assertions still do not prove.
6. **Strengthen the changed areas.** New code gets all three layers; legacy code improves opportunistically as it is touched.

Avoid giant "test everything" pull requests unless explicitly requested. Focus on behavior that is being changed or relied upon.

## Mutation-Focused Assertion Rules

Before declaring a unit-test change complete, check all applicable items:

- [ ] Every `if` has tests for both the true and false branch.
- [ ] Every boundary (`>=`, `<=`, `<`, `>`) has a test **at the exact boundary**.
- [ ] Arithmetic tests do not rely only on `0` or `1`, which can mask operator mutations.
- [ ] String assertions use exact expected values when exact text matters.
- [ ] Boolean assertions use `toBe(true)` / `toBe(false)` when the boolean value is the contract.
- [ ] Every meaningful `&&` / `||` condition has cases where only the left side is true and only the right side is true.
- [ ] Optional chains (`?.`) have null/undefined coverage when nullish behavior is part of the contract.
- [ ] Pure functions have at least one meaningful property where an invariant can be stated.
- [ ] Changed source files have no unexplained meaningful Stryker survivors.

## CI Policy

Ordinary unit tests should gate CI if they are part of the repository's merge contract.

Mutation testing is **local/on-demand by default** because full runs can be expensive. Prefer fast changed-file or concern-scoped mutation runs during development and review.

A hard mutation threshold is appropriate only when the risk justifies it and the scope is narrow enough to be reliable. Example: a small security-sensitive URL/authentication function may deserve a high break threshold even when the rest of the repository does not.

Verify that the CI test step can actually fail the build. A test command hidden behind `continue-on-error`, `|| true`, an error-swallowing wrapper, or a non-propagated exit code is not a real quality gate.

## Test Organization

Prefer one test file per source file when repository conventions allow it. Keep examples, regressions, properties, and mutant-killing tests together so a reviewer can see the complete behavioral contract for the module.

Name mutation-driven tests after the behavior being proven. A short comment may record the mutant type and source line when that context explains why the test exists:

```ts
describe("getDefaultAggregateSpan — exact default", () => {
  // Kills StringLiteral survivor at the default return.
  it("returns exactly 'minute'", () => {
    expect(getDefaultAggregateSpan()).toBe("minute");
  });
});
```

Do not write tests that are coupled to implementation details solely to inflate mutation score.

## Environment and Tooling Gotchas

When applicable:

- `window.location` is non-configurable in jsdom; prefer `history.pushState` for URL-dependent tests.
- Jest mock hoisting can make prototype methods plus `jest.spyOn` more reliable than late reassignment.
- For Jest environment docblocks under Stryker, use the Stryker-provided environment path when required by the installed runner.
- Quote `--mutate` glob patterns in shells such as zsh.
- Ensure every mutated source file is included by the TypeScript config used by the Stryker checker.
- If Stryker incremental results look stale after changing tests/config, clear the incremental cache before trusting survivors.
- Do not let test-discovery ignore patterns accidentally exclude Stryker's sandbox.
- For `node:test` or command-runner setups with explicit test lists, register new test files in both the normal test command and the mutation test command.

## Common Rationalizations

| Rationalization | Response |
|---|---|
| "Coverage is already 100%." | Coverage proves execution, not that assertions detect defects. Run mutation analysis. |
| "The happy path passes." | Branch, boundary, nullish, and logical-operator mutants commonly survive happy-path-only tests. |
| "fast-check is just random testing." | It generates reproducible counterexamples and shrinks failures; use the reported seed/path to replay. |
| "A surviving mutant is probably equivalent." | Prove equivalence. Do not classify a survivor as equivalent because writing a distinguishing test is inconvenient. |
| "Mutation testing should run on every PR." | Only if cost and risk justify it. Changed-file/local mutation usually gives faster decision value. |
| "This unit test proves the UI bug is fixed." | Unit tests prove the logic they observe. Use browser/E2E/VRT/manual verification for visual behavior. |
| "The property says it doesn't throw, so behavior is correct." | Never-throws is a smoke invariant, not a full specification. Add stronger invariants where the contract allows them. |
| "We can pin the fast-check seed to make CI stable." | Replay the failure with seed/path, then add a deterministic regression. Keep the property exploring. |

## Red Flags

Stop and investigate when:

- a test passes before the intended behavior exists and is supposed to prove that behavior;
- a boundary condition has no exact-boundary case;
- a property merely restates the implementation;
- generated inputs are filtered so heavily that almost nothing is exercised;
- a fast-check failure is fixed without preserving the important counterexample;
- Stryker reports `NoCoverage` for code that supposedly has tests;
- all mutants survive;
- a changed test file is not actually discovered by Stryker;
- the mutation score rises only because files were excluded;
- CI says "green" even when the test command can fail locally;
- a test asserts only truthiness, call count, or non-empty output when a stronger observable result exists.

## Verification Before Completion

Run the repository's actual commands, not assumed defaults.

Minimum evidence:

1. focused tests for the changed module pass;
2. relevant fast-check properties pass;
3. the repository's full unit-test suite passes;
4. changed/high-value source files have no unexplained meaningful Stryker survivors;
5. important property-generated defects have deterministic regression guards;
6. test configuration discovers the new tests in both normal and mutation runs;
7. CI's unit-test command propagates failures;
8. claims in the PR or summary match what the tests can actually prove.

A good completion summary reports:

- tests added/changed;
- properties added and the invariants they express;
- mutation scope run;
- survivor status;
- any real defects discovered;
- any surviving equivalent/tooling mutants and why they remain;
- whether mutation is local-only or gated for this scope.
