import { isBenchId, type BenchId } from './types'

const KEY = 'pitei-workshop-v1'

export function readStamps(): Set<BenchId> {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return new Set()
    const parsed: unknown = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return new Set()
    const stamps = (parsed as { stamps?: unknown }).stamps
    if (!Array.isArray(stamps)) return new Set()
    const ids = stamps.filter((item): item is BenchId => typeof item === 'string' && isBenchId(item))
    return new Set(ids)
  } catch {
    return new Set()
  }
}

export function writeStamp(id: BenchId): Set<BenchId> {
  const next = readStamps()
  next.add(id)
  localStorage.setItem(KEY, JSON.stringify({ stamps: [...next] }))
  return next
}
