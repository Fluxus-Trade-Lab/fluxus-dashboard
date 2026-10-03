import { useCorrectionRisk } from '../../hooks/useCorrectionRisk'
import { useLanguage } from '../../i18n/LanguageContext'

/**
 * Correction risk — three layers, on RND Linda's ruling (DATA_CONTRACTS §七,
 * 2026-09-11, v1 + v2; Andy: 「COrrection risk保留，和Linda协商，应该放什么」 and
 * 「我要我们研究turin的结果还有linda的tick cycle 研究放上去」). Each layer carries a
 * chart and a caption under it (Andy, same day: 「尽量配上图表，再加上注释」).
 *
 *   L1  P(≥5% drawdown within 21 sessions) for today's cell of the three-way
 *       table — with the cell's day count and the all-days base rate in the
 *       SAME box, always; prob never appears alone. Chart: the whole table as
 *       a grid, today's cell ringed, so the reader sees where today sits.
 *   L2  turin's two side readings, each with the historical rate for its state.
 *       Annotations — never folded into L1. Chart: each reading's own state
 *       table against its OWN base rate, drawn only once Linda publishes the
 *       tables (§七 933cd87b); until then the two text rows stand alone,
 *       because a bar against L1's base would compare two different samples.
 *   L3  (removed 2026-10-03, Andy on the two TICK blocks: 「上面那个没数据，删除。」
 *       The TICK now lives as its own chart, TickCycleChart. TickEvidence stays
 *       exported, unused on the page, so its tests still hold.)
 *
 * Standing rules: no danger colour (a historical frequency is not an alarm),
 * no vote in the regime band, every layer goes to "not measured" on its own
 * staleness (>2 sessions behind the page). Charts use ink and greys only.
 */

const STALE_SESSIONS = 2
const THIN = 100          // a cell with fewer days than this is drawn pale — too few to read
const pct = (v, d = 1) => (v == null ? '—' : `${(v * 100).toFixed(d)}%`)

/** Weekdays between two ISO dates — the browser has no holiday calendar
 *  (same stance as session.js), so a holiday can make this one day generous. */
function sessionsBehind(iso, ref) {
  if (!iso || !ref) return Infinity
  const a = new Date(`${iso}T12:00:00Z`), b = new Date(`${ref}T12:00:00Z`)
  if (!(a < b)) return 0
  let n = 0
  for (let d = new Date(a); d < b; d.setUTCDate(d.getUTCDate() + 1)) {
    const w = d.getUTCDay()
    if (w !== 0 && w !== 6) n += 1
  }
  return n
}
const fresh = (iso, ref) => sessionsBehind(iso, ref) <= STALE_SESSIONS

/** useLanguage, with {placeholders} filled even outside a LanguageProvider —
 *  the chart pieces are exported and tested bare, where the fallback t()
 *  returns the raw English template. */
function useT() {
  const { lang, t } = useLanguage()
  const fill = (str, v) => (v ? String(str).replace(/\{(\w+)\}/g, (m, k) => (v[k] != null ? String(v[k]) : m)) : str)
  return { lang, t: (k, v) => fill(t(k, v), v) }
}

/** A data label like "oversold (<0.30)" or "low dealer gamma (Q1)" in the
 *  page's language: the word is ours to translate, the cut in brackets is the
 *  data's and is kept as sent. Unknown words pass through untouched. */
const STATE_WORD = { oversold: 'oversold', mid: 'mid', overbought: 'overbought', 'low dealer gamma': 'lowGamma', 'high dealer gamma': 'highGamma' }
function stateLabel(lab, lang, t) {
  if (lang !== 'zh' || lab == null) return lab
  const m = String(lab).match(/^(.*?)\s*\(([^)]*)\)\s*$/)
  const word = m ? m[1] : String(lab)
  const key = STATE_WORD[word]
  if (!key) return lab
  return m ? `${t(`cr.state.${key}`)}（${m[2]}）` : t(`cr.state.${key}`)
}

function NotMeasured({ what, date }) {
  const { t } = useT()
  return (
    <p className="m-0 text-[13px] text-[var(--color-text-muted)] italic">
      {date ? t('cr.notMeasuredLast', { what, date }) : t('cr.notMeasured', { what })}
    </p>
  )
}

