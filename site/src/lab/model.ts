export interface KilnShare {
  word: string
  p: number
}

export const KILN_WORDS = [
  { word: 'kiln', count: 5 },
  { word: 'book', count: 3 },
  { word: 'gate', count: 2 },
  { word: 'walk', count: 2 },
] as const

export const KILN_MIN = 0.3
export const KILN_MAX = 2.6
export const KILN_COOL = 0.7
export const KILN_HOT = 0.34

export function kilnShares(temperature: number): KilnShare[] {
  const t = Math.min(KILN_MAX, Math.max(KILN_MIN, temperature))
  const logits = KILN_WORDS.map((word) => Math.log(word.count) / t)
  const peak = Math.max(...logits)
  const lifted = logits.map((value) => Math.exp(value - peak))
  const sum = lifted.reduce((total, value) => total + value, 0)
  return KILN_WORDS.map((word, index) => ({ word: word.word, p: lifted[index] / sum }))
}

export function kilnPeak(temperature: number): number {
  return Math.max(...kilnShares(temperature).map((share) => share.p))
}

export function kilnShownPeak(temperature: number): number {
  return Math.round(kilnPeak(temperature) * 100)
}

export function kilnCoolEnough(temperature: number): boolean {
  return kilnShownPeak(temperature) >= 70
}

export function kilnHotEnough(temperature: number): boolean {
  return kilnShownPeak(temperature) <= 34
}

export function kilnMode(temperature: number): string {
  return kilnShares(temperature).reduce((best, share) => (share.p > best.p ? share : best)).word
}

export function kilnSample(temperature: number, rand: number): string {
  const shares = kilnShares(temperature)
  let cursor = 0
  const draw = Math.min(0.999999, Math.max(0, rand))
  for (const share of shares) {
    cursor += share.p
    if (draw <= cursor) return share.word
  }
  return shares[shares.length - 1].word
}

export type ShapeName = 'star' | 'house' | 'ring'

export const SHAPES: readonly ShapeName[] = ['star', 'house', 'ring']

export const GRAIN_SIZE = 160
export const GRAIN_STEPS = 36
export const GRAIN_READY_AT = 8
export const GRAIN_LATE_AT = 22

export type GrainMoment = 'early' | 'ready' | 'late'

export function grainMoment(step: number): GrainMoment {
  if (step < GRAIN_READY_AT) return 'early'
  if (step > GRAIN_LATE_AT) return 'late'
  return 'ready'
}

function paintBase(size: number): Uint8ClampedArray {
  const pixels = new Uint8ClampedArray(size * size * 4)
  for (let i = 0; i < size * size; i++) {
    pixels[i * 4] = 22
    pixels[i * 4 + 1] = 18
    pixels[i * 4 + 2] = 16
    pixels[i * 4 + 3] = 255
  }
  return pixels
}

function dot(pixels: Uint8ClampedArray, size: number, x: number, y: number, rgb: [number, number, number]) {
  if (x < 0 || y < 0 || x >= size || y >= size) return
  const index = (y * size + x) * 4
  pixels[index] = rgb[0]
  pixels[index + 1] = rgb[1]
  pixels[index + 2] = rgb[2]
  pixels[index + 3] = 255
}

function insidePolygon(x: number, y: number, points: readonly (readonly [number, number])[]): boolean {
  let crossed = false
  for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
    const [xi, yi] = points[i]
    const [xj, yj] = points[j]
    const intersect = yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi + 0.00001) + xi
    if (intersect) crossed = !crossed
  }
  return crossed
}

function starPoints(cx: number, cy: number, outer: number, inner: number): [number, number][] {
  const points: [number, number][] = []
  for (let i = 0; i < 10; i++) {
    const radius = i % 2 === 0 ? outer : inner
    const angle = -Math.PI / 2 + (i * Math.PI) / 5
    points.push([cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius])
  }
  return points
}

export function paintShape(kind: ShapeName, size = GRAIN_SIZE): Uint8ClampedArray {
  const pixels = paintBase(size)
  const cx = size / 2
  const cy = size / 2
  const reach = size * 0.36
  if (kind === 'star') {
    const points = starPoints(cx, cy, reach, reach * 0.42)
    const rgb: [number, number, number] = [242, 176, 72]
    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        if (insidePolygon(x + 0.5, y + 0.5, points)) dot(pixels, size, x, y, rgb)
      }
    }
    return pixels
  }
  if (kind === 'house') {
    const rgb: [number, number, number] = [232, 108, 74]
    const left = Math.round(cx - reach * 0.72)
    const right = Math.round(cx + reach * 0.72)
    const roof = Math.round(cy - reach * 0.15)
    const floor = Math.round(cy + reach * 0.95)
    const roofPoints: [number, number][] = [
      [cx - reach, roof],
      [cx + reach, roof],
      [cx, cy - reach * 1.05],
    ]
    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const inBody = x >= left && x <= right && y >= roof && y <= floor
        if (inBody || insidePolygon(x + 0.5, y + 0.5, roofPoints)) dot(pixels, size, x, y, rgb)
      }
    }
    return pixels
  }
  const rgb: [number, number, number] = [118, 198, 162]
  const outer = reach * reach
  const inner = (reach * 0.52) * (reach * 0.52)
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const dx = x + 0.5 - cx
      const dy = y + 0.5 - cy
      const distance = dx * dx + dy * dy
      if (distance <= outer && distance >= inner) dot(pixels, size, x, y, rgb)
    }
  }
  return pixels
}

