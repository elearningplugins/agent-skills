#!/usr/bin/env python3
"""Generate a draft Markdown LOC breakdown for a git diff."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

TEST_MARKERS = ("/tests/", "/test/", "/__tests__/", "/spec/")
TEST_SUFFIXES = (
    ".test.ts", ".test.tsx", ".test.js", ".test.jsx",
    ".spec.ts", ".spec.tsx", ".spec.js", ".spec.jsx",
    "_test.py", "_test.go",
)
CONFIG_NAMES = {
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "tsconfig.json", "jest.config.js", "jest.config.ts", "jest.config.json",
    "vitest.config.js", "vitest.config.ts", "stryker.config.mjs",
    "eslint.config.js", "eslint.config.mjs", ".eslintrc", ".eslintrc.json",
    ".prettierrc", ".prettierrc.json", "pyproject.toml", "go.mod", "go.sum",
    "Cargo.toml", "Cargo.lock", "Dockerfile", "Makefile",
}
CONFIG_PARTS = ("/.github/workflows/", "/config/")


def git(*args: str) -> str:
    proc = subprocess.run(["git", *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        print(proc.stderr.strip(), file=sys.stderr)
        raise SystemExit(proc.returncode)
    return proc.stdout


def classify(path: str) -> str:
    normalized = "/" + path.replace("\\", "/").lower()
    name = Path(path).name
    lower_name = name.lower()
    if any(marker in normalized for marker in TEST_MARKERS):
        return "Tests"
    if any(lower_name.endswith(suffix) for suffix in TEST_SUFFIXES):
        return "Tests"
    if name in CONFIG_NAMES or any(part in normalized for part in CONFIG_PARTS):
        return "Fix (config)"
    if lower_name.startswith(("eslint.", "prettier.", "jest.", "vitest.", "stryker.")):
        return "Fix (config)"
    if lower_name.endswith((".yml", ".yaml", ".toml")):
        return "Fix (config)"
    return "Fix"


def parse_numstat(base: str):
    output = git("diff", "--numstat", f"{base}...HEAD")
    rows = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        rows.append((classify(path), path, added, deleted))
    return rows


def display_count(value: str) -> str:
    return value if value != "-" else "binary"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/main", help="Git base ref, e.g. origin/main or origin/develop")
    args = parser.parse_args()

    rows = parse_numstat(args.base)
    if not rows:
        print(f"No diff found for {args.base}...HEAD", file=sys.stderr)
        raise SystemExit(1)

    order = ["Fix", "Fix (config)", "Tests"]
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[0]].append(row)

    total_add = total_del = 0
    production_add = production_del = 0

    print("| Category | File | + | − |")
    print("|---|---|---:|---:|")

    for category in order:
        category_rows = grouped.get(category, [])
        if not category_rows:
            continue

        sub_add = sub_del = 0
        has_binary = False
        for _, path, added, deleted in category_rows:
            print(f"| {category} | `{path}` | {display_count(added)} | {display_count(deleted)} |")
            if added == "-" or deleted == "-":
                has_binary = True
                continue
            a, d = int(added), int(deleted)
            sub_add += a
            sub_del += d
            total_add += a
            total_del += d
            if category == "Fix":
                production_add += a
                production_del += d

        suffix = "+binary" if has_binary else ""
        print(f"| **{category} subtotal** | | **{sub_add}{suffix}** | **{sub_del}{suffix}** |")

    print(f"| **Total** | | **{total_add}** | **{total_del}** |")
    net = production_add - production_del
    sign = "+" if net >= 0 else ""
    print()
    print(f"Net production change: **{sign}{net} lines**.")
    print()
    print("> Draft classification only: review each file before using this table in a PR.")


if __name__ == "__main__":
    main()
