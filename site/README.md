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
pnpm pages:dev # Wrangler Pages emulation
```

## Deploy to Cloudflare Pages

Connect the GitHub repo in the Cloudflare dashboard:

| Setting | Value |
|---------|--------|
| Root directory | `site` |
| Build command | `pnpm install && pnpm build` |
| Build output | `dist` |
| Deploy command | *(empty — do not set)* |
| Node version | `24` (`NODE_VERSION=24` or use `.node-version`) |

Or deploy manually from `site/`:

```bash
pnpm pages:deploy   # CLI only — do not put this in the Cloudflare build/deploy command
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

- Pure static output (`output: 'static'`) — no Cloudflare adapter/worker required.
- Mermaid (~600 KB) loads only on concept pages via dynamic import, not on the home page.
- `public/_headers` sets cache rules for Cloudflare Pages.
