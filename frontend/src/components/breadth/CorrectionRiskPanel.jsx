import { useCorrectionRisk } from '../../hooks/useCorrectionRisk'
import { useTickCycle } from '../../hooks/useTickCycle'
import { englishReading, niceDate } from '../../lib/tickReading'

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
 *   L3  the TICK cycle, a different question, set apart. Chart: the 21 sessions
 *       after past entries into today's band, against all sessions.
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

function NotMeasured({ what, date }) {
  return (
    <p className="m-0 text-[13px] text-[var(--color-text-muted)] italic">
      {what} — not measured{date ? ` (last ${date})` : ''}.
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

const TS_LABEL = { 1: 'complacent (<0.8)', 2: 'neutral (0.8–1.0)', 3: 'backwardation (>1.0)' }
const SHADE_MAX = 0.4

/** Grey by rate: the ground at 0%, near-ink at SHADE_MAX and above. */
const shade = (r) => `color-mix(in srgb, var(--color-text) ${Math.round(Math.min(1, r / SHADE_MAX) * 78)}%, var(--color-bg))`

export function CondGrid({ ts, today }) {
  const g = ts?.table?.by_vix_quintile_x_200dma_x_ts
  if (!g) return null
  const edges = ts.table.vix_edges_this_sample ?? []
  const rows = []
  for (const side of ['above200', 'below200']) {
    for (const s of [1, 2, 3]) {
      const cells = [1, 2, 3, 4, 5].map((q) => g[`Q${q}_${side}_ts${s}`] ?? null)
      if (cells.some(Boolean)) rows.push({ side, s, cells })
    }
  }
  const todayKey = today && `${today.above_200dma ? 'above200' : 'below200'}_${today.ts_state}`
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
           aria-label="share of days followed by a 5% drawdown within 21 sessions, by VIX level, 200-day side and VIX term structure">
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
                  {r.side === 'above200' ? 'Above 200-day' : 'Below 200-day'}
                </text>
              )}
              <text x="96" y={y + 19} fontSize="11"
                    style={{ fill: isTodayRow ? 'var(--color-text)' : 'var(--color-text-muted)' }}>{TS_LABEL[r.s]}</text>
              {r.cells.map((c, i) => {
                const x = LW + i * CW
                const on = isTodayRow && today.vix_quintile === i + 1
                if (!c) {
                  return <text key={i} x={x + CW / 2} y={y + 19} fontSize="11" textAnchor="middle"
                               style={{ fill: 'var(--color-border)' }}>—</text>
                }
                const thin = c.n < THIN
                const dark = !thin && c.rate / SHADE_MAX > 0.5
                return (
                  <g key={i}>
                    <title>{`${r.side === 'above200' ? 'above' : 'below'} 200-day · term structure ${TS_LABEL[r.s]} · ${colLabel(i)}: ${pct(c.rate)} of ${c.n.toLocaleString()} days${thin ? ' — too few days to read' : ''}`}</title>
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
  if (!cr || !fresh(cr.date, session)) return <NotMeasured what="Correction risk" date={cr?.date} />
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
        P(S&amp;P 500 falls ≥5% within 21 sessions)
      </p>
      <p className="m-0 mt-0.5 flex items-baseline flex-wrap gap-x-3">
        <span className="text-[26px] font-semibold text-[var(--color-text-bold)] tabular-nums">{pct(prob)}</span>
        <span className="text-[13px] text-[var(--color-text-secondary)] tabular-nums">
          {n?.toLocaleString()} days in this cell · {pct(base)} across all days since 1990
        </span>
      </p>
      <p className="m-0 mt-1 text-[11px] font-mono text-[var(--color-text-muted)]">
        VIX {t.vix?.toFixed(2)} (quintile {t.vix_quintile} of 5) · {t.above_200dma ? 'above' : 'below'} the 200-day
        {has3d ? ` · term structure ${TS_LABEL[ts.ts_state] ?? ts.ts_label}` : ' · term-structure dimension not measured'}
      </p>

      {has3d && (
        <div className="mt-4">
          <CondGrid ts={cr.ts_dimension} today={{ ...t, ts_state: ts.ts_state }} />
          <Note>
            Each cell: of all days since {sample?.from?.slice(0, 4) ?? '2006'} in that state, the share followed by a
            ≥5% S&amp;P 500 drop within 21 sessions ({sample?.sessions?.toLocaleString() ?? '—'} days,{' '}
            {sample?.episodes ?? '—'} separate drops). Darker = it happened more often. The ringed cell is today.
            Pale dashed cells have fewer than {THIN} days — too few to read. Conditional base-rate table, no fitted
            parameters.
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
  const table = reading?.table
  if (!table || reading.base_rate == null) return null
  const keys = Object.keys(table).sort()
  const max = Math.max(0.3, ...keys.map((k) => table[k]?.rate ?? 0))
  const W = 300, H = 74, B = 18, bw = Math.min(48, (W - 8) / keys.length - 10)
  const step = (W - 8) / keys.length
  const y = (r) => (H - B) - (r / max) * (H - B - 4)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-[320px] h-auto block" role="img"
         aria-label="share of days followed by a 5% drawdown, by state of this reading">
      {keys.map((k, i) => {
        const r = table[k]?.rate ?? 0
        const x = 4 + i * step + (step - bw) / 2
        const on = String(reading.today_state) === k
        const lab = reading.labels?.[k] ?? k
        return (
          <g key={k}>
            <title>{`${lab}: ${pct(r)} of ${table[k]?.n?.toLocaleString()} days`}</title>
            <rect x={x} y={y(r)} width={bw} height={(H - B) - y(r)} rx="3"
                  fill={on ? 'var(--color-text)' : 'var(--color-untested)'} opacity={on ? 1 : 0.55} />
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
  const rows = [
    side?.nhnl && {
      key: 'nhnl', name: 'Breadth washout (NH/NL)', asks: 'how deep the internal flush is',
      state: `${side.nhnl.state} · 10-EMA ratio ${side.nhnl.ratio_10ema?.toFixed(2)}`,
      rate: side.nhnl.hist_rate_e1, date: side.nhnl.date, reading: side.nhnl,
    },
    side?.gex && {
      key: 'gex', name: 'Dealer gamma (GEX)', asks: 'how thick the dealer cushion is',
      state: `${Math.round((side.gex.pct_rank_252d ?? 0) * 100)}th percentile of the year`,
      rate: side.gex.hist_rate_e1, date: side.gex.date, reading: side.gex,
    },
  ].filter(Boolean)
  if (!rows.length) return null
  const anyChart = rows.some((r) => r.reading?.table && r.reading.base_rate != null)
  return (
    <div>
      <Label aside="annotations — not part of the probability above">Side readings</Label>
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
                  {r.state} — a 5% drawdown followed {pct(r.rate)} of days in this state
                </span>
                <div className="mt-1.5"><StateBars reading={r.reading} /></div>
              </div>
            ) : (
              <span className="text-[var(--color-text-muted)] italic">not measured (last {r.date})</span>
            )}
          </div>
        ))}
      </div>
      {anyChart && (
        <Note>
          Bars: the same 5%-drop question, split by this reading's own states, over its own history. The dashed line is
          that history's all-days rate — not the {pct(base)} above, which comes from a longer sample. Today's state is the dark bar.
        </Note>
      )}
    </div>
  )
}

/* ── L3 · TICK cycle ───────────────────────────────────────────────────── */

/** Two pairs of bars: after entering today's band vs all sessions. */
export function TickEvidence({ e }) {
  if (!e || e.sell_fwd21_med == null || e.sell_p_dd5 == null) return null
  const groups = [
    { key: 'ret', label: 'Median 21-session return', a: e.sell_fwd21_med, b: e.base_fwd21_med, signed: true },
    { key: 'dd', label: 'Chance of a ≥5% drop', a: e.sell_p_dd5, b: e.base_p_dd5 },
  ]
  const W = 520, RH = 22, LW = 190, VW = 70
  const H = groups.length * (RH * 2 + 14)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-[560px] h-auto block" role="img"
         aria-label="after entering this TICK band versus all sessions">
      {groups.map((g, gi) => {
        const max = Math.max(Math.abs(g.a), Math.abs(g.b)) * 1.15 || 1
        const x0 = LW, span = W - LW - VW
        const y0 = gi * (RH * 2 + 14)
        const bar = (v, dy, ink, lab) => (
          <g>
            <title>{`${g.label}, ${lab}: ${g.signed && v > 0 ? '+' : ''}${pct(v)}`}</title>
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
            {bar(g.a, 0, true, 'after entering this band')}
            {bar(g.b, RH, false, 'all sessions')}
          </g>
        )
      })}
    </svg>
  )
}

function TickCycle({ tc, session }) {
  if (!tc) return null
  const e = tc.evidence
  const rank = tc.spread_rank252 == null ? null : Math.max(1, Math.round(tc.spread_rank252 * 100))
  const grindWithEvidence = tc.band === 'grind' && e?.sell_p_dd5 != null
  return (
    <div>
      <Label aside="a different question — grinding or trending, not crashing">TICK cycle</Label>
      {!fresh(tc.as_of, session) ? <NotMeasured what="TICK cycle" date={tc.as_of} /> : grindWithEvidence ? (
        <>
          <p className="m-0 mb-2 text-[13px] text-[var(--color-text-secondary)]">
            Since {niceDate(tc.band_since)} the TICK&rsquo;s high–low band has been contracted
            {rank != null && <> — the tightest {rank}% of the past year</>}. A grind, not a break.
          </p>
          <TickEvidence e={e} />
          <Note>
            Dark bars: the 21 sessions after each of the {e.n_sell_entries} times the TICK band contracted this far in
            the last {e.window_years} years. Grey bars: all sessions. Returns come out thinner and a 5% drop comes out
            rarer — the market tends to grind, not break.
          </Note>
        </>
      ) : (
        <p className="m-0 text-[13px] leading-relaxed text-[var(--color-text-secondary)] max-w-[80ch]">{englishReading(tc)}</p>
      )}
    </div>
  )
}

export default function CorrectionRiskPanel({ session }) {
  const { data: cr, loading } = useCorrectionRisk()
  const { data: tc } = useTickCycle()
  if (loading) return null
  return (
    <div className="bg-[var(--color-bg)] rounded-2xl p-4 space-y-4">
      <Headline cr={cr} session={session} />
      {cr && fresh(cr.date, session) && (
        <div className="pt-3 border-t border-[var(--color-border-light)]">
          <SideNotes side={cr.side_readings} session={session} base={cr.base_rate} />
        </div>
      )}
      {/* a heavier rule on purpose: L3 answers another question */}
      <div className="pt-3 border-t border-[var(--color-text-muted)]">
        <TickCycle tc={tc} session={session} />
      </div>
    </div>
  )
}
