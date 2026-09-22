import type { BenchId } from './types'

export interface Reading {
  title: string
  by: string
  year: number
  minutes: number
  why: string
  href: string
  kind: 'foundation' | 'now'
}

export interface PathStop {
  id: BenchId
  name: string
  gist: string
  hold: string
  hides: string
  now: string
  readings: Reading[]
}

export const PATH: readonly PathStop[] = [
  {
    id: 'kiln',
    name: 'Kiln',
    gist: 'Drag the heat and watch one word take over.',
    hold: 'Heat does not add words. It changes how the chance is shared.',
    hides: 'This kiln has four words and fixed counts. A real model has a huge vocabulary and a learned sense of what came before.',
    now: 'Tool calls usually run cold, close to the sure word. Drafts run warmer. Reasoning models spend extra tokens before the answer, and each of those tokens is still a draw.',
    readings: [
      {
        kind: 'foundation',
        title: 'The Curious Case of Neural Text Degeneration',
        by: 'Holtzman, Buys, Du, Forbes, and Choi',
        year: 2020,
        minutes: 45,
        why: 'Shows why always picking the likeliest word goes bland, and why sampling from the top of the distribution keeps the text alive.',
        href: 'https://arxiv.org/abs/1904.09751',
      },
      {
        kind: 'now',
        title: 'Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters',
        by: 'Snell, Lee, Xu, and Kumar',
        year: 2024,
        minutes: 40,
        why: 'The current move is to spend more compute at answer time. Sampling is still how each step is chosen.',
        href: 'https://arxiv.org/abs/2408.03314',
      },
    ],
  },
  {
    id: 'desk',
    name: 'Desk',
    gist: 'Press the lit button. Think, then a tool, then read.',
    hold: 'An agent is a loop. The answer is illegal until the tool has been read.',
    hides: 'The calculator here cannot be wrong, and there is only one sum. Real tools fail, drift, and need a check.',
    now: 'Useful agents keep the loop small. They show the steps, use a few clear tools, and stop for a person when the call is risky. MCP is the common way those tools are plugged in.',
    readings: [
      {
        kind: 'foundation',
        title: 'ReAct: Synergizing Reasoning and Acting in Language Models',
        by: 'Yao, Zhao, Yu, and colleagues',
        year: 2022,
        minutes: 40,
        why: 'The paper that made think, act, observe a concrete loop instead of a single reply.',
        href: 'https://arxiv.org/abs/2210.03629',
      },
      {
        kind: 'now',
        title: 'Building effective agents',
        by: 'Anthropic',
        year: 2024,
        minutes: 25,
        why: 'The field note on when a fixed workflow is enough and when a model should steer its own tool loop.',
        href: 'https://www.anthropic.com/engineering/building-effective-agents',
      },
      {
        kind: 'now',
        title: 'Model Context Protocol documentation',
        by: 'Model Context Protocol',
        year: 2026,
        minutes: 20,
        why: 'How current agents discover and call tools without a private plug for every product.',
        href: 'https://modelcontextprotocol.io/docs/getting-started/intro',
      },
    ],
  },
  {
    id: 'shelf',
    name: 'Shelf',
    gist: 'Read three lines, then search for the one that leaves.',
    hold: 'The window forgets. A store remembers if your words touch the line.',
    hides: 'The match here is a few tags, not a learned retriever. A real store embeds the question and the notes and returns the nearest ones.',
    now: 'Context windows got long. Models still miss a fact buried in the middle. Agents keep a store and pull a few matching lines instead of rereading everything.',
    readings: [
      {
        kind: 'foundation',
        title: 'Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks',
        by: 'Lewis and colleagues',
        year: 2020,
        minutes: 40,
        why: 'The pattern of answering from retrieved notes instead of from the model alone.',
        href: 'https://arxiv.org/abs/2005.11416',
      },
      {
        kind: 'foundation',
        title: 'Lost in the Middle: How Language Models Use Long Contexts',
        by: 'Liu, Lin, Hewitt, and Paranjape',
        year: 2023,
        minutes: 35,
        why: 'Why stuffing the whole tape into the prompt still drops the fact in the middle.',
        href: 'https://arxiv.org/abs/2307.03172',
      },
      {
        kind: 'now',
        title: 'Effective context engineering for AI agents',
        by: 'Anthropic',
        year: 2025,
        minutes: 20,
        why: 'How working agents choose what stays in the window and what is fetched at the moment it is needed.',
        href: 'https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents',
      },
    ],
  },
  {
    id: 'grain',
    name: 'Grain',
    gist: 'Watch the shape arrive, then name it while it is noisy.',
    hold: 'The shape arrives before the grain is gone.',
    hides: 'This toy already knows the picture and blends toward it. A real model learns the direction from data and never stores the answer.',
    now: 'Newer image models train with flow matching. The network learns a velocity from noise toward pictures. The sample is still a walk that reveals structure early.',
    readings: [
      {
        kind: 'foundation',
        title: 'Denoising Diffusion Probabilistic Models',
        by: 'Ho, Jain, and Abbeel',
        year: 2020,
        minutes: 60,
        why: 'The paper that made generation a learned walk from noise back to a picture.',
        href: 'https://arxiv.org/abs/2006.11239',
      },
      {
        kind: 'foundation',
        title: 'Flow Matching for Generative Modeling',
        by: 'Lipman and colleagues',
        year: 2023,
        minutes: 45,
        why: 'A cleaner way to learn that walk. A lot of current image training starts here.',
        href: 'https://arxiv.org/abs/2210.02747',
      },
      {
        kind: 'now',
        title: 'Scaling Rectified Flow Transformers for High-Resolution Image Synthesis',
        by: 'Esser and colleagues',
        year: 2024,
        minutes: 50,
        why: 'How that idea shows up in a modern text-to-image system.',
        href: 'https://arxiv.org/abs/2403.03206',
      },
    ],
  },
  {
    id: 'blobs',
    name: 'Blobs',
    gist: 'Drag each blob onto a dot.',
    hold: 'A scene can be a few soft blobs you can move.',
    hides: 'You place three blobs by hand. A real capture uses millions of 3D blobs, fitted to photos, and rendered from a new viewpoint.',
    now: 'Splats became a practical scene format. People edit them, shrink them, and run them on headsets. The picture is still blobs with a center, a size, and a color.',
    readings: [
      {
        kind: 'foundation',
        title: '3D Gaussian Splatting for Real-Time Radiance Field Rendering',
        by: 'Kerbl, Kopanas, Leimkühler, and Drettakis',
        year: 2023,
        minutes: 50,
        why: 'The paper that made an explicit cloud of blobs fast enough to be the scene itself.',
        href: 'https://arxiv.org/abs/2308.04079',
      },
      {
        kind: 'now',
        title: 'The Impact and Outlook of 3D Gaussian Splatting',
        by: 'Kerbl',
        year: 2025,
        minutes: 30,
        why: 'The author of the original paper on what changed after it. Editing, scale, and speed.',
        href: 'https://arxiv.org/abs/2510.26694',
      },
    ],
  },
]

export function stopById(id: BenchId): PathStop {
  const stop = PATH.find((item) => item.id === id)
  if (!stop) throw new Error(`missing path stop ${id}`)
  return stop
}

export function nextStop(id: BenchId): PathStop | null {
  const index = PATH.findIndex((item) => item.id === id)
  return PATH[index + 1] ?? null
}
