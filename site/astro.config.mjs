import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

// https://astro.build/config
export default defineConfig({
  site: 'https://prototype-it-to-explain-itself.pages.dev',
  output: 'static',
  integrations: [tailwind({ applyBaseStyles: false })],
  markdown: {
    shikiConfig: {
      theme: 'github-light',
    },
  },
  vite: {
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules/mermaid')) return 'mermaid';
          },
        },
      },
    },
  },
});
