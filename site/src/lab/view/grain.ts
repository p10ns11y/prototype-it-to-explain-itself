import {
  GRAIN_LATE_AT,
  GRAIN_READY_AT,
  GRAIN_SIZE,
  GRAIN_STEPS,
  SHAPES,
  grainMoment,
  makeNoise,
  mixFrame,
  paintShape,
  type ShapeName,
} from '../model'
import type { BenchHandle, BenchHooks } from '../types'

const LABELS: Record<ShapeName, string> = { star: 'Star', house: 'House', ring: 'Ring' }
const SHOW_AT = Math.round((GRAIN_READY_AT + GRAIN_LATE_AT) / 2)

function icon(kind: ShapeName): string {
  if (kind === 'star') {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.4 14.7 8.8 21.6 9.4 16.4 14.1 18 20.8 12 17.2 6 20.8 7.6 14.1 2.4 9.4 9.3 8.8Z"/></svg>'
  }
  if (kind === 'house') {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 11.5 12 4l9 7.5V20a1 1 0 0 1-1 1h-5.2v-6.2H9.2V21H4a1 1 0 0 1-1-1Z"/></svg>'
  }
  return '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="7.2" fill="none" stroke="currentColor" stroke-width="3.2"/></svg>'
}

export function mountGrain(host: HTMLElement, hooks: BenchHooks): BenchHandle {
  let shape: ShapeName = 'star'
  let noise = makeNoise(GRAIN_SIZE, Math.random)
  let target = paintShape(shape)
  let step = 0
  let timer = 0
  let playing = false
  let sealed = hooks.alreadySealed
  let order: ShapeName[] = []
  let note = ''

  host.innerHTML = `
    <section class="bench">
      <div class="instrument">
        <canvas class="viewer" id="viewer" width="${GRAIN_SIZE}" height="${GRAIN_SIZE}"></canvas>
        <label class="slider light-slider">Step <output id="step-out"></output>
          <input id="step" type="range" min="0" max="${GRAIN_STEPS}" step="1" value="0" />
        </label>
      </div>
      <aside class="plate">
        <h2>Name the shape</h2>
        <p id="verdict" aria-live="polite"></p>
        <div class="choices" id="choices"></div>
        <div class="actions">
          <button type="button" class="act ghost-btn" id="play">${hooks.reducedMotion ? 'Step' : 'Play'}</button>
          <button type="button" class="act ghost-btn" id="again">New grain</button>
        </div>
        <p class="lesson" id="lesson"${sealed ? '' : ' hidden'}>The shape shows up while the picture is still noisy.</p>
      </aside>
    </section>
  `

  const canvas = host.querySelector<HTMLCanvasElement>('#viewer')!
  const ctx = canvas.getContext('2d')!
  const stepInput = host.querySelector<HTMLInputElement>('#step')!
  const stepOut = host.querySelector<HTMLOutputElement>('#step-out')!
  const play = host.querySelector<HTMLButtonElement>('#play')!
  const again = host.querySelector<HTMLButtonElement>('#again')!
  const choices = host.querySelector<HTMLElement>('#choices')!
  const verdictEl = host.querySelector<HTMLElement>('#verdict')!
  const lesson = host.querySelector<HTMLElement>('#lesson')!

  function draw() {
    const frame = mixFrame(noise, target, step / GRAIN_STEPS)
    ctx.putImageData(new ImageData(new Uint8ClampedArray(frame), GRAIN_SIZE, GRAIN_SIZE), 0, 0)
    stepInput.value = String(step)
    stepOut.textContent = `${step} / ${GRAIN_STEPS}`
  }

  function stop() {
    playing = false
    window.clearTimeout(timer)
    timer = 0
    play.textContent = hooks.reducedMotion ? 'Step' : 'Play'
  }

  function buildChoices() {
    choices.replaceChildren()
    for (const name of order) {
      const button = document.createElement('button')
      button.type = 'button'
      button.className = 'choice'
      button.innerHTML = `${icon(name)}<span>${LABELS[name]}</span>`
      button.addEventListener('click', () => choose(name))
      choices.append(button)
    }
  }

  function sync() {
    const moment = grainMoment(step)
    choices.hidden = moment !== 'ready' || sealed
    lesson.hidden = !sealed
    if (note) verdictEl.textContent = note
    else if (sealed) verdictEl.textContent = 'The shape shows up while the picture is still noisy.'
    else if (moment === 'early') verdictEl.textContent = 'Move the step forward. The shape is not clear yet.'
    else if (moment === 'late') verdictEl.textContent = 'Move the step back. Name it while it is still noisy.'
    else verdictEl.textContent = 'Name the shape. It is still noisy on purpose.'
    draw()
  }

  function arrive() {
    if (hooks.reducedMotion || step >= SHOW_AT) {
      step = Math.max(step, SHOW_AT)
      sync()
      return
    }
    sync()
    playing = true
    play.textContent = 'Pause'
    const tick = () => {
      if (!playing) return
      if (step >= SHOW_AT) {
        stop()
        sync()
        return
      }
      step += 1
      sync()
      timer = window.setTimeout(tick, 120)
    }
    timer = window.setTimeout(tick, 120)
  }

  function fresh() {
    stop()
    shape = SHAPES[Math.floor(Math.random() * SHAPES.length)]
    noise = makeNoise(GRAIN_SIZE, Math.random)
    target = paintShape(shape)
    order = [...SHAPES].sort(() => Math.random() - 0.5)
    step = 0
    note = ''
    buildChoices()
    arrive()
  }

  function onPlay() {
    if (hooks.reducedMotion) {
      step = Math.min(GRAIN_STEPS, step + 1)
      note = ''
      sync()
      return
    }
    if (playing) {
      stop()
      sync()
      return
    }
    playing = true
    play.textContent = 'Pause'
    const tick = () => {
      if (!playing) return
      if (step >= GRAIN_STEPS) {
        stop()
        sync()
        return
      }
      step += 1
      note = ''
      sync()
      if (playing) timer = window.setTimeout(tick, 120)
    }
    timer = window.setTimeout(tick, 120)
  }

  function choose(name: ShapeName) {
    if (grainMoment(step) !== 'ready') {
      note = 'Move the step into the noisy middle, then name it.'
      sync()
      return
    }
    if (name !== shape) {
      note = 'Not that one. Look at the silhouette and try again.'
      sync()
      return
    }
    note = ''
    if (!sealed) {
      sealed = true
      hooks.onSeal()
    }
    sync()
  }

  function onStep() {
    stop()
    step = Number(stepInput.value)
    note = ''
    sync()
  }

  play.addEventListener('click', onPlay)
  again.addEventListener('click', fresh)
  stepInput.addEventListener('input', onStep)
  fresh()

  return {
    destroy() {
      stop()
      play.removeEventListener('click', onPlay)
      again.removeEventListener('click', fresh)
      stepInput.removeEventListener('input', onStep)
    },
  }
}
