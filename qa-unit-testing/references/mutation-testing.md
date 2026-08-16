# Writing Tests That Kill Mutants

Use this reference when Stryker reports surviving mutants or when setting up mutation testing for a TypeScript repository.

## Core Principle

Coverage tells you code ran. Mutation testing tells you whether the tests were strong enough to notice plausible defects.

**Every important test should contain an assertion that would fail if the implementation were slightly wrong.**

## Mutant Patterns

### EqualityOperator (`>`, `>=`, `<`, `<=`, `===`, `!==`)

Stryker flips comparison operators. Test the **exact boundary** and a neighboring value.

```ts
// Source: if (abs < 1e-4)

// Weak: does not distinguish < from <=
expect(format(0.00001)).toBe("1e-5");

// Strong
expect(format(1e-4)).toBe("0.0001");
expect(format(9.99e-5)).toBe("9.99e-5");
```

**Rule:** for each important numeric boundary, include a case at the boundary and one just inside/outside.

### LogicalOperator (`&&` ↔ `||`)

Cover inputs where:

- both operands are true;
- only the left operand is true;
- only the right operand is true;
- both are false.

The left-only and right-only cases are what distinguish `&&` from `||`.

```ts
it("does not match when the condition is correct but the value is not less", () => {
  expect(evaluate("Less than", 5, 5)).toBe(false);
});

it("does not match when the value is less but the condition is wrong", () => {
  expect(evaluate("Greater than", 3, 5)).toBe(false);
});
```

### ConditionalExpression (condition → `true` / `false`)

Exercise both branches and assert distinguishable output.

```ts
expect(fn(true)).toBe(valueA);
expect(fn(false)).toBe(valueB);
```

### ArithmeticOperator (`+` ↔ `-`, `*` ↔ `/`, etc.)

Choose values that produce visibly different results under the mutant.

```ts
// Weak: basePadding=0 masks + versus -
expect(getWidth(0, 10, 5)).toBe(50);

// Strong
expect(getWidth(4, 10, 5)).toBe(54);
```

**Rule:** do not use only `0` or `1` for arithmetic behavior; they frequently neutralize operator mutations.

### BlockStatement (block removed)

Assert the externally observable effect of the block executing **and** not executing.

```ts
expect(fn({ isHidden: true, now: 1000, lastTime: 800 }).diff).toBe(200);
expect(fn({ isHidden: false, now: 1000, lastTime: 800 }).diff).toBe(0);
```

### StringLiteral (string → `""`)

Assert exact strings when exact text is the contract.

```ts
// Weak
expect(getLabel()).toBeTruthy();

// Strong
expect(getLabel()).toBe("Expected Label");
```

### BooleanLiteral (`true` ↔ `false`)

```ts
// Weak
expect(config.resizable).toBeTruthy();

// Strong
expect(config.resizable).toBe(true);
```

### MethodExpression

Stryker may replace/remove method behavior. Assert the behavioral difference produced by the method.

```ts
// Source depends on label.toLowerCase()
expect(
  getKeyColumn([{ label: "TIMESTAMP", dataKey: "ts" }], "timestamp"),
).toBe("ts");
```

### OptionalChaining (`?.` → `.`)

Test nullish input explicitly.

```ts
expect(getKey(null)).toBeUndefined();
```

### Array and collection mutants

If an array literal or collection construction is mutated, weak length-only assertions may survive.

Prefer exact contents plus inclusion/exclusion when those details are contractual:

```ts
expect(result).toEqual(["alpha", "beta"]);
expect(result).toContain("alpha");
expect(result).not.toContain("gamma");
```

### Sorting mutants

Assert ordering with distinct values. Avoid test values that compare equal. If the native/default sort semantics are the intended behavior, do not introduce a custom comparator merely for style; comparator branches can create equivalent or hard-to-distinguish mutants.

## Common Mistakes

| Mistake | Typical survivor |
|---|---|
| `toBeTruthy()` instead of exact boolean/string | BooleanLiteral / StringLiteral |
| Happy path only | ConditionalExpression |
| Arithmetic only with `0`/`1` | ArithmeticOperator |
| No exact boundary case | EqualityOperator |
| Assert "called" but not the resulting behavior | BlockStatement |
| Only one side of `&&` / `||` | LogicalOperator |
| Loose `toContain` when exact output matters | StringLiteral / collection mutants |
| Tests discovered normally but not under Stryker | `NoCoverage` / universal survivors |

## Survivor-Driven Test Naming

When a surviving mutant directly caused a new test, preserve enough context to explain the test's existence:

```ts
describe("generateRandomData — y range", () => {
  // Kills ArithmeticOperator survivor at the y calculation.
  it("produces values in the intended range", () => {
    const data = generateRandomData(200);
    expect(Math.max(...data.map((d) => d.y))).toBeGreaterThanOrEqual(1);
  });
});
```

Do not encode brittle source line numbers if they will immediately drift; use the mutator/behavior context that will still help a future reader.

## Canonical Stryker Configuration

Adapt the runner and mutate scope to the repository. Keep all `@stryker-mutator/*` packages on compatible versions.