function Label({ children, aside }) {
  return (
    <div className="flex items-baseline justify-between gap-3 mb-2">
      <h3 className="m-0 text-[11px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)]">{children}</h3>
      {aside && <span className="text-[11px] text-[var(--color-text-muted)]">{aside}</span>}
    </div>
  )
}

/** How to read the chart above it. Muted, short, always under the chart. */
function Note({ children }) {
  return <p className="m-0 mt-2 text-[11px] leading-relaxed text-[var(--color-text-muted)] max-w-[88ch]">{children}</p>
}

/* ── L1 · the whole table, today ringed ────────────────────────────────── */

// @turintrader's three cuts, 0.8 / 1.0 / 1.1 (2026-09-21: 1.1 restored, four states).
const TS_STATES = [1, 2, 3, 4]
const tsLabel = (t, s) => (TS_STATES.includes(Number(s)) ? t(`cr.ts.${s}`) : undefined)
const SHADE_MAX = 0.4

/** Grey by rate: the ground at 0%, near-ink at SHADE_MAX and above. */
const shade = (r) => `color-mix(in srgb, var(--color-text) ${Math.round(Math.min(1, r / SHADE_MAX) * 78)}%, var(--color-bg))`

/** Same rule as the pipeline's quintile_of (correction_risk.py) — the ts-dimension
 *  table is built from its own (shorter, VIX3M-limited) sample, so its quintile
 *  edges land on different cuts than the headline 2-dim table's. `today.vix_quintile`
 *  is bucketed with those other edges; reusing it here rings the wrong column
 *  whenever the two edge sets disagree on where today's VIX falls (09-23: VIX 16.04
 *  was Q2 by the 2-dim edges but Q3 by this table's own — the ringed cell's rate
 *  didn't match prob_3d/n_cell_3d because it was the wrong cell). */
function quintileOfEdges(v, edges) {
  if (v == null || !edges?.length) return null
  for (let q = 1; q <= 5; q++) {
    if (edges[q - 1] < v && v <= edges[q]) return q
  }
  return v > edges[edges.length - 1] ? 5 : 1
}

