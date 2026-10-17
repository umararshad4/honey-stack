# Micro-frontends

**First: are they worth it?** MFEs solve an org/deploy problem (multiple teams needing independent deploy cadence), not code-splitting. Costs: shared-dep version skew, runtime integration bugs invisible at build time, duplicated vendor code, harder E2E. Default to a **modular monolith** until multiple teams genuinely can't share one release pipeline.

## Options
- **Module Federation 2** (`@module-federation/enhanced`) — runtime-independent of webpack; Webpack 5 and Rspack; federation runtime + TypeScript type sharing. `@module-federation/vite` for Vite.
- **Rspack** — Rust, webpack-compatible, much faster, first-class MF.
- **Native Federation** — browser-native ESM + import maps, bundler-agnostic, more future-proof.
- **single-spa** — runtime orchestration of independently-built apps (can mix frameworks), composition at the router.
- `@originjs/vite-plugin-federation` — community Vite MF; fine for simple cases.

## The #1 bug: shared-dep skew
Mark framework libs as `shared` with `singleton: true` + `requiredVersion`. Two React copies → invalid-hook-call crash at runtime. Pin shared versions centrally. Host owns the shell + top-level router; remotes expose mounted components. Avoid shared global state — use events or a thin contract.

**Pitfalls:** `singleton` not set on React → crash; host/remote drifting on a shared major; no design-system versioning → visual drift; using MFEs to split code (that's just a library) rather than teams/deploys.