export function makeNoise(size: number, rand: () => number): Uint8ClampedArray {
  const pixels = new Uint8ClampedArray(size * size * 4)
  for (let i = 0; i < size * size; i++) {
    const grain = Math.round(rand() * 255)
    pixels[i * 4] = grain
    pixels[i * 4 + 1] = grain
    pixels[i * 4 + 2] = grain
    pixels[i * 4 + 3] = 255
  }
  return pixels
}

export function mixFrame(noise: Uint8ClampedArray, target: Uint8ClampedArray, t: number): Uint8ClampedArray {
  const blend = Math.min(1, Math.max(0, t))
  const stay = 1 - blend
  const frame = new Uint8ClampedArray(target.length)
  for (let i = 0; i < target.length; i += 4) {
    frame[i] = stay * noise[i] + blend * target[i]
    frame[i + 1] = stay * noise[i + 1] + blend * target[i + 1]
    frame[i + 2] = stay * noise[i + 2] + blend * target[i + 2]
    frame[i + 3] = 255
  }
  return frame
}

export function frameDistance(left: Uint8ClampedArray, right: Uint8ClampedArray): number {
  let total = 0
  const pixels = left.length / 4
  for (let i = 0; i < left.length; i += 4) {
    total += Math.abs(left[i] - right[i]) + Math.abs(left[i + 1] - right[i + 1]) + Math.abs(left[i + 2] - right[i + 2])
  }
  return total / (pixels * 3 * 255)
}

export interface Splat {
  x: number
  y: number
  sigma: number
  rgb: [number, number, number]
  weight: number
}

export const BLOB_W = 180
export const BLOB_H = 120
export const BLOB_PAPER: [number, number, number] = [244, 236, 220]
export const BLOB_SEAL = 0.84

export const SCENE: readonly Splat[] = [
  { x: 52, y: 40, sigma: 20, rgb: [226, 146, 54], weight: 0.95 },
  { x: 118, y: 78, sigma: 34, rgb: [196, 86, 62], weight: 0.92 },
  { x: 86, y: 62, sigma: 15, rgb: [58, 122, 96], weight: 0.9 },
]

export function starterSplats(): Splat[] {
  return [
    { x: 28, y: 96, sigma: 10, rgb: [70, 62, 54], weight: 0.8 },
    { x: 42, y: 100, sigma: 10, rgb: [70, 62, 54], weight: 0.8 },
    { x: 56, y: 104, sigma: 10, rgb: [70, 62, 54], weight: 0.8 },
  ]
}

export const SWATCHES: readonly [number, number, number][] = [
  [226, 146, 54],
  [196, 86, 62],
  [58, 122, 96],
  [70, 62, 54],
  [232, 214, 180],
]

export function renderSplats(splats: readonly Splat[], width = BLOB_W, height = BLOB_H): Float32Array {
  const buffer = new Float32Array(width * height * 4)
  for (let i = 0; i < width * height; i++) {
    buffer[i * 4] = BLOB_PAPER[0]
    buffer[i * 4 + 1] = BLOB_PAPER[1]
    buffer[i * 4 + 2] = BLOB_PAPER[2]
    buffer[i * 4 + 3] = 1
  }
  for (const splat of splats) {
    const span = splat.sigma * 3
    const x0 = Math.max(0, Math.floor(splat.x - span))
    const x1 = Math.min(width - 1, Math.ceil(splat.x + span))
    const y0 = Math.max(0, Math.floor(splat.y - span))
    const y1 = Math.min(height - 1, Math.ceil(splat.y + span))
    const sigma2 = splat.sigma * splat.sigma
    for (let y = y0; y <= y1; y++) {
      for (let x = x0; x <= x1; x++) {
        const dx = x - splat.x
        const dy = y - splat.y
        const falloff = Math.exp((-0.5 * (dx * dx + dy * dy)) / sigma2)
        const srcA = Math.min(1, splat.weight * falloff)
        if (srcA < 0.004) continue
        const index = (y * width + x) * 4
        const dstA = buffer[index + 3]
        const outA = srcA + dstA * (1 - srcA)
        for (let channel = 0; channel < 3; channel++) {
          buffer[index + channel] =
            (splat.rgb[channel] * srcA + buffer[index + channel] * dstA * (1 - srcA)) / outA
        }
        buffer[index + 3] = outA
      }
    }
  }
  const rgb = new Float32Array(width * height * 3)
  for (let i = 0; i < width * height; i++) {
    rgb[i * 3] = buffer[i * 4]
    rgb[i * 3 + 1] = buffer[i * 4 + 1]
    rgb[i * 3 + 2] = buffer[i * 4 + 2]
  }
  return rgb
}

