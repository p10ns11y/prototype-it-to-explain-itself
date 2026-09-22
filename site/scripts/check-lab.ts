import { PATH } from '../src/lab/brief.ts'
import { BENCH_IDS } from '../src/lab/types.ts'
import {
  BLOB_SEAL,
  GRAIN_LATE_AT,
  GRAIN_READY_AT,
  GRAIN_SIZE,
  GRAIN_STEPS,
  KILN_COOL,
  KILN_HOT,
  KILN_MAX,
  KILN_MIN,
  SCENE,
  SHAPES,
  deskLegal,
  deskStart,
  deskStep,
  frameDistance,
  grainMoment,
  kilnCoolEnough,
  kilnHotEnough,
  kilnMode,
  kilnPeak,
  kilnSample,
  kilnShownPeak,
  likeness,
  makeNoise,
  SHELF_ANSWER,
  shelfLookup,
  shelfWindow,
  mixFrame,
  paintShape,
  renderSplats,
  starterSplats,
} from '../src/lab/model.ts'

let failed = 0

function assert(ok: boolean, message: string) {
  if (ok) {
    console.log(`ok  ${message}`)
    return
  }
  failed += 1
  console.error(`FAIL  ${message}`)
}

const coolPeak = kilnPeak(KILN_MIN)
const midPeak = kilnPeak(1)
const hotPeak = kilnPeak(KILN_MAX)
console.log(`kiln peaks  cool ${coolPeak.toFixed(3)}  mid ${midPeak.toFixed(3)}  hot ${hotPeak.toFixed(3)}`)
assert(coolPeak >= KILN_COOL, 'low heat can make one word own 70%')
assert(midPeak < KILN_COOL && midPeak > KILN_HOT, 'the starting heat wins neither call')
assert(hotPeak <= KILN_HOT, 'high heat flattens the tallest word under 34%')
assert(kilnCoolEnough(KILN_MIN) && !kilnCoolEnough(1), 'the shown percent, not the raw peak, opens the cool lock')
assert(kilnHotEnough(KILN_MAX) && !kilnHotEnough(1), 'the shown percent opens the hot draw')
let labelAgrees = false
for (let step = 0; step <= 120; step++) {
  const heat = Math.min(KILN_MAX, KILN_MIN + step * 0.02)
  if (kilnShownPeak(heat) <= 34 && kilnPeak(heat) > KILN_HOT && kilnHotEnough(heat)) labelAgrees = true
}
assert(labelAgrees, 'a bar that reads 34% is hot enough to draw')
assert(kilnMode(KILN_MIN) === 'kiln', 'the cooled mode is kiln')

const draws = new Set<string>()
for (let i = 0; i < 40; i++) draws.add(kilnSample(KILN_MAX, (i + 0.5) / 40))
assert(draws.size >= 3, 'a hot kiln can land on more than two words')

for (const shape of SHAPES) {
  const painted = paintShape(shape, 48)
  let ink = 0
  for (let i = 0; i < painted.length; i += 4) {
    if (painted[i] + painted[i + 1] + painted[i + 2] > 90) ink += 1
  }
  assert(ink > 40, `${shape} paints a visible mass (${ink} px)`)
}

let noiseSeed = 7
const noise = makeNoise(GRAIN_SIZE, () => {
  noiseSeed = (noiseSeed * 16807) % 2147483647
  return noiseSeed / 2147483647
})
const target = paintShape('star')
const startDistance = frameDistance(mixFrame(noise, target, 0), target)
const endDistance = frameDistance(mixFrame(noise, target, 1), target)
const midDistance = frameDistance(mixFrame(noise, target, 0.5), target)
console.log(`grain distance  start ${startDistance.toFixed(3)}  mid ${midDistance.toFixed(3)}  end ${endDistance.toFixed(3)}`)
assert(startDistance > midDistance && midDistance > endDistance, 'each step of denoise moves toward the shape')
assert(endDistance < 0.02, 'the last frame is the shape')
assert(grainMoment(GRAIN_READY_AT - 1) === 'early', 'before the window is too early')
assert(grainMoment(GRAIN_READY_AT) === 'ready' && grainMoment(GRAIN_LATE_AT) === 'ready', 'the catch window is open')
assert(grainMoment(GRAIN_LATE_AT + 1) === 'late', 'after the window the picture is too clean')
assert(GRAIN_STEPS > GRAIN_LATE_AT, 'the playhead can walk past the window')

