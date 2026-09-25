import { useRef, useEffect, useCallback, useState } from 'react'
import { ema, sma, viewport, priceRange } from './replayMath'

/* The chart is the page now, so it is drawn rather than delegated: the replay
   needs to control the x-domain, the reveal edge and the act marks together,
   and a canvas says exactly what happens on each frame.

   Everything about WHAT is on screen lives in `replayMath`; this file is the
   pen. Semi-log is the default because O'Neil and IBD model books are drawn
   semi-log, and a 10x advance on a linear axis is a line lying along the floor. */

/* Four lines have to be told apart at a glance, and the candles already own
   blue and red — so the ladder cannot lean on hue alone. Each line differs from
   its neighbours on TWO channels (weight and dash), with one chromatic line to
   anchor the eye:

     10E   lightest, thin, dashed      the noisy one; it is meant to recede
     21E   accent, thickest, solid     the one coloured line — 强势股生命线，
                                       and the thickest because it is the one you trade off
     50    mid ink, medium, solid
     200   full ink, long dash         牛熊界; brightest, but kept thin so a long
                                       flat line does not out-shout the candles

   Andy, 2026-09-25: "均线颜色稍微要有区分 10E和21E没太多差别" — in dark mode
   the old pair resolved to #b0aaa2 and #979594, two greys a few points apart.
   Weight and dash carry the distinction even where colour cannot (print,
   colour-blindness), which is why they are not decoration here. */
const MA_LINES = [
  { period: 10, type: 'ema', tone: '--color-untested', width: 1, dash: [3, 3], label: '10E' },
  { period: 21, type: 'ema', tone: '--color-accent', width: 1.9, dash: null, label: '21E' },
  { period: 50, type: 'sma', tone: '--color-text-secondary', width: 1.4, dash: null, label: '50' },
  { period: 200, type: 'sma', tone: '--color-text-bold', width: 1.4, dash: [9, 4], label: '200' },
]

const token = name =>
  getComputedStyle(document.documentElement).getPropertyValue(name).trim()

/* The legend lives in the header row, not floating over the canvas: overlaid on
   the top right it sat on top of the price scale's own labels, which is how
   "50" and "200" ended up reading as "50 1→200". */
export function MaLegend() {
  return (
    <span className="flex items-center gap-2.5 flex-wrap">
      {MA_LINES.map(ma => (
        <span key={ma.label} className="flex items-center gap-1">
          <svg width="16" height="6" aria-hidden="true" className="shrink-0">
            <line x1="0" y1="3" x2="16" y2="3"
                  stroke={`var(${ma.tone})`} strokeWidth={ma.width}
                  strokeDasharray={ma.dash ? ma.dash.join(' ') : undefined} />
          </svg>
          <span className="text-[11px] font-mono text-[var(--color-text-muted)]">{ma.label}</span>
        </span>
      ))}
    </span>
  )
}

