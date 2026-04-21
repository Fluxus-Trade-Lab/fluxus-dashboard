import { useState } from 'react'
import RangeFilter from './RangeFilter'

export default function FilterPanel({ filters, onChange, onSearch }) {
  const [open, setOpen] = useState(true)
  const [tickerSearch, setTickerSearch] = useState('')

  const updateFilter = (key, value) => {
    onChange({ ...filters, [key]: value })
  }

  return (
    <div className="border border-[var(--color-border)] rounded-lg mb-4 bg-[var(--color-surface)]">
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="w-full flex items-center justify-between px-4 py-2 text-xs font-medium uppercase tracking-wide text-[var(--color-text-secondary)]"
      >
        <span>Filter Settings</span>
        <span>{open ? '▾' : '▸'}</span>
      </button>

      {open && (
        <div className="px-4 pb-4 grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Column 1: Ticker + Basic Info */}
          <div className="space-y-3">
            <div className="text-xs font-semibold text-[var(--color-text)] uppercase">Ticker</div>
            <div className="flex gap-1">
              <input
                type="text"
                value={tickerSearch}
                onChange={(e) => setTickerSearch(e.target.value)}
                placeholder="AAPL"
                className="border border-[var(--color-input-border)] rounded px-2 py-1 text-sm w-24"
              />
              <button
                onClick={() => onSearch(tickerSearch)}
                className="text-xs px-2 py-1 border border-[var(--color-input-border)] rounded hover:bg-[var(--color-hover-bg)]"
              >
                Search
              </button>
            </div>

            <div className="text-xs font-semibold text-[var(--color-text)] uppercase mt-3">Basic Info</div>
            <label className="flex items-center gap-1.5">
              <input type="checkbox" checked={filters.marketCapEnabled ?? true}
                onChange={(e) => updateFilter('marketCapEnabled', e.target.checked)}
                className="rounded border-[var(--color-input-border)]" />
              <span className="text-xs text-[var(--color-text-secondary)]">Market Cap</span>
            </label>
            <div className="flex items-center gap-1 text-xs text-[var(--color-text-secondary)]">
              <span>Min Market Cap (B)</span>
              <input type="number" value={filters.marketCapMin ?? 1}
                onChange={(e) => updateFilter('marketCapMin', Number(e.target.value))}
                className="border border-[var(--color-input-border)] rounded px-1.5 py-0.5 text-xs w-16 text-center" step="0.1" />
            </div>

            <label className="flex items-center gap-1.5">
              <input type="checkbox" checked={filters.vol50dEnabled ?? true}
                onChange={(e) => updateFilter('vol50dEnabled', e.target.checked)}
                className="rounded border-[var(--color-input-border)]" />
              <span className="text-xs text-[var(--color-text-secondary)]">Volume (M)</span>
            </label>
            <div className="flex items-center gap-1 text-xs text-[var(--color-text-secondary)]">
              <span>Min 50d Vol (M)</span>
              <input type="number" value={filters.vol50dMin ?? 1}
                onChange={(e) => updateFilter('vol50dMin', Number(e.target.value))}
                className="border border-[var(--color-input-border)] rounded px-1.5 py-0.5 text-xs w-16 text-center" step="0.1" />
            </div>

            <RangeFilter label="Rel Vol" filterKey="relVolume" value={filters.relVolume} onChange={(k,v) => updateFilter(k,v)} />

            <label className="flex items-center gap-1.5">
              <input type="checkbox" checked={filters.excludeHealthcare ?? false}
                onChange={(e) => updateFilter('excludeHealthcare', e.target.checked)}
                className="rounded border-[var(--color-input-border)]" />
              <span className="text-xs text-[var(--color-text-secondary)]">Exclude Healthcare</span>
            </label>

            <div className="text-xs font-semibold text-[var(--color-text)] uppercase mt-3">Flags</div>
            <label className="flex items-center gap-1.5">
              <input type="checkbox" checked={filters.trendBaseOnly ?? false}
                onChange={(e) => updateFilter('trendBaseOnly', e.target.checked)}
                className="rounded border-[var(--color-input-border)]" />
              <span className="text-xs text-[var(--color-text-secondary)]">Trend Base</span>
            </label>
            <label className="flex items-center gap-1.5">
              <input type="checkbox" checked={filters.pocketPivotOnly ?? false}
                onChange={(e) => updateFilter('pocketPivotOnly', e.target.checked)}
                className="rounded border-[var(--color-input-border)]" />
              <span className="text-xs text-[var(--color-text-secondary)]">Pocket Pivot</span>
            </label>
            <label className="flex items-center gap-1.5">
              <input type="checkbox" checked={filters.momentum97Only ?? false}
                onChange={(e) => updateFilter('momentum97Only', e.target.checked)}
                className="rounded border-[var(--color-input-border)]" />
              <span className="text-xs text-[var(--color-text-secondary)]">Momentum 97</span>
            </label>
          </div>

          {/* Column 2: Changes % + Price Action */}
          <div className="space-y-2">
            <div className="text-xs font-semibold text-[var(--color-text)] uppercase">Changes %</div>
            <RangeFilter label="Daily %" filterKey="dailyPct" value={filters.dailyPct} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="Weekly %" filterKey="weeklyPct" value={filters.weeklyPct} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="Monthly %" filterKey="monthlyPct" value={filters.monthlyPct} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="From Open %" filterKey="fromOpenPct" value={filters.fromOpenPct} onChange={(k,v) => updateFilter(k,v)} />

            <div className="text-xs font-semibold text-[var(--color-text)] uppercase mt-4">Price Action</div>
            <RangeFilter label="DCR %" filterKey="dcrPct" value={filters.dcrPct} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="PP Count" filterKey="ppCount" value={filters.ppCount} onChange={(k,v) => updateFilter(k,v)} />
          </div>

          {/* Column 3: Distance from MA + Volatility */}
          <div className="space-y-2">
            <div className="text-xs font-semibold text-[var(--color-text)] uppercase">Distance from MA</div>
            <RangeFilter label="21EMA Dist%" filterKey="sma20Dist" value={filters.sma20Dist} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="50SMA Dist%" filterKey="sma50Dist" value={filters.sma50Dist} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="200SMA Dist%" filterKey="sma200Dist" value={filters.sma200Dist} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="21EMA ATR Dist" filterKey="ema21Atr" value={filters.ema21Atr} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="50SMA ATR Dist" filterKey="sma50Atr" value={filters.sma50Atr} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="21EMA Low Dist%" filterKey="ema21LowDist" value={filters.ema21LowDist} onChange={(k,v) => updateFilter(k,v)} />

            <div className="text-xs font-semibold text-[var(--color-text)] uppercase mt-4">Volatility</div>
            <RangeFilter label="ADR %" filterKey="adrPct" value={filters.adrPct} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="VCS" filterKey="vcs" value={filters.vcs} onChange={(k,v) => updateFilter(k,v)} />
          </div>

          {/* Column 4: RS Scores + Other */}
          <div className="space-y-2">
            <div className="text-xs font-semibold text-[var(--color-text)] uppercase">RS Scores</div>
            <RangeFilter label="Hybrid RS" filterKey="hScore" value={filters.hScore} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="F Score" filterKey="fScore" value={filters.fScore} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="I Score" filterKey="iScore" value={filters.iScore} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="RS 1M" filterKey="rs21d" value={filters.rs21d} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="RS 3M" filterKey="rs63d" value={filters.rs63d} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="RS 6M" filterKey="rs126d" value={filters.rs126d} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="IBD RS" filterKey="rsIbd" value={filters.rsIbd} onChange={(k,v) => updateFilter(k,v)} />

            <div className="text-xs font-semibold text-[var(--color-text)] uppercase mt-4">Percentile</div>
            <RangeFilter label="1W Pctile" filterKey="perf1wPctile" value={filters.perf1wPctile} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="3M Pctile" filterKey="perf3mPctile" value={filters.perf3mPctile} onChange={(k,v) => updateFilter(k,v)} />

            <div className="text-xs font-semibold text-[var(--color-text)] uppercase mt-4">Other</div>
            <RangeFilter label="52W High%" filterKey="high52wDist" value={filters.high52wDist} onChange={(k,v) => updateFilter(k,v)} />
          </div>
        </div>
      )}
    </div>
  )
}