export function CondGrid({ ts, today }) {
  const { t } = useT()
  const g = ts?.table?.by_vix_quintile_x_200dma_x_ts
  if (!g) return null
  const edges = ts.table.vix_edges_this_sample ?? []
  const rows = []
  for (const side of ['above200', 'below200']) {
    for (const s of [1, 2, 3, 4]) {
      const cells = [1, 2, 3, 4, 5].map((q) => g[`Q${q}_${side}_ts${s}`] ?? null)
      if (cells.some(Boolean)) rows.push({ side, s, cells })
    }
  }
  const todayKey = today && `${today.above_200dma ? 'above200' : 'below200'}_${today.ts_state}`
  const todayQ = quintileOfEdges(today?.vix, edges) ?? today?.vix_quintile
  const LW = 214, CW = 70, RH = 30, TOP = 30, GAP = 10
  const sides = [...new Set(rows.map((r) => r.side))]
  const H = TOP + rows.length * RH + (sides.length - 1) * GAP + 6
  const W = LW + CW * 5 + 4
  let yCursor = TOP
  let prevSide = null

  const colLabel = (i) => {
    const a = edges[i], b = edges[i + 1]
    if (a == null || b == null) return `Q${i + 1}`
    if (i === 0) return `VIX <${b.toFixed(1)}`
    if (i === 4) return `>${a.toFixed(1)}`
    return `${a.toFixed(1)}–${b.toFixed(1)}`
  }

  return (
    <div className="overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-[620px] h-auto block" role="img"
           aria-label={t('cr.grid.aria')}>
        {[0, 1, 2, 3, 4].map((i) => (
          <text key={i} x={LW + i * CW + CW / 2} y={TOP - 10} fontSize="11" textAnchor="middle"
                style={{ fill: 'var(--color-text-muted)' }}>{colLabel(i)}</text>
        ))}
        {rows.map((r) => {
          if (prevSide && prevSide !== r.side) yCursor += GAP
          const first = prevSide !== r.side
          prevSide = r.side
          const y = yCursor
          yCursor += RH
          const isTodayRow = `${r.side}_${r.s}` === todayKey
          return (
            <g key={`${r.side}${r.s}`}>
              {first && (
                <text x="0" y={y + 19} fontSize="11" fontWeight="600" style={{ fill: 'var(--color-text)' }}>
                  {r.side === 'above200' ? t('cr.grid.above') : t('cr.grid.below')}
                </text>
              )}
              <text x="96" y={y + 19} fontSize="11"
                    style={{ fill: isTodayRow ? 'var(--color-text)' : 'var(--color-text-muted)' }}>{tsLabel(t, r.s)}</text>
              {r.cells.map((c, i) => {
                const x = LW + i * CW
                const on = isTodayRow && todayQ === i + 1
                if (!c) {
                  return <text key={i} x={x + CW / 2} y={y + 19} fontSize="11" textAnchor="middle"
                               style={{ fill: 'var(--color-border)' }}>—</text>
                }
                const thin = c.n < THIN
                const dark = !thin && c.rate / SHADE_MAX > 0.5
                return (
                  <g key={i}>
                    <title>{t(r.side === 'above200' ? 'cr.grid.tipAbove' : 'cr.grid.tipBelow', {
                      ts: tsLabel(t, r.s), col: colLabel(i), rate: pct(c.rate), n: c.n.toLocaleString(),
                      thin: thin ? t('cr.grid.thin') : '' })}</title>
                    <rect x={x + 2} y={y + 2} width={CW - 4} height={RH - 4} rx="4"
                          fill={thin ? 'var(--color-bg)' : shade(c.rate)}
                          stroke={thin ? 'var(--color-border)' : 'none'} strokeDasharray={thin ? '3 2' : undefined} />
                    {on && (
                      <rect x={x} y={y} width={CW} height={RH} rx="6" fill="none"
                            stroke="var(--color-text)" strokeWidth="2.2" />
                    )}
                    <text x={x + CW / 2} y={y + 19} fontSize="11" textAnchor="middle" fontWeight={on ? 700 : 400}
                          style={{ fill: thin ? 'var(--color-text-muted)' : dark ? 'var(--color-bg)' : 'var(--color-text)' }}>
                      {pct(c.rate, 0)}
                    </text>
                  </g>
                )
              })}
            </g>
          )
        })}
      </svg>
    </div>
  )
}

function Headline({ cr, session }) {
  const { t: tr } = useT()
  if (!cr || !fresh(cr.date, session)) return <NotMeasured what={tr('cr.what')} date={cr?.date} />
  const t = cr.today ?? {}
  const ts = cr.ts_dimension?.today
  const has3d = ts && !ts.stale_warning && ts.prob_3d != null && ts.n_cell_3d != null
  const prob = has3d ? ts.prob_3d : cr.prob
  const n = has3d ? ts.n_cell_3d : t.n_cell
  const base = cr.base_rate
  const sample = cr.ts_dimension?.table?.sample

  return (
    <div>
      {/* the three numbers live in one line and one element — never split */}
      <p className="m-0 text-[13px] text-[var(--color-text-secondary)]">
        {tr('cr.head.q')}
      </p>
      <p className="m-0 mt-0.5 flex items-baseline flex-wrap gap-x-3">
        <span className="text-[26px] font-semibold text-[var(--color-text-bold)] tabular-nums">{pct(prob)}</span>
        <span className="text-[13px] text-[var(--color-text-secondary)] tabular-nums">
          {tr('cr.head.counts', { n: n?.toLocaleString() ?? '', base: pct(base) })}
        </span>
      </p>
      <p className="m-0 mt-1 text-[11px] font-mono text-[var(--color-text-muted)]">
        {tr(t.above_200dma ? 'cr.head.vixAbove' : 'cr.head.vixBelow', { vix: t.vix?.toFixed(2) ?? '', q: t.vix_quintile ?? '' })}
        {has3d ? tr('cr.head.ts', { ts: tsLabel(tr, ts.ts_state) ?? ts.ts_label }) : tr('cr.head.tsNone')}
      </p>

      {has3d && (
        <div className="mt-4">
          <CondGrid ts={cr.ts_dimension} today={{ ...t, ts_state: ts.ts_state }} />
          <Note>
            {tr('cr.head.note', {
              from: sample?.from?.slice(0, 4) ?? '2006', sessions: sample?.sessions?.toLocaleString() ?? '—',
              episodes: sample?.episodes ?? '—', thin: THIN })}
          </Note>
        </div>
      )}
      {cr.caveats?.[0] && <Note>{cr.caveats[0]}</Note>}
    </div>
  )
}

