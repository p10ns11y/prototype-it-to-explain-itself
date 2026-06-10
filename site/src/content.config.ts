import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';

/**
 * Canonical docs live in the monorepo (../llm/*.md and ../PROTOTYPE_ROADMAP.md).
 * Edit those files; the site picks them up on dev reload / build.
 */
const docs = defineCollection({
  loader: glob({
    base: '..',
    pattern: ['llm/*.md', 'PROTOTYPE_ROADMAP.md'],
    generateId({ entry }) {
      const normalized = entry.replace(/\\/g, '/');
      if (normalized === 'PROTOTYPE_ROADMAP.md') return 'prototype-roadmap';
      if (normalized === 'llm/README.md') return 'readme';
      if (normalized.startsWith('llm/')) {
        return normalized.slice('llm/'.length).replace(/\.md$/, '');
      }
      return normalized.replace(/\.md$/, '');
    },
  }),
});

export const collections = { docs };
