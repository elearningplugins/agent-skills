#!/usr/bin/env bash
# Validate every skill under skills/*/SKILL.md.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fail=0

if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh is required for validation" >&2
  exit 1
fi

echo "==> gh skill publish --dry-run"
if ! gh skill publish --dry-run; then
  fail=1
fi

echo "==> skills-ref validate (each skill)"
if command -v npx >/dev/null 2>&1; then
  for skill_md in skills/*/SKILL.md; do
    dir="$(dirname "$skill_md")"
    echo "--- $dir"
    if ! npx --yes skills-ref validate "$dir"; then
      fail=1
    fi
  done
else
  echo "warn: npx not found; skipping skills-ref" >&2
fi

echo "==> referenced paths exist"
python3 - <<'PY'
import pathlib, re, sys
root = pathlib.Path("skills")
missing = []
# Paths like `scripts/foo.py` or `references/bar.md` — stop at whitespace.
pat = re.compile(r"`((?:scripts|references|assets)/[A-Za-z0-9_./-]+)`")
for skill_md in root.glob("*/SKILL.md"):
    skill_dir = skill_md.parent
    text = skill_md.read_text(encoding="utf-8")
    for rel in pat.findall(text):
        path = skill_dir / rel
        if not path.exists():
            missing.append(f"{skill_md}: missing {rel}")
if missing:
    print("\n".join(missing), file=sys.stderr)
    sys.exit(1)
print("ok: referenced scripts/references/assets paths exist")
PY

echo "==> scripts parse"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('skills/pr-quality/scripts/loc_breakdown.py').read_text())"
node --check skills/qa-unit-testing/scripts/mutation.mjs
echo "ok: scripts parse"

if [[ "$fail" -ne 0 ]]; then
  echo "validation failed" >&2
  exit 1
fi

echo "all skill validation checks passed"
