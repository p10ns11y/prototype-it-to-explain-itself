# Deploying the Prove it that you learned it Hub to Cloudflare Pages

> **Important:** This project **always uses pnpm** (see root README). Never use `npm` or `yarn` for the `site/` Astro project or any JS tooling.

## The two artifacts

1. **Tester** — `reflect-and-attempt-quizz.html` (single file, zero build, fully portable).
2. **Reference Site** — the Astro project in `site/` (renders monorepo markdown with Mermaid, typography, and Practice CTAs linking back to the tester).

## Recommended Cloudflare Pages setup (monorepo)

Connect the GitHub repo directly in the Cloudflare dashboard — no Workers adapter required (pure static output).

| Setting | Value |
|---------|--------|
| Root directory | `site` |
| Build command | `pnpm install && pnpm build` |
| Build output directory | `dist` |
| **Deploy command** | **Leave empty / disabled** |
| Node version | `24` (matches `site/.node-version`) |

### Do not run `wrangler deploy` in CI

If the build log shows `wrangler deploy` or asks for a Worker entry-point, the dashboard has a **Deploy command** set incorrectly. This project is **Cloudflare Pages (static)** — Pages publishes `dist/` automatically after the build.

- **Correct:** build command only → `pnpm install && pnpm build`, output `dist`, no deploy command
- **Wrong:** `wrangler deploy`, `npx wrangler deploy`, or `pnpm deploy` / `pnpm pages:deploy` in the build or deploy step

Manual CLI upload (optional, not used by Git CI):

```bash
cd site
pnpm pages:deploy   # runs wrangler pages deploy, not wrangler deploy
```

### Content sources

The site does **not** duplicate markdown under `site/`. It loads canonical files via the Astro content loader:

- `llm/architecture.md` → `/concepts/llm-architecture`
- `llm/README.md` → `/concepts/llm-readme`
- `llm/sampling-strategies.md` → `/concepts/sampling-strategies`
- `PROTOTYPE_ROADMAP.md` → `/concepts/prototype-roadmap`

Routing metadata and Practice CTA links live in `site/src/lib/concept-meta.ts`.

### Tester bundled with the site

`prebuild` / `predev` copy `reflect-and-attempt-quizz.html` into `site/public/` before Astro builds, so it lands at the root of `dist/`:

- Tester: `https://prototype-it-to-explain-itself.pages.dev/reflect-and-attempt-quizz.html`
- Hub home: `https://prototype-it-to-explain-itself.pages.dev/`

You can also deploy the tester as a separate static Pages project if you prefer.

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

**Cloudflare Pages emulation:**

```bash
cd site
pnpm pages:dev   # build + wrangler pages dev dist
```

Or deploy manually:

```bash
cd site
pnpm pages:deploy
```

## Caching

`site/public/_headers` is copied into `dist/` and sets cache rules for Cloudflare Pages:

- `/_astro/*` — long-lived immutable assets (hashed filenames)
- `/concepts/*`, `/reflect-and-attempt-quizz.html`, and other HTML — 1 hour

## Architecture notes

- **Static only** — `output: 'static'` in `astro.config.mjs`; no `@astrojs/cloudflare` adapter or `_worker.js`.
- **Mermaid** — loaded via dynamic import only on concept pages that contain ` ```mermaid ` blocks (~600 KB chunk, not on the home page).
- **Wrangler config** — `site/wrangler.toml` is for local `wrangler pages dev`; production uses dashboard Git integration.
