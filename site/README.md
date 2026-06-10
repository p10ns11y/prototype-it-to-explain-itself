# site/ — Knowledge Reference Site (Astro + MDX)

This is the Astro-powered reference documentation for the project.

## Local development

```bash
cd site
npm install
npm run dev
```

## Build for Cloudflare Pages

```bash
npm run build
```

The output in `dist/` can be deployed directly.

## Unified deploy with the tester

The single-file `knowledge-reflection-tester.html` (at the monorepo root) is the portable experience.

For a unified Cloudflare Pages project you can:

1. Build this Astro site (`npm run build` inside `site/`).
2. Copy `../knowledge-reflection-tester.html` into the `dist/` root (or a `/tester` subfolder).
3. Deploy the combined `dist/`.

The tester links to `/concepts/...` and the concept pages contain "Practice" CTAs that link back to the tester with `?concept=...&review=1` (supported by the tester's URL param logic).

## Evolution path

This site (and the MDX sources) can later be absorbed into a TanStack Router + Query application with almost no content changes. The current setup is deliberately low-commitment while giving excellent reference pages today.
