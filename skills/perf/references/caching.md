# Caching

**Layers (cheapest/closest first):** CDN/edge → HTTP cache headers (`Cache-Control`, `ETag`/`If-None-Match`, `stale-while-revalidate`) → in-process LRU (bounded) → distributed (Redis/memcached) → DB (materialized views, buffer cache). Push caching as close to the client as correctness allows.

**Invalidation:** TTL expiry (simplest; add jitter so keys don't expire together), write-through, write-behind, or explicit event/tag-based on write. Prefer short TTL + `stale-while-revalidate` over clever manual invalidation when staleness is tolerable.

**Stampede / thundering herd** (many misses recompute the same key at once): per-key lock / single-flight (one recomputes, others wait), probabilistic early expiration, or serve stale while one refreshes.

**TTL:** derive from tolerable staleness and change rate.

**Never cache:** per-user sensitive/auth data in a shared cache, secrets/PII at the edge, rarely-reused results, cheap-to-compute values, or anything where staleness is a correctness bug (balances, inventory at point of sale).
