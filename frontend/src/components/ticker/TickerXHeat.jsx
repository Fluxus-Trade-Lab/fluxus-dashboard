/**
 * X 热度: how many distinct X accounts mentioned this ticker in the
 * file's own trailing window (data/output/x_heat.json). This is a head
 * count, not sentiment — DATA_CONTRACTS §七 2026-09-23 is explicit that the
 * column answers "how many people are talking", not bullish/bearish.
 *
 * A ticker missing from `rows` means nobody mentioned it in the window, but
 * that reads identically to a broken fetch, so it must never collapse to
 * "0 人" — the two need to stay visually distinguishable as "no data".
 */
export default function TickerXHeat({ symbol, xHeat }) {
  if (!xHeat) return null

  const row = (xHeat.rows || []).find((r) => r.ticker === symbol) || null
  const windowLabel = formatWindow(xHeat.window)

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-4 mb-4">
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-[11px] text-[var(--color-text-muted)] uppercase tracking-wide">X 热度</span>
        {windowLabel && (
          <span className="text-[11px] text-[var(--color-text-muted)]">{windowLabel}</span>
        )}
      </div>
      {row ? (
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className="tabular-nums text-[13px] font-semibold">近 7 日 {row.people_7d} 人提及</span>
          {row.peak_day != null && row.peak_people != null && (
            <span className="text-[11px] text-[var(--color-text-muted)]">
              峰值 {formatDay(row.peak_day)}（{row.peak_people} 人）
            </span>
          )}
        </div>
      ) : (
        <span className="tabular-nums text-[13px] text-[var(--color-text-muted)]">— 无数据</span>
      )}
    </div>
  )
}

function formatDay(d) {
  return String(d).slice(5)
}

function formatWindow(w) {
  if (!w || !w.start || !w.end) return null
  return `${formatDay(w.start)}–${formatDay(w.end)}`
}
