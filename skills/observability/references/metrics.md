# Metrics

**Types:** counter (monotonic — requests, errors), gauge (point-in-time — queue depth, memory, connections), **histogram** (distributions — latency → percentiles). Use histograms for latency, never a gauge/average.

**RED** (services): Rate, Errors, Duration per endpoint. **USE** (resources): Utilization, Saturation, Errors per resource.

**Stack:** Prometheus (scrape, PromQL) + Grafana + Alertmanager; or OTel metrics → Prometheus via OTLP/remote-write. Prometheus native histograms (stable 2025, opt-in) collapse the bucket-per-series model — the main cardinality fix for latency histograms.

**Cardinality explosion = the #1 mistake:** a metric's series count = the product of all its label cardinalities. Never put unbounded values in labels — user id, email, request id, raw URL with ids, timestamps, trace ids. That multiplies series, blows up memory/cost, can crash Prometheus. Keep labels bounded: route *template* (not raw path), status class, method, region. High-cardinality context goes in traces/wide events, not labels.
