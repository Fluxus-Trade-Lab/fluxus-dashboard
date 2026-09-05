/**
 * Power Trend -- Mike Webster (O'Neil Capital Management / IBD Market School).
 *
 * Not Minervini's, and not "Oratnek-style"; this component and the pipeline
 * both used to say otherwise. Webster describes it in his own words in
 * `data/research/videos_2026-08/webster_21ema_wro9_GxQpyUfZv4U.txt`; the four
 * conditions and the OFF condition below are the written form from TradingSim
 * and Deepvue, both of which credit him. Citation trail:
 * `data/research/ops/recap_vocab_sources_2026-09-06.md` section 7.
 *
 * The state is the point. Power Trend turns on when the four conditions line up
 * and stays on until the 21-day EMA loses the 50-day SMA -- so on most days of a
 * healthy trend the row of checks will NOT be all green while the trend is on.
 * That is correct, and it is why the state gets its own row at the top.
 */

/** Webster's four ON conditions, in his order. */
const CHECKS = [
  { key: 'low_gt_ema21_10d', label: 'Low > 21 EMA (10d)' },
  { key: 'ema21_gt_sma50_5d', label: '21 EMA > 50 SMA (5d)' },
  { key: 'sma50_rising', label: '50 SMA rising' },
  { key: 'close_gt_open', label: 'Close > open' },
]

/** Ours, not Webster's -- shown under their own heading so they cannot pass for his. */
const STRUCTURE_CHECKS = [
  { key: '3d_gt_50sma', label: 'Close > 50 SMA (3d)' },
  { key: '3d_gt_200sma', label: 'Close > 200 SMA (3d)' },
  { key: '50sma_gt_200sma', label: '50 SMA > 200 SMA' },
]

const TICKERS = ['SPY', 'QQQ', 'IWM', 'RSP']

const HEAD_CELL =
  'text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] pb-1.5'

function YesNo({ on }) {
  return (
    <td
      className={`font-mono text-[13px] py-0.5 text-center ${
        on ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'
      }`}
    >
      {on ? 'Yes' : 'No'}
    </td>
  )
}

function CheckTable({ title, note, rows, field, stateRow }) {
  return (
    <div>
      <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
        {title}
      </h3>
      {note && (
        <p className="text-[11px] text-[var(--color-text-muted)] -mt-1 mb-2">{note}</p>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr>
              <th className={`${HEAD_CELL} pr-2`}>Check</th>
              {TICKERS.map((t) => (
                <th key={t} className={`${HEAD_CELL} text-center`}>
                  {t}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {stateRow}
            {rows.map((check) => (
              <tr key={check.key}>
                <td className="text-[13px] text-[var(--color-text-secondary)] py-0.5 pr-2">
                  {check.label}
                </td>
                {TICKERS.map((t) => (
                  <YesNo key={t} on={field(t)?.[check.key]} />
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function PowerTrend({ signals }) {
  if (!signals) return null

  const pt = (t) => signals[t]?.power_trend
  const ms = (t) => signals[t]?.ma_structure

  const stateRow = (
    <tr className="border-b border-[var(--color-border)]">
      <td className="text-[13px] font-medium text-[var(--color-text-primary)] py-0.5 pr-2">
        Power Trend
      </td>
      {TICKERS.map((t) => {
        const on = pt(t)?.is_power_trend
        return (
          <td
            key={t}
            className={`font-mono text-[13px] py-0.5 text-center ${
              on ? 'text-[var(--color-profit)]' : 'text-[var(--color-text-muted)]'
            }`}
          >
            {on ? 'ON' : 'OFF'}
          </td>
        )
      })}
    </tr>
  )

  return (
    <div className="space-y-4">
      <CheckTable
        title="Power Trend"
        note="Webster: on when all four line up, off when 21 EMA loses 50 SMA."
        rows={CHECKS}
        field={pt}
        stateRow={stateRow}
      />
      <CheckTable
        title="MA Structure"
        note="Ours, not part of the Power Trend definition."
        rows={STRUCTURE_CHECKS}
        field={ms}
      />
    </div>
  )
}
