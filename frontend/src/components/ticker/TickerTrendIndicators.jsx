import { indicators } from './tickerReadings'

/**
 * Readings — printed, not narrated.
 *
 * What this replaced invented "Golden alignment", "Death cross alignment",
 * "Trending — near 52W high", "Pullback in uptrend" and an
 * overbought/neutral/oversold ladder: a second model living in the frontend, on
 * a site whose pipeline already publishes `sp_setup` / `sp_signal` / `sp_phase`
 * for that exact question and whose universe hook warns in its own comment that
 * a frontend re-deriving a pipeline definition is how this site once ended up
 * with two Watchlists.
 *
 * So the numbers are ours to show and the naming stays the pipeline's. ATR 位
 * is the same `atr_from_sma50` every other page on the site reads, which is the
 * point — a reading that means one thing here and another thing on Today's List
 * is worse than no reading.
 */
export default function TickerTrendIndicators({ universe }) {
  const rows = indicators(universe)
  if (!rows.length) {
    return (
      <div className="bg-[var(--color-bg)] rounded-3xl p-5">
        <div className="font-semibold mb-3 text-[14px]">Readings</div>
        <p className="m-0 text-[13px] text-[var(--color-text-muted)]">
          这个代码不在 universe.json 里。
        </p>
      </div>
    )
  }
  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5">
      <div className="font-semibold mb-3 text-[14px]">Readings</div>
      {/* The table scrolls inside itself; the page never scrolls sideways.
          Adding the distance column pushed Key Levels 41px past a 375px
          viewport and took the whole document with it. */}
      <div className="overflow-x-auto -mx-1 px-1">
      <table className="w-full min-w-[300px] text-[12.5px]">
        <thead>
          <tr className="text-left text-[10px] text-[var(--color-text-muted)] uppercase
                         tracking-wide border-b border-[var(--color-border-light)]">
            <th className="px-2 py-1.5">Reading</th>
            <th className="px-2 py-1.5">Value</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.label} className="border-b border-[var(--color-border-light)]">
              <td className="px-2 py-1.5 font-semibold whitespace-nowrap">{r.label}</td>
              <td className="px-2 py-1.5 text-[var(--color-text-secondary)]">
                {r.value == null ? (
                  <span className="italic text-[var(--color-text-muted)] text-[11.5px]">
                    未测量{r.from === 'ticker_file' && ' —— 来自 tickers/ 的那半边，今天抓空'}
                  </span>
                ) : (
                  <>
                    <span className="tabular-nums text-[var(--color-text-bold)]">{r.value}</span>
                    {r.note && (
                      <span className="ml-2 text-[11px] text-[var(--color-text-muted)]">{r.note}</span>
                    )}
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  )
}
