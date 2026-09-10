import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';

/**
 * Canonical docs live in domain folders at repo root (same shape as `llm/`):
 *   llm/, diffusion/, computer-vision/, gaussian-splatting/, multimodal/, nlp/, …
 * plus PROTOTYPE_ROADMAP.md.
 * Edit those files; the site picks them up on dev reload / build.
 */
const DOMAIN_GLOBS = [
  'llm/*.md',
  'diffusion/*.md',
  'computer-vision/*.md',
  'gaussian-splatting/*.md',
  'multimodal/*.md',
  'nlp/*.md',
] as const;

const docs = defineCollection({
  loader: glob({
    base: '..',
    pattern: [...DOMAIN_GLOBS, 'PROTOTYPE_ROADMAP.md'],
    generateId({ entry }) {
      const normalized = entry.replace(/\\/g, '/');
      if (normalized === 'PROTOTYPE_ROADMAP.md') return 'prototype-roadmap';

      // domain/README.md → domain id (maps cleanly to folder / concepts)
      const readme = normalized.match(/^([^/]+)\/README\.md$/i);
      if (readme) {
        const domain = readme[1];
        // Keep historical id for the LLM collection hub page
        if (domain === 'llm') return 'readme';
        return domain;
      }

      // domain/other.md → other (llm/architecture → architecture, etc.)
      const nested = normalized.match(/^([^/]+)\/(.+)\.md$/);
      if (nested) {
        return nested[2];
      }

      return normalized.replace(/\.md$/, '');
    },
  }),
});

export const collections = { docs };
