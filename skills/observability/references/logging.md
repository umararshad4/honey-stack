# Structured logging

JSON, one object per line. Consistent fields: `timestamp`, `level`, `service`, `trace_id`/`span_id` (log↔trace correlation), and a request/correlation ID propagated across services.

**Levels:** ERROR (needs attention), WARN (recoverable anomaly), INFO (business-significant), DEBUG (dev only). Keep INFO useful, not noisy.

**Never log:** secrets/tokens/keys, passwords, full card numbers, auth headers, PII beyond what's lawful. Redact at the logger (allow/deny field lists). Assume logs are widely readable and long-retained.

**Sampling:** at volume, keep all errors and sample INFO/DEBUG (head or tail, tied to traces) to control cost.

**Libraries:** pino (Node), zap/zerolog/slog (Go), structlog or stdlib `logging` with a JSON formatter (Python). Emit through the OTel logs bridge to unify with traces.
