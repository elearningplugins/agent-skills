# Property-Based Testing with fast-check

Use this reference when designing arbitraries, choosing invariants, or diagnosing a property failure.

## Core Principle

Example tests cover cases you thought of. Property tests explore a domain and assert behavior that must remain true across many generated cases.

A useful property states a contract, not an implementation detail.

```ts
import fc from "fast-check";

it("preserves input length", () => {
  fc.assert(
    fc.property(fc.array(fc.string()), (input) => {
      expect(transform(input)).toHaveLength(input.length);
    }),
  );
});
```

## Invariant Families

### Conservation / no loss / no duplication

Best for grouping and partitioning functions.

```ts
fc.assert(
  fc.property(itemsArb, (items) => {
    const groups = groupItems(items);
    const seen = groups.flatMap((g) => [g.primary, ...g.related]);

    expect(new Set(seen.map((x) => x.id)).size).toBe(items.length);
    expect(seen).toHaveLength(items.length);
  }),
);
```

Ask:

- Does every input appear exactly once?
- Is anything duplicated?
- Is anything silently dropped?
- Is every output identifier drawn from the input domain?

### Length / permutation

Useful for sorting, reordering, prioritization, and stable transforms.

```ts
fc.assert(
  fc.property(fc.array(fc.integer()), (input) => {
    const output = prioritize(input);
    expect(output).toHaveLength(input.length);
    expect([...output].sort()).toEqual([...input].sort());
  }),
);
```

### Ordering

Assert the relationship that matters rather than one hard-coded list.

```ts
fc.assert(
  fc.property(dataArb, (input) => {
    const output = sortByPriority(input);
    for (let i = 1; i < output.length; i += 1) {
      expect(output[i - 1].priority).toBeLessThanOrEqual(output[i].priority);
    }
  }),
);
```

### Bounds / sign / range

```ts
fc.assert(
  fc.property(widthInputArb, (input) => {
    for (const width of distributeWidths(input)) {
      expect(width).toBeGreaterThanOrEqual(0);
    }
  }),
);
```

### Total-function / never throws

Useful as a **smoke property**, especially when bootstrapping tests.

```ts
fc.assert(
  fc.property(validInputArb, (input) => {
    expect(() => pureFn(input)).not.toThrow();
  }),
);
```

Do not mistake this for a full specification. Strengthen it with output invariants.

### Type / shape guarantees

```ts
fc.assert(
  fc.property(inputArb, (input) => {
    const result = format(input);
    expect(typeof result).toBe("string");
    expect(result).not.toBe("");
  }),
);
```

### Idempotence

```ts
fc.assert(
  fc.property(inputArb, (input) => {
    const once = normalize(input);
    expect(normalize(once)).toEqual(once);
  }),
);
```

### Round trip

```ts
fc.assert(
  fc.property(idArb, (id) => {
    expect(decode(encode(id))).toBe(id);
  }),
);
```

### Monotonicity

```ts
fc.assert(
  fc.property(fc.array(toolArb), toolArb, (tools, extra) => {
    expect(cost([...tools, extra])).toBeGreaterThanOrEqual(cost(tools));
  }),
);
```

### Non-contamination

Changing one semantic field must not corrupt unrelated data.

```ts
fc.assert(
  fc.property(recordArb, fc.string(), (record, replacement) => {
    const result = replaceName(record, replacement);
    expect(result.id).toBe(record.id);
    expect(result.metadata).toEqual(record.metadata);
  }),
);
```

### Policy invariants

Property testing is excellent for ranges with a few exceptions.

```ts
it("never retries ordinary 4xx responses", async () => {
  await fc.assert(
    fc.asyncProperty(
      fc.integer({ min: 400, max: 499 }).filter((s) => s !== 408 && s !== 429),
      async (status) => {
        const calls = await invokeWithStatus(status);
        expect(calls).toBe(1);
      },
    ),
  );
});
```

## Designing Arbitraries

Generate **valid structured states**, not bags of unrelated random values.

Compose arbitraries when fields depend on one another:

```ts
const graphArb = fc
  .uniqueArray(fc.uuid(), { minLength: 2, maxLength: 8 })
  .chain((ids) =>
    fc.array(
      fc.record({
        source: fc.constantFrom(...ids),
        target: fc.constantFrom(...ids),
        type: fc.constantFrom("cancelled_by", "correlated_with", "superseded_by"),
      }),
      { maxLength: ids.length * 2 },
    ),
  );
```

Keep the generated domain small enough that shrinking produces readable counterexamples but broad enough to reach meaningful interactions.

Avoid heavy `.filter(...)` chains that discard most generated values. Prefer constructing valid data directly with `map`, `chain`, `tuple`, `record`, `uniqueArray`, and dependent generators.

## Numbers

JavaScript uses 64-bit IEEE-754 numbers. When the code under test depends on normal JavaScript number precision, prefer:

```ts
fc.double({ noNaN: true, noDefaultInfinity: true });
```

Do not substitute `fc.float()` merely because the production value is called a "float"; `fc.float()` generates 32-bit values and loses precision much earlier.

## Prototype-Sensitive Keys

String generators can reach object-property names humans rarely hand-write. These are particularly valuable when plain objects are used as maps.

Keep explicit regressions for:

```ts
["__proto__", "constructor", "toString"]
```

Safer implementation patterns may include `Object.hasOwn`, `Map`, or null-prototype objects depending on the contract.

## Run Counts

Start with fast-check defaults unless the risk or generated domain justifies more runs. Increasing `numRuns` is not a substitute for a stronger property or better arbitrary.

Use a larger count selectively for small, important domains such as reserved-character round trips:

```ts
fc.assert(fc.property(idArb, property), { numRuns: 200 });
```

## Failure Handling

When fast-check fails, record:

- property name;
- seed;
- path / counterexample path;
- minimized counterexample;
- whether it represents a product defect, test defect, or invalid arbitrary.

Replay using the seed/path while debugging. Once understood, add a deterministic regression for important concrete cases instead of permanently pinning the entire property suite to one seed.

## Property Strength

Weak property:

```ts
expect(total).toBeGreaterThan(0);
```

Stronger property when the real contract is known:

```ts
expect(total).toBe(expectedContainerWidth);
```

Smoke properties are useful while bootstrapping, but label them mentally as smoke tests. Tighten them as the contract becomes clear.

## Property Review Checklist

- [ ] Does the property state behavior rather than mirror implementation?
- [ ] Is the generated domain valid?
- [ ] Can the arbitrary shrink to a readable counterexample?
- [ ] Is the property stronger than "does not throw" when a stronger contract exists?
- [ ] Are important discovered counterexamples pinned as deterministic regressions?
- [ ] Are prototype-sensitive keys covered when plain objects act as maps?
- [ ] Are run-count overrides justified?
