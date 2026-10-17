# Microservices

**When NOT to:** most teams. A bad split becomes a **distributed monolith** — services that deploy together, chatty sync calls, a shared DB — monolith coupling plus microservice ops cost. Default: a modular monolith with clear internal boundaries; extract a service only for a distinct scaling profile, independent deploy cadence, or separate team ownership.

- **Boundaries:** align to business capabilities / bounded contexts (DDD). Each service owns its data (no shared DB). If two always change together, they're one service.
- **Contracts:** OpenAPI for REST (contract-first, generate clients/validation); gRPC + Protobuf internally (typed, streaming — but still needs contract testing for compatibility); **Pact** for consumer-driven contract tests + a Pact Broker with `can-i-deploy` gating deploys.
- **Local dev:** docker-compose (simplest), Tilt (multi-service live reload for k8s), dev containers (`.devcontainer/devcontainer.json`).
- **Discovery:** in k8s, DNS via Services; outside, a registry (Consul) or mesh. Keep it boring.

**Mistakes:** shared database; synchronous call chains coupling latency/failure (prefer async events); no contract tests → integration breaks only in prod; splitting before the domain is understood.
