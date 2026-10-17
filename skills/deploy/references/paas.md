# PaaS deploy

## Pick & deploy
- **Vercel** — Next.js/frontend, best previews. `vercel` (preview) / `vercel --prod` (production — confirm). Env scoped Production/Preview/Development; pin Node via `engines`.
- **Netlify** — static/JAMstack + functions. `netlify.toml`; `netlify deploy` (draft) / `--prod`.
- **Cloudflare** — edge. `wrangler.jsonc` + Wrangler 4.x; `wrangler deploy`; secrets `wrangler secret put NAME`, local `.dev.vars`. Set a current `compatibility_date`. New projects: Workers with static assets, not Pages.
- **Fly.io** — containers near users. `fly launch` → `fly.toml`, `fly deploy`; `release_command` for migrations; `fly secrets set`. Needs a Dockerfile.
- **Railway** — fastest push-and-run. `railway up`; builder is Railpack (Nixpacks is maintenance-mode).
- **Render** — `render.yaml` (`buildCommand`, `startCommand`); mostly dashboard/API-driven.

## Common errors
1. Builds locally, fails on the platform → Node/package-manager version mismatch. Pin engine + commit the lockfile.
2. Env var missing at runtime → set it for the right scope (preview vs prod); frontend vars need the public prefix (`NEXT_PUBLIC_`, `VITE_`).
3. Monorepo → set the root/base directory to the app subfolder.
4. White screen / 404 → wrong output directory.
