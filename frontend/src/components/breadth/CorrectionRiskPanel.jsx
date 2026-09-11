import { useCorrectionRisk } from '../../hooks/useCorrectionRisk'
import { useTickCycle } from '../../hooks/useTickCycle'
import { englishReading } from '../../lib/tickReading'

/**
 * Correction risk — three layers, on RND Linda's ruling (DATA_CONTRACTS §七,
 * 2026-09-11, v1 + v2; Andy: 「COrrection risk保留，和Linda协商，应该放什么」 and
 * 「我要我们研究turin的结果还有linda的tick cycle 研究放上去」).
 *
 *   L1  P(≥5% drawdown within 21 sessions) for today's cell of the three-way
 *       table (VIX quintile × 200-day side × VIX term structure) — with the
 *       cell's day count and the all-days base rate in the SAME box, always.
 *       prob never appears alone. If the term-structure dimension is missing
 *       or stale, fall back to the two-way table and say so.
 *   L2  turin's two side readings (NH/NL washout, dealer gamma), each with the
 *       historical rate for its state. Annotations — never folded into L1.
 *   L3  the TICK cycle: "grinding or trending", a different question from L1,
 *       set apart so the two are not read as two votes on one question.
 *
 * Standing rules from the same ruling: no danger colour (a historical
 * frequency is not an alarm), no vote in the regime band, every layer goes to
 * "not measured" on its own staleness (>2 sessions behind the page).
 */

const STALE_SESSIONS = 2
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

/* ── L1 ───────────────────────────────────────────────────────────────── */

/** The five VIX quintiles, 1990→ — the evidence under the headline. Today's
 *  quintile is the ink bar; the base rate is the dashed line. Neutral inks
 *  only: this is a frequency, not a warning. */
function QuintileBars({ table, today, base }) {
  const full = table?.by_vix_quintile?.full
  if (!full) return null
  const qs = ['1', '2', '3', '4', '5']
  const max = Math.max(0.35, ...qs.map((q) => full[q]?.rate ?? 0))
  const W = 360, H = 90, L = 4, B = 18, bw = 48, gap = (W - L * 2 - bw * 5) / 4
  const y = (r) => (H - B) - (r / max) * (H - B - 4)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-[420px] h-auto block" role="img"
         aria-label="frequency of a 5% drawdown within 21 sessions by VIX quintile, 1990 onward">
      {qs.map((q, i) => {
        const r = full[q]?.rate ?? 0
        const x = L + i * (bw + gap)
        const on = Number(q) === today
        return (
          <g key={q}>
            <title>{`VIX quintile ${q}: ${pct(r)} of ${full[q]?.n?.toLocaleString()} days`}</title>
            <rect x={x} y={y(r)} width={bw} height={(H - B) - y(r)} rx="3"
                  fill={on ? 'var(--color-text)' : 'var(--color-untested)'} opacity={on ? 1 : 0.55} />
            <text x={x + bw / 2} y={H - 4} fontSize="11" textAnchor="middle"
                  fontWeight={on ? 600 : 400}
                  style={{ fill: on ? 'var(--color-text)' : 'var(--color-text-muted)' }}>{`Q${q} ${pct(r, 0)}`}</text>
          </g>
        )
      })}
      <line x1={L} x2={W - L} y1={y(base)} y2={y(base)} stroke="var(--color-text-secondary)"
            strokeDasharray="4 3" strokeWidth="1" />
    </svg>
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

  return (
    <div>
      {/* the three numbers live in one line and one element — never split */}
      <p className="m-0 text-[13px] text-[var(--color-text-secondary)]">
        P(S&amp;P 500 falls ≥5% within 21 sessions)
      </p>
      <p className="m-0 mt-0.5 flex items-baseline flex-wrap gap-x-3">
        <span className="text-[26px] font-semibold text-[var(--color-text-bold)] tabular-nums">{pct(prob)}</span>
        <span className="text-[13px] text-[var(--color-text-secondary)] tabular-nums">
          {n?.toLocaleString()} days in this cell since 1990 · {pct(base)} across all days
        </span>
      </p>
      <p className="m-0 mt-1 text-[11px] font-mono text-[var(--color-text-muted)]">
        VIX {t.vix?.toFixed(2)} (quintile {t.vix_quintile} of 5) · {t.above_200dma ? 'above' : 'below'} the 200-day
        {has3d ? ` · term structure ${String(ts.ts_label).replace('(', ' (').replace('-', '–')}` : ' · term-structure dimension not measured'}
      </p>
      <div className="mt-3 flex flex-wrap items-end gap-x-6 gap-y-2">
        <QuintileBars table={cr.table} today={t.vix_quintile} base={base} />
        <p className="m-0 text-[11px] text-[var(--color-text-muted)] max-w-[34ch]">
          VIX alone, by quintile — dashed line is the all-days rate. Conditional base-rate table,
          no fitted parameters.
        </p>
      </div>
      {cr.caveats?.[0] && (
        <p className="m-0 mt-2 text-[11px] text-[var(--color-text-muted)]">{cr.caveats[0]}</p>
      )}
    </div>
  )
}

/* ── L2 ───────────────────────────────────────────────────────────────── */

function SideNotes({ side, session }) {
  const rows = [
    side?.nhnl && {
      key: 'nhnl', name: 'Breadth washout (NH/NL)', asks: 'how deep the internal flush is',
      state: `${side.nhnl.state} · 10-EMA ratio ${side.nhnl.ratio_10ema?.toFixed(2)}`,
      rate: side.nhnl.hist_rate_e1, date: side.nhnl.date,
    },
    side?.gex && {
      key: 'gex', name: 'Dealer gamma (GEX)', asks: 'how thick the dealer cushion is',
      state: `${Math.round((side.gex.pct_rank_252d ?? 0) * 100)}th percentile of the year`,
      rate: side.gex.hist_rate_e1, date: side.gex.date,
    },
  ].filter(Boolean)
  if (!rows.length) return null
  return (
    <div>
      <Label aside="annotations — not part of the probability above">Side readings</Label>
      <div className="space-y-1.5">
        {rows.map((r) => (
          <div key={r.key} className="grid grid-cols-[180px_1fr] gap-3 items-baseline text-[13px]">
            <span className="text-[var(--color-text)]">
              {r.name}
              <span className="block text-[11px] text-[var(--color-text-muted)]">{r.asks}</span>
            </span>
            {fresh(r.date, session) ? (
              <span className="text-[var(--color-text-secondary)] tabular-nums">
                {r.state} — a 5% drawdown followed {pct(r.rate)} of days in this state
              </span>
            ) : (
              <span className="text-[var(--color-text-muted)] italic">not measured (last {r.date})</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

/* ── L3 ───────────────────────────────────────────────────────────────── */

function TickCycle({ tc, session }) {
  if (!tc) return null
  return (
    <div>
      <Label aside="a different question — grinding or trending, not crashing">TICK cycle</Label>
      {fresh(tc.as_of, session)
        ? <p className="m-0 text-[13px] leading-relaxed text-[var(--color-text-secondary)] max-w-[80ch]">{englishReading(tc)}</p>
        : <NotMeasured what="TICK cycle" date={tc.as_of} />}
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
          <SideNotes side={cr.side_readings} session={session} />
        </div>
      )}
      {/* a heavier rule on purpose: L3 answers another question */}
      <div className="pt-3 border-t border-[var(--color-text-muted)]">
        <TickCycle tc={tc} session={session} />
      </div>
    </div>
  )
}
