# What REA can analyze

Pick the evidence type the question needs. Static first; runtime only when authorized and necessary. Use the connected server's real tool names and input schemas — the table below is capability, not the API.

| Target | REA returns | Needs |
|---|---|---|
| Native binaries | Pseudocode, assembly, strings, symbols, calls/refs | Hopper, Ghidra or IDA |
| Go / Rust binaries | Build info, modules, crate names/versions | Built-in static parsing |
| WASM | Validation, sections, WAT import/export forms | WABT |
| EVM bytecode | Selectors, offsets, inferred args, mutability | Local carrier (Linux x64) |
| JavaScript / Electron | Modules, imports, source maps, routes, IPC, native add-ons | Node + npm |
| .NET assemblies | Metadata, CIL, native deps, build comparison | None (static) |
| Android APK | Manifest, classes, decompiled methods, refs | JADX + JDK |
| Android device | Packages, processes, logs, dumps, screen, transfers | adb (authorized device) |
| Flutter | Dart snapshot hash, per-ABI digests, engine build | None (static) |
| Websites | Structure, scripts, network observations, screenshots | Chrome-family browser |
| Network captures | Requests, responses, payloads, source locations | HAR / SAZ / PCAP tools |
| Firmware | Regions, extraction, native handoffs | Binwalk / Unblob (Linux) |
| Crash dumps | Threads, registers, signals, mapping candidates | pwntools (Linux x64) |
| SQLite DB | Tables, columns, indexes, views, triggers, rows | Local snapshot |
| Process behavior | Terminal I/O, exit, filesystem observations, run comparisons | Native PTY (Linux/macOS) |

Runtime rows **execute the target** under the user's permissions. Only use them on targets the user authorized, and never broaden the target or action.

## Evidence discipline
REA returns Evidence IDs. Page large results with `detail: "summary"` and filters rather than pulling whole bundles; drill in by selecting the returned ID. A client may truncate a result — treat a preview as incomplete and re-request a smaller view by its parent ID. Keep inline evidence when the server doesn't retain references.
