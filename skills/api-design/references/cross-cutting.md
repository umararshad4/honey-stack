# Cross-cutting

**Auth:** OAuth 2.0 / OIDC for user auth (auth-code + PKCE for apps, client-credentials for machine-to-machine). API keys only for low-risk server-side identity (rotate, scope, never in URLs). **JWT pitfalls:** validate `alg` (reject `none`, pin expected algs), verify `iss`/`aud`/`exp`, short TTLs + refresh, can't easily revoke (keep short-lived or a denylist), no secrets/PII in the readable payload, prefer asymmetric (RS/ES) with JWKS rotation.

**Rate limiting:** 429 + `Retry-After` (seconds or HTTP-date) + `RateLimit`/`RateLimit-Policy` headers (IETF draft, formerly `X-RateLimit-*`). Token-bucket or sliding-window, per key/user/IP.

**CORS:** echo specific origins (avoid `*` with credentials); handle preflight `OPTIONS`; set `Allow-Methods/Headers`, `Max-Age`.

**Validation:** validate/normalize every input at the edge against the schema; decide and document whether unknown fields are rejected or ignored.

**Timestamps:** ISO-8601 / RFC 3339 in UTC with `Z` (`2026-10-18T14:30:00Z`). Store UTC; clients localize.

**Money/decimal:** never floats — integer minor units (cents) or decimal string `"19.99"` + explicit ISO-4217 `currency`. Document rounding.
