# site/ — Knowledge Reference Site (Astro)

Static reference docs rendered from the monorepo markdown sources (`../llm/*.md`, `../PROTOTYPE_ROADMAP.md`).

## Requirements

- Node.js **24 LTS** (see `.node-version`, currently 24.16.0)
- pnpm **11.5+** (see `packageManager` in `package.json`)

## Local development

```bash
cd site
pnpm install
pnpm dev
```

`predev` copies `reflect-and-attempt-quizz.html` into `public/` so the tester is available at `/reflect-and-attempt-quizz.html` during dev.

## Build

```bash
pnpm build
pnpm preview   # Astro static preview
# or
pnpm workers:dev # Cloudflare wrangler dev (after build)
```

## Deploy to Cloudflare

Cloudflare now uses **Workers static assets** (not a separate `pages.dev` toggle). Your live URL will be `*.workers.dev`.

| Setting | Value |
|---------|--------|
| Root directory | `site` |
| Build command | `pnpm install && pnpm build` |
| Build output | `dist` |
| Deploy command | `npx wrangler deploy` |
| Node version | `24` |

Or deploy manually from `site/`:

```bash
pnpm deploy
```

See `../site-deploy.md` for full details.

## Content sources

Edit markdown in the repo — not duplicated under `site/`:

| Source file | URL |
|-------------|-----|
| `llm/architecture.md` | `/concepts/llm-architecture` |
| `llm/README.md` | `/concepts/llm-readme` |
| `llm/sampling-strategies.md` | `/concepts/sampling-strategies` |
| `PROTOTYPE_ROADMAP.md` | `/concepts/prototype-roadmap` |

Routing and Practice CTA links are configured in `src/lib/concept-meta.ts`.  
Glob loader paths are in `src/content.config.ts`.

## Architecture notes

- Pure static output (`output: 'static'`) — assets-only Worker via `wrangler.toml` `[assets]`.
- Mermaid (~600 KB) loads only on concept pages via dynamic import, not on the home page.
- `public/_headers` sets cache rules for Cloudflare Pages.
