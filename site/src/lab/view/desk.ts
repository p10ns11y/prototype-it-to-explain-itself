import { deskLegal, deskStart, deskStep, type DeskAction } from '../model'
import type { BenchHandle, BenchHooks } from '../types'

const MOVES: { id: DeskAction; label: string; hint: string }[] = [
  { id: 'think', label: '1. Think', hint: 'Start here' },
  { id: 'calc', label: '2. Calculator', hint: 'This tool can add' },
  { id: 'lookup', label: 'or the village log', hint: 'This one may not know' },
  { id: 'read', label: '3. Read the result', hint: 'Look before you write' },
  { id: 'answer', label: '4. Write 2 + 3', hint: 'Only after you read 5' },
]

export function mountDesk(host: HTMLElement, hooks: BenchHooks): BenchHandle {
  let state = deskStart()
  let sealed = hooks.alreadySealed

  host.innerHTML = `
    <section class="bench">
      <div class="instrument light">
        <div class="trace" id="trace"></div>
      </div>
      <aside class="plate">
        <h2>Press the lit button</h2>
        <p id="say" aria-live="polite"></p>
        <div class="moves" id="moves"></div>
        <p class="lesson" id="lesson"${sealed ? '' : ' hidden'}>Think, use a tool, read the result, then write.</p>
        <div class="actions">
          <button type="button" class="act ghost-btn" id="replay">Reset the desk</button>
        </div>
      </aside>
    </section>
  `

  const trace = host.querySelector<HTMLElement>('#trace')!
  const say = host.querySelector<HTMLElement>('#say')!
  const moves = host.querySelector<HTMLElement>('#moves')!
  const lesson = host.querySelector<HTMLElement>('#lesson')!
  const replay = host.querySelector<HTMLButtonElement>('#replay')!

  const buttons = new Map<DeskAction, HTMLButtonElement>()
  for (const move of MOVES) {
    const button = document.createElement('button')
    button.type = 'button'
    button.className = 'move'
    button.innerHTML = `<strong></strong><span></span>`
    button.querySelector('strong')!.textContent = move.label
    button.querySelector('span')!.textContent = move.hint
    button.addEventListener('click', () => act(move.id, button))
    button.addEventListener('animationend', () => button.classList.remove('shake'))
    moves.append(button)
    buttons.set(move.id, button)
  }

  function paint() {
    trace.replaceChildren()
    state.trace.forEach((line, index) => {
      const card = document.createElement('article')
      card.className = index === state.trace.length - 1 ? 'card rise' : 'card'
      const title = document.createElement('h3')
      title.textContent = line.title
      const body = document.createElement('p')
      body.textContent = line.body
      card.append(title, body)
      trace.append(card)
    })
    trace.scrollTop = trace.scrollHeight
    say.textContent = state.say
    lesson.hidden = !(sealed || state.won)
    const legal = new Set(deskLegal(state))
    for (const [id, button] of buttons) {
      button.classList.toggle('legal', legal.has(id))
      button.disabled = state.won
    }
  }

  function act(action: DeskAction, button: HTMLButtonElement) {
    const allowed = deskLegal(state).includes(action)
    state = deskStep(state, action)
    if (!allowed) button.classList.add('shake')
    if (state.won && !sealed) {
      sealed = true
      hooks.onSeal()
    }
    paint()
  }

  function onReplay() {
    state = deskStart()
    paint()
  }

  replay.addEventListener('click', onReplay)
  paint()
  return {
    destroy() {
      replay.removeEventListener('click', onReplay)
    },
  }
}
