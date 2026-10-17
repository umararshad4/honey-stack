# Frontend performance

Read for slow pages, bundle growth, render cost, image loading, caching or runtime choices. Distilled from MCT `performance-audit`. The measure-first loop lives in the `debug` skill's perf branch; this file lists where frontend time usually goes.

## Start from a number

Name the symptom (slow first load, janky scroll, laggy input, big bundle) and measure it before changing anything. Size the tooling to the change: a one-line style edit needs no profiler.

| Question | Tool |
|---|---|
| Page load, Core Web Vitals | Lighthouse (Chrome DevTools MCP `lighthouse_audit`, or `npx -y lighthouse <url> --view`) |
| What blocks the main thread | A DevTools performance trace (Chrome DevTools MCP `performance_start_trace`) |
| Which components rerender | React DevTools Profiler, "Highlight updates when components render" |
| What's in the bundle | `@next/bundle-analyzer`, `npx -y vite-bundle-visualizer`, or `source-map-explorer` on the build output |

Targets at the 75th percentile: LCP 2.5 s or less, INP 200 ms or less, CLS 0.1 or less.

## Where the time goes

**Client JavaScript**
- Client components that don't need to be (Next.js). Move `"use client"` down to the interactive leaf.
- A new dependency. Check its size before adding it; prefer what the repo or platform already has.
- Heavy UI that isn't visible at load (charts, editors, modals, maps): load it with `next/dynamic` or `React.lazy`.

**Rendering**
- Rerenders from broad context or a parent's state. Split the context or move the state down.
- Expensive work in render. Move it out, cache it, or memoize it once measured.
- Long lists. Virtualize past a few hundred rows if the repo has a virtualization library.

**Images and fonts**
- Serve images at display size in a modern format, with `width` and `height` set so they don't shift layout.
- `loading="lazy"` below the fold. Prioritize only the LCP image.
- Self-host or use `next/font`; `font-display: swap` for custom fonts.

**Network and caching**
- Request waterfalls: parent fetches, then child fetches. Fetch in parallel or higher up.
- Missing cache or revalidation on data that rarely changes. Over-caching on data that must be fresh.
- Runtime choice: edge for latency-sensitive reads near users, Node for heavy work and full library support.

## Report

Baseline, after, delta, the tool that measured each, and what limits the number now.
