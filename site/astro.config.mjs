import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import tailwind from '@astrojs/tailwind';

// https://astro.build/config
export default defineConfig({
  site: 'https://prototype-knowledge.example.com', // update after real CF deploy
  integrations: [mdx(), tailwind()],
  markdown: {
    shikiConfig: {
      theme: 'github-dark',
    },
  },
  // For now we keep content inside src/content/docs for a clean first version.
  // Later this can be pointed at the real .md files from the monorepo root
  // (or we can add a content sync step).
});