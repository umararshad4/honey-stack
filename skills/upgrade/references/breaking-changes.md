# Breaking changes, codemods & EOL

## Semver reality
Minors/patches can still break. Pin-and-test critical deps; don't auto-trust ranges for anything that matters.

## Codemods
Use the framework's official codemod (jscodeshift-based) for mechanical changes; it handles rote rewrites but **misses** peer-dep conflicts and library-level usage, so still run the full suite.
- **React 19:** bridge via 18.3.1 first (surfaces deprecation warnings) → `npx codemod@latest react/19/migration-recipe` + `npx types-react-codemod@latest preset-19 ./src`. Handles `ReactDOM.render`→`createRoot`, string refs, `propTypes`/`defaultProps` on function components, legacy Context.
- **Next.js:** `npx @next/codemod@latest upgrade latest` (needs Next 15+ for React 19).
Upgrade on a branch and bump adjacent peers together (React + types + testing-library + Next).

## Runtime EOL
EOL runtimes get no security patches. **Node:** 18 EOL Apr 2025, 20 EOL Apr 2026 → target 22 (EOL Apr 2027) or 24 (EOL Apr 2028); even-numbered releases get LTS. **Python:** ~5-year support; 3.13 current, move off 3.9. Upgrade off EOL for the security feed alone.
