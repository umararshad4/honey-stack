# Azure deploy

## Pick
- **Container Apps** — default for containers (serverless, scale-to-zero, revisions, KEDA/Dapr).
- **App Service** — managed web apps (code or container), easy custom domains/SSL.
- **Functions** — event-driven serverless.
- **AKS** — full Kubernetes when needed.

## Commands
- `az containerapp up --name N --resource-group G --source .` or `--image <ACR image> --target-port 8080 --ingress external`
- New revision: `az containerapp update …`; ingress: `az containerapp ingress show/update`
- App Service: `az webapp up` / `az webapp deploy`. Functions: `func azure functionapp publish <app>`
- Logs: `az containerapp logs show --type console` (app) / `--type system` (platform)

## Top errors
1. Container start / probe fails → **target port mismatch**: the default probe uses the ingress `--target-port`; the app must listen there. Most common failure.
2. Not reachable externally → ingress not set to `external`.
3. `ImagePullBackOff`/pull failure → wrong tag or creds; prefer managed identity + AcrPull role over stored passwords.
