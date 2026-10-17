# Common backend bottlenecks & fixes

- **N+1 / slow queries** — usually #1. Batch, eager-load, index, keyset-paginate, `pg_stat_statements`. See the `database` skill.
- **Missing caching** — repeated identical computation/queries → add a cache layer (see `caching.md`).
- **Serialization cost** — large JSON encode/decode, over-fetching fields → trim payloads, stream, paginate, faster codec.
- **Synchronous/blocking I/O** — a blocking call on an event loop (Node) or request thread stalls everything → make I/O async, move CPU work to worker threads / a queue.
- **Inefficient algorithms (big-O)** — an O(n²) loop or a per-item DB call → fix the algorithm/data structure before micro-tuning.
- **Unbounded concurrency** — unlimited parallel tasks/connections → resource exhaustion, tail-latency collapse → bounded pools / semaphores / backpressure.
- **GC pressure / memory leaks** — high allocation churn or retained refs (unbounded caches, listener leaks, closures) → profile allocations, bound caches, fix retention.
- **Cold starts (serverless)** — init cost on first request → provisioned concurrency, smaller bundles, lazy-load non-critical deps, reuse connections via a pooler.
