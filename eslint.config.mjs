import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

export default defineConfig([
  ...nextVitals,
  ...nextTypescript,
  {
    files: ["**/*.{js,mjs,ts,tsx}"],
    settings: { next: { rootDir: "apps/web/" } },
    rules: { "no-debugger": "error" },
  },
  {
    files: ["infra/local/mongo-init.js"],
    // mongosh bootstrap uses its CommonJS filesystem bridge.
    rules: { "@typescript-eslint/no-require-imports": "off" },
  },
  globalIgnores([
    "**/node_modules/**",
    "**/.next/**",
    "**/dist/**",
    "**/.venv/**",
    "apps/web/next-env.d.ts",
    "packages/contracts/src/generated.ts",
  ]),
]);
