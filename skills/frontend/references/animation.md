# Animation

UI motion rules, distilled from Emil Kowalski's design-engineering skills (emilkowalski/skills, MIT), updated against a81dbca07f2217b7103e510c0f13f8d5b017afc9, `skills/review-animations/STANDARDS.md`. Load this when a change adds or fixes application animation. The frontend parity rules still win on an existing surface. Use [motion review](motion-review.md) for review/audit and [motion performance](motion-performance.md) for measured stutter.

## Should it animate at all?

Animate by how often the action happens, not by how it looks:

| Frequency | Example | Motion |
|---|---|---|
| Very frequent (100+/day) | keyboard shortcuts, typing | none |
| Frequent (tens/day) | hover, list nav | none or barely any |
| Occasional | modal, drawer, toast | standard |
| Rare | onboarding, celebration | room for delight |

Keyboard-initiated actions never animate — they must feel instant. "It looks cool" is not a reason to animate a frequent action. A valid purpose is spatial continuity, state indication, press feedback, or softening an abrupt appear/disappear.

## Easing — the most common mistake

**Never use `ease-in` for UI.** It delays the first movement and feels sluggish.

| Motion | Easing |
|---|---|
| Entering or exiting | `ease-out` |
| Moving / morphing on screen | `ease-in-out` |
| Hover, color change | `ease` |
| Constant motion (marquee, progress) | `linear` |
| Unsure | `ease-out` |

Reuse the product's easing token first. When no suitable token exists, upstream reference curves are `cubic-bezier(0.23, 1, 0.32, 1)` for a strong ease-out, `cubic-bezier(0.77, 0, 0.175, 1)` for on-screen movement and `cubic-bezier(0.32, 0.72, 0, 1)` for a drawer. Choose by the action, not at random. Make the **exit faster than the enter**. Where the user is deciding (hold-to-delete), make the press slow and the release snappy.

## Duration

Keep UI animations **under 300ms**. Faster reads as faster product.

- Button press: 100–160ms
- Tooltip / small popover: 125–200ms
- Dropdown / select: 150–250ms
- Modal / drawer: 200–300ms by default; a longer 300–500ms physical transition needs a product-specific reason and interaction testing
- Marketing / explanatory: can be longer

## Properties — performance

- Prefer **`transform` and `opacity`**. Animating layout properties such as `width`, `height`, `top` and `left` can trigger layout and paint; require a measured reason when cheaper properties cannot preserve the intended effect.
- Avoid `transition: all` — name the exact properties.
- Don't update CSS variables on a parent during animation (recalcs every child); set `transform` directly.
- Check the installed Motion version and rendered animation path before diagnosing shorthands. If a trace shows main-thread updates during load, compare full `transform` strings, CSS or WAAPI; property names alone do not prove acceleration or dropped frames.
- Keep animated `blur` under ~20px (heavy blur is costly, worst in Safari).
- Virtualize long animated lists.
- Add `will-change: transform` only after you observe a 1px shift when motion starts — not pre-emptively.
- Write to `ref.current.style` instead of React state to avoid re-renders mid-animation.
- Prefer CSS for simple predetermined motion and the existing motion library or WAAPI for dynamic controls. Confirm smoothness under the load where the user sees the issue.

## Component patterns

- **Buttons:** scale to `0.95–0.98` on `:active` for instant feedback.
- **Entry:** never from `scale(0)`; start near `0.9–0.95` with `opacity: 0`.
- **Popovers:** `transform-origin` at the trigger, not center. Modals stay centered.
- **Tooltips:** delay the first, then open adjacent ones instantly.
- **Transitions over keyframes** for rapidly re-triggered UI — transitions interrupt and retarget; keyframes restart from zero.
- **Entry styling:** `@starting-style` where supported; else a mounted-state attribute pattern.
- Use percentage translates (`translateY(100%)`) so motion scales with the element.
- Stagger list items by 30–80ms; never block interaction while a stagger plays.

## Springs

Use for drag with momentum, interruptible gestures, decorative tracking — not for serious functional UI. Springs keep velocity when interrupted; keyframes restart. Keep bounce subtle (~0.1–0.3), and out of most UI.

For gesture-driven motion, reverse direction mid-flight and release at different speeds. Preserve the current position and velocity instead of resetting to the first frame; dismissal should account for velocity as well as distance. Keep pointer capture and cancellation behavior intact.

## Accessibility

- Under `prefers-reduced-motion`, cut movement but keep helpful opacity/color changes.
- Gate hover effects behind `@media (hover: hover) and (pointer: fine)` so taps don't trigger false hovers.

## Review checklist

| Smell | Fix |
|---|---|
| `transition: all` | name exact properties |
| `scale(0)` entry | start ~0.95 + `opacity: 0` |
| `ease-in` on UI | `ease-out` or custom curve |
| center origin on popover | origin at the trigger (modals excepted) |
| animation on keyboard action | remove it |
| >300ms on a UI element | reduce to 150–250ms |
| unguarded hover animation | add the hover/pointer media query |
| same enter and exit speed | make exit faster |
| all list items at once | stagger 30–80ms |
| animating `width`/`top`/layout props | compare a `transform`/`opacity` equivalent and profile the necessary exception |
