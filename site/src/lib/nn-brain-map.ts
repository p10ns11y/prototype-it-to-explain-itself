export interface BrainMapLink {
  href: string;
  label: string;
}

export interface NnBrainMapping {
  id: string;
  nnTitle: string;
  nnDetail: string;
  brainTitle: string;
  brainDetail: string;
  links: BrainMapLink[];
}

/**
 * Neural-network ↔ brain teaching analogies for the self-explain flip cards.
 * Every pairing is a pedagogical metaphor — not a claim about biology or clinical neuroscience.
 * Inspired by public lecture framing.
 */
export const NN_BRAIN_MAPPINGS: NnBrainMapping[] = [
  {
    id: 'cnn',
    nnTitle: 'Convolutional Neural Network',
    nnDetail: 'Stacked filters that hunt for local patterns — edges first, then shapes, then objects.',
    brainTitle: 'Visual Cortex (V1 → V4)',
    brainDetail:
      'Historical teaching analogy: early vision areas like V1 respond to edges; V4 adds color and form. CNNs borrowed this layered idea as inspiration — not a one-to-one biological map.',
    links: [{ href: '/concepts/computer-vision', label: 'Computer vision demos' }],
  },
  {
    id: 'vit',
    nnTitle: 'Vision Transformer',
    nnDetail: 'Treats an image as patches and relates them globally — whole-scene context, not just local filters.',
    brainTitle: 'Holistic recognition (IT analogy)',
    brainDetail:
      'Loose analogy only: inferotemporal cortex is often discussed alongside whole-scene and face recognition. ViTs relate patches globally — a similar job on paper, not the mechanism IT uses.',
    links: [
      { href: '/concepts/computer-vision', label: 'Computer vision demos' },
      { href: '/concepts/multimodal', label: 'Multimodal spine' },
    ],
  },
  {
    id: 'transformer',
    nnTitle: 'Transformer Network',
    nnDetail: 'Attention over tokens — the architecture behind large language models. Needs serious compute at scale.',
    brainTitle: 'Language & Reasoning',
    brainDetail:
      'Function-level analogy: transformers process token sequences and sit at the base of modern LLMs. The parallel is what the system does — language, inference, planning — not a named cortical region.',
    links: [
      { href: '/concepts/llm-readme', label: 'LLM prototypes' },
      { href: '/concepts/nlp', label: 'NLP coherence & style' },
    ],
  },
  {
    id: 'probabilistic',
    nnTitle: 'Probabilistic Neural Network',
    nnDetail: 'Outputs a distribution, not a single answer. Trained to estimate probability density under Bayesian principles.',
    brainTitle: 'Uncertainty & Prediction',
    brainDetail:
      'Pedagogical analogy: instead of one hard guess, the network keeps a spread of plausible outcomes — like weighing odds before you commit to an answer.',
    links: [
      {
        href: '/concepts/sampling-strategies',
        label: 'Related: sampling & probability (no dedicated demo yet)',
      },
    ],
  },
  {
    id: 'multimodal',
    nnTitle: 'Multimodal AI Model',
    nnDetail: 'Different neural networks handle different data types — vision, language, audio — then meet in a shared space.',
    brainTitle: 'Integrated Perception',
    brainDetail:
      'Everyday analogy: sight, sound, and speech feed one experience. Multimodal models route each data type through its own encoder, then merge in shared space.',
    links: [{ href: '/concepts/multimodal', label: 'Multimodal spine demos' }],
  },
];
