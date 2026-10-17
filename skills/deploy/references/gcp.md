# GCP deploy

## Pick
- **Cloud Run** — default. Any container or source, scale-to-zero, HTTPS, pay-per-use.
- **GKE Autopilot** — when you need Kubernetes without node management.
- **Cloud Functions (2nd gen)** — event-driven single functions (built on Cloud Run).
- App Engine — legacy; prefer Cloud Run.

## Commands
- `gcloud run deploy SERVICE --source .` (Cloud Build + buildpacks, or your Dockerfile if present) or `--image <AR image>`
- Public: add `--allow-unauthenticated --region <r>`
- Enable APIs first: `gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com`
- Rollback (instant): `gcloud run services update-traffic SERVICE --to-revisions GOOD=100`
- Canary: `--to-revisions NEW=10,OLD=90`

## Service accounts (the GCP gotcha)
- **Build identity** (Cloud Build SA) needs `roles/run.builder`. IAM grants take ~2 min to propagate.
- **Runtime identity** (service SA): least privilege; don't reuse the default SA in prod.

## Top errors
1. `PERMISSION_DENIED`/403 on deploy → missing `run.builder`/`run.admin`/`iam.serviceAccountUser`, or APIs not enabled.
2. "Container failed to start. Failed to listen on PORT" → the app must listen on `$PORT` (default 8080) on `0.0.0.0`. The #1 Cloud Run error.
3. Build fails, no Dockerfile → buildpack can't detect; add a Dockerfile or fix the start script.
4. 403 at request time → `--no-allow-unauthenticated` set; caller lacks `run.invoker`.
5. Slow cold starts → set `--min-instances`, raise `--timeout`, enable startup CPU boost.
