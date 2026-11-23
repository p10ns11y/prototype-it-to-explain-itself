export type BenchId = 'kiln' | 'desk' | 'shelf' | 'grain' | 'blobs'

export const BENCH_IDS: readonly BenchId[] = ['kiln', 'desk', 'shelf', 'grain', 'blobs']

export function isBenchId(value: string): value is BenchId {
  return (BENCH_IDS as readonly string[]).includes(value)
}

export interface BenchHooks {
  reducedMotion: boolean
  alreadySealed: boolean
  onSeal: () => void
}

export interface BenchHandle {
  destroy: () => void
}

export interface Bench {
  id: BenchId
  name: string
  gist: string
  note: string
  mount: (host: HTMLElement, hooks: BenchHooks) => BenchHandle
}
