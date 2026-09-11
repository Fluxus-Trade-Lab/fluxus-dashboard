import HealthChart from './HealthChart'

/**
 * Benchmarks — SPY and QQQ, everything this page knows about each, in one fold.
 *
 * Until 2026-09-11 one benchmark was spread over two folds: its price chart
 * under "Benchmark health", its five warnings under "Danger signals", and the
 * moving-average distance table hung under the chart. Three objects about one
 * name, read in two places. Now each benchmark is one card — chart on top, its
 * five warnings as five cells under it (lit = firing; count the cells, no
 * sentence to read) — and the distance table becomes one ruler for all four.
 *
 * Data: market_health.json (candles, danger) · signals.json (trend_status).
 * Nothing here is computed; the warnings and distances arrive composed.
 */

const WARN = [
  ['below_20sma', 'Below 20 SMA'],
  ['stoch_cross', 'Fast stoch < slow'],
  ['stoch_down', 'Stochs curving down'],
  ['lower_lows', '3 lower lows'],
  ['close_below_lows', 'Close < 3 prior lows'],
]

function Warnings({ danger }) {
  if (!danger?.signals) return null
  return (
    <div className="grid grid-cols-5 gap-1 mt-2" aria-label={`${danger.count ?? 0} of 5 warnings firing`}>
      {WARN.map(([k, label]) => {
        const on = danger.signals[k] === true
        return (
          <div key={k} title={`${label} — ${on ? 'firing' : 'quiet'}`}
               className={`rounded-md px-1.5 py-1.5 text-[11px] leading-tight min-h-[40px] ${on
                 ? 'bg-[var(--color-refused)] text-[var(--color-bg)] font-medium'
                 : 'bg-[var(--color-v2-off)] text-[var(--color-text-muted)]'}`}>
            {label}
          </div>
        )
      })}
    </div>
  )
}

function Benchmark({ title, block, state, t2108 }) {
  if (!block?.candles?.length) return null
  return (
    <div className="bg-[var(--color-bg)] rounded-2xl p-3">
      <HealthChart title={title} block={block} state={state} t2108={t2108}
                   warnCount={block.danger?.count} />
      <Warnings danger={block.danger} />
    </div>
  )
}

/* ── the ruler ────────────────────────────────────────────────────────── */

const MARKS = [
  ['9ema_dist', '9E'], ['21ema_dist', '21E'], ['50sma_dist', '50S'],
  ['200sma_dist', '200S'], ['52w_high_dist', '52wH'],
]
const TICKERS = ['SPY', 'QQQ', 'IWM', 'RSP']
const W = 820, ROW = 40, PAD_L = 56, PAD_R = 16, TOP = 22

/** Spread labels on one row so two averages a tenth of a percent apart do not
 *  print on top of each other: sorted by x, a label that would touch the one
 *  before it moves to the other side of the line. */
function placeLabels(pts, minGap = 30) {
  const sorted = [...pts].sort((a, b) => a.x - b.x)
  let lastUp = -Infinity, lastDown = -Infinity
  for (const p of sorted) {
    if (p.x - lastUp >= minGap) { p.up = true; lastUp = p.x }
    else if (p.x - lastDown >= minGap) { p.up = false; lastDown = p.x }
    else { p.up = true; lastUp = p.x }
  }
  return pts
}

export function MaRuler({ signals }) {
  const rows = TICKERS.map((t) => [t, signals?.[t]?.trend_status]).filter(([, ts]) => ts)
  if (!rows.length) return null
  const vals = rows.flatMap(([, ts]) => MARKS.map(([k]) => ts[k])).filter(Number.isFinite)
  // even-number bounds around the data, always including zero
  const lo = Math.min(0, Math.floor(Math.min(...vals) / 2) * 2)
  const hi = Math.max(0, Math.ceil(Math.max(...vals) / 2) * 2)
  const x = (v) => PAD_L + ((v - lo) / (hi - lo || 1)) * (W - PAD_L - PAD_R)
  const H = TOP + rows.length * ROW + 18
  const ticks = []
  for (let v = lo; v <= hi; v += 2) ticks.push(v)

  return (
    <div className="bg-[var(--color-bg)] rounded-2xl p-3">
      <div className="flex items-baseline justify-between mb-1">
        <h3 className="text-[11px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)]">
          Distance from each average
        </h3>
        <span className="text-[11px] text-[var(--color-text-muted)]">right of 0 = above it</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto block" role="img"
           aria-label="distance of SPY, QQQ, IWM and RSP from their 9/21-day EMA, 50/200-day SMA and 52-week high">
        {ticks.map((v) => (
          <g key={v}>
            <line x1={x(v)} x2={x(v)} y1={TOP - 6} y2={H - 18}
                  stroke={v === 0 ? 'var(--color-text)' : 'var(--color-border-light)'}
                  strokeWidth={v === 0 ? 1.2 : 1} />
            <text x={x(v)} y={H - 4} fontSize="11" textAnchor="middle"
                  style={{ fill: 'var(--color-text-muted)' }}>{v > 0 ? `+${v}` : v}%</text>
          </g>
        ))}
        {rows.map(([t, ts], r) => {
          const y = TOP + r * ROW + ROW / 2
          const pts = placeLabels(MARKS.filter(([k]) => Number.isFinite(ts[k]))
            .map(([k, label]) => ({ k, label, v: ts[k], x: x(ts[k]) })))
          return (
            <g key={t}>
              <text x={4} y={y + 4} fontSize="13" fontWeight="600"
                    style={{ fill: 'var(--color-text)' }}>{t}</text>
              <line x1={PAD_L} x2={W - PAD_R} y1={y} y2={y} stroke="var(--color-border-light)" />
              {pts.map((p) => (
                <g key={p.k}>
                  <title>{`${t} vs ${p.label}: ${p.v > 0 ? '+' : ''}${p.v.toFixed(2)}%`}</title>
                  <circle cx={p.x} cy={y} r="5" stroke="var(--color-bg)" strokeWidth="1.5"
                          fill={p.v >= 0 ? 'var(--color-took)' : 'var(--color-refused)'} />
                  <text x={p.x} y={p.up ? y - 9 : y + 17} fontSize="11" textAnchor="middle"
                        style={{ fill: 'var(--color-text-muted)' }}>{p.label}</text>
                </g>
              ))}
            </g>
          )
        })}
      </svg>
    </div>
  )
}

export default function BenchmarkPanel({ mh, verdict, t2108, signals }) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Benchmark title="SPY" block={mh?.spy} state={verdict?.spy_state} t2108={t2108} />
        <Benchmark title="QQQ" block={mh?.qqq} state={verdict?.qqq_state} t2108={t2108} />
      </div>
      <MaRuler signals={signals} />
    </div>
  )
}
