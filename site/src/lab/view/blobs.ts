import {
  BLOB_H,
  BLOB_SEAL,
  BLOB_W,
  SCENE,
  SWATCHES,
  likeness,
  renderSplats,
  starterSplats,
  type Splat,
} from '../model'
import type { BenchHandle, BenchHooks } from '../types'

function blit(canvas: HTMLCanvasElement, rgb: Float32Array) {
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  const image = ctx.createImageData(BLOB_W, BLOB_H)
  for (let i = 0; i < BLOB_W * BLOB_H; i++) {
    image.data[i * 4] = rgb[i * 3]
    image.data[i * 4 + 1] = rgb[i * 3 + 1]
    image.data[i * 4 + 2] = rgb[i * 3 + 2]
    image.data[i * 4 + 3] = 255
  }
  ctx.putImageData(image, 0, 0)
}

export function mountBlobs(host: HTMLElement, hooks: BenchHooks): BenchHandle {
  const splats: Splat[] = starterSplats()
  let active = 0
  let dragging = false
  let sealed = hooks.alreadySealed
  const scene = renderSplats(SCENE)

  host.innerHTML = `
    <section class="bench">
      <div class="instrument light">
        <div class="pair">
          <figure>
            <canvas id="scene" width="${BLOB_W}" height="${BLOB_H}"></canvas>
            <figcaption>The scene</figcaption>
          </figure>
          <figure>
            <canvas id="yours" width="${BLOB_W}" height="${BLOB_H}" tabindex="0" aria-label="Your blobs. Drag a blob, or use the arrow keys."></canvas>
            <figcaption>Your blobs</figcaption>
          </figure>
        </div>
        <p class="meter" id="meter"></p>
      </div>
      <aside class="plate">
        <h2>Match the scene</h2>
        <p>Drag each blob onto a dot. Use the color from the scene. Seal appears around ${Math.round(BLOB_SEAL * 100)}%.</p>
        <div class="blob-picks" id="picks"></div>
        <div class="swatches" id="swatches"></div>
        <label class="slider">Radius <output id="radius-out"></output>
          <input id="radius" type="range" min="8" max="46" step="1" />
        </label>
        <div class="actions">
          <button type="button" class="act" id="seal">Seal this match</button>
        </div>
        <p class="lesson" id="lesson"${sealed ? '' : ' hidden'}>A scene can be a few soft blobs you can move.</p>
      </aside>
    </section>
  `

  const sceneCanvas = host.querySelector<HTMLCanvasElement>('#scene')!
  const yours = host.querySelector<HTMLCanvasElement>('#yours')!
  const meter = host.querySelector<HTMLElement>('#meter')!
  const picks = host.querySelector<HTMLElement>('#picks')!
  const swatches = host.querySelector<HTMLElement>('#swatches')!
  const radius = host.querySelector<HTMLInputElement>('#radius')!
  const radiusOut = host.querySelector<HTMLOutputElement>('#radius-out')!
  const seal = host.querySelector<HTMLButtonElement>('#seal')!
  const lesson = host.querySelector<HTMLElement>('#lesson')!
  blit(sceneCanvas, scene)

  const pickButtons = splats.map((_, index) => {
    const button = document.createElement('button')
    button.type = 'button'
    button.className = 'pick'
    button.textContent = `Blob ${index + 1}`
    button.addEventListener('click', () => {
      active = index
      paint()
    })
    picks.append(button)
    return button
  })

  const swatchButtons = SWATCHES.map((rgb) => {
    const button = document.createElement('button')
    button.type = 'button'
    button.className = 'swatch'
    button.style.background = `rgb(${rgb.join(',')})`
    button.setAttribute('aria-label', `Color ${rgb.join(' ')}`)
    button.addEventListener('click', () => {
      splats[active].rgb = [rgb[0], rgb[1], rgb[2]]
      paint()
    })
    swatches.append(button)
    return button
  })

  function pointOf(event: PointerEvent) {
    const rect = yours.getBoundingClientRect()
    return {
      x: ((event.clientX - rect.left) / rect.width) * BLOB_W,
      y: ((event.clientY - rect.top) / rect.height) * BLOB_H,
    }
  }

  function paint() {
    const rgb = renderSplats(splats)
    blit(yours, rgb)
    const ctx = yours.getContext('2d')
    const splat = splats[active]
    if (ctx) {
      ctx.beginPath()
      ctx.arc(splat.x, splat.y, splat.sigma, 0, Math.PI * 2)
      ctx.strokeStyle = 'rgba(36, 28, 20, 0.75)'
      ctx.lineWidth = 1.25
      ctx.setLineDash([3, 3])
      ctx.stroke()
      ctx.setLineDash([])
      for (const spot of SCENE) {
        ctx.beginPath()
        ctx.arc(spot.x, spot.y, 3.5, 0, Math.PI * 2)
        ctx.fillStyle = 'rgba(36, 28, 20, 0.55)'
        ctx.fill()
      }
    }
    const score = likeness(rgb, scene)
    meter.textContent = `${Math.round(score * 100)}% like the scene`
    seal.disabled = score < BLOB_SEAL
    seal.textContent = sealed ? 'Sealed' : 'Seal this match'
    lesson.hidden = !sealed
    radius.value = String(Math.round(splat.sigma))
    radiusOut.textContent = radius.value
    pickButtons.forEach((button, index) => button.classList.toggle('on', index === active))
    swatchButtons.forEach((button, index) => {
      const color = SWATCHES[index]
      const same = splat.rgb[0] === color[0] && splat.rgb[1] === color[1] && splat.rgb[2] === color[2]
      button.classList.toggle('on', same)
    })
  }

  function onPointerDown(event: PointerEvent) {
    const point = pointOf(event)
    let best = 0
    let bestDistance = Infinity
    splats.forEach((splat, index) => {
      const dx = splat.x - point.x
      const dy = splat.y - point.y
      const distance = dx * dx + dy * dy
      if (distance < bestDistance) {
        best = index
        bestDistance = distance
      }
    })
    active = best
    dragging = true
    yours.setPointerCapture(event.pointerId)
    paint()
  }

  function onPointerMove(event: PointerEvent) {
    if (!dragging) return
    const point = pointOf(event)
    splats[active].x = Math.min(BLOB_W - 2, Math.max(2, point.x))
    splats[active].y = Math.min(BLOB_H - 2, Math.max(2, point.y))
    paint()
  }

  function onPointerUp() {
    dragging = false
  }

  function onRadius() {
    splats[active].sigma = Number(radius.value)
    paint()
  }

  function onSeal() {
    const score = likeness(renderSplats(splats), scene)
    if (score < BLOB_SEAL) return
    if (!sealed) {
      sealed = true
      hooks.onSeal()
    }
    paint()
  }

  function onKey(event: KeyboardEvent) {
    if (event.target instanceof HTMLInputElement) return
    const nudge = event.shiftKey ? 8 : 3
    if (event.key === 'ArrowLeft') splats[active].x -= nudge
    else if (event.key === 'ArrowRight') splats[active].x += nudge
    else if (event.key === 'ArrowUp') splats[active].y -= nudge
    else if (event.key === 'ArrowDown') splats[active].y += nudge
    else return
    event.preventDefault()
    splats[active].x = Math.min(BLOB_W - 2, Math.max(2, splats[active].x))
    splats[active].y = Math.min(BLOB_H - 2, Math.max(2, splats[active].y))
    paint()
  }

  yours.addEventListener('pointerdown', onPointerDown)
  yours.addEventListener('pointermove', onPointerMove)
  yours.addEventListener('pointerup', onPointerUp)
  yours.addEventListener('pointercancel', onPointerUp)
  radius.addEventListener('input', onRadius)
  seal.addEventListener('click', onSeal)
  window.addEventListener('keydown', onKey)
  paint()

  return {
    destroy() {
      yours.removeEventListener('pointerdown', onPointerDown)
      yours.removeEventListener('pointermove', onPointerMove)
      yours.removeEventListener('pointerup', onPointerUp)
      yours.removeEventListener('pointercancel', onPointerUp)
      radius.removeEventListener('input', onRadius)
      seal.removeEventListener('click', onSeal)
      window.removeEventListener('keydown', onKey)
    },
  }
}