/* ── L2 · side readings ────────────────────────────────────────────────── */

/** A reading's own state table as bars — its own base rate as the dashed line,
 *  today's state in ink. Drawn only when the table is in the payload. */
export function StateBars({ reading }) {
  const { lang, t } = useT()
  const table = reading?.table
  if (!table || reading.base_rate == null) return null
  const keys = Object.keys(table).sort()
  const max = Math.max(0.3, ...keys.map((k) => table[k]?.rate ?? 0))
  const W = 320, H = 92, B = 32, bw = Math.min(48, (W - 8) / keys.length - 10)
  const step = (W - 8) / keys.length
  const y = (r) => (H - B) - (r / max) * (H - B - 4)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-[320px] h-auto block" role="img"
         aria-label={t('cr.bars.aria')}>
      {keys.map((k, i) => {
        const r = table[k]?.rate ?? 0
        const x = 4 + i * step + (step - bw) / 2
        const on = String(reading.today_state) === k
        const raw = reading.labels?.[k] ?? k
        const lab = stateLabel(raw, lang, t)
        // short name under the bar: "Q2" out of "low dealer gamma (Q1)"-style
        // labels, the plain word out of "oversold (<0.30)"-style ones
        const short = (lab.match(/[(（](Q\d)[)）]/)?.[1]) ?? lab.replace(/\s*[(（].*[)）]\s*$/, '')
        return (
          <g key={k}>
            <title>{t('cr.bars.tip', { lab, rate: pct(r), n: table[k]?.n?.toLocaleString() })}</title>
            <rect x={x} y={y(r)} width={bw} height={(H - B) - y(r)} rx="3"
                  fill={on ? 'var(--color-text)' : 'var(--color-untested)'} opacity={on ? 1 : 0.55} />
            <text x={x + bw / 2} y={H - 18} fontSize="11" textAnchor="middle" fontWeight={on ? 600 : 400}
                  style={{ fill: on ? 'var(--color-text)' : 'var(--color-text-muted)' }}>{short}</text>
            <text x={x + bw / 2} y={H - 4} fontSize="11" textAnchor="middle" fontWeight={on ? 600 : 400}
                  style={{ fill: on ? 'var(--color-text)' : 'var(--color-text-muted)' }}>{pct(r, 0)}</text>
          </g>
        )
      })}
      <line x1="4" x2={W - 4} y1={y(reading.base_rate)} y2={y(reading.base_rate)}
            stroke="var(--color-text-secondary)" strokeDasharray="4 3" />
    </svg>
  )
}