export function likeness(player: Float32Array, target: Float32Array): number {
  let weight = 0
  let error = 0
  for (let i = 0; i < target.length; i += 3) {
    const ink =
      (Math.abs(target[i] - BLOB_PAPER[0]) +
        Math.abs(target[i + 1] - BLOB_PAPER[1]) +
        Math.abs(target[i + 2] - BLOB_PAPER[2])) /
      3
    const importance = 0.12 + ink / 255
    const diff =
      (Math.abs(player[i] - target[i]) +
        Math.abs(player[i + 1] - target[i + 1]) +
        Math.abs(player[i + 2] - target[i + 2])) /
      3
    error += importance * diff
    weight += importance
  }
  return 1 - error / weight / 255
}

export type DeskAction = 'think' | 'calc' | 'lookup' | 'read' | 'answer'
export type DeskPhase = 'think' | 'tool' | 'read' | 'next'
export type DeskLast = 'none' | 'five' | 'miss'

export interface TraceLine {
  title: string
  body: string
}

export interface DeskState {
  phase: DeskPhase
  pending: 'calc' | 'lookup' | null
  last: DeskLast
  won: boolean
  trace: TraceLine[]
  say: string
}

export function deskStart(): DeskState {
  return {
    phase: 'think',
    pending: null,
    last: 'none',
    won: false,
    trace: [{ title: 'Goal', body: 'Write 2 + 3 in the ledger.' }],
    say: 'Press Think. It is the lit button.',
  }
}

export function deskLegal(state: DeskState): DeskAction[] {
  if (state.won) return []
  if (state.phase === 'think') return ['think']
  if (state.phase === 'tool') return ['calc', 'lookup']
  if (state.phase === 'read') return ['read']
  return ['think', 'answer']
}

function deskBlock(state: DeskState): string {
  if (state.phase === 'think') return 'Think before you reach for a tool.'
  if (state.phase === 'tool') return 'A thought is open. Pick the calculator or the log.'
  if (state.phase === 'read') return 'Read what came back before you do anything else.'
  return 'Write the answer, or think again.'
}

export interface ShelfFact {
  id: string
  text: string
  tags: readonly string[]
}

export const SHELF_FACTS: readonly ShelfFact[] = [
  { id: 'key', text: 'The kiln key hangs on a nail.', tags: ['kiln', 'key', 'nail'] },
  { id: 'gate', text: 'The gate code is 19.', tags: ['gate', 'code', '19'] },
  { id: 'book', text: 'The green book is under the bench.', tags: ['book', 'bench', 'green'] },
  { id: 'lane', text: 'Elara walks the lane at dusk.', tags: ['lane', 'dusk', 'walk'] },
]

export const SHELF_WINDOW = 3
export const SHELF_ANSWER = 'key'

export function shelfWindow(shift: number): ShelfFact[] {
  const start = Math.min(Math.max(0, shift), SHELF_FACTS.length - SHELF_WINDOW)
  return SHELF_FACTS.slice(start, start + SHELF_WINDOW)
}

export function shelfLookup(query: string): ShelfFact | null {
  const words = query
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((word) => word.length >= 3 || /^\d+$/.test(word))
  if (words.length === 0) return null
  return (
    SHELF_FACTS.find((fact) =>
      fact.tags.some((tag) => words.some((word) => tag === word || tag.includes(word) || word.includes(tag))),
    ) ?? null
  )
}

export function deskStep(state: DeskState, action: DeskAction): DeskState {
  if (state.won) return state
  if (!deskLegal(state).includes(action)) return { ...state, say: deskBlock(state) }
  if (action === 'think') {
    const again = state.trace.some((line) => line.title === 'Think')
    return {
      ...state,
      phase: 'tool',
      say: 'Now pick a tool.',
      trace: [
        ...state.trace,
        {
          title: 'Think',
          body: again
            ? 'Use what you just read. The calculator knows sums. The log may not.'
            : 'This is 2 + 3. The calculator knows sums. The village log may not.',
        },
      ],
    }
  }
  if (action === 'calc' || action === 'lookup') {
    return {
      ...state,
      phase: 'read',
      pending: action,
      say: 'The tool finished. Read it before you write in the ledger.',
      trace: [
        ...state.trace,
        {
          title: action === 'calc' ? 'Calculator' : 'Village log',
          body: action === 'calc' ? 'The calculator ran.' : 'The log was checked.',
        },
      ],
    }
  }
  if (action === 'read') {
    const five = state.pending === 'calc'
    return {
      ...state,
      phase: 'next',
      pending: null,
      last: five ? 'five' : 'miss',
      say: five ? 'You read 5. Write it, or think again.' : 'The log had no sum. Think again.',
      trace: [...state.trace, { title: 'Observe', body: five ? '5' : 'No entry for 2 + 3.' }],
    }
  }
  if (state.last !== 'five') {
    return { ...state, say: 'You can only write a sum you have actually read.' }
  }
  return {
    ...state,
    won: true,
    say: 'Think, act, observe. The ledger opened only after you read the tool.',
    trace: [...state.trace, { title: 'Ledger', body: '2 + 3 = 5' }],
  }
}
