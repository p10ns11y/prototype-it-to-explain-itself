import { nextStop, stopById } from './brief'
import { mountBrief } from './brief-view'
import { readStamps, writeStamp } from './progress'
import { BENCHES } from './registry'
import { isBenchId, type BenchHandle, type BenchId } from './types'

function benchFromHash(): BenchId {
  const raw = location.hash.replace(/^#/, '')
  return isBenchId(raw) ? raw : 'kiln'
}

export function boot(root: HTMLElement) {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  let stamps = readStamps()
  let handle: BenchHandle | null = null

  root.innerHTML = `
    <header class="top">
      <div>
        <h1 id="bench-title"></h1>
        <p class="lede" id="bench-gist"></p>
      </div>
      <p class="score" id="score"></p>
    </header>
    <nav class="path" id="path" aria-label="Benches"></nav>
    <a id="next-step" class="next-step"></a>
    <div id="stage"></div>
    <div id="brief"></div>
    <footer class="foot">
      <a href="/concepts">Reading</a>
      <a href="/reflect-and-attempt-quizz.html">Recall cards</a>
    </footer>
  `

  const title = root.querySelector<HTMLElement>('#bench-title')!
  const gist = root.querySelector<HTMLElement>('#bench-gist')!
  const score = root.querySelector<HTMLElement>('#score')!
  const path = root.querySelector<HTMLElement>('#path')!
  const nextStep = root.querySelector<HTMLAnchorElement>('#next-step')!
  const stage = root.querySelector<HTMLElement>('#stage')!
  const brief = root.querySelector<HTMLElement>('#brief')!

  const buttons = new Map<BenchId, HTMLButtonElement>()
  for (const bench of BENCHES) {
    const button = document.createElement('button')
    button.type = 'button'
    button.innerHTML = `<span class="seal-dot"></span><span></span>`
    button.querySelector('span:last-child')!.textContent = `${BENCHES.indexOf(bench) + 1} ${bench.name}`
    button.addEventListener('click', () => {
      if (location.hash === `#${bench.id}`) return
      location.hash = bench.id
    })
    path.append(button)
    buttons.set(bench.id, button)
  }

  function paintChrome(id: BenchId) {
    const bench = BENCHES.find((item) => item.id === id)!
    title.textContent = bench.name
    gist.textContent = bench.gist
    document.title = `${bench.name} · The workshop`
    for (const [benchId, button] of buttons) {
      button.setAttribute('aria-current', benchId === id ? 'true' : 'false')
      button.querySelector('.seal-dot')!.classList.toggle('on', stamps.has(benchId))
    }
    const index = BENCHES.findIndex((item) => item.id === id)
    const next = nextStop(id)
    score.textContent = `Step ${index + 1} of ${BENCHES.length}`
    if (!next) {
      nextStep.hidden = true
    } else {
      nextStep.hidden = false
      nextStep.href = `#${next.id}`
      nextStep.textContent = `Next. ${next.name}`
    }
  }

  function show(id: BenchId) {
    handle?.destroy()
    stage.replaceChildren()
    const bench = BENCHES.find((item) => item.id === id)!
    paintChrome(id)
    mountBrief(brief, stopById(id))
    handle = bench.mount(stage, {
      reducedMotion,
      alreadySealed: stamps.has(id),
      onSeal() {
        stamps = writeStamp(id)
        paintChrome(id)
      },
    })
  }

  if (!isBenchId(location.hash.replace(/^#/, ''))) {
    history.replaceState(null, '', '#kiln')
  }
  window.addEventListener('hashchange', () => show(benchFromHash()))
  show(benchFromHash())
}
