# Motion performance

Adapted from `emilkowalski/skills` at `a81dbca07f2217b7103e510c0f13f8d5b017afc9`, `skills/animation-performance/SKILL.md` (MIT). Use for stutter, frame drops, or a motion performance review. Choose motion behavior with [animation](animation.md); this branch measures whether the chosen behavior completes frames on time.

## 1. Reproduce the load

Name the element, trigger, device/browser, refresh rate, build mode and content size. Record the interaction with the browser performance tools under the load where it fails: navigation, hydration, network completion, a long list or repeated dragging. Keep the same workload for before and after. A 60 Hz display has roughly 16.7 ms between frames; 120 Hz has roughly 8.3 ms. That interval is shared by the browser, not a budget for JavaScript alone.

Inspect the recording for long tasks, dropped frames, style recalculation, layout, paint and compositing. CPU throttling can expose a busy main thread but does not reproduce a phone's GPU or memory constraints. Use a representative real phone for a phone-performance claim; record unavailable hardware as a limit.

Done when: the stutter is captured with its environment, or the report states exactly which reproduction or measurement is unavailable.

## 2. Follow the work, not the API name

| Suspect | How to distinguish it | Cheapest candidate fix |
|---|---|---|
| Layout/paint each frame | Trace shows layout or expensive paint during the animation | Compare an equivalent transform/opacity effect; retain necessary layout motion only with a measured reason |
| Busy main thread | Drops coincide with hydration, data work or scripts | Use CSS/WAAPI for a simple effect, or move unrelated work out of the interaction |
| React work per frame | Profiler shows renders from pointer/scroll/rAF state updates | Use the library's motion values or a ref for transient values; keep committed application state in React |
| Inherited CSS custom property | Style recalculation grows with descendant count | Write the transform on the moving element; compare the same list size |
| Motion shorthand path | Actual library/version and trace show main-thread work | Compare full transform strings or a supported accelerated path; do not assume all versions behave alike |
| Filters and large layers | Paint/composite cost grows with blur or surface area | Reduce blur/area; test Safari as well as Chromium when supported |
| Too many animated nodes | Cost grows with simultaneous elements | Limit active nodes or reuse the project's virtualization |

Do not claim that `transform` guarantees compositing or that JavaScript guarantees jank. A library may supply necessary gesture, spring or layout behavior. Preserve that behavior while profiling the actual rendering path. Add `will-change` only when a recording shows a promotion/paint problem it solves; remove it when it does not, since layers consume memory.

Done when: one measured cause explains the affected frames, or remaining causes are explicitly hypotheses with a next measurement.

## 3. Compare and report

Re-run the same interaction and realistic content load after an authorized fix. Use the `perf` benchmark discipline for repeatable comparisons. Also reverse/retrigger the motion, exercise reduced motion, and check focus/state through `qa`; a smooth effect that loses the interaction is a regression.

Report element and source location, environment, observed cause, before/after trace measurements, behavior preserved, and recording paths. If only source inspection was possible, report `source-only risk; frame behavior unverified`, not “fixed at 60 fps.”

Done when: each performance claim is backed by recorded frames under comparable conditions and any untested device remains named.