```js
const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
const full = process.env.STRYKER_FULL === "true";

/** @type {import('@stryker-mutator/api/core').PartialStrykerOptions} */
const config = {
  testRunner: "jest",
  jest: {
    configFile: "jest.config.json",
    enableFindRelatedTests: true,
  },
  checkers: ["typescript"],
  tsconfigFile: "tsconfig.json",

  mutate: full
    ? ["src/**/*.{ts,tsx}", "!src/**/*.test.{ts,tsx}", "!src/**/*.d.ts"]
    : [
        "src/utils/helpers/**/*.ts",
        "src/store/**/*.ts",
        "!src/**/*.test.{ts,tsx}",
        "!src/**/*.d.ts",
      ],

  ignoreStatic: true,

  thresholds: {
    high: 80,
    low: 70,
    break: null,
  },

  reporters: ["html", "clear-text", "progress", "json"],
  htmlReporter: {
    fileName: `build/mutation/report${full ? ".full" : ""}-${timestamp}.html`,
  },
  jsonReporter: {
    fileName: `build/mutation/report${full ? ".full" : ""}-${timestamp}.json`,
  },

  concurrency: 4,
  coverageAnalysis: "perTest",
  incremental: true,
};

export default config;
```

### Why these defaults

- **Scoped default + `STRYKER_FULL`**: quick feedback on high-value pure logic; full repository only when justified.
- **`break: null`**: mutation is a diagnostic by default, not a global CI gate.
- **`coverageAnalysis: "perTest"`**: lets supported runners select relevant tests efficiently.
- **`incremental: true`**: avoids re-running unaffected mutations when supported.
- **TypeScript checker**: rejects mutants that cannot type-check instead of wasting test runtime on them.
- **Timestamped reports**: makes runs inspectable without overwriting the previous report.

## Runner Adaptation

### Jest

Use `@stryker-mutator/jest-runner`. For Jest environment docblocks, Stryker provides compatible environment wrappers such as:

```text
@stryker-mutator/jest-runner/jest-env/jsdom
```

If Stryker cannot find related tests because tests reach source indirectly, verify runner configuration rather than assuming surviving mutants are real.

### Vitest

Use `@stryker-mutator/vitest-runner`. Verify source/test relationships and the installed runner's current `related` behavior. The current Vitest runner handles per-test coverage internally.

### node:test or another unsupported runner

Use Stryker's command runner and execute the repository's real compiled test command. If the test list is explicit, every new test must be added to both the ordinary test command and the Stryker command.

## Risk-Weighted Thresholds

Do not make an arbitrary repository-wide mutation score the goal.

A narrow high-risk function may justify a hard threshold:

```json
{
  "thresholds": { "high": 95, "low": 90, "break": 90 }
}
```

Use this only when:

- the scope is small and stable;
- the code is materially high-risk (for example auth/security-sensitive logic);
- the test suite can reliably distinguish meaningful mutations;
- runtime is acceptable.

## Local Commands

Recommended script ladder:

```bash
# Default high-value scope
npm run test:mutation

# Changed source files
npm run test:mutation:changes

# One source file
npm run test:mutation:file -- src/utils/helpers/date.helpers.ts

# One concern/directory
npm run test:mutation:utils
npm run test:mutation:store

# Full repository — expensive
npm run test:mutation:full
```

Example `package.json` entries:

```json
{
  "scripts": {
    "test:mutation": "stryker run",
    "test:mutation:changes": "node scripts/mutation.mjs",
    "test:mutation:file": "node scripts/mutation.mjs",
    "test:mutation:full": "STRYKER_FULL=true stryker run"
  }
}
```

On Windows, use a cross-platform environment-variable helper or repository-native equivalent for `STRYKER_FULL=true`.

## Mutation CI Policy

Default:

```text
ordinary unit tests → CI gate
mutation testing    → local/on-demand
```

Full mutation runs can be slow. A changed-file mutation run often gives better feedback per minute than a mandatory whole-repository job.

If mutation is added to CI, justify:

- scope;
- expected runtime;
- threshold policy;
- failure semantics;
- how equivalent mutants are handled;
- who owns breakage when tool versions change.

## Diagnosing Suspicious Results

### Everything is `NoCoverage`

Check:

- test discovery under the mutation runner;
- whether tests import/execute the mutated source;
- mutate patterns;
- test ignore patterns;
- explicit test lists for command runners.

### Every mutant survives

Do not immediately write more tests. First verify that the tests actually run in the Stryker sandbox.

### Incremental results look stale

Clear the repository's Stryker incremental cache/report and re-run before changing assertions based on stale survivors.

### TypeScript checker errors

Ensure every mutated source file is included in the configured `tsconfigFile`. A checker cannot validate a file the TypeScript project does not watch/include.

### jsdom/Jest environment problems

If a file uses a Jest environment docblock, use the Stryker-compatible environment wrapper required by the installed Jest runner.

## Pre-Submission Checklist

- [ ] Both sides of important branches are tested.
- [ ] Exact boundaries are tested.
- [ ] Arithmetic inputs distinguish mutated operators.
- [ ] String and boolean assertions are exact when exactness is contractual.
- [ ] `&&` / `||` conditions have operand-distinguishing cases.
- [ ] Optional chains have nullish coverage.
- [ ] Observable side effects are asserted, not only call counts.
- [ ] Changed source files have no unexplained meaningful survivors.
- [ ] Equivalent mutants are explained rather than ignored.
- [ ] New test files are discovered under Stryker, not only the normal runner.
