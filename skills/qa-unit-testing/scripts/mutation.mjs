// Mutate a single file (pass path as arg) or all locally changed source files.
// Usage: npm run test:mutation:file -- src/path/file.ts
// Usage: npm run test:mutation:changes
import { execSync } from "child_process";

const file = process.argv[2];
let mutateArg;

if (file) {
  mutateArg = file;
} else {
  const changed = execSync("git diff --name-only HEAD", { encoding: "utf8" })
    .split("\n")
    .concat(
      execSync("git diff --cached --name-only", { encoding: "utf8" }).split("\n"),
    )
    .filter((f) => f.match(/\.tsx?$/) && !f.match(/\.test\.tsx?$/))
    .filter(Boolean);

  const unique = [...new Set(changed)];

  if (unique.length === 0) {
    console.log(
      "No changed source files found. Use npm run test:mutation for the default scope.",
    );
    process.exit(0);
  }

  console.log(
    `Mutating ${unique.length} file(s):\n${unique.map((f) => `  ${f}`).join("\n")}\n`,
  );
  mutateArg = unique.join(",");
}

execSync(`npx stryker run --mutate "${mutateArg}"`, { stdio: "inherit" });
