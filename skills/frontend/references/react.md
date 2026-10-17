# React

Read when a change touches components, hooks, state, effects, context, forms or client data fetching. Distilled from MCT `react-quality`, `react-doctor` and `frontend-architecture`.

## State

- Put state at the lowest component that needs it. Lift it only when siblings share it.
- Compute derived values during render. Storing them in state and syncing with an effect causes an extra render and stale frames.
- Reset state on an identity change with `key={id}`, not an effect that watches the prop.
- Use stable ids as list keys. An index key breaks state and focus when items reorder or get removed.

## Effects

Effects synchronize with something outside React: subscriptions, timers, DOM APIs, non-React widgets.

- Logic that responds to a user action goes in the event handler, not in an effect that watches state.
- Every subscription, listener and timer has a cleanup.
- A fetch in an effect needs an `AbortController` or an ignore flag, or a slow response overwrites a newer one. Prefer the repo's data layer (TanStack Query, SWR, server components) over hand-rolled effect fetching.
- A dependency array tells the truth. Suppressing `react-hooks/exhaustive-deps` hides a stale-closure bug.

## Memoization

- `useMemo`, `useCallback` and `memo` earn their place when there's a measured cost or when a memoized child or dependency array needs referential stability.
- If the repo runs the React Compiler (`babel-plugin-react-compiler`, `reactCompiler: true` in Next config), skip manual memoization. The compiler handles it.

## Context

- A frequently changing value in a broad context rerenders every consumer. Split fast-changing values from stable ones, or use the store the repo already has (Zustand, Redux, `useSyncExternalStore`) with selectors.
- Memoize the provider `value` object when the provider itself rerenders often.

## Composition

- Pass `children` or slot props before reaching for context to avoid prop drilling.
- Keep presentational components free of data fetching so they can be tested and reused.

## Forms

- Follow the repo's form library (react-hook-form, Formik, native `FormData` with server actions) and its schema library (zod, valibot, yup).
- Client validation is for feedback. The server validates again because the client can be bypassed (see the `security` skill).
- Show field errors next to the field, tie them with `aria-describedby`, and move focus to the first invalid field on submit.

## Types and modules

- Explicit prop types at module boundaries. No `any` in props.
- Type API responses at the client boundary instead of passing raw `res.json()` through the tree.
- Follow the repo's export style. Add barrel files only where the repo already uses them.

## React 19, when installed

Check `react` in `package.json` first.

- `ref` is a regular prop on function components; `forwardRef` is no longer needed.
- Form actions: `useActionState`, `useOptimistic`, and `useFormStatus` from `react-dom`.
- `use()` reads a promise or context, including conditionally.

## React Doctor

- After a change: `npx -y react-doctor@latest . --verbose --diff`. A score regression blocks done.
- Cleanup or audit work only: `npx -y react-doctor@latest . --verbose` for a full scan. Fix errors first, then warnings. Keep broad cleanup out of unrelated feature work.
- Report the score and whether it regressed, what was fixed, what was left for later and why, and the exact error if the command failed.