function SideNotes({ side, session, base }) {
  const { lang, t } = useT()
  const rows = [
    side?.nhnl && {
      key: 'nhnl', name: t('cr.side.nhnl'), asks: t('cr.side.nhnlAsks'),
      state: t('cr.side.nhnlState', { state: stateLabel(side.nhnl.state, lang, t), ratio: side.nhnl.ratio_10ema?.toFixed(2) }),
      rate: side.nhnl.hist_rate_e1, date: side.nhnl.date, reading: side.nhnl,
    },
    side?.gex && {
      key: 'gex', name: t('cr.side.gex'), asks: t('cr.side.gexAsks'),
      state: t('cr.side.gexState', { p: Math.round((side.gex.pct_rank_252d ?? 0) * 100) }),
      rate: side.gex.hist_rate_e1, date: side.gex.date, reading: side.gex,
    },
  ].filter(Boolean)
  if (!rows.length) return null
  const anyChart = rows.some((r) => r.reading?.table && r.reading.base_rate != null)
  return (
    <div>
      <Label aside={t('cr.side.aside')}>{t('cr.side.label')}</Label>
      <div className="space-y-3">
        {rows.map((r) => (
          <div key={r.key} className="grid grid-cols-1 md:grid-cols-[180px_1fr] gap-x-3 gap-y-1 items-baseline text-[13px]">
            <span className="text-[var(--color-text)]">
              {r.name}
              <span className="block text-[11px] text-[var(--color-text-muted)]">{r.asks}</span>
            </span>
            {fresh(r.date, session) ? (
              <div>
                <span className="text-[var(--color-text-secondary)] tabular-nums">
                  {t('cr.side.followed', { state: r.state, rate: pct(r.rate) })}
                </span>
                {r.reading?.table && r.reading.base_rate != null && (
                  <div className="mt-1.5">
                    <StateBars reading={r.reading} />
                    <p className="m-0 text-[11px] text-[var(--color-text-muted)]">
                      {t('cr.side.since', { from: r.reading.sample?.from?.slice(0, 4) ?? '—', base: pct(r.reading.base_rate) })}
                      {r.key === 'gex' && t('cr.side.gexKey')}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <span className="text-[var(--color-text-muted)] italic">{t('cr.side.stale', { date: r.date })}</span>
            )}
          </div>
        ))}
      </div>
      {anyChart && (
        <Note>{t('cr.side.note', { base: pct(base) })}</Note>
      )}
    </div>
  )
}

/* ── L3 · TICK cycle ───────────────────────────────────────────────────── */

/** Two pairs of bars: after entering today's band vs all sessions. */
export function TickEvidence({ e }) {
  const { t } = useT()
  if (!e || e.sell_fwd21_med == null || e.sell_p_dd5 == null) return null
  const groups = [
    { key: 'ret', label: t('cr.tick.ret'), a: e.sell_fwd21_med, b: e.base_fwd21_med, signed: true },
    { key: 'dd', label: t('cr.tick.dd'), a: e.sell_p_dd5, b: e.base_p_dd5 },
  ]
  const W = 520, RH = 22, LW = 190, VW = 70
  const H = groups.length * (RH * 2 + 14)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-[560px] h-auto block" role="img"
         aria-label={t('cr.tick.aria')}>
      {groups.map((g, gi) => {
        const max = Math.max(Math.abs(g.a), Math.abs(g.b)) * 1.15 || 1
        const x0 = LW, span = W - LW - VW
        const y0 = gi * (RH * 2 + 14)
        const bar = (v, dy, ink, lab) => (
          <g>
            <title>{t(ink ? 'cr.tick.tipAfter' : 'cr.tick.tipAll', { label: g.label, v: `${g.signed && v > 0 ? '+' : ''}${pct(v)}` })}</title>
            <rect x={x0} y={y0 + dy + 4} width={Math.max(1, (Math.abs(v) / max) * span)} height={RH - 8} rx="3"
                  fill={ink ? 'var(--color-text)' : 'var(--color-untested)'} opacity={ink ? 1 : 0.6} />
            <text x={x0 + (Math.abs(v) / max) * span + 6} y={y0 + dy + 15} fontSize="11"
                  style={{ fill: ink ? 'var(--color-text)' : 'var(--color-text-muted)' }}>
              {g.signed && v > 0 ? '+' : ''}{pct(v)} <tspan style={{ fill: 'var(--color-text-muted)' }}>{lab}</tspan>
            </text>
          </g>
        )
        return (
          <g key={g.key}>
            <text x="0" y={y0 + 15} fontSize="11" fontWeight="600" style={{ fill: 'var(--color-text)' }}>{g.label}</text>
            {bar(g.a, 0, true, t('cr.tick.after'))}
            {bar(g.b, RH, false, t('cr.tick.all'))}
          </g>
        )
      })}
    </svg>
  )
}

export default function CorrectionRiskPanel({ session }) {
  const { data: cr, loading } = useCorrectionRisk()
  if (loading) return null
  return (
    <div className="bg-[var(--color-bg)] rounded-2xl p-4 space-y-4">
      <Headline cr={cr} session={session} />
      {cr && fresh(cr.date, session) && (
        <div className="pt-3 border-t border-[var(--color-border-light)]">
          <SideNotes side={cr.side_readings} session={session} base={cr.base_rate} />
        </div>
      )}
    </div>
  )
}
