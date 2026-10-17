# Tracing

**Spans** form a tree per request (root + child per operation), each with name, start/end, attributes, status, events. A **trace** = all spans sharing a `trace_id`.

**Context propagation** carries `trace_id`/`span_id` across process boundaries via headers — standardize on **W3C Trace Context** (`traceparent`/`tracestate`); OTel does it automatically for instrumented clients/servers. Broken propagation (unforwarded headers, async boundaries, queues) = disconnected traces — a common bug.

**Pipeline:** app → OTel SDK → (OTLP) → **Collector** → backend(s). Run a Collector (gateway and/or agent) rather than exporting straight to a vendor: it centralizes batching, retry, redaction, sampling, and lets you swap backends without touching apps.

**Sampling:**
- **Head** — decide at trace start (e.g. 10%); cheap, but may drop the rare error trace you needed.
- **Tail** — decide after the trace completes (Collector `tailsamplingprocessor`): keep all errors + slow traces, sample the boring ones. Needs the whole trace buffered (more Collector memory). Preferred for keeping signal while cutting cost.
