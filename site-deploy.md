# Deploying the Prove it that you learned it Hub to Cloudflare

> **Important:** This project **always uses pnpm** (see root README). Never use `npm` or `yarn` for the `site/` Astro project or any JS tooling.

## The two artifacts

1. **Tester** — `reflect-and-attempt-quizz.html` (single file, zero build, fully portable).
2. **Reference Site** — the Astro project in `site/` (renders monorepo markdown with Mermaid, typography, and Practice CTAs linking back to the tester).

## Cloudflare has merged Pages into Workers

There is **no separate “enable pages.dev” toggle** in the current dashboard. New Git-connected projects live under **Workers & Pages** and publish to:

`https://<project-name>.<your-subdomain>.workers.dev/`

(for example `https://prototype-it-to-explain-itself.sathyam-peram.workers.dev/`)

Legacy Pages projects still use `*.pages.dev`. New projects use **`workers.dev`** — that is expected. See [Migrate from Pages to Workers](https://developers.cloudflare.com/workers/static-assets/migration-guides/migrate-from-pages/).

This repo is configured for **Workers static assets** (no Worker script — just `dist/`).

## Recommended dashboard setup (monorepo)

**Workers & Pages → your project → Settings → Builds**

| Setting | Value |
|---------|--------|
| Root directory | `site` |
| Build command | `pnpm install && pnpm build` |
| Build output directory | `dist` *(optional cache hint; wrangler.toml is source of truth)* |
| **Deploy command** | `npx wrangler deploy` |
| Node version | `24` (matches `site/.node-version`) |

`site/wrangler.toml` points at static assets:

```toml
[assets]
directory = "./dist"
```

Wrangler uploads `dist/` on deploy. **Do not** use a no-op `echo` deploy — that skips uploading your Astro build.

### Remove the default “Hello world” Worker

If the live URL still shows **Hello world**, the project still has a placeholder Worker script from creation. In the dashboard:

1. Open the project → **Settings** → check for a Worker entrypoint / `main` script.
2. Remove it, or ensure deploy uses only `wrangler.toml` (assets-only, no `main` field).
3. Redeploy.

With assets configured, `/` serves `dist/index.html` from your Astro build.

### Content sources

The site does **not** duplicate markdown under `site/`. It loads canonical files via the Astro content loader:

- `llm/architecture.md` → `/concepts/llm-architecture`
- `llm/README.md` → `/concepts/llm-readme`
- `llm/sampling-strategies.md` → `/concepts/sampling-strategies`
- `PROTOTYPE_ROADMAP.md` → `/concepts/prototype-roadmap`

Routing metadata and Practice CTA links live in `site/src/lib/concept-meta.ts`.

### Tester bundled with the site

`prebuild` / `predev` copy `reflect-and-attempt-quizz.html` into `site/public/` before Astro builds, so it lands at the root of `dist/`:

- Tester: `https://<project>.<account>.workers.dev/reflect-and-attempt-quizz.html`
- Hub home: `https://<project>.<account>.workers.dev/`

## Local preview

**Day-to-day development (HMR):**

```bash
cd site
pnpm install
pnpm dev
```

**Production-like static preview:**

```bash
cd site
pnpm build
pnpm preview   # Astro static server
```

**Cloudflare runtime emulation:**

```bash
cd site
pnpm workers:dev   # build + wrangler dev
```

**Manual deploy from CLI:**

```bash
cd site
pnpm deploy   # build + wrangler deploy
```

## Caching

`site/public/_headers` is copied into `dist/` and sets cache rules:

- `/_astro/*` — long-lived immutable assets (hashed filenames)
- `/concepts/*`, `/reflect-and-attempt-quizz.html`, and other HTML — 1 hour

## Architecture notes

- **Static only** — `output: 'static'` in `astro.config.mjs`; no Worker script, no `@astrojs/cloudflare` adapter.
- **Mermaid** — dynamic import only on concept pages with diagrams (~600 KB chunk, not on the home page).
- **Wrangler** — `[assets] directory = "./dist"` in `site/wrangler.toml`.
