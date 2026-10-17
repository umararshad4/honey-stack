# Schema-first contracts

## OpenAPI
3.1.0 aligns the Schema Object to JSON Schema Draft 2020-12 (the big 3.0→3.1 win) — safe default. 3.2.0 (Sept 2025) adds `QUERY`, explicit SSE/streaming media types, `additionalOperations`, but tooling is uneven. Design-first: write the spec, generate stubs/clients/validators/docs/mocks. Tools: `redocly lint`, `spectral lint`, `openapi-generator`, `oapi-codegen` (Go), Prism (mock), Schemathesis (property/contract testing).

## gRPC / protobuf evolution
Fields match by **tag number**, not name. Never change or reuse a tag; `reserved 4, 7; reserved "old_field";` tombstones removed tags/names. Adding fields is safe (unknown fields preserved). Don't change a field's type. Prefer `optional`/wrappers over proto3 default-zero ambiguity. Enums keep a `0` = `UNSPECIFIED`; never renumber.

## GraphQL schema
Default fields nullable; non-null (`!`) only when truly guaranteed (a non-null field that errors nulls its whole parent). **Relay Connections** for pagination (`edges { node cursor } pageInfo { hasNextPage endCursor }`). **DataLoader** to batch/cache per-request and kill N+1. Mitigate abuse with depth limits, complexity/cost analysis, persisted queries. Mutations: single input object → payload type with the entity + `userErrors`.

## JSON Schema
2020-12 for request/response validation independent of OpenAPI; share `$defs`, use `$ref`.
