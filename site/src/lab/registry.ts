import { PATH } from './brief'
import type { Bench, BenchId } from './types'
import { mountBlobs } from './view/blobs'
import { mountDesk } from './view/desk'
import { mountGrain } from './view/grain'
import { mountKiln } from './view/kiln'
import { mountShelf } from './view/shelf'

const MOUNTS: Record<BenchId, Bench['mount']> = {
  kiln: mountKiln,
  desk: mountDesk,
  shelf: mountShelf,
  grain: mountGrain,
  blobs: mountBlobs,
}

export const BENCHES: readonly Bench[] = PATH.map((stop) => ({
  id: stop.id,
  name: stop.name,
  gist: stop.gist,
  note: `/concepts#${stop.id}`,
  mount: MOUNTS[stop.id],
}))
