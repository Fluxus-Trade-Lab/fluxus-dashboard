import { useMemo } from 'react'
import { useTickerEvents } from '../../hooks/useTickerEvents'

/**
 * Signal history — the v2 ticker object.
 *
 * Design: Fluxus_Brand/visual/explorations/2026-08-08/ticker.html (scored 93)
 *
 * The old version was a reverse-chronological list, which answers "what fired"
 * and hides the only question worth asking: what did price do afterwards. So
 * every appearance is drawn at the close it appeared at, against the tape. The
 * distance between a mark and where the line went is the reading; the count is
 * not.
 *
 * Three encodings, none of them hue alone:
 *   · solid square   — quality tier (EP · VCP · MOM), the ones with a thesis
 *   · outlined square — participation; a 4% day is not a setup
 *   · triangle       — your own fill, up for long and down for short. Shape,
 *                      not colour, so it never competes with the signal set.
 *
 * And the lede this page nearly shipped without: the name is reachable from a
 * heat list that ranks by what already stacked, so any total return quoted here
 * is a selection, not a result. That sentence is printed next to the number it
 * qualifies, never below the fold.
 */

const LABELS = {
  episodic_pivot: 'EP',
  vcp: 'VCP',
  momentum_97: 'MOM',
  gainers_4pct: '4%',
  vol_up_gainers: 'VOL',
  ema21_watch: '21D',
  healthy_charts: 'CHART',
}

const LONG_LABELS = {
  episodic_pivot: 'Episodic Pivot',
  vcp: 'VCP',
  momentum_97: 'Composite 97',
  gainers_4pct: 'Up 4% day',
  vol_up_gainers: 'Volume-up gainer',
  ema21_watch: '21 EMA watch',
  healthy_charts: 'Healthy chart',
}

const QUALITY = new Set(['episodic_pivot', 'vcp', 'momentum_97'])

/** Show the tape from a few bars before the first appearance, not from IPO. */
const LEAD_IN = 8

const TAPE = { w: 1000, l: 46, r: 58, top: 30, bot: 244, h: 288 }