const scene = renderSplats(SCENE)
const copied = likeness(renderSplats(SCENE), scene)
const started = likeness(renderSplats(starterSplats()), scene)
const blank = likeness(renderSplats([]), scene)
console.log(`blobs likeness  copy ${copied.toFixed(3)}  start ${started.toFixed(3)}  blank ${blank.toFixed(3)}  seal ${BLOB_SEAL}`)
assert(copied >= 0.98, 'copying the scene seals easily')
assert(started < BLOB_SEAL - 0.08, 'the starting pile is not already a seal')
assert(blank < BLOB_SEAL, 'an empty page does not seal')
const nudged = SCENE.map((splat) => ({ ...splat, x: splat.x + 6, y: splat.y + 4 }))
const nudgedScore = likeness(renderSplats(nudged), scene)
console.log(`blobs likeness  nudged ${nudgedScore.toFixed(3)}`)
assert(nudgedScore >= BLOB_SEAL, 'a close placement still seals, the target is not pixel-perfect')

function play(actions: Parameters<typeof deskStep>[1][]) {
  return actions.reduce((state, action) => deskStep(state, action), deskStart())
}

const won = play(['think', 'calc', 'read', 'answer'])
assert(won.won && won.trace.at(-1)?.body === '2 + 3 = 5', 'think, calc, read, answer seals the ledger')
assert(deskLegal(won).length === 0, 'a sealed desk has no further legal move')

const skipped = play(['answer'])
assert(!skipped.won && skipped.phase === 'think', 'answering first does not open the ledger')

const wrongTool = play(['think', 'lookup', 'read', 'answer'])
assert(!wrongTool.won && wrongTool.last === 'miss', 'the log cannot supply the sum')

const recovered = play(['think', 'lookup', 'read', 'think', 'calc', 'read', 'answer'])
assert(recovered.won, 'a missed lookup can still reach the calculator')

const unread = play(['think', 'calc', 'answer'])
assert(!unread.won && unread.phase === 'read', 'skipping the read is refused')

assert(PATH.map((stop) => stop.id).join() === BENCH_IDS.join(), 'the path and the bench ids are the same list')
for (const stop of PATH) {
  const foundations = stop.readings.filter((reading) => reading.kind === 'foundation')
  const current = stop.readings.filter((reading) => reading.kind === 'now')
  assert(foundations.length > 0 && current.length > 0, `${stop.name} has a foundation and a current reading`)
  assert(stop.readings.every((reading) => reading.href.startsWith('https://')), `${stop.name} readings are outside links`)
  assert(stop.hold.length > 20 && stop.now.length > 20, `${stop.name} says what sticks and what people do now`)
}
assert(shelfWindow(0).some((fact) => fact.id === SHELF_ANSWER), 'the key starts on the tape')
assert(!shelfWindow(1).some((fact) => fact.id === SHELF_ANSWER), 'the key falls off the tape')
assert(shelfLookup('kiln key')?.id === SHELF_ANSWER, 'searching kiln key finds the fallen line')
assert(shelfLookup('19')?.id === 'gate', 'a number can find the gate code')
assert(shelfLookup('zzz') === null, 'unknown words find nothing')
assert(shelfLookup('a') === null, 'a tiny query does not match everything')

if (failed > 0) {
  console.error(`${failed} check(s) failed`)
  throw new Error('workshop checks failed')
}
console.log('workshop checks passed')