export default function ReplayChart({
  bars, cursor, windowSize, logScale = true, acts = [], height = 420, lowres = false,
  onScrub,
}) {
  const wrapRef = useRef(null)
  const canvasRef = useRef(null)
  const [width, setWidth] = useState(0)
  const [theme, setTheme] = useState(0)

  // A theme flip changes every colour we resolved to a literal; redraw on it.
  useEffect(() => {
    const observer = new MutationObserver(() => setTheme(t => t + 1))
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const onScheme = () => setTheme(t => t + 1)
    mq.addEventListener('change', onScheme)
    return () => { observer.disconnect(); mq.removeEventListener('change', onScheme) }
  }, [])

  useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const ro = new ResizeObserver(([e]) => setWidth(e.contentRect.width))
    ro.observe(el)
    setWidth(el.clientWidth)
    return () => ro.disconnect()
  }, [])

  const draw = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas || !bars?.length || !width) return
    const ctx = canvas.getContext('2d')
    const dpr = window.devicePixelRatio || 1
    canvas.width = width * dpr
    canvas.height = height * dpr
    canvas.style.height = `${height}px`
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, width, height)

    const padL = 8, padR = 62, padT = 8, padB = 22
    const volH = Math.round(height * 0.16)
    const plotW = width - padL - padR
    const plotH = height - padT - padB - volH - 6

    const { from, to, domain } = viewport(bars.length, cursor, windowSize)
    const range = priceRange(bars, from, to)
    if (!range) return

    const usableLog = logScale && range.lo > 0
    const f = v => (usableLog ? Math.log(Math.max(v, range.lo * 0.999)) : v)
    const fLo = f(range.lo), span = (f(range.hi) - fLo) || 1
    const Y = v => padT + plotH - ((f(v) - fLo) / span) * plotH * 0.97
    const X = i => padL + ((i - from + 0.5) / domain) * plotW
    const bw = Math.max(1, Math.min(14, (plotW / domain) * 0.68))

    const ink = token('--color-text-bold') || '#111'
    const muted = token('--color-text-muted') || '#888'
    const rule = token('--color-border-light') || '#eee'
    const up = token('--color-took') || '#1f5288'
    const down = token('--color-refused') || '#c23a2b'
    const accent = token('--color-accent') || '#b5541c'

    // price grid
    ctx.font = '11px ui-monospace, Menlo, monospace'
    ctx.textBaseline = 'middle'
    for (let t = 0; t <= 6; t++) {
      const fv = fLo + span * (t / 6)
      const price = usableLog ? Math.exp(fv) : fv
      const y = Math.round(Y(price)) + 0.5
      ctx.strokeStyle = rule
      ctx.lineWidth = 1
      ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(padL + plotW, y); ctx.stroke()
      ctx.fillStyle = muted
      ctx.textAlign = 'left'
      ctx.fillText(price >= 100 ? price.toFixed(0) : price >= 1 ? price.toFixed(2) : price.toFixed(3),
        padL + plotW + 6, y)
    }

    // volume, scaled to the window so a single blow-off bar elsewhere in the
    // file cannot flatten everything on screen
    let maxVol = 0
    for (let i = from; i <= to; i++) maxVol = Math.max(maxVol, bars[i].volume || 0)
    const volTop = padT + plotH + 6
    if (maxVol > 0) {
      for (let i = from; i <= to; i++) {
        const b = bars[i]
        const h = ((b.volume || 0) / maxVol) * volH
        ctx.fillStyle = `color-mix(in srgb, ${b.close >= b.open ? up : down} 32%, transparent)`
        ctx.fillRect(X(i) - bw / 2, volTop + volH - h, bw, h)
      }
    }

    // candles
    for (let i = from; i <= to; i++) {
      const b = bars[i]
      const c = b.close >= b.open ? up : down
      ctx.strokeStyle = c
      ctx.fillStyle = c
      ctx.lineWidth = 1
      const x = Math.round(X(i)) + 0.5
      ctx.beginPath(); ctx.moveTo(x, Y(b.high)); ctx.lineTo(x, Y(b.low)); ctx.stroke()
      const y1 = Y(b.open), y2 = Y(b.close)
      ctx.fillRect(X(i) - bw / 2, Math.min(y1, y2), bw, Math.max(1.2, Math.abs(y2 - y1)))
    }

    // moving averages: computed over everything revealed, drawn only on screen
    const closes = []
    for (let i = 0; i <= to; i++) closes.push(bars[i].close)
    for (const ma of MA_LINES) {
      const values = ma.type === 'ema' ? ema(closes, ma.period) : sma(closes, ma.period)
      ctx.strokeStyle = token(ma.tone) || muted
      ctx.lineWidth = ma.width
      ctx.setLineDash(ma.dash || [])
      ctx.beginPath()
      let started = false
      for (let i = Math.max(from - 1, 0); i <= to; i++) {
        if (values[i] == null) { started = false; continue }
        const x = X(i), y = Y(values[i])
        if (started) ctx.lineTo(x, y)
        else { ctx.moveTo(x, y); started = true }
      }
      ctx.stroke()
      ctx.setLineDash([])
    }

    // acts — only the ones already walked past and inside the window
    for (const act of acts) {
      if (act.index > to || act.index < from) continue
      const x = X(act.index)
      ctx.strokeStyle = act.kind === 'stated' ? accent : muted
      ctx.lineWidth = act.kind === 'stated' ? 1.4 : 1
      ctx.setLineDash(act.kind === 'stated' ? [] : [2, 3])
      ctx.beginPath(); ctx.moveTo(x, padT); ctx.lineTo(x, padT + plotH); ctx.stroke()
      ctx.setLineDash([])
    }

    // the reveal edge
    if (to < bars.length - 1) {
      const x = Math.round(X(to) + bw / 2 + 1) + 0.5
      ctx.strokeStyle = ink
      ctx.lineWidth = 1
      ctx.setLineDash([3, 3])
      ctx.beginPath(); ctx.moveTo(x, padT); ctx.lineTo(x, volTop + volH); ctx.stroke()
      ctx.setLineDash([])
    }

    // dates, by day when the window is short enough that two ticks share a month
    ctx.font = '11px ui-monospace, Menlo, monospace'
    ctx.textAlign = 'center'
    ctx.fillStyle = muted
    const seen = new Set()
    for (let k = 0; k <= 3; k++) {
      const i = Math.round(from + (to - from) * (k / 3))
      if (seen.has(i) || !bars[i]) continue
      seen.add(i)
      const label = domain <= 70 ? bars[i].time.slice(5) : bars[i].time.slice(0, 7)
      const x = Math.max(padL + 24, Math.min(padL + plotW - 24, X(i)))
      ctx.fillText(label, x, height - 8)
    }

    if (lowres) {
      ctx.textAlign = 'left'
      ctx.fillStyle = down
      ctx.font = '11px system-ui'
      ctx.fillText('资料精度不足：多数 K 线开＝高＝低＝收', padL + 4, padT + plotH - 4)
    }
  }, [bars, cursor, windowSize, logScale, acts, height, width, theme, lowres])

  useEffect(() => { draw() }, [draw])

  /* Dragging on the chart scrubs, which is the gesture people already have in
     their hands from every video player. Wheel is deliberately NOT bound: this
     page scrolls, and a chart that eats the wheel traps the reader on it. */
  const scrubTo = useCallback((clientX) => {
    if (!onScrub || !wrapRef.current || !bars?.length) return
    const r = wrapRef.current.getBoundingClientRect()
    const padL = 8, padR = 62
    const plotW = r.width - padL - padR
    const { from, domain } = viewport(bars.length, cursor, windowSize)
    const rel = (clientX - r.left - padL) / Math.max(plotW, 1)
    onScrub(Math.round(from + rel * domain))
  }, [onScrub, bars, cursor, windowSize])

  return (
    <div
      ref={wrapRef}
      className="relative select-none"
      style={{ cursor: onScrub ? 'ew-resize' : 'default' }}
      onPointerDown={e => { e.currentTarget.setPointerCapture(e.pointerId); scrubTo(e.clientX) }}
      onPointerMove={e => { if (e.buttons) scrubTo(e.clientX) }}
    >
      <canvas ref={canvasRef} className="block w-full" />
    </div>
  )
}