export default function TickerSignalHistory({ symbol, trades, ohlc }) {
  const { events, loading } = useTickerEvents(symbol)

  const fills = useMemo(() => (trades ?? [])
    .filter((t) => t.ticker === symbol && t.entryDate)
    .map((t) => ({
      date: String(t.entryDate).slice(0, 10),
      direction: t.direction,
      price: t.entryPrice,
      qty: t.originalQty ?? t.currentQty,
    }))
    .sort((a, b) => a.date.localeCompare(b.date)), [trades, symbol])

  const model = useMemo(() => build(events, ohlc, fills), [events, ohlc, fills])

  if (loading || !events.length) return null

  const { bars, marks, fillMarks, path, gridlines, firstQuality, span, counts,
          qualityHits, move, priceAt, offTape, tapeEnd } = model

  return (
    <div className="bg-[var(--color-surface)] rounded-3xl p-4">
      <div className="flex items-baseline justify-between pb-2 border-b border-[var(--color-v2-ink)]">
        <h3 className="text-[10px] font-mono uppercase tracking-[.24em] text-[var(--color-text-muted)]">
          Signal history
        </h3>
        <span className="text-[11px] text-[var(--color-text-secondary)]">
          Every appearance drawn at the close it appeared at
        </span>
      </div>

      {/* the selection disclosure sits next to the number it qualifies */}
      <p className="text-[12.5px] leading-relaxed text-[var(--color-text-secondary)] mt-3 mb-0">
        <span className="text-[10px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] mr-2">
          Read
        </span>
        {events.length} appearance{events.length === 1 ? '' : 's'} since{' '}
        <b className="text-[var(--color-text)]">{span.first}</b>
        {priceAt && (
          <>, first printed at {priceAt.first.toFixed(2)} and last printed at{' '}
            {priceAt.last.toFixed(2)} on {tapeEnd}</>
        )}.{' '}
        {move != null && (
          <span className="text-[var(--color-text)]">
            This name is reachable because it is already hot, so{' '}
            <b>{move >= 0 ? '+' : ''}{move.toFixed(1)}% is a selection, not a result.</b>
          </span>
        )}
      </p>

      {offTape > 0 && (
        <p className="text-[11px] leading-relaxed text-[var(--color-signal-caution)] mt-2 mb-0
                      border border-dashed border-[var(--color-untested)] px-3 py-2">
          <b>{offTape} of {events.length} appearances are not on the tape.</b> The local price
          history for {symbol} ends {tapeEnd}, but the screeners kept firing through{' '}
          {span.last}. Anything quoted above is measured to {tapeEnd} — not to today.
        </p>
      )}

      {bars.length ? (
        <>
          <svg viewBox={`0 0 ${TAPE.w} ${TAPE.h}`} className="w-full mt-3 overflow-visible"
               role="img"
               aria-label={`${symbol} closing prices with ${events.length} screener appearances marked`}>
            {gridlines.map((g) => (
              <g key={g.v}>
                <line x1={TAPE.l} y1={g.y} x2={TAPE.w - TAPE.r} y2={g.y}
                      stroke="var(--color-border-light)" strokeWidth=".7" />
                <text x={TAPE.w - TAPE.r + 8} y={g.y + 3.5}
                      className="fill-[var(--color-text-muted)]"
                      style={{ font: '400 9.5px var(--font-mono)' }}>{g.v.toFixed(0)}</text>
              </g>
            ))}
            <polyline points={path} fill="none" stroke="var(--color-v2-ink)"
                      strokeWidth="1.6" strokeLinejoin="round" />

            {marks.map((m, i) => (m.quality ? (
              <g key={`q${i}`}>
                {/* the stem belongs to the labelled first signal only — drawn on all
                    thirty-odd of them it stops pointing at anything and becomes a fence */}
                {m === firstQuality && (
                  <line x1={m.x} y1={m.y} x2={m.x} y2={TAPE.top - 6}
                        stroke="var(--color-text-bold)" strokeWidth=".8" opacity=".45" />
                )}
                <rect x={m.x - 3.5} y={m.y - 3.5} width="7" height="7" fill="var(--color-text-bold)">
                  <title>{`${LONG_LABELS[m.screener] ?? m.screener} · ${m.date} · ${m.close.toFixed(2)}`}</title>
                </rect>
              </g>
            ) : (
              <rect key={`p${i}`} x={m.x - 2.5} y={m.y - 2.5} width="5" height="5" fill="none"
                    stroke="var(--color-untested)" strokeWidth="1.1">
                <title>{`${LONG_LABELS[m.screener] ?? m.screener} · ${m.date} · ${m.close.toFixed(2)}`}</title>
              </rect>
            )))}

            {/* fills: shape carries direction, so it never competes with the signal set */}
            {fillMarks.map((f, i) => (
              <polygon key={`f${i}`} fill="var(--color-v2-ink)"
                       points={f.long
                         ? `${f.x},${f.y + 13} ${f.x - 5},${f.y + 22} ${f.x + 5},${f.y + 22}`
                         : `${f.x},${f.y - 13} ${f.x - 5},${f.y - 22} ${f.x + 5},${f.y - 22}`}>
                <title>{`${f.long ? 'BOUGHT' : 'SOLD SHORT'} ${f.qty ?? ''} @ ${f.price ?? '—'} · ${f.date}`}</title>
              </polygon>
            ))}

            {firstQuality && (
              <text x={firstQuality.x} y={TAPE.top - 16} textAnchor="middle"
                    fill="var(--color-text-bold)"
                    style={{ font: '500 10px var(--font-mono)' }}>
                {`first ${LABELS[firstQuality.screener] ?? firstQuality.screener} · ${firstQuality.close.toFixed(2)}`}
              </text>
            )}

            {/* The pending slot says "one more session is coming". That is only true
                when the tape is current — on a stale one it would promise tomorrow
                while sitting months behind, so it is withheld rather than reworded. */}
            {!offTape && (
              <>
                <rect x={model.nextX} y={TAPE.top} width={model.nextW}
                      height={TAPE.bot - TAPE.top}
                      fill="none" stroke="var(--color-untested)" strokeDasharray="3 3" />
                <text x={model.nextX + 6} y={TAPE.top - 8}
                      className="fill-[var(--color-text-muted)]"
                      style={{ font: '500 9.5px var(--font-mono)', letterSpacing: '.1em' }}>NEXT</text>
              </>
            )}

            <text x={TAPE.l} y={TAPE.bot + 22} className="fill-[var(--color-text-muted)]"
                  style={{ font: '400 9.5px var(--font-mono)' }}>{bars[0].date}</text>
            <text x={TAPE.w - TAPE.r} y={TAPE.bot + 22} textAnchor="end"
                  className="fill-[var(--color-text-muted)]"
                  style={{ font: '400 9.5px var(--font-mono)' }}>{bars[bars.length - 1].date}</text>
          </svg>

          <p className="text-[11px] leading-relaxed text-[var(--color-text-secondary)] mt-1 mb-0">
            <span className="text-[10px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] mr-2">
              Method
            </span>
            Solid squares are the quality tier (EP · VCP · MOM); outlined squares are
            participation; triangles are your own fills, pointing the way you went. Each mark sits
            at <b>the close it appeared at</b>, so the gap between a mark and the line's later
            position is the thing worth reading — not the count.
            {!fills.length && (
              <> No fill is drawn on this name because <b>you never took one</b> — the lane is
              empty, not missing.</>
            )}
          </p>
        </>
      ) : (
        <p className="text-[11px] leading-relaxed text-[var(--color-text-secondary)] mt-3 mb-0
                      border border-dashed border-[var(--color-untested)] px-3 py-2">
          No local price history for {symbol}, so the appearances below are counted but
          <b> not placed against the tape</b>. The count alone cannot tell you whether any of
          them led anywhere — that reading is absent, not zero.
        </p>
      )}

      {/* the strip: countable, oldest left, one mark per appearance */}
      <div className="mt-4 pt-3 border-t border-[var(--color-border-light)] space-y-2">
        {counts.map((c) => (
          <div key={c.screener} className="flex items-baseline gap-3">
            <span className="w-[124px] shrink-0 text-right">
              <span className="block text-[12.5px] font-semibold text-[var(--color-text)]"
                    style={{ fontFamily: 'var(--font-cond)' }}>
                {(LABELS[c.screener] ?? c.screener).toUpperCase()}
              </span>
              <span className="block text-[10px] text-[var(--color-text-muted)]">
                {c.quality ? 'quality · ×3' : 'participation · ×1'}
              </span>
            </span>
            <span className="flex flex-wrap gap-1 items-center">
              {c.dates.map((d) => (
                <i key={d} title={d} className="block w-[11px] h-[11px]" style={{
                  background: c.quality ? 'var(--color-text-bold)' : 'transparent',
                  boxShadow: c.quality ? undefined : 'inset 0 0 0 1.1px var(--color-untested)',
                }} />
              ))}
              <span className="text-[12.5px] font-semibold ml-1"
                    style={{ fontFamily: 'var(--font-cond)',
                             color: c.quality ? 'var(--color-text-bold)' : 'var(--color-text-muted)' }}>
                {c.dates.length}
              </span>
            </span>
          </div>
        ))}
        <p className="text-[12.5px] text-[var(--color-text)] pt-1 mb-0">
          <b>{qualityHits} of {events.length}</b> appearances were the quality tier. The rest is
          participation — a 4% day is not a setup.
        </p>
      </div>
    </div>
  )
}

