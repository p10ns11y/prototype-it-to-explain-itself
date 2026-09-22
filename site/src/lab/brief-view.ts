import { nextStop, type PathStop, type Reading } from './brief'

function readingLine(reading: Reading): HTMLLIElement {
  const item = document.createElement('li')
  const link = document.createElement('a')
  link.href = reading.href
  link.target = '_blank'
  link.rel = 'noopener noreferrer'
  link.textContent = reading.title
  const meta = document.createElement('p')
  const kind = reading.kind === 'foundation' ? 'Foundation' : 'Right now'
  meta.textContent = `${kind}. ${reading.by}, ${reading.year}. About ${reading.minutes} minutes. ${reading.why}`
  item.append(link, meta)
  return item
}

export function mountBrief(host: HTMLElement, stop: PathStop) {
  host.replaceChildren()
  const hold = document.createElement('p')
  hold.className = 'hold'
  hold.textContent = stop.hold

  const more = document.createElement('details')
  more.className = 'more'
  const summary = document.createElement('summary')
  summary.textContent = 'Why, and what to read'
  const hides = document.createElement('p')
  hides.textContent = stop.hides
  const now = document.createElement('p')
  now.textContent = stop.now
  const list = document.createElement('ol')
  list.className = 'readings'
  for (const reading of stop.readings) list.append(readingLine(reading))
  more.append(summary, hides, now, list)

  const next = nextStop(stop.id)
  const onward = document.createElement('p')
  onward.className = 'onward'
  if (next) {
    const link = document.createElement('a')
    link.href = `#${next.id}`
    link.textContent = `Next. ${next.name}`
    onward.append(link)
  } else {
    onward.textContent = 'That is the last machine. Open Why if you want the reading.'
  }

  const section = document.createElement('section')
  section.className = 'brief'
  section.append(hold, onward, more)
  host.append(section)
}
