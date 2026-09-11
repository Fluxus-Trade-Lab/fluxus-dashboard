import { useRotation } from '../../hooks/useRotation'

/**
 * Style rotation, sitting under the verdict and above the board.
 *
 * **Why here and not on Themes.** Placement follows the decision a reading
 * feeds, not what it resembles. These baskets are styles, so the question is
 * "is the market paying for risk" — the risk-budget question, the same one the
 * regime score answers from the other side. Themes answers "which one", a
 * different decision. Filed there, this panel would be read as a stock screen.
 *
 * **Why adjacent to the score specifically.** The two readings are usually in
 * tension and the tension is the information: today the board is Extended while
 * rotation says the turn is two weeks old and the month still disagrees. Apart,
 * a reader believes whichever they saw; together, "not yet a regime" has
 * something to contradict.
 *
 * The sentence is the product. The chart underneath is there so the sentence
 * can be checked, not so it can be skimmed instead.
 *
 * 2026-09-11: the three-cut table became one chart (fortnight solid, month
 * outline, both against a zero line — "do the horizons agree" is now a shape,
 * not two columns to compare), and the eleven baskets with their ten-week
 * ribbons were removed. Andy: 「11个主题百分比可以删除」 — Themes already
 * carries that board, and here it read as a stock screen.
 */

const pp = (v) => (v == null ? '—' : `${(v * 100 >= 0 ? '+' : '')}${(v * 100).toFixed(1)}pp`)

const PHASE_NOTE = {
  established: 'Both horizons agree — a regime.',
  turning: 'The fortnight has flipped and the month has not — a turn.',
  split: 'The cuts disagree with each other.',
}

export default function RotationPanel() {
  const { rotation, loading, error } = useRotation()

  // A missing rotation.json costs this panel and nothing else. Silence would be
  // worse than absence: the page would look complete while a reading it claims
  // to carry was gone.
  if (loading) return null
  if (error || !rotation?.verdict) {
    return (
      <div className="bg-[var(--color-bg)] rounded-2xl p-4">
        <h3 className="text-[11px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] m-0">
          Risk on / risk off
        </h3>
        <p className="mt-2 mb-0 text-[13px] text-[var(--color-text-muted)]">
          Rotation data unavailable — the verdict above is unaffected.
        </p>
      </div>
    )
  }

  const { verdict: v, cuts } = rotation
  // Was a paragraph under the panel; now the chart's hover note — Andy 09-06:
  // no explanatory text on the card, method goes where the curious look.
  const caveat = 'The cuts share large-cap names, so agreement between them means more ' +
    'instruments moved the same way — not three independent samples.'

  return (
    <div className="bg-[var(--color-bg)] rounded-2xl p-4">
      <div className="flex items-baseline justify-between gap-3 mb-3">
        <h3 className="text-[11px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] m-0">
          Risk on / risk off
        </h3>
        <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
          vs {rotation.benchmark} · {rotation.date}
        </span>
      </div>

      {/* The one line. Everything below exists to let it be checked. */}
      {/* a whole sentence in the encoding colour was the loudest instance of
          the leak — the phase note under it carries the reading in words */}
      <p className="m-0 text-[13px] leading-snug font-medium text-[var(--color-text)]">
        {v.sentence}
      </p>
      {PHASE_NOTE[v.phase] && (
        <p className="mt-1 mb-0 text-[11px] text-[var(--color-text-muted)]">
          {PHASE_NOTE[v.phase]}
        </p>
      )}

      <CutsChart cuts={cuts} caveat={caveat} />
    </div>
  )
}

/* ── the three cuts, one chart ─────────────────────────────────────────── */

const CW = 760, CROW = 44, CL = 230, CR = 60, CTOP = 24

function CutsChart({ cuts, caveat }) {
  if (!cuts?.length) return null
  const vals = cuts.flatMap((c) => [c.spread, c.month_spread]).filter(Number.isFinite).map((v) => v * 100)
  const lo = Math.min(-1, Math.floor(Math.min(...vals)))
  const hi = Math.max(1, Math.ceil(Math.max(...vals)))
  const x = (v) => CL + ((v - lo) / (hi - lo)) * (CW - CL - CR)
  const H = CTOP + cuts.length * CROW + 20
  const ticks = []
  for (let v = lo; v <= hi; v += 1) ticks.push(v)
  const bar = (v, y, solid, key) => {
    if (!Number.isFinite(v)) return null
    const a = x(Math.min(0, v)), b = x(Math.max(0, v))
    return (
      <g key={key}>
        <rect x={a} y={y} width={Math.max(1, b - a)} height="9" rx="2"
              fill={solid ? 'var(--color-took)' : 'none'} stroke="var(--color-took)" strokeWidth="1.2" />
        <text x={v >= 0 ? b + 6 : a - 6} y={y + 8} fontSize="11" textAnchor={v >= 0 ? 'start' : 'end'}
              style={{ fill: 'var(--color-text-secondary)' }}>{v > 0 ? '+' : ''}{v.toFixed(1)}</text>
      </g>
    )
  }
  return (
    <div className="mt-4" title={caveat}>
      <svg viewBox={`0 0 ${CW} ${H}`} className="w-full h-auto block" role="img"
           aria-label="risk-on minus risk-off spread for three cuts, fortnight and month">
        {ticks.map((v) => (
          <g key={v}>
            <line x1={x(v)} x2={x(v)} y1={CTOP - 8} y2={H - 18}
                  stroke={v === 0 ? 'var(--color-text)' : 'var(--color-border-light)'} strokeWidth={v === 0 ? 1.2 : 1} />
            <text x={x(v)} y={H - 4} fontSize="11" textAnchor="middle"
                  style={{ fill: 'var(--color-text-muted)' }}>{v > 0 ? `+${v}` : v}pp</text>
          </g>
        ))}
        <text x={x(lo)} y={CTOP - 12} fontSize="11" style={{ fill: 'var(--color-text-muted)' }}>← risk off</text>
        <text x={x(hi)} y={CTOP - 12} fontSize="11" textAnchor="end" style={{ fill: 'var(--color-text-muted)' }}>risk on →</text>
        {cuts.map((c, i) => {
          const y = CTOP + i * CROW
          return (
            <g key={c.key}>
              <title>{`${c.label}: fortnight ${pp(c.spread)}, month ${pp(c.month_spread)}, speed ${pp(c.delta)}`}</title>
              <text x="0" y={y + 12} fontSize="13" fontWeight="600" style={{ fill: 'var(--color-text)' }}>{c.label}</text>
              <text x="0" y={y + 28} fontSize="11" style={{ fill: 'var(--color-text-muted)' }}>
                {c.long.join('/')} − {c.short.join('/')} · speed {pp(c.delta)}
              </text>
              {bar(c.spread * 100, y + 2, true, 'f')}
              {bar(c.month_spread * 100, y + 15, false, 'm')}
            </g>
          )
        })}
      </svg>
      <div className="flex gap-4 mt-1 text-[11px] text-[var(--color-text-muted)]">
        <span><i className="inline-block w-3 h-[8px] mr-1.5 align-[0px] rounded-sm bg-[var(--color-took)]" />fortnight</span>
        <span><i className="inline-block w-3 h-[8px] mr-1.5 align-[0px] rounded-sm border border-[var(--color-took)]" />month</span>
      </div>
    </div>
  )
}
