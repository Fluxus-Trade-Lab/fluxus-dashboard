import { useRotation } from '../../hooks/useRotation'
import StateRibbon from '../shared/StateRibbon'

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
 * The sentence is the product. The table underneath is there so the sentence
 * can be checked, not so it can be skimmed instead.
 */

const pp = (v) => (v == null ? '—' : `${(v * 100 >= 0 ? '+' : '')}${(v * 100).toFixed(1)}pp`)

const CALL_STYLE = {
  risk_on: 'text-[var(--color-profit)]',
  risk_off: 'text-[var(--color-loss)]',
}

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
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] m-0">
          Style Rotation
        </h3>
        <p className="mt-2 mb-0 text-sm text-[var(--color-text-muted)]">
          Rotation data unavailable — the verdict above is unaffected.
        </p>
      </div>
    )
  }

  const { verdict: v, cuts, baskets, bucket_labels: labels, state_windows: win } = rotation
  const windowNote =
    `State computed on ${win?.level_sessions ?? 63}-session level and ` +
    `${win?.near_sessions ?? 21}-session near windows, not on the fortnight grid.`

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
      <div className="flex items-baseline justify-between gap-3 mb-3">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] m-0">
          Style Rotation · Risk On / Risk Off
        </h3>
        <span className="text-[10px] font-mono text-[var(--color-text-muted)]">
          vs {rotation.benchmark} · {rotation.date}
        </span>
      </div>

      {/* The one line. Everything below exists to let it be checked. */}
      <p className={`m-0 text-[15px] leading-snug font-medium ${CALL_STYLE[v.call] ?? ''}`}>
        {v.sentence}
      </p>
      {PHASE_NOTE[v.phase] && (
        <p className="mt-1 mb-0 text-[11px] text-[var(--color-text-muted)]">
          {PHASE_NOTE[v.phase]}
        </p>
      )}

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-[12px] border-collapse">
          <thead>
            <tr className="text-[var(--color-text-muted)] text-[9px] uppercase tracking-[.14em]">
              <th className="text-left font-medium py-1 pr-2">Cut</th>
              <th className="text-right font-medium py-1 px-2">Fortnight</th>
              <th className="text-right font-medium py-1 px-2">Month</th>
              <th className="text-right font-medium py-1 pl-2" title="This fortnight's spread against the previous one — the speed of the turn">
                Speed
              </th>
            </tr>
          </thead>
          <tbody>
            {cuts.map((c) => (
              <tr key={c.key} className="border-t border-[var(--color-border)]">
                <td className="py-1.5 pr-2">
                  <span className="font-medium">{c.label}</span>
                  <span className="ml-2 text-[10px] font-mono text-[var(--color-text-muted)]">
                    {c.long.join('/')} − {c.short.join('/')}
                  </span>
                </td>
                <td className={`py-1.5 px-2 text-right tabular-nums ${CALL_STYLE[c.vote] ?? ''}`}>
                  {pp(c.spread)}
                </td>
                <td className={`py-1.5 px-2 text-right tabular-nums ${CALL_STYLE[c.month_vote] ?? ''}`}>
                  {pp(c.month_spread)}
                </td>
                <td className="py-1.5 pl-2 text-right tabular-nums text-[var(--color-text-secondary)]">
                  {pp(c.delta)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Ten weeks of state per basket. The bucket labels are printed once,
          under the ribbons, because five repeats of the same axis is noise. */}
      <div className="mt-5">
        <div className="grid grid-cols-[minmax(96px,auto)_1fr_auto] gap-x-3 gap-y-[6px] items-center">
          {baskets.map((b) => (
            <div key={b.ticker} className="contents">
              <span className="text-[11px] truncate" title={`${b.name} (${b.ticker})`}>
                {b.name}
              </span>
              <StateRibbon steps={b.ribbon} labels={labels} windowNote={windowNote} />
              <span className={`text-[10px] font-mono tabular-nums w-[52px] text-right ${
                b.side === 'risk_on' ? 'text-[var(--color-text-secondary)]'
                                     : 'text-[var(--color-text-muted)]'}`}>
                {b.level == null ? '—' : `${(b.level * 100).toFixed(1)}%`}
              </span>
            </div>
          ))}

          {/* The axis lives inside the same grid rather than being pushed into
              place with calculated padding. Structural alignment cannot drift
              when a column width changes; arithmetic alignment silently can.
              Five equal columns so each label centres under its own segment —
              justify-between would pin the ends and let the middle three wander. */}
          <span />
          <span className="grid mt-1 text-[9px] font-mono text-[var(--color-text-muted)]"
                style={{ gridTemplateColumns: `repeat(${labels?.length ?? 5}, minmax(0, 1fr))`,
                         gap: '2px' }}>
            {labels?.map((l) => <span key={l} className="text-center">{l}</span>)}
          </span>
          <span />
        </div>
      </div>

      <p className="mt-4 pt-3 border-t border-[var(--color-border)] m-0
                    text-[10px] leading-relaxed text-[var(--color-text-muted)]">
        The cuts share large-cap names, so agreement between them means more
        instruments moved the same way — not three independent samples. Ribbon
        blocks are fortnights of drawing; {windowNote.charAt(0).toLowerCase() + windowNote.slice(1)}
      </p>
    </div>
  )
}
