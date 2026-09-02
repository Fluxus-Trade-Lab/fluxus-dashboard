import { keyLevels } from './tickerReadings'
import { fmtCur } from '../portfolio/lib/portfolioFormat'

/**
 * Key Levels — off universe.json, which is the file that is actually current.
 *
 * This table used to read `tickers/<T>.json`. On 2026-08-20 that file was empty
 * of prices for half the site and eleven days old for the other half, so the
 * page printed eight dashes for MRNA while universe.json held its 52-week
 * position, all three moving-average distances and the pivot stop, dated
 * 2026-08-19.
 *
 * Two things the old table did that this one does not: it named a moving
 * average and then wrote its own opinion of it ("Trend support lost —
 * caution"), and it printed "—" for a level nobody measured, which is the same
 * mark it printed for a level that came out empty. A price recovered from a
 * published distance is labelled as recovered; a level this file cannot supply
 * says which file it would have come from.
 */
export default function TickerKeyLevels({ universe, tickerData }) {
  const rows = keyLevels(universe)
  if (!rows.length) {
    return (
      <div className="bg-[var(--color-bg)] rounded-3xl p-5">
        <div className="font-semibold mb-3 text-[13px]">Key Levels</div>
        <p className="m-0 text-[13px] text-[var(--color-text-muted)]">
          这个代码不在 universe.json 里 —— 不是没有水平位，是这个名字没被扫到。
        </p>
      </div>
    )
  }
  const fileAlive = (tickerData?.ohlc_2y?.length || tickerData?.ohlc_1y?.length || 0) > 0

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5">
      <div className="font-semibold mb-3 text-[13px]">Key Levels</div>
      {/* The table scrolls inside itself; the page never scrolls sideways.
          Adding the distance column pushed Key Levels 41px past a 375px
          viewport and took the whole document with it. */}
      <div className="overflow-x-auto -mx-1 px-1">
      <table className="w-full min-w-[420px] text-[13px]">
        <thead>
          <tr className="text-left text-[11px] text-[var(--color-text-muted)] uppercase
                         tracking-wide border-b border-[var(--color-border-light)]">
            <th className="px-2 py-1.5">Level</th>
            <th className="px-2 py-1.5 text-right">Price</th>
            <th className="px-2 py-1.5 text-right">离现价</th>
            <th className="px-2 py-1.5">Notes</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.label} className="border-b border-[var(--color-border-light)]">
              <td className="px-2 py-1.5 font-semibold whitespace-nowrap">{r.label}</td>
              <td className="px-2 py-1.5 text-right tabular-nums">
                {r.price == null
                  ? <span className="text-[var(--color-text-muted)] italic text-[11px]">未测量</span>
                  : <>{fmtCur(r.price)}{r.derived && (
                      <span className="ml-1 text-[11px] text-[var(--color-text-muted)]"
                            title="由管线发布的距离反推：close / (1 + dist)。200 日线对得上 0.01%，算法本身核过">
                        ↩
                      </span>)}</>}
              </td>
              <td className="px-2 py-1.5 text-right tabular-nums text-[var(--color-text-secondary)]">
                {r.dist == null ? '' : `${r.dist > 0 ? '+' : ''}${r.dist.toFixed(1)}%`}
              </td>
              <td className="px-2 py-1.5 text-[var(--color-text-muted)] text-[11px]">
                {r.from === 'ticker_file'
                  ? <>来自 tickers/{universe.ticker}.json{fileAlive ? '' : '（今天抓空）'}</>
                  : r.note}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
      <p className="m-0 mt-2.5 text-[11px] font-mono text-[var(--color-text-muted)]">
        ↩ = 由管线发布的距离反推的价，不是管线直接给的价
      </p>
    </div>
  )
}
