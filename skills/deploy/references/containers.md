# Containers & Kubernetes

## Dockerfile (2026)
- First line `# syntax=docker/dockerfile:1` (BuildKit).
- **Multi-stage**: build in a full image, copy artifacts into a minimal runtime stage (no compilers/caches in prod).
- **Base**: distroless or slim, Chainguard for low-CVE. Pin by digest, never `:latest`.
- **Non-root**: `USER 65532:65532` (numeric high UID; distroless has no `groupadd`, and `runAsNonRoot` can't verify a name).
- **Layer cache**: copy dependency manifests and install BEFORE copying app code.
- **BuildKit cache mount**: `RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt` (npm/go equivalents).
- **Build secrets**: `RUN --mount=type=secret,id=…` — never `COPY .env`.
- **`.dockerignore`**: `.git`, `node_modules`, `.env`, build output, tests.

## Kubernetes
- **Deployment** (replicas + rolling update), **Service** (ClusterIP/LoadBalancer), **Ingress** (HTTP + TLS).
- **Probes**: `readinessProbe` gates traffic (critical for zero-downtime), `livenessProbe` restarts a hang, `startupProbe` for slow starters. Point them at a real health endpoint on the right port.
- **Resources**: set requests (scheduling) and limits (cap). Missing requests → eviction/noisy-neighbor.
- **Rollout**: `maxSurge`/`maxUnavailable`; `kubectl rollout status deploy/X`; rollback `kubectl rollout undo deploy/X`.
- **Diagnose**: `kubectl get pods`, `kubectl describe pod` (events), `kubectl logs --previous`.

### Common K8s errors
- `CrashLoopBackOff` → app exits; `logs --previous`, missing env/config.
- `ImagePullBackOff`/`ErrImagePull` → bad tag or registry auth (imagePullSecret).
- `CreateContainerConfigError` → referenced ConfigMap/Secret missing.
- `Pending` → unschedulable: insufficient resources or a taint with no toleration.
- `OOMKilled` → memory limit too low.

## Helm
`helm upgrade --install RELEASE ./chart -f values.yaml`; `helm diff upgrade` (plugin) before applying; `helm rollback RELEASE N`. Chart = `Chart.yaml`, `values.yaml`, `templates/`.
