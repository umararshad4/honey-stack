# Next.js App Router

Read when a change touches routes, layouts, server or client components, metadata, `loading`/`error`/`not-found` files, route handlers, server actions, caching or data fetching. Distilled from MCT `nextjs-app-router` and `frontend-architecture`.

## Check the version first

Read `next` in `package.json`. Defaults moved between majors, so read the installed version's docs (the `opensrc` skill, or `node_modules/next/dist/docs` when present) before relying on caching behavior.

- Next 15: `params`, `searchParams`, `cookies()` and `headers()` are async, so await them. `fetch` and `GET` route handlers are no longer cached by default.
- Next 16: `proxy.ts` replaces `middleware.ts`, and Cache Components (`"use cache"`) is the explicit caching model when enabled.
- `pages/` router projects follow their own conventions. Don't mix in App Router patterns.

## Server and client boundary

- Components are server components unless a file says `"use client"`. Keep it that way unless the component needs state, effects, event handlers or browser APIs.
- Put `"use client"` on the smallest leaf. A client layout drags its whole subtree into the bundle.
- Pass server-rendered content into client components as `children` instead of importing server code into them.
- Props that cross into a client component must be serializable. Functions can't cross, except server actions.
- Modules that hold secrets or DB access start with `import "server-only"` so a client import fails the build.
- Only `NEXT_PUBLIC_*` env vars reach the browser. Secrets never get that prefix.
- No `window`, `document` or `localStorage` in server components.

## Data fetching and caching

- Fetch in the server component that uses the data. Run independent fetches in parallel with `Promise.all` to avoid waterfalls.
- Deduplicate non-`fetch` data access across a render with `React.cache`.
- Make caching explicit at each fetch: `export const revalidate = <s>`, `fetch(url, { next: { revalidate, tags } })`, `cache: "no-store"`, or `"use cache"` where Cache Components is on.
- After a mutation, call `revalidatePath` or `revalidateTag` for every view that shows the changed data.

## Server actions and route handlers

- A server action is a public POST endpoint. Authenticate, authorize and validate input inside every action, not only in the page that renders the form (see the `security` skill).
- Route handlers live in `route.ts`. Return proper status codes and typed JSON.

## Route files

- `loading.tsx` wraps the segment in Suspense. Add one where the data wait is visible to the user.
- `error.tsx` must be a client component. It receives `error` and `reset`. `global-error.tsx` covers the root layout.
- `not-found.tsx` pairs with `notFound()` from `next/navigation`.
- Add these files where they improve behavior, not to every segment.

## Metadata, links, images, fonts

- Export `metadata` or `generateMetadata` from server files only.
- Internal navigation uses `next/link`.
- `next/image` needs `width` and `height`, or `fill` with `sizes`. Prioritize only the LCP image.
- Load fonts with `next/font` to avoid layout shift and external requests.

## Hydration

- Output that differs between server and client (`Date.now()`, `Math.random()`, locale formatting, `window` checks in render) causes hydration errors. Move it into an effect or a client-only component.
- `suppressHydrationWarning` is for one unavoidable node, such as a timestamp. It doesn't fix a mismatch in a subtree.
- "Hydration failed" or "Text content did not match" in the console is a bug, even when the page looks right.

## Verify

Typecheck any route, params or data change. Exercise the route through the `qa` skill, clicking client-side links rather than only loading URLs, because client navigation catches routing bugs a full load hides.
