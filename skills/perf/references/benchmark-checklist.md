# Validate a performance claim

Distilled from pstack `benchmark-checklist` at 4dd1d05818d19792e7cd6e818f1667f95f7e1dbe (MIT).

Before reporting a speedup or choosing an implementation:

1. Write the proposed claim, workload and unit. Read what the harness times and excludes. Confirm the work happened inside the timed region: awaited requests, consumed generators, committed rows and correct output.
2. Count failures, retries and timeouts alongside latency and throughput. A fast rejection is not a faster successful request. Validate output equivalence before comparing performance.
3. Identify the limiter with a separate profiling run; don't report instrumented timings as ordinary performance. Check whether the load generator, machine contention, database pool or a configuration limit saturates before the code under test.
4. Tune both sides as they would run in production: build mode, versions, data, concurrency, transactions, cache state and connection pools. If one cannot be tuned, report the limitation without declaring an implementation winner.
5. Sanity-check the number against disk/network bandwidth, CPU capacity and the share of end-to-end time the changed code previously used. A result beyond the physical or algorithmic bound needs investigation.
6. Alternate at least five runs per side for a comparison. Report median and range, or the harness's justified statistical method. Differences within run-to-run noise are **no measurable difference**. A user-requested ballpark may use one run, explicitly labeled; it still needs correct outputs and proof that work ran.
7. Measure the real user path as well as a microbenchmark. A 2x faster helper that occupies 1% of the request is not a 2x faster product.

Done when: the claim includes environment, workload, unit, error counts, run count, spread, limiter and end-to-end impact. Otherwise report **inconclusive** with the missing evidence.
