# Profiling by stack

Pick the profile type for the symptom: CPU (where cycles go), heap/RSS (what's retained → leaks), allocation (churn → GC pressure).

- **Node.js**: built-in `--cpu-prof`/`--heap-prof` → open the `.cpuprofile`/`.heapprofile` in Chrome DevTools; `0x` for one-command flamegraphs; `clinic` (Doctor/Flame/Bubbleprof); `@datadog/pprof`; `--inspect` for live. (0x/clinic are lightly maintained; the built-in flags are the current path.)
- **Python**: **py-spy** — sampling, attaches to a running prod process with no code change, low overhead (the go-to for prod); cProfile (deterministic, offline analysis with snakeviz); Scalene (CPU+GPU+memory, line-level, Python vs native vs system time); memray for allocation/leaks.
- **Go**: built-in `pprof` (`import _ "net/http/pprof"`, then `go tool pprof http://host/debug/pprof/profile?seconds=30`); `-cpuprofile`/`-memprofile`/`-blockprofile`/`-mutexprofile`; `go test -bench` + benchstat; `go tool trace`.
- **JVM**: async-profiler (low-overhead CPU/alloc/lock flamegraphs, no safepoint bias); JFR + Mission Control; `jstack`/`jcmd`.
- **Linux (any)**: `perf record -g` / `perf report`; flamegraphs via FlameGraph scripts or `perf script | speedscope`; eBPF (bcc/bpftrace) for syscalls and **off-CPU analysis** (catches I/O-bound waits on-CPU profilers miss).
