import { defineCollection, z } from 'astro:content';

const docsCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    conceptIds: z.array(z.string()).optional(), // links back to knowledgeItems in the tester
  }),
});

export const collections = {
  docs: docsCollection,
};