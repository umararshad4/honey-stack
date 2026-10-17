# Instrumenting a service

**Auto-instrumentation first:** OTel agents/SDKs auto-capture HTTP servers/clients, DB drivers and queues with near-zero code — `opentelemetry-instrument python app.py`, Node `--require @opentelemetry/auto-instrumentations-node/register`, Java `-javaagent:opentelemetry-javaagent.jar`. Gets traces + basic metrics immediately.

**Manual spans** where business logic matters and auto-instrumentation can't see: wrap meaningful operations, add domain attributes (`order.id`, `tenant`, `items.count`), record exceptions and span status. Don't span trivial calls (span bloat); do span network/DB/external calls and significant compute.

**Vendor-neutral pipeline:** app → OTel SDK (OTLP) → OTel **Collector** (batch, redact PII, tail-sample, fan-out) → backends (traces → Jaeger/Tempo/Honeycomb; metrics → Prometheus; logs → Loki). Configure via OTel's stable declarative config.

**Resource attributes everywhere:** set `service.name`, `service.version`, `deployment.environment` — they power correlation across logs, metrics and traces. OTel traces + metrics are stable; logs are maturing; GenAI (`gen_ai.*`) conventions are still experimental — don't treat those attribute names as stable.
