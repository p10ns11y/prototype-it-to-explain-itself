import {
  KILN_COOL,
  KILN_HOT,
  KILN_MAX,
  KILN_MIN,
  KILN_WORDS,
  kilnCoolEnough,
  kilnHotEnough,
  kilnMode,
  kilnSample,
  kilnShares,
} from '../model'
import type { BenchHandle, BenchHooks } from '../types'

export function mountKiln(host: HTMLElement, hooks: BenchHooks): BenchHandle {
  let temperature = 1
  let call: 0 | 1 | 2 = 0
  let locked = ''
  let ghost = ''
  let sameWord = false
  let sealed = hooks.alreadySealed

  host.innerHTML = `
    <section class="bench">
      <div class="instrument">
        <p class="utter">Elara took the <em id="locked">____</em></p>
        <div class="vessels" id="vessels"></div>
        <p class="ghost" id="ghost"></p>
        <p class="sr" id="share-live" aria-live="polite"></p>
      </div>
      <aside class="plate">
        <h2 id="call-title"></h2>
        <p id="call-body"></p>
        <label class="slider">Heat <output id="heat-out"></output>
          <input id="heat" type="range" min="${KILN_MIN}" max="${KILN_MAX}" step="0.02" value="1" />
        </label>
        <div class="actions">
          <button type="button" class="act" id="lock">Lock the sure word</button>
          <button type="button" class="act" id="sample" hidden>Draw once</button>
          <button type="button" class="act ghost-btn" id="replay" hidden>Run it again</button>
        </div>
        <p class="lesson" id="lesson"${sealed ? '' : ' hidden'}></p>
      </aside>
    </section>
  `

  const vessels = host.querySelector<HTMLElement>('#vessels')!
  const bars = KILN_WORDS.map((word) => {
    const vessel = document.createElement('div')
    vessel.className = 'vessel'
    vessel.innerHTML = `<span class="pct"></span><div class="level"></div><div class="liquid"></div><span class="word"></span>`
    vessel.querySelector('.word')!.textContent = word.word
    vessels.append(vessel)
    return {
      root: vessel,
      pct: vessel.querySelector<HTMLElement>('.pct')!,
      liquid: vessel.querySelector<HTMLElement>('.liquid')!,
      mark: vessel.querySelector<HTMLElement>('.level')!,
    }
  })

  const lockedEl = host.querySelector<HTMLElement>('#locked')!
  const ghostEl = host.querySelector<HTMLElement>('#ghost')!
  const live = host.querySelector<HTMLElement>('#share-live')!
  const title = host.querySelector<HTMLElement>('#call-title')!
  const body = host.querySelector<HTMLElement>('#call-body')!
  const lesson = host.querySelector<HTMLElement>('#lesson')!
  const heat = host.querySelector<HTMLInputElement>('#heat')!
  const heatOut = host.querySelector<HTMLOutputElement>('#heat-out')!
  const lock = host.querySelector<HTMLButtonElement>('#lock')!
  const sample = host.querySelector<HTMLButtonElement>('#sample')!
  const replay = host.querySelector<HTMLButtonElement>('#replay')!

  lesson.textContent = 'Heat does not add words. It changes how the chance is shared.'

  function paintShares() {
    const shares = kilnShares(temperature)
    const line = call === 1 ? KILN_HOT : KILN_COOL
    shares.forEach((share, index) => {
      const bar = bars[index]
      const percent = Math.round(share.p * 100)
      bar.liquid.style.transform = `scaleY(${share.p})`
      bar.pct.textContent = `${percent}%`
      bar.mark.style.bottom = `${line * 100}%`
      bar.mark.hidden = call === 2
      bar.root.classList.toggle('sure', call === 0 && kilnCoolEnough(temperature))
      bar.root.classList.toggle('flat', call === 1 && kilnHotEnough(temperature))
    })
    heatOut.textContent = temperature.toFixed(2)
    heat.value = String(temperature)
    lock.disabled = !kilnCoolEnough(temperature)
    lock.textContent = kilnCoolEnough(temperature) ? `Lock “${kilnMode(temperature)}”` : 'Lock the sure word'
    sample.disabled = !kilnHotEnough(temperature)
    live.textContent = shares.map((share) => `${share.word} ${Math.round(share.p * 100)} percent`).join(', ')
  }

  function paintCall() {
    lock.hidden = call !== 0
    sample.hidden = call !== 1
    replay.hidden = call !== 2
    heat.disabled = call === 2
    if (call === 0) {
      title.textContent = 'Drag left'
      body.textContent = 'Stop when one word passes 70%. Then press the button.'
    } else if (call === 1) {
      title.textContent = 'Drag right'
      body.textContent = sameWord
        ? 'Same word. Draw again.'
        : 'Stop when no word is above 34%. Draw until a different word appears.'
    } else {
      title.textContent = 'That is heat'
      body.textContent = 'Low heat picks the sure word. High heat lets another word win.'
    }
    lesson.hidden = !sealed && call !== 2
    lockedEl.textContent = locked || '____'
    ghostEl.textContent = ghost ? `A hot draw came up “${ghost}”.` : ''
    paintShares()
  }

  function onHeat() {
    temperature = Number(heat.value)
    sameWord = false
    paintShares()
  }

  function onLock() {
    if (!kilnCoolEnough(temperature)) return
    locked = kilnMode(temperature)
    call = 1
    temperature = 1
    sameWord = false
    paintCall()
  }

  function onSample() {
    if (!kilnHotEnough(temperature)) return
    const drawn = kilnSample(temperature, Math.random())
    ghost = drawn
    if (drawn === locked) {
      sameWord = true
      paintCall()
      return
    }
    sameWord = false
    call = 2
    if (!sealed) {
      sealed = true
      hooks.onSeal()
    }
    paintCall()
  }

  function onReplay() {
    call = 0
    temperature = 1
    locked = ''
    ghost = ''
    sameWord = false
    paintCall()
  }

  heat.addEventListener('input', onHeat)
  lock.addEventListener('click', onLock)
  sample.addEventListener('click', onSample)
  replay.addEventListener('click', onReplay)
  paintCall()

  return {
    destroy() {
      heat.removeEventListener('input', onHeat)
      lock.removeEventListener('click', onLock)
      sample.removeEventListener('click', onSample)
      replay.removeEventListener('click', onReplay)
    },
  }
}
