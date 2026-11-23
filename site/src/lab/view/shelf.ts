import { SHELF_ANSWER, shelfLookup, shelfWindow, type ShelfFact } from '../model'
import type { BenchHandle, BenchHooks } from '../types'

export function mountShelf(host: HTMLElement, hooks: BenchHooks): BenchHandle {
  let shift = 0
  let found: ShelfFact | null = null
  let sealed = hooks.alreadySealed
  let moved = false

  host.innerHTML = `
    <section class="bench">
      <div class="instrument light">
        <ol class="tape" id="tape"></ol>
        <p class="ask" id="ask" hidden>Where is the kiln key?</p>
      </div>
      <aside class="plate">
        <h2 id="shelf-title">Read three lines</h2>
        <p id="say" aria-live="polite"></p>
        <div class="actions">
          <button type="button" class="act" id="shift">Let one line leave</button>
        </div>
        <form id="finder">
          <label class="slider" for="query">Search the store
            <input id="query" type="search" autocomplete="off" placeholder="try kiln or nail" />
          </label>
          <div class="actions">
            <button type="submit" class="act ghost-btn" id="search">Search</button>
            <button type="button" class="act" id="use" disabled>Use this line</button>
          </div>
        </form>
        <p class="found" id="found"></p>
        <p class="lesson" id="lesson"${sealed ? '' : ' hidden'}>The window forgets. A store remembers if your words touch the line.</p>
      </aside>
    </section>
  `

  const tape = host.querySelector<HTMLOListElement>('#tape')!
  const ask = host.querySelector<HTMLElement>('#ask')!
  const title = host.querySelector<HTMLElement>('#shelf-title')!
  const say = host.querySelector<HTMLElement>('#say')!
  const shiftBtn = host.querySelector<HTMLButtonElement>('#shift')!
  const form = host.querySelector<HTMLFormElement>('#finder')!
  const query = host.querySelector<HTMLInputElement>('#query')!
  const use = host.querySelector<HTMLButtonElement>('#use')!
  const foundEl = host.querySelector<HTMLElement>('#found')!
  const lesson = host.querySelector<HTMLElement>('#lesson')!

  function paint(note?: string) {
    const lines = shelfWindow(shift)
    tape.replaceChildren()
    for (const fact of lines) {
      const item = document.createElement('li')
      item.textContent = fact.text
      if (moved && !hooks.reducedMotion) item.classList.add('rise')
      tape.append(item)
    }
    ask.hidden = !moved
    shiftBtn.hidden = moved
    title.textContent = sealed ? 'The line came back' : moved ? 'Search the store' : 'Read three lines'
    if (note) {
      say.textContent = note
    } else if (!moved) {
      say.textContent = 'One line is the kiln key. Press the button and it will leave.'
    } else if (!found) {
      say.textContent = 'The key left. Type kiln or nail, then search.'
    } else if (found.id === SHELF_ANSWER && sealed) {
      say.textContent = 'The window forgot that line. The store still had it.'
    } else if (found.id === SHELF_ANSWER) {
      say.textContent = 'That line was off the tape. Use it.'
    } else {
      say.textContent = 'That line is about something else. Try words from the question.'
    }
    foundEl.textContent = found ? found.text : ''
    use.disabled = found?.id !== SHELF_ANSWER
    lesson.hidden = !sealed
    query.disabled = !moved
  }

  function onShift() {
    shift = 1
    moved = true
    found = null
    paint()
    query.focus()
  }

  function onSearch(event: Event) {
    event.preventDefault()
    if (!moved) {
      say.textContent = 'Read the tape first. The store matters after a line falls off.'
      return
    }
    found = shelfLookup(query.value)
    paint(found ? undefined : 'Nothing in the store matches those words.')
  }

  function onUse() {
    if (found?.id !== SHELF_ANSWER) return
    if (!sealed) {
      sealed = true
      hooks.onSeal()
    }
    paint()
  }

  shiftBtn.addEventListener('click', onShift)
  form.addEventListener('submit', onSearch)
  use.addEventListener('click', onUse)
  paint()

  return {
    destroy() {
      shiftBtn.removeEventListener('click', onShift)
      form.removeEventListener('submit', onSearch)
      use.removeEventListener('click', onUse)
    },
  }
}
