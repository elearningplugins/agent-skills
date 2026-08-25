# Skill design principles

These principles govern how skills in this repository are written and revised.

## Evidence over confidence

Do not say something works because the implementation looks reasonable.

Run it. Measure it. Inspect the output. Show the evidence. If it was not measured, say so.

## Test behavior, not lines

Coverage shows code ran. It does not prove assertions catch defects.

Prefer tests that exercise important behavior, edge cases, and failure modes. Combine example tests, property-based tests, and mutation analysis when they answer different questions.

## Review the solution, not the diff

Correctness is necessary and insufficient. Ask whether the approach is the right solution: blast radius, complexity, existing abstractions, downstream consumers, failure modes, rollback, and whether a smaller design exists.

## Production is part of development

Deployment behavior, logs, telemetry, customer reports, performance, and operational failures feed back into implementation and tests. Shipping is not the end of the loop.

## Measure before optimizing

Establish a baseline. Change one thing. Measure again. A plausible optimization is not a demonstrated improvement.

## Make failure visible

A test that cannot fail CI is not a gate. Quality systems should make failures hard to ignore and easy to investigate.

## Automate repeatable judgment

Useful automation captures a decision process: inspect, gather evidence, identify risk, run the right checks, analyze failures, communicate results. Skills encode that process for agents.

## AI amplifies engineering judgment

AI makes verification more important, not less. The useful question is whether the agent has enough context, constraints, tools, and feedback that the result can be trusted.

## Preserve uncertainty

Agents and skill authors should distinguish:

| Label | Meaning |
| --- | --- |
| Observed | Directly seen in code, UI, logs, or output |
| Measured | Quantified with a stated method and conditions |
| Inferred | Reasonable conclusion from evidence, not proven |
| Proposed | Suggested change or hypothesis |
| Unknown | Not yet investigated; do not invent |

Do not upgrade Unknown or Inferred to Observed without new evidence.

## Accuracy beats consistency

If new evidence disproves an earlier conclusion, change the conclusion. Consistency with a wrong prior claim is not a virtue.

## Progressive disclosure

Keep `SKILL.md` under ~500 lines when practical. Put durable detail in `references/`, executable helpers in `scripts/`, and templates in `assets/`. Agents should load depth only when the task needs it.

## Portability

Do not encode one employer’s ticket tracker, product names, or internal process as if they were universal. Use repository conventions. Keep provenance examples anonymized.
