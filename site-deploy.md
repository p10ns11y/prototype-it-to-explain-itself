# Deploying the Knowledge Hub to Cloudflare Pages

## The two artifacts

1. **Tester** — `knowledge-reflection-tester.html` (single file, zero build, fully portable).
2. **Reference Site** — the Astro project in `site/` (renders the explainer .md files with Mermaid, nice typography, and "Practice" CTAs that link back to the tester).

## Recommended Cloudflare Pages setup (monorepo style)

Option A — Two separate Pages projects (simplest)
- Project 1: point at the repo root, build command empty or a no-op, output directory left as-is or use a custom build that just copies the HTML. Or simply upload the single HTML directly.
- Project 2: point the build at the `site/` directory (`cd site && npm ci && npm run build`), output directory `site/dist`.

Option B — Single unified project (recommended for nice URLs)
- Build command (run from repo root):
  ```bash
  cd site && npm ci && npm run build
  # Then copy the tester into the Astro output so both are served from one origin
  cp ../knowledge-reflection-tester.html dist/
  ```
- Output directory: `site/dist`
- The tester will be available at `/knowledge-reflection-tester.html` (or `/` if you rename it to `index.html` in the final output).
- The Astro site will be at `/` (or move it under `/docs` by adjusting Astro config + the copy step).

## Local preview with wrangler

```bash
# After building the Astro site
wrangler pages dev site/dist
```

You can also use the included `wrangler.toml` as a starting point.

## Custom domains & caching

- Use a custom domain for the whole hub.
- Add a `_headers` file in the final dist for long-lived caching of the static tester and built docs assets.

Example `_headers`:

```
/knowledge-reflection-tester.html
  Cache-Control: public, max-age=3600

/concepts/*
  Cache-Control: public, max-age=3600
```

## Future evolution

When the team is ready to move to a full TanStack (Router + Query) experience:

- The MDX sources in `site/src/content` (or the real .md files) stay the same.
- The `knowledgeItems` data structure from the tester can be reused as route data / loaders.
- Cloudflare Pages + Functions (or Workers + Assets) remains an excellent target.

The current setup deliberately keeps the "single portable HTML" experience while giving the reference documentation the rich renderer it deserves.
