# REST details

## Resources & methods
Nouns, plural collections (`/orders`, `/orders/{id}`). Nesting ≤2 levels; deep relations → top-level resource + filter. Non-CRUD actions → command sub-resource (`POST /orders/{id}/cancel`). Methods: GET (safe), POST (create/non-idempotent), PUT (full replace, idempotent), PATCH (partial — JSON Merge Patch RFC 7386 or JSON Patch RFC 6902), DELETE (idempotent).

## Status codes
200, 201 (+`Location`), 202 (async), 204, 206. 301/308. 400 (malformed), 401 (unauthenticated), 403 (forbidden), 404, 405, 409 (conflict), 412 (precondition failed), 415, 422 (semantic validation), 428 (precondition required), 429 (+`Retry-After`), 500, 503 (+`Retry-After`). Never 200-with-error-body.

## Pagination
Prefer **cursor/keyset** (`?limit=&cursor=<opaque>`) — stable across inserts/deletes, O(1) deep. Offset drifts and is O(n) deep. Return `next`/`prev` cursors or a `Link` header (RFC 8288) `rel="next"`, or a `{data, next_cursor}` envelope. Always cap `limit`.

## Filtering/sorting
`?status=open&sort=-created_at,name` (leading `-` = desc), explicit operators (`?price[gte]=10`). Document allowed fields; reject unknown ones.

## HATEOAS reality
Full hypermedia is rarely adopted; most APIs are Richardson Level 2. Pragmatic: include `Link` headers / `next` cursors and resource URLs, skip a hypermedia control vocabulary clients won't use.
