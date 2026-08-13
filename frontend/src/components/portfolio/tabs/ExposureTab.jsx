import { useState, useMemo, Fragment } from 'react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, ReferenceLine } from 'recharts'
import { usePortfolio } from '../context/PortfolioContext'
import SortableHeader from '../ui/SortableHeader'
import CapitalAtRiskWidget from '../ui/CapitalAtRiskWidget'
import TickerLink from '../../ticker/TickerLink'
import { groupByCampaigns } from '../lib/campaign'
import { fmtCur, fmtPct, fmt, clr, SECTOR_COLORS, MASK } from '../lib/portfolioFormat'

export default function ExposureTab({ openTrades, mergedHoldingsData, performanceData, capitalEfficiency }) {
  const { state } = usePortfolio()
  const pm = state.privacyMode

  // Capital deployment over time: cash % of equity, with cumulative return overlaid.
  const deployData = useMemo(
    () => (performanceData || []).map(p => ({
      date: p.date,
      cashPct: Math.round((p.cashPct ?? 100) * 10) / 10,
      returnPct: Math.round((p.returnPct ?? 0) * 10) / 10,
    })),
    [performanceData]
  )
  const ce = capitalEfficiency
  // Risk as a share of capital needs current equity, not starting capital — the
  // latter overstates the percentage as the account grows.
  const lastMark = performanceData?.length ? performanceData[performanceData.length - 1] : null
  // Leverage = gross exposure ÷ CURRENT equity (not starting capital, which
  // overstates as the account grows). Averaged over days with a position.
  const lev = useMemo(() => {
    const vals = (performanceData || []).map(p => p.leveragePct).filter(v => v > 0.5)
    if (!vals.length) return null
    return { avg: vals.reduce((a, b) => a + b, 0) / vals.length, peak: Math.max(...vals) }
  }, [performanceData])

  const [expandedTickers, setExpandedTickers] = useState({})

  const toggleTicker = (ticker) => {
    setExpandedTickers(prev => ({ ...prev, [ticker]: !prev[ticker] }))
  }

  // Group OPEN trades into pyramid campaigns (Phase 1: campaign view)
  const groupedTrades = useMemo(() => {
    const campaigns = groupByCampaigns(openTrades)
    return campaigns.map(c => {
      const totalQty = c.layers.reduce((s, t) => s + t.currentQty, 0)
      const totalCostBasis = c.layers.reduce((s, t) => s + t.entryPrice * t.currentQty, 0)
      const avgEntry = totalQty > 0 ? totalCostBasis / totalQty : c.blendedEntry
      return {
        ticker: c.ticker,
        trades: c.layers,
        isGroup: c.layers.length > 1,
        direction: c.direction,
        totalQty,
        avgEntry,
        lastPrice: c.layers[0].lastPrice,
        weight: c.layers.reduce((s, t) => s + t.weight, 0),
        marketVal: c.layers.reduce((s, t) => s + t.marketVal, 0),
        totalPL: c.layers.reduce((s, t) => s + t.totalPL, 0),
        totalReturnPct: totalCostBasis > 0
          ? c.layers.reduce((s, t) => s + t.totalPL, 0) / totalCostBasis * 100
          : 0,
        _campaignLayers: c.openLayersCount,
        _totalRDollars: c.totalRDollars,
      }
    })
  }, [openTrades])

  const DETAIL_HEADERS = [
    { label: 'Ticker', key: 'ticker' },
    { label: 'Dir', key: 'direction' },
    { label: 'Entry', key: 'avgEntry' },
    { label: 'Last', key: 'lastPrice' },
    { label: 'Wt%', key: 'weight' },
    { label: 'P/L%', key: 'totalReturnPct' },
    { label: 'Qty', key: 'totalQty' },
    { label: 'Mkt Val', key: 'marketVal' },
    { label: 'P/L $', key: 'totalPL' },
  ]

  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'desc' })

  const handleSort = (key) => {
    setSortConfig(prev => {
      if (prev.key === key) return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' }
      const stringCol = ['ticker', 'direction'].includes(key)
      return { key, direction: stringCol ? 'asc' : 'desc' }
    })
  }

  const sortedGroupedTrades = useMemo(() => {
    if (!sortConfig.key) return groupedTrades
    const arr = [...groupedTrades]
    arr.sort((a, b) => {
      const av = a[sortConfig.key]
      const bv = b[sortConfig.key]
      const aNull = av == null || av === ''
      const bNull = bv == null || bv === ''
      if (aNull && bNull) return 0
      if (aNull) return 1
      if (bNull) return -1
      if (typeof av === 'string' && typeof bv === 'string') {
        return sortConfig.direction === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
      }
      return sortConfig.direction === 'asc' ? av - bv : bv - av
    })
    return arr
  }, [groupedTrades, sortConfig])

  // Every hook above runs unconditionally. This guard used to sit near the top
  // with four hooks below it, so the hook count changed the moment the last
  // position closed and React tore the tab down — the same conditional-hook
  // bug that took out the Screener page on 2026-08-09.
  if (openTrades.length === 0) {
    return <div className="text-center py-16 text-[var(--color-text-muted)]">No open positions.</div>
  }

  // Privacy-aware currency
  const cur = (v) => pm ? MASK : fmtCur(v)

  return (
    <div>
      {deployData.length > 0 && (
        <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5 mb-5">
          <div className="flex items-center justify-between mb-3">
            <span className="font-semibold text-[14px]">Capital Deployment</span>
            <span className="text-[12.5px] text-[var(--color-text-muted)]">How hard the capital worked over time</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            {[
              ['Return on deployed', ce?.returnOnDeployed != null ? ce.returnOnDeployed.toFixed(1) + '%' : '—', 'P&L per $1 at risk'],
              ['vs total capital', ce?.totalReturnPct != null ? '+' + ce.totalReturnPct.toFixed(1) + '%' : '—', 'return on full base'],
              ['Avg leverage', lev ? (lev.avg / 100).toFixed(2) + '×' : '—', 'gross ÷ equity'],
              ['Peak leverage', lev ? (lev.peak / 100).toFixed(2) + '×' : '—', 'gross ÷ equity'],
            ].map(([l, v, sub]) => (
              <div key={l} className="bg-[var(--color-surface-raised)] rounded p-3">
                <div className="text-[12.5px] text-[var(--color-text-muted)]">{l}</div>
                <div className="text-[17px] font-bold">{v}</div>
                <div className="text-[10px] text-[var(--color-text-muted)]">{sub}</div>
              </div>
            ))}
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={deployData} margin={{ top: 5, right: 8, left: -8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} minTickGap={44} tickFormatter={d => d.slice(5)} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} tickFormatter={v => v + '%'} width={44} />
              <Tooltip
                contentStyle={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 8, fontSize: 12 }}
                formatter={(val, name) => [val + '%', name]}
              />
              <ReferenceLine y={0} stroke="var(--color-text-muted)" />
              <ReferenceLine y={100} stroke="var(--color-border)" strokeDasharray="4 4" />
              <Line type="monotone" dataKey="cashPct" name="Cash %" stroke="#2a78d6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="returnPct" name="Cumulative return %" stroke="#1baf7a" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
          <div className="flex gap-4 mt-2 text-[12.5px] text-[var(--color-text-muted)]">
            <span><span style={{ color: '#2a78d6' }}>■</span> Cash % of equity</span>
            <span><span style={{ color: '#1baf7a' }}>■</span> Cumulative return %</span>
            <span className="ml-auto">100% = fully in cash · below 0 = on margin</span>
          </div>
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5">
        <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
          <div className="font-semibold mb-3 text-[14px]">Holdings</div>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={mergedHoldingsData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={90}
                label={({ name, weight }) => `${name} ${weight}%`}
                labelLine={{ strokeWidth: 1 }}
                stroke="var(--color-surface)"
                strokeWidth={2}
              >
                {mergedHoldingsData.map((_, i) => (
                  <Cell key={i} fill={SECTOR_COLORS[i % SECTOR_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => pm ? MASK : fmtCur(v)} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <CapitalAtRiskWidget openTrades={openTrades} pm={pm}
                             equity={lastMark?.value} markDate={lastMark?.date} />
      </div>

      <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
        <div className="font-semibold mb-3 text-[14px]">Detail</div>
        <table className="w-full border-collapse text-[12.5px]">
          <thead>
            <tr>
              {DETAIL_HEADERS.map(h => (
                <SortableHeader
                  key={h.key}
                  label={h.label}
                  sortKey={h.key}
                  sortConfig={sortConfig}
                  onSort={handleSort}
                />
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedGroupedTrades.map((g, idx) => {
              const expanded = expandedTickers[g.ticker]
              const rowBg = idx % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-bg)]'
              return (
                <Fragment key={g.ticker}>{/* Group header row */}
                  <tr key={g.ticker} className={`${rowBg} ${g.isGroup ? 'cursor-pointer hover:bg-[var(--color-surface-raised)]' : ''}`} onClick={() => g.isGroup && toggleTicker(g.ticker)}>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] font-bold">
                      {g.isGroup && <span className="inline-block w-3.5 text-[var(--color-text-muted)] text-[10px]">{expanded ? '▼' : '▶'}</span>}
                      <TickerLink symbol={g.ticker} />
                      {g.isGroup && (
                        <span className="ml-1 text-[10px] text-[var(--color-text-muted)]">
                          campaign · {g.trades.length} layers
                        </span>
                      )}
                    </td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)]">
                      <span className={'text-[var(--color-text-secondary)]'}>{g.direction.toUpperCase()}</span>
                    </td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(g.avgEntry)}</td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(g.lastPrice)}</td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmt(g.weight, 1)}%</td>
                    <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${clr(g.totalReturnPct)}`}>{fmtPct(g.totalReturnPct)}</td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{pm ? MASK : g.totalQty}</td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{cur(g.marketVal)}</td>
                    <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums font-semibold ${pm ? '' : clr(g.totalPL)}`}>{cur(g.totalPL)}</td>
                  </tr>
                  {/* Expanded child rows */}
                  {g.isGroup && expanded && g.trades.map((t) => (
                    <tr key={t.id} className="bg-[var(--color-surface-raised)]">
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] pl-7 text-[var(--color-text-muted)]">
                        <TickerLink symbol={t.ticker} className="text-[var(--color-text-muted)]" />
                      </td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)]">
                        <span className={'text-[var(--color-text-secondary)]'}>{t.direction.toUpperCase()}</span>
                      </td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(t.entryPrice)}</td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(t.lastPrice)}</td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums">{fmt(t.weight, 1)}%</td>
                      <td className={`px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums ${clr(t.totalReturnPct)}`}>{fmtPct(t.totalReturnPct)}</td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums">{pm ? MASK : t.currentQty}</td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums">{cur(t.marketVal)}</td>
                      <td className={`px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums font-semibold ${pm ? '' : clr(t.totalPL)}`}>{cur(t.totalPL)}</td>
                    </tr>
                  ))}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
