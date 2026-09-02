import { fmtCur, fmtPct, fmt } from '../portfolio/lib/portfolioFormat'

/**
 * Flat row of stats sourced from universe.json. Placeholder for Phase 3b/3c
 * where the rich fundamentals + technicals tables will live.
 */
export default function TickerStats({ universe }) {
  const u = universe
  if (!u) {
    return (
      <div className="bg-[var(--color-bg)] rounded-3xl p-5">
        <div className="font-semibold mb-3 text-[13px]">Stats</div>
        <div className="text-[var(--color-text-muted)] text-[13px]">
          Not in current screener universe (delisted or under filter floor).
        </div>
      </div>
    )
  }

  const cells = [
    ['Sector', u.sector || '—'],
    ['Industry', u.industry || '—'],
    ['Mkt Cap', u.market_cap ? `$${(u.market_cap / 1e9).toFixed(2)}B` : '—'],
    ['Avg Vol (50D)', u.avg_volume ? `${(u.avg_volume / 1e6).toFixed(1)}M` : '—'],
    ['ADR%', u.adr_pct != null ? `${u.adr_pct.toFixed(1)}%` : '—'],
    ['ATR', u.atr ? fmtCur(u.atr) : '—'],
    ['Hybrid RS', u.h_score ?? '—'],
    ['RS 21D', u.rs_21d ?? '—'],
    ['RS 63D', u.rs_63d ?? '—'],
    ['Perf 1W', u.perf_1w != null ? fmtPct(u.perf_1w * 100) : '—'],
    ['Perf 1M', u.perf_1m != null ? fmtPct(u.perf_1m * 100) : '—'],
    ['Perf 3M', u.perf_3m != null ? fmtPct(u.perf_3m * 100) : '—'],
    ['Perf 1Y', u.perf_1y != null ? fmtPct(u.perf_1y * 100) : '—'],
    ['52W High%', u.high_52w_dist != null ? `${u.high_52w_dist.toFixed(1)}%` : '—'],
    ['Dist 20EMA%', u.sma20_dist != null ? `${(u.sma20_dist * 100).toFixed(1)}%` : '—'],
    ['Dist 50SMA%', u.sma50_dist != null ? `${(u.sma50_dist * 100).toFixed(1)}%` : '—'],
    ['Dist 200SMA%', u.sma200_dist != null ? `${(u.sma200_dist * 100).toFixed(1)}%` : '—'],
    ['Rel Vol', u.rel_volume != null ? `${u.rel_volume.toFixed(2)}×` : '—'],
  ]

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5">
      <div className="font-semibold mb-3 text-[13px]">Stats</div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-x-4 gap-y-2 text-[13px]">
        {cells.map(([label, value]) => (
          <div key={label} className="flex flex-col">
            <span className="text-[11px] text-[var(--color-text-muted)] uppercase tracking-wide">{label}</span>
            <span className="tabular-nums">{value}</span>
          </div>
        ))}
      </div>
      <div className="text-[11px] text-[var(--color-text-muted)] mt-4">
        Fundamentals (P/S, P/E, margins, EPS history, analyst sentiment, catalysts, trade plan)
        ship in Phase 3b–3d. The <code>/tearsheet {u.ticker}</code> slash command will refresh AI-synthesized narrative.
      </div>
    </div>
  )
}
