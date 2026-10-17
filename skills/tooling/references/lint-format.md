# Lint / format / typecheck

## Biome 2 (new standard projects) — `biome.json`
```json
{
  "$schema": "https://biomejs.dev/schemas/2.0.0/schema.json",
  "formatter": { "enabled": true, "indentStyle": "space", "lineWidth": 100 },
  "linter": { "enabled": true, "rules": { "recommended": true } },
  "javascript": { "formatter": { "quoteStyle": "single" } }
}
```
`pnpm add -D @biomejs/biome && pnpm exec biome init`. Scripts: `"lint": "biome check .", "format": "biome format --write ."`. One fast Rust binary for lint+format, type-aware without `tsc`, multi-language. **Still use ESLint** when you need plugins Biome lacks (`eslint-plugin-import` resolution, Vue/Angular/Storybook/testing-library plugins, many custom rules). Never run both on the same files.

## ESLint 10 flat config — `eslint.config.js`
```js
import js from "@eslint/js";
import tseslint from "typescript-eslint";
export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  { languageOptions: { parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname } } },
  { ignores: ["dist/**", "**/*.config.*"] }
);
```
`pnpm add -D eslint @eslint/js typescript-eslint`. Type-aware rules need `projectService: true` (easy to miss → rules silently don't fire). Flat config has no nested per-dir files — one root file with `files`/`ignores` globs. Add Prettier via `.prettierrc.json` + `eslint-config-prettier` (never run Prettier rules through ESLint).

## Ruff (Python) — `pyproject.toml`
```toml
[tool.ruff]
line-length = 100
target-version = "py312"
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]   # pycodestyle, pyflakes, isort, pyupgrade, bugbear
[tool.ruff.format]
quote-style = "double"
```
`uv add --dev ruff` (or `pip install ruff`); `ruff check --fix .` and `ruff format .`. Replaces flake8+black+isort+pyupgrade. Don't enable `E501` while using `ruff format`.
