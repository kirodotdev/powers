---
name: "vercel-deployment"
displayName: "Vercel Deployment"
description: "Deploy and manage websites on Vercel using CLI-first workflow with vercel.json configuration"
keywords: ["vercel", "deploy", "hosting", "cli", "deployment", "web", "nextjs", "serverless"]
author: "Vercel"
---

# Vercel Deployment (CLI-First)

> Use this file whenever you are asked to deploy or update a site on Vercel.
> **Default behavior:** prefer the Vercel CLI.

## 1. Defaults & Principles

- Prefer **Vercel CLI** as the primary deployment method.
- **Preview before production**: always deploy to preview first, then promote.
- Vercel **auto-detects** frameworks (Next.js, Nuxt, SvelteKit, Vite, Astro, etc.) — only override when necessary.
- Use `vercel.json` only when customizing defaults. Most projects need none.
- Never hardcode secrets; use **Vercel environment variables**.
- For framework-specific details, run `vercel help` or reference official Vercel docs rather than inventing patterns.

## 2. Deploy with Vercel CLI (Preferred)

### Install & Authenticate

```bash
npm install -g vercel

# Check if already logged in
vercel whoami

# Only if not logged in
vercel login
```

### Link or Create a Project

Check if the project is already linked by looking for a `.vercel` directory.

If not already linked:

1. Run `vercel link` for interactive linking.
2. If the project doesn't exist on Vercel yet, run `vercel` — it will create the project and deploy in one step.
3. For monorepos, use `vercel link --repo`.

### Dependencies

Confirm all dependencies are installed (e.g., `npm install`) before deploying.

### Deploy

If creating a new project, do a preview deploy first.
If linking an existing project, create a preview deploy unless the user explicitly asked for production.

```bash
# Preview deploy (default — always do this first)
vercel

# Production deploy (only when explicitly requested or after preview is verified)
vercel --prod

# Force rebuild, skip cache
vercel --force

# Deploy without waiting for completion
vercel --no-wait
```

### After Deploying

```bash
# Check deployment status and details
vercel inspect <deployment-url>

# View build logs if something failed
vercel logs <deployment-url>

# Promote a preview to production
vercel promote <deployment-url>

# Rollback production to previous deployment
vercel rollback

# Test an endpoint with automatic auth bypass
vercel curl /api/health
```

## 3. Environment Variables

```bash
# List current env vars
vercel env ls

# Add a variable (interactive — prompts for environment)
vercel env add

# Pull all env vars to local .env.local
vercel env pull

# Run a command with env vars loaded (no file written)
vercel env run -- npm run dev
```

- Variables are scoped to **development**, **preview**, and **production**.
- Use `vercel env pull` before local development to stay in sync.

## 4. vercel.json (Only When Needed)

Most projects work without any configuration. Only add `vercel.json` when you need to customize behavior.

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json"
}
```

Common reasons to add config:

| Need | Property |
|------|----------|
| Override build command | `"buildCommand": "npm run build"` |
| Override output directory | `"outputDirectory": "dist"` |
| Set function regions | `"regions": ["iad1"]` |
| Add redirects/rewrites | `"redirects"` / `"rewrites"` |
| Configure cron jobs | `"crons": [{"path": "/api/cron", "schedule": "0 5 * * *"}]` |
| Set function limits | `"functions": {"api/**/*.js": {"maxDuration": 30}}` |

Do not duplicate framework defaults. If Vercel auto-detects correctly, leave it alone.

## 5. Troubleshooting

```bash
# Build failed — check logs
vercel logs <deployment-url>

# Deployment stuck — force rebuild
vercel --force

# Env vars missing locally — sync them
vercel env pull

# Cache issues — purge CDN or data cache
vercel cache purge

# Check HTTP timing on a deployment endpoint
vercel httpstat /api/health

# Open project dashboard in browser
vercel open
```

- Functions default to `iad1` (Washington D.C.) — set region close to your data source.
- Cron schedules are **UTC**, not local timezone.
- If `vercel inspect` shows the deployment is still building, use `vercel inspect <url> --wait`.
