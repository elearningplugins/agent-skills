# Repository principles

Skills in this repository encode engineering practices Brian has used in real production environments.

A skill must be:

1. **Evidence driven** — claims require commands, measurements, or explicit “not measured.”
2. **Specific enough to execute** — an agent can follow the steps without inventing ceremony.
3. **Tool agnostic where practical** — prefer portable methods; name tools only when required.
4. **Clear about when not to use it** — activation boundaries matter as much as activation.
5. **Verifiable** — success conditions can be checked, not merely asserted.
6. **Focused on behavior rather than ceremony** — prefer outcomes over templates for their own sake.
7. **Honest about uncertainty** — distinguish observed, measured, inferred, proposed, and unknown.
8. **Designed for progressive disclosure** — keep `SKILL.md` focused; put detail in `references/`, `scripts/`, and `assets/`.

## Before changing a skill

1. Read its `SKILL.md` and any referenced files you will touch.
2. Run `bash scripts/validate-skills.sh`.
3. Read relevant eval trigger cases under `evals/<skill>/`.
4. Prefer moving detail into `references/` over growing `SKILL.md` past ~500 lines.
5. Do not add employer-specific process, ticket formats, or product names to portable skills.

## Accuracy beats consistency

If new evidence disproves an earlier conclusion in a skill, change the conclusion. Do not preserve a wrong claim to keep docs consistent.
