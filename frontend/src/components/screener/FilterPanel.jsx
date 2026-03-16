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

            <label className="flex items-center gap-1.5">
              <input type="checkbox" checked={filters.excludeHealthcare ?? false}
                onChange={(e) => updateFilter('excludeHealthcare', e.target.checked)}
                className="rounded border-[var(--color-input-border)]" />
              <span className="text-xs text-[var(--color-text-secondary)]">Exclude Healthcare</span>
            </label>
          </div>

          {/* Column 2: Changes % */}
          <div className="space-y-2">
            <div className="text-xs font-semibold text-[var(--color-text)] uppercase">Changes %</div>
            <RangeFilter label="Daily %" filterKey="dailyPct" value={filters.dailyPct} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="Weekly %" filterKey="weeklyPct" value={filters.weeklyPct} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="Monthly %" filterKey="monthlyPct" value={filters.monthlyPct} onChange={(k,v) => updateFilter(k,v)} />
          </div>

          {/* Column 3: Distance from MA */}
          <div className="space-y-2">
            <div className="text-xs font-semibold text-[var(--color-text)] uppercase">Distance from MA</div>
            <RangeFilter label="21EMA Dist%" filterKey="sma20Dist" value={filters.sma20Dist} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="50SMA Dist%" filterKey="sma50Dist" value={filters.sma50Dist} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="200SMA Dist%" filterKey="sma200Dist" value={filters.sma200Dist} onChange={(k,v) => updateFilter(k,v)} />
          </div>

          {/* Column 4: Volatility + RS + Other */}
          <div className="space-y-2">
            <div className="text-xs font-semibold text-[var(--color-text)] uppercase">Volatility</div>
            <RangeFilter label="ADR %" filterKey="adrPct" value={filters.adrPct} onChange={(k,v) => updateFilter(k,v)} />

            <div className="text-xs font-semibold text-[var(--color-text)] uppercase mt-4">RS Scores</div>
            <RangeFilter label="IBD RS" filterKey="rsIbd" value={filters.rsIbd} onChange={(k,v) => updateFilter(k,v)} />
            <RangeFilter label="RS 63d" filterKey="rs63d" value={filters.rs63d} onChange={(k,v) => updateFilter(k,v)} />

            <div className="text-xs font-semibold text-[var(--color-text)] uppercase mt-4">Other</div>
            <RangeFilter label="52W High%" filterKey="high52wDist" value={filters.high52wDist} onChange={(k,v) => updateFilter(k,v)} />
          </div>
        </div>
      )}
    </div>
  )
}