/** Everything geometric in one place so the JSX stays a drawing, not a calculator. */
function build(events, ohlc, fills) {
  const sorted = [...events].sort((a, b) => a.date.localeCompare(b.date))
  const span = { first: sorted[0]?.date, last: sorted[sorted.length - 1]?.date }

  const byScreener = new Map()
  for (const e of sorted) {
    if (!byScreener.has(e.screener)) byScreener.set(e.screener, [])
    byScreener.get(e.screener).push(e.date)
  }
  const counts = [...byScreener.entries()]
    .map(([screener, dates]) => ({ screener, dates, quality: QUALITY.has(screener) }))
    .sort((a, b) => (b.quality ? 1 : 0) - (a.quality ? 1 : 0) || b.dates.length - a.dates.length)
  const qualityHits = sorted.filter((e) => QUALITY.has(e.screener)).length

  const all = ohlc ?? []
  const firstIdx = all.findIndex((b) => b.date >= span.first)
  if (!all.length || firstIdx < 0) {
    return { bars: [], marks: [], fillMarks: [], path: '', gridlines: [], firstQuality: null,
             span, counts, qualityHits, move: null, priceAt: null, nextX: 0, nextW: 0,
             offTape: sorted.length, tapeEnd: all.length ? all[all.length - 1].date : null }
  }
  const bars = all.slice(Math.max(0, firstIdx - LEAD_IN))
  const idx = new Map(bars.map((b, i) => [b.date, i]))
  const tapeEnd = bars[bars.length - 1].date
  // The local OHLC store goes stale independently of ticker_events, so some
  // appearances land past the end of the tape. Count them out loud — dropping
  // them silently would make a short tape look like a complete one.
  const offTape = sorted.filter((e) => e.date > tapeEnd).length

  const lo = Math.min(...bars.map((b) => b.low))
  const hi = Math.max(...bars.map((b) => b.high))
  // one extra slot on the right so the pending session has somewhere to sit
  const x = (i) => TAPE.l + (i * (TAPE.w - TAPE.l - TAPE.r)) / bars.length
  const y = (v) => TAPE.bot - ((v - lo) / (hi - lo || 1)) * (TAPE.bot - TAPE.top)

  const place = (date) => (idx.has(date) ? idx.get(date) : null)
  const marks = sorted.flatMap((e) => {
    const i = place(e.date)
    if (i == null) return []
    return [{ x: x(i), y: y(bars[i].close), quality: QUALITY.has(e.screener),
              screener: e.screener, date: e.date, close: bars[i].close }]
  })
  const fillMarks = fills.flatMap((f) => {
    const i = place(f.date)
    if (i == null) return []
    return [{ ...f, x: x(i), y: y(bars[i].close), long: f.direction !== 'short' }]
  })

  const step = Math.pow(10, Math.floor(Math.log10(hi - lo || 1)))
  const gridlines = []
  for (let v = Math.ceil(lo / step) * step; v < hi; v += step) gridlines.push({ v, y: y(v) })

  const fq = marks.find((m) => m.quality) ?? null
  // only quote a first price if the first appearance is actually on this tape
  const firstOnTape = place(span.first)
  const priceFirst = firstOnTape != null ? bars[firstOnTape].close : null
  const priceLast = bars[bars.length - 1].close

  return {
    bars, marks, fillMarks, counts, qualityHits, span, gridlines, firstQuality: fq,
    offTape, tapeEnd,
    path: bars.map((b, i) => `${x(i)},${y(b.close)}`).join(' '),
    priceAt: priceFirst != null ? { first: priceFirst, last: priceLast } : null,
    move: priceFirst ? (priceLast / priceFirst - 1) * 100 : null,
    nextX: x(bars.length - 1) + 8,
    nextW: Math.max(6, x(bars.length) - x(bars.length - 1) - 8),
  }
}
