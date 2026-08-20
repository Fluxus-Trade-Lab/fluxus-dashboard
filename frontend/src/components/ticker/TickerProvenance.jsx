import { provenance } from './tickerReadings'

/**
 * Which file each half of this page is standing on, and how old it is.
 *
 * The page loads two sources and until 2026-08-20 said nothing about either.
 * That was survivable while both worked and became a lie when one stopped: the
 * header quoted a price from a file dated yesterday while the tables under it
 * printed dashes from a file that had failed, and no mark on the page told them
 * apart. A reader cannot size a position off numbers whose date they cannot
 * establish.
 *
 * `alive` is about PRICE specifically. A ticker file holding ten news items and
 * zero bars is not a feed that half worked — the news call succeeded and the
 * price call failed, and calling that "partial" would hide which half is the
 * one you were about to trade on.
 */
export default function TickerProvenance({ universe, tickerData }) {
  const p = provenance(universe, tickerData)
  const dead = p.tickerFile.present && !p.tickerFile.alive
  const stale = p.tickerFile.alive && p.tickerFile.ageDays != null && p.tickerFile.ageDays >= 3

  return (
    <div className="mb-4">
      <p className="m-0 text-[11px] font-mono leading-relaxed text-[var(--color-text-muted)]">
        水平位与读数 ← <b className="font-semibold">universe.json</b>
        {p.universe.barDate ? ` · ${p.universe.barDate} 收盘` : ' · 无日期'}
        {p.universe.stale === true && ' · 管线标了 bars_stale'}
        {'　'}｜{'　'}
        图表 / 财报 / 估值 / RSI ← <b className="font-semibold">tickers/{universe?.ticker ?? '—'}.json</b>
        {p.tickerFile.present
          ? ` · 抓取于 ${(p.tickerFile.fetched || '').slice(0, 10) || '未知'}`
          : ' · 无此文件'}
      </p>

      {(dead || stale) && (
        <p className="m-0 mt-1.5 text-[11.5px] leading-relaxed text-[var(--color-text-secondary)]
                      border-l-2 border-[var(--color-refused)] pl-2.5">
          {dead ? (
            <>
              这个名字的<b className="font-semibold">价格抓取失败了</b> —— 文件在，
              {p.tickerFile.hasNews ? '新闻也在，' : ''}K 线是空的。
              下面凡是标「未测量」的都是因为这个，<b className="font-semibold">不是这只票没有那个读数</b>。
              上面的水平位来自 universe.json，是新鲜的。
            </>
          ) : (
            <>
              这个名字的价格文件是 <b className="font-semibold">{p.tickerFile.ageDays} 天前</b>抓的
              （universe 是 {p.universe.barDate}）。20 日线这类跑得快的读数会明显偏；
              长周期的偏得少。
            </>
          )}
        </p>
      )}
    </div>
  )
}
