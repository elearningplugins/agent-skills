# Recovered PR Pattern Examples

These are provenance examples explaining why the skill contains each requirement. Do not copy private/product-specific details into unrelated repositories.

## Bug fix + ticket + property discovery

A split-by-tags chart PR used the exact legacy ticket format and grew from two reported defects into four related fixes. Property testing generated `__proto__`, exposing a prototype-sensitive failure outside the original customer report.

**Lesson:** state exactly which issue is closed, surface additional fixes, and report defects discovered by stronger testing.

## Adjacent behavior + incidental behavior

A timeline drag-to-scrub PR became the canonical example for two questions: drag-to-scrub must not break existing click-to-seek on the same timeline, and an incidental video-presence behavior had to be disclosed. The recorded diff was 13 files, +317/−21.

**Lesson:** inspect the shared event/state surface and disclose bundled behavior.

## Performance evidence

A stream-picker rewrite replaced an oversized metadata path with lighter stream discovery, bounded fan-out, progressive rendering, and `latestOnly` value reads. Evidence included roughly 324k metadata rows / 29 MB / 11 s for one high-cardinality device, roughly 140 logical names actually needed, and a worst-path lookup reduced from roughly 11–16 s to about 0.5 s. It also had 188 local tests and a 100% mutation score for the tested scope; the tests were not CI-enforced because of tooling constraints.

**Lesson:** performance questions need real before/after data and precise claim boundaries.

## Rich testing body

One large testing PR reported 1,715 passing tests across 56 suites, 100% statement and branch coverage, and exact killed-mutant counts of 67/67, 225/225, and 52/52 for three focused areas. Mutation analysis also identified redundant/dead optional chains. That PR remained unmerged.

**Lesson:** test metrics and defects discovered are PR evidence; merge/adoption status is a separate claim.

## Equivalent-mutant accounting

A separate PR reported mutation scores below 100% and maintained an equivalent-mutant register explaining why individual survivors were behaviorally equivalent or tooling-constrained.

**Lesson:** classify survivors rather than writing artificial tests for a vanity score.

## Shared-consumer rollout

A shared-core PR contained an explicit `Embed / external rendering ⚠️ (rollout coordination)` section documenting that embedded rendering lived in another consumer repository.

**Lesson:** a library change is not fully reviewed until downstream consumption and rollout are understood.

## Staff-level solution review

A Python SDK compatibility PR prompted questions beyond correctness: whether code-generation assumptions were empirically verified, whether a duplicated tool pin should be centralized rather than guarded by tests, whether a dependency cap was a time bomb, whether the Python floor was stricter than required, and whether every changed compatibility path had meaningful CI coverage.

**Lesson:** ask whether the design prevents the class of problem and whether compatibility decisions are justified.
