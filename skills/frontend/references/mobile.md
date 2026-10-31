# Mobile web behavior

Adapted from `emilkowalski/skills` at `a81dbca07f2217b7103e510c0f13f8d5b017afc9`, `skills/mobile-native/SKILL.md` (MIT). This is for mobile web/PWA behavior; it does not replace native iOS/Android guidance. Browser/device capability and the observed symptom determine the fix.

## 1. Locate the mobile symptom

Identify the target device, OS/browser, standalone or browser mode, orientation and input method. Read the affected CSS, viewport metadata and gesture handlers. On hardware, reproduce with the URL bar expanded/collapsed and the keyboard open; a desktop viewport alone cannot prove keyboard, safe-area, browser-chrome or touch behavior.

Done when: the symptom is tied to a real interaction and environment, or hardware reproduction is explicitly unavailable.

## 2. Apply only the matching remedy

| Symptom | Candidate remedy and boundary |
|---|---|
| Hover sticks after a tap | Gate pointer-hover effects with `@media (hover: hover) and (pointer: fine)`; preserve keyboard focus and touch press feedback. Check compiled Tailwind behavior before adding a duplicate rule. |
| Tap highlight conflicts with custom feedback | Remove it only on controls that already have visible pressed feedback; do not remove the only activation cue. |
| Bottom control hides behind browser chrome | Use `dvh` for an app shell tracking visible height and `svh` for a stable hero; respect the project's supported browsers. |
| Focusing an input zooms Safari | Check computed input font size; prefer at least 16 CSS px at mobile size. Keep pinch zoom available; never add `user-scalable=no` or `maximum-scale=1`. |
| Keyboard covers an action | Exercise focus, scrolling and viewport resize with the real keyboard; keep the action reachable without trapping the user in a fixed panel. |
| Content crosses a notch/home indicator | Where edge-to-edge layout is intended, use `viewport-fit=cover` and the appropriate `env(safe-area-inset-*)` padding. Check orientation changes. |
| Drag fights page scrolling | Choose `touch-action` for the gesture surface: a horizontal drag often leaves vertical page panning enabled with `pan-y`. Preserve pinch zoom and normal scrolling outside it. |
| Nested scrolling chains unexpectedly | Use targeted `overscroll-behavior` after reproduction; do not globally disable browser gestures or pull-to-refresh by habit. |
| Long press selects a control's text | Scope `user-select: none` to the control, not readable content or editable fields. |
| Tap feels delayed | Inspect event handlers and expensive work first; use immediate pressed feedback and a suitable `touch-action`, while keeping zoom and intended gestures. |
| Browser chrome mismatches the theme | Verify supported `theme-color` metadata in light/dark and standalone/browser modes. |

Use CSS capabilities rather than user-agent sniffing or screen-width guesses about touch. A touchscreen can have a mouse; a narrow window can use a keyboard. Preserve the current component primitives and accessibility semantics.

Done when: each change fixes a reproduced symptom, leaves zoom/scroll/selection usable, and introduces no unrelated global reset.

## 3. Verify on hardware

Run the affected flow through `qa` on the real target using Safari Web Inspector, Chrome remote debugging, or the available device tooling. Cover tap, long press, drag, keyboard open/close, orientation, scrolling and reduced motion when relevant. Include the hybrid keyboard/mouse path when the product supports it.

Report `device: <model> <OS/browser> <mode> "<interaction>" result=pass|fail` with evidence. Report desktop responsive/emulated checks separately. If hardware is unavailable, record `mobile hardware unverified: <missing device/access>` and keep the successful code/emulation checks as limited evidence.

Done when: hardware-specific claims have hardware evidence, and untested platform behavior is clearly separated from measured results.
