import { useMemo } from 'react'
import Empty from '../Empty'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import StatCard from '../../portfolio/ui/StatCard'
import { computeBeta } from '../../portfolio/lib/diagnostics'
import { fmtCur, fmtPct, fmt, clr } from '../../portfolio/lib/portfolioFormat'

export default function RiskSection({ openTrades, enriched, heatData, sectorData, dailyPrices, spyHistory, portfolioValue }) {

  // Beta-weighted exposure
  const betaData = useMemo(() => {
    if (!openTrades.length) return null

    const rows = openTrades.map(t => {
      const beta = computeBeta(t.ticker, dailyPrices, spyHistory)
      const dir = t.direction === 'long' ? 1 : -1
      const mktVal = t.marketVal || 0
      const betaAdj = beta != null ? mktVal * beta * dir : null

      return {
        ticker: t.ticker,
        id: t.id,
        qty: t.currentQty,
        mktVal,
        beta,
        betaAdj,
        direction: t.direction,
        weight: t.weight || 0,
      }
    })

    const totalBetaAdj = rows.reduce((s, r) => s + (r.betaAdj ?? 0), 0)
    const portfolioBeta = portfolioValue > 0
      ? rows.reduce((s, r) => s + (r.weight / 100) * (r.beta ?? 1), 0)
      : 1

    return { rows, totalBetaAdj, portfolioBeta }
  }, [openTrades, dailyPrices, spyHistory, portfolioValue])

  // Heat bar chart data
  const heatChartData = heatData.positions
    .filter(p => p.hasStop)
    .slice(0, 15)
    .map(p => ({
      name: p.ticker,
      heat: Number(p.heat?.toFixed(2)) || 0,
    }))

  // Concentration by ticker
  const tickerConcentration = useMemo(() => {
    const byTicker = {}
    openTrades.forEach(t => {
      byTicker[t.ticker] = (byTicker[t.ticker] || 0) + (t.weight || 0)
    })
    return Object.entries(byTicker)
      .map(([name, weight]) => ({ name, weight: Number(weight.toFixed(1)) }))
      .sort((a, b) => b.weight - a.weight)
  }, [openTrades])

  // Long vs Short exposure
  const exposure = useMemo(() => {
    let longVal = 0, shortVal = 0
    openTrades.forEach(t => {
      if (t.direction === 'long') longVal += (t.marketVal || 0)
      else shortVal += (t.marketVal || 0)
    })
    const gross = longVal + shortVal
    const net = longVal - shortVal
    return {
      longPct: portfolioValue > 0 ? (longVal / portfolioValue) * 100 : 0,
      shortPct: portfolioValue > 0 ? (shortVal / portfolioValue) * 100 : 0,
      netPct: portfolioValue > 0 ? (net / portfolioValue) * 100 : 0,
      grossPct: portfolioValue > 0 ? (gross / portfolioValue) * 100 : 0,
    }
  }, [openTrades, portfolioValue])

  // Below every hook, so the hook count cannot change when the last position
  // closes. Sitting above `tickerConcentration` and `exposure`, this guard was
  // the same conditional-hook bug that took out the Screener page on
  // 2026-08-09.
  if (!openTrades.length) {
    return <Empty k="empty.noOpen" />
  }

  // v3: risk heat is a constraint scale — red only where risk binds (>2R),
  // grey below it. Green retired: an acceptable risk is not good news to
  // celebrate, it is the absence of a problem.
  const heatColor = (v) => v > 2 ? 'var(--color-loss)' : v > 1 ? 'var(--color-text-secondary)' : 'var(--color-untested)'

  return (
    <div className="space-y-5">
      {/* Portfolio Heat */}
      <div className="bg-[var(--color-surface)] rounded-3xl p-5">
        <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
          Portfolio Heat
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <StatCard
            label="Total Heat"
            value={fmtPct(heatData.totalHeat)}
            colorClass={heatData.totalHeat > 8 ? 'text-[var(--color-loss)]' : heatData.totalHeat > 6 ? 'text-[var(--color-signal-caution)]' : 'text-[var(--color-profit)]'}
          />
          <StatCard label="Positions" value={openTrades.length} />
          <StatCard
            label="No Stop Set"
            value={heatData.noStopCount}
            colorClass={heatData.noStopCount > 0 ? 'text-[var(--color-loss)]' : 'text-[var(--color-profit)]'}
          />
          <StatCard label="Avg Heat/Pos" value={fmtPct(heatData.positions.filter(p => p.hasStop).length > 0 ? heatData.totalHeat / heatData.positions.filter(p => p.hasStop).length : 0)} />
        </div>

        {heatData.totalHeat > 8 && (
          <div className="bg-[color-mix(in_srgb,var(--color-loss)_10%,transparent)] border border-[color-mix(in_srgb,var(--color-loss)_30%,transparent)] rounded-md px-3 py-2 text-[13px] text-[var(--color-loss)] mb-4">
            Total heat is {fmt(heatData.totalHeat, 1)}% — above 8% threshold. Consider reducing position sizes or tightening stops.
          </div>
        )}
        {heatData.noStopCount > 0 && (
          <div className="bg-[color-mix(in_srgb,var(--color-signal-caution)_10%,transparent)] border border-[color-mix(in_srgb,var(--color-signal-caution)_30%,transparent)] rounded-md px-3 py-2 text-[13px] text-[var(--color-signal-caution)] mb-4">
            {heatData.noStopCount} position{heatData.noStopCount > 1 ? 's have' : ' has'} no stop set — untracked risk.
          </div>
        )}

        {heatChartData.length > 0 && (
          <ResponsiveContainer width="100%" height={Math.max(200, heatChartData.length * 28)}>
            <BarChart data={heatChartData} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
              <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} tickFormatter={v => `${v}%`} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} width={60} />
              <Tooltip formatter={v => `${v}%`} contentStyle={{ fontSize: 11, background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }} />
              <Bar dataKey="heat" radius={[0, 4, 4, 0]}>
                {heatChartData.map((d, i) => <Cell key={i} fill={heatColor(d.heat)} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Concentration & Exposure */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Ticker concentration */}
        <div className="bg-[var(--color-surface)] rounded-3xl p-5">
          <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
            Concentration by Ticker
          </h3>
          <div className="space-y-1.5">
            {tickerConcentration.slice(0, 10).map(t => (
              <div key={t.name} className="flex items-center gap-2 text-[13px]">
                <span className="w-12 font-medium">{t.name}</span>
                <div className="flex-1 bg-[var(--color-bg)] rounded-full h-3 overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.min(100, t.weight)}%`,
                      // v3: red only where the weight binds (>15%); under it, grey
                      background: t.weight > 15 ? 'var(--color-loss)' : 'var(--color-text-secondary)',
                    }}
                  />
                </div>
                <span className={`w-12 text-right tabular-nums ${t.weight > 15 ? 'text-[var(--color-loss)] font-semibold' : ''}`}>{fmt(t.weight, 1)}%</span>
              </div>
            ))}
          </div>
          {tickerConcentration.some(t => t.weight > 15) && (
            <div className="mt-3 bg-[color-mix(in_srgb,var(--color-signal-caution)_10%,transparent)] border border-[color-mix(in_srgb,var(--color-signal-caution)_30%,transparent)] rounded-md px-3 py-2 text-[13px] text-[var(--color-signal-caution)]">
              Single-name concentration above 15% detected.
            </div>
          )}
        </div>

        {/* Direction exposure */}
        <div className="bg-[var(--color-surface)] rounded-3xl p-5">
          <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
            Exposure
          </h3>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <div className="text-[11px] text-[var(--color-text-muted)] uppercase mb-1">Long</div>
              <div className="text-[17px] font-bold tabular-nums text-[var(--color-profit)]">{fmt(exposure.longPct, 1)}%</div>
            </div>
            <div>
              <div className="text-[11px] text-[var(--color-text-muted)] uppercase mb-1">Short</div>
              <div className="text-[17px] font-bold tabular-nums text-[var(--color-loss)]">{fmt(exposure.shortPct, 1)}%</div>
            </div>
            <div>
              <div className="text-[11px] text-[var(--color-text-muted)] uppercase mb-1">Net</div>
              <div className={`text-[17px] font-bold tabular-nums ${clr(exposure.netPct)}`}>{fmt(exposure.netPct, 1)}%</div>
            </div>
            <div>
              <div className="text-[11px] text-[var(--color-text-muted)] uppercase mb-1">Gross</div>
              <div className="text-[17px] font-bold tabular-nums">{fmt(exposure.grossPct, 1)}%</div>
            </div>
          </div>

          {/* Sector breakdown */}
          {sectorData.length > 0 && (
            <>
              <h4 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2 mt-4">By Sector</h4>
              <div className="space-y-1.5">
                {sectorData.map(s => {
                  const pct = portfolioValue > 0 ? (s.value / portfolioValue) * 100 : 0
                  return (
                    <div key={s.name} className="flex items-center gap-2 text-[13px]">
                      <span className="w-24 truncate">{s.name}</span>
                      <div className="flex-1 bg-[var(--color-bg)] rounded-full h-3 overflow-hidden">
                        <div className="h-full rounded-full"
                             style={{ width: `${Math.min(100, pct)}%`,
                                      background: pct > 30 ? 'var(--color-loss)' : 'var(--color-text-secondary)' }} />
                      </div>
                      <span className={`w-12 text-right tabular-nums ${pct > 30 ? 'text-[var(--color-loss)] font-semibold' : ''}`}>{fmt(pct, 1)}%</span>
                    </div>
                  )
                })}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Beta-weighted exposure */}
      {betaData && (
        <div className="bg-[var(--color-surface)] rounded-3xl p-5">
          <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
            Beta-Weighted Exposure
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
            <StatCard label="Portfolio Beta" value={fmt(betaData.portfolioBeta, 2)} colorClass={betaData.portfolioBeta > 1.3 ? 'text-[var(--color-signal-caution)]' : ''} />
            <StatCard label="Beta-Adj Net" value={fmtCur(betaData.totalBetaAdj)} />
            <StatCard
              label="SPY Equivalent"
              value={`1% SPY ~ ${fmt(betaData.portfolioBeta * 100, 0)}bps`}
              sub={`A 1% SPY move ≈ ${fmt(betaData.portfolioBeta, 2)}% portfolio move`}
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[13px]">
              <thead>
                <tr>
                  {['Ticker', 'Dir', 'Qty', 'Mkt Val', 'Wt%', 'Beta', 'Beta-Adj Exp'].map(h => (
                    <th key={h} className="text-left px-2 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[11px] uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {betaData.rows.map((r, i) => (
                  <tr key={r.id || r.ticker + i} className={i % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-bg)]'}>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] font-medium">{r.ticker}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)]">
                      <span className={'text-[var(--color-text-secondary)]'}>{r.direction?.toUpperCase()}</span>
                    </td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{r.qty}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(r.mktVal)}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmt(r.weight, 1)}%</td>
                    <td className={`px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${r.beta != null && r.beta > 1.5 ? 'text-[var(--color-signal-caution)] font-semibold' : ''}`}>
                      {r.beta != null ? fmt(r.beta, 2) : '—'}
                    </td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{r.betaAdj != null ? fmtCur(r.betaAdj) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
