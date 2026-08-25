# Contributing

This repository is **source-available**. Pull requests from outside collaborators are not accepted (GitHub PR creation is restricted to collaborators).

If you maintain a fork or want to propose a skill idea via Issues:

## What makes a good skill here

A skill should:

- solve a **repeated** engineering problem
- come from an **actual workflow** or repeated failure mode
- have clear **activation** and **non-activation** conditions
- define a **verifiable** completion condition
- avoid duplicating an existing skill
- keep `SKILL.md` focused; put depth in `references/`
- include positive and negative **trigger evals** under `evals/<skill>/`

Skills should be specific, verifiable, battle-tested, and minimal.

## Validation

```bash
bash scripts/validate-skills.sh
```

## License

Contributions, if ever accepted from a collaborator, are under the MIT License (see `LICENSE`).
