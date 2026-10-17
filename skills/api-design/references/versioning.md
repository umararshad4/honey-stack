# Versioning & evolution

**Schemes:** URL path `/v1/...` (common, cache/visibility-friendly, blunt); custom header (`API-Version: 2025-10-01`); media-type (`Accept: application/vnd.acme.v2+json`). Date-based versions pin per-key behavior cleanly (Stripe-style).

**Expand–contract:** within a version, only **additive** changes — add optional fields/endpoints; never remove, rename, or retype an existing field; never tighten validation or change a default. Expand (add new) → migrate clients → contract (remove old) only across a major version.

**Deprecation:** advertise with the `Deprecation` header (RFC 9745) and `Sunset` header (RFC 8594, HTTP-date of removal); link migration docs via `Link; rel="deprecation"`. Give a published window (commonly 6–12 months) and log/alert on deprecated-path usage before removing.
