/**
 * The regime band — one word, one binding condition.
 *
 * Design: Fluxus_Brand/visual/2026-08-10_TSF_PAGE_MAP.md §三 (approved 2026-08-10)
 *
 * Three voters, each already computed elsewhere and only READ here:
 *
 *   breadth    verdict.score        the twelve votes, −12…+12
 *   structure  spy_state/qqq_state  price structure of the two decision benchmarks
 *   power      macro signal         POWER_3 · CAUTION · WARNING · RISK_OFF
 *
 * The reading is the WEAKEST of the three, never the average. Averaging dilutes
 * one danger into a caution, and that one danger is the most expensive
 * information on the page. The other two voters print beside it so the
 * disagreement — which is the actual content — stays visible.
 *
 * Five bands in position language, not emotion language: what the state permits
 * you to hold, not how it feels. The line under the band names the binding
 * voter and the specific condition it is failing on — the same grammar as
 * Market State's "what would change this".
 */

export const BANDS = ['Defence', 'Caution', 'Neutral', 'Constructive', 'Full']

const POWER_LEVEL = { POWER_3: 4, CAUTION: 3, WARNING: 1, RISK_OFF: 0 }

/** Human names for the five power-trend checks, used when power is binding. */
const CHECK_LABEL = {
  '3d_gt_20sma': 'close > 20sma (3d)',
  '3d_gt_50sma': 'close > 50sma (3d)',
  '3d_gt_200sma': 'close > 200sma (3d)',
  '20sma_gt_50sma': '20sma > 50sma',
  '50sma_gt_200sma': '50sma > 200sma',
}

function breadthVoter(verdict) {
  const s = verdict?.score
  if (s == null) return null
  const level = s >= 8 ? 4 : s >= 4 ? 3 : s >= -3 ? 2 : s >= -7 ? 1 : 0
  // votes to the next band up, in the "what would change this" grammar
  const nextAt = [-7, -3, 4, 8][level] // threshold of the band above, if any
  const gap = level >= 4 ? null : nextAt - s
  return {
    name: 'breadth', level,
    word: `${s > 0 ? '+' : ''}${s}/12`,
    binding: gap == null ? null : `${gap} more vote${gap === 1 ? '' : 's'} to the next band`,
  }
}

function structureVoter(verdict) {
  const states = [verdict?.spy_state, verdict?.qqq_state]
  if (states.some((x) => x == null)) return null
  const up = states.filter((x) => x === 'Uptrend').length
  const down = states.filter((x) => x === 'Downtrend').length
  const level = down === 2 ? 0 : down === 1 ? 1 : up === 2 ? 4 : up === 1 ? 3 : 2
  const failing = ['SPY', 'QQQ'].filter((_, i) => states[i] !== 'Uptrend')
  return {
    name: 'structure', level,
    word: up === 2 ? 'both uptrends' : `${failing.join('+')} not in uptrend`,
    binding: failing.length ? `${failing.join(' and ')} below trend` : null,
  }
}

function powerVoter(signals) {
  const rows = ['SPY', 'QQQ'].map((t) => ({ t, s: signals?.[t] })).filter((r) => r.s)
  if (rows.length < 2) return null
  const weakest = rows.reduce((a, b) =>
    (POWER_LEVEL[a.s.signal] ?? 2) <= (POWER_LEVEL[b.s.signal] ?? 2) ? a : b)
  const level = POWER_LEVEL[weakest.s.signal] ?? 2
  const failing = Object.entries(weakest.s.power_trend ?? {})
    .filter(([, ok]) => !ok).map(([k]) => CHECK_LABEL[k] ?? k)
  return {
    name: 'power', level,
    word: `${weakest.t} ${weakest.s.signal.replace('_', ' ')}`,
    binding: failing.length ? `${weakest.t}: ${failing.join(', ')}` : null,
  }
}

export default function RegimeBand({ verdict, signals, onNavigate }) {
  const voters = [breadthVoter(verdict), structureVoter(verdict), powerVoter(signals)]
    .filter(Boolean)
  if (voters.length < 3) return null // a reading off partial voters would lie by omission

  const binding = voters.reduce((a, b) => (a.level <= b.level ? a : b))
  const level = binding.level

  return (
    <section className="border border-[var(--color-border)] rounded-lg px-4 py-3
                        bg-[var(--color-surface)]">
      <div className="flex items-baseline justify-between gap-4 flex-wrap">
        <span className="text-[10px] font-mono uppercase tracking-[.24em]
                         text-[var(--color-text-muted)]">
          Regime — the weakest of three, never the average
        </span>
        <button type="button" onClick={() => onNavigate?.('#/breadth')}
                className="text-[10px] bg-transparent border-0 p-0 cursor-pointer underline
                           text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
          the full instrument →
        </button>
      </div>

      <div className="flex items-center gap-[3px] mt-2">
        {BANDS.map((b, i) => (
          <div key={b} className="flex-1 text-center py-[5px] text-[11px] font-semibold
                                  uppercase tracking-wide"
               style={i === level
                 ? { background: level <= 1 ? 'var(--color-refused)' : 'var(--color-took)',
                     color: 'var(--color-bg)' }
                 : { border: '1px solid var(--color-border)',
                     color: 'var(--color-text-muted)' }}>
            {b}
          </div>
        ))}
      </div>

      <div className="mt-2 text-[11px] text-[var(--color-text-secondary)]">
        {voters.map((v, i) => (
          <span key={v.name}>
            {i > 0 && ' · '}
            <span className={v === binding ? 'font-semibold text-[var(--color-text)]' : ''}>
              {v.name} {v.word}
            </span>
          </span>
        ))}
        {binding.binding && (
          <span className="text-[var(--color-text-muted)]"> — held here by {binding.name}: {binding.binding}</span>
        )}
      </div>
    </section>
  )
}
