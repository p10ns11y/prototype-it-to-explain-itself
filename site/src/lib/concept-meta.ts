export interface PracticeLink {
  concept: string;
  label: string;
}

export interface ConceptPageMeta {
  /** Collection entry id (matches glob loader id). */
  entryId: string;
  /** Public URL slug under /concepts/ */
  slug: string;
  title: string;
  description: string;
  practiceLinks?: PracticeLink[];
}

/** Site routing + display metadata. Markdown body lives in the repo sources below. */
export const CONCEPT_PAGES: ConceptPageMeta[] = [
  {
    entryId: 'architecture',
    slug: 'llm-architecture',
    title: 'Architecture & the Predictor Seam',
    description: 'The narrow waist that makes the entire collection composable and polyglot-ready.',
    practiceLinks: [
      { concept: 'predictor-narrow-waist', label: 'Test your understanding of the Predictor seam' },
      { concept: 'why-not-bloat-base', label: 'Why we refuse to bloat the base prototype' },
    ],
  },
  {
    entryId: 'readme',
    slug: 'llm-readme',
    title: 'LLM Prototypes Guide',
    description: 'The living reference for the entire collection.',
    practiceLinks: [
      { concept: 'react-responsibility', label: 'Test the ReAct responsibility split' },
    ],
  },
  {
    entryId: 'sampling-strategies',
    slug: 'sampling-strategies',
    title: 'Sampling Strategies',
    description: 'Why temperature alone is not enough, and how Top-k / Top-p actually work in practice.',
    practiceLinks: [
      { concept: 'tiny-model-lesson', label: 'Reflect on why a tiny model makes these problems extremely visible' },
    ],
  },
  {
    entryId: 'prototype-roadmap',
    slug: 'prototype-roadmap',
    title: 'The 9-Prototype Roadmap',
    description: 'Why each prototype exists, what it teaches, and the production stack it mirrors.',
    practiceLinks: [
      { concept: 'evaluator-enables-synthetic', label: 'How does the Evaluator enable the Synthetic Data Factory?' },
      { concept: 'synthetic-flywheel', label: 'Describe the self-improvement flywheel' },
      { concept: 'multi-agent-value', label: 'Why do multiple agents + a critic help on hard tasks?' },
    ],
  },
];
