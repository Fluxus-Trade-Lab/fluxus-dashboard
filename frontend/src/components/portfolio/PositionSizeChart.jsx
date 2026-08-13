import { useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Cell, ResponsiveContainer } from 'recharts'
import { rMultiple } from './lib/diagnosticsR'

/**
 * Position size per trade — notional at entry ÷ equity at entry (%), in the SAME
 * order as the RR chart (by exit date) so the bars line up one-to-one. Green =
 * the trade won, red = it lost. Studies bet-sizing / conviction calibration: do
 * the big bets earn their size, or are the biggest positions the biggest mistakes?
 */
export default function PositionSizeChart({ enrichedTrades, performanceData, startingCapital }) {
  const { data, avg, corr, lossShareTopQ } = useMemo(() => {
    const eq = performanceData || []
    const equityAt = (date) => {
      const d = (date || '').slice(0, 10)
      let v = startingCapital
      for (const p of eq) { if (p.date <= d) v = p.value; else break }
      return v || startingCapital
    }
    const rows = (enrichedTrades || [])
      .filter(t => t.isClosed)
      .map(t => {
        const exit = (t.trims?.length ? t.trims[t.trims.length - 1].date : t.entryDate) || ''
        const notional = (t.originalQty || 0) * (t.entryPrice || 0)
        const size = notional / equityAt(t.entryDate) * 100
        return { size: Math.round(size * 100) / 100, r: rMultiple(t), pl: t.realizedPL ?? t.totalPL ?? 0, ticker: t.ticker, exit: exit.slice(0, 10) }
      })
      .filter(d => d.size > 0)
      .sort((a, b) => (a.exit < b.exit ? -1 : 1))
      .map((d, i) => ({ ...d, i }))
    if (rows.length < 3) return { data: [] }

    const sizes = rows.map(d => d.size)
    const Rs = rows.map(d => d.r).filter(r => r != null)
    const mean = a => a.reduce((s, x) => s + x, 0) / a.length
    const std = a => { const m = mean(a); return Math.sqrt(a.reduce((s, x) => s + (x - m) ** 2, 0) / a.length) }
    let corr = null
    const paired = rows.filter(d => d.r != null)
    if (paired.length > 2 && std(paired.map(d => d.size)) > 0 && std(paired.map(d => d.r)) > 0) {
      const ms = mean(paired.map(d => d.size)), mr = mean(paired.map(d => d.r))
      const cov = mean(paired.map(d => (d.size - ms) * (d.r - mr)))
      corr = cov / (std(paired.map(d => d.size)) * std(paired.map(d => d.r)))
    }
    const order = [...rows].sort((a, b) => b.size - a.size)
    const topQ = new Set(order.slice(0, Math.max(1, Math.floor(rows.length / 4))).map(d => d.i))
    const grossLoss = rows.filter(d => d.pl < 0).reduce((s, d) => s + -d.pl, 0) || 1
    const lossTopQ = rows.filter(d => topQ.has(d.i) && d.pl < 0).reduce((s, d) => s + -d.pl, 0)
    return { data: rows, avg: mean(sizes), corr, lossShareTopQ: lossTopQ / grossLoss * 100 }
  }, [enrichedTrades, performanceData, startingCapital])

  if (data.length < 3) return null

  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
      <div className="flex items-center justify-between mb-1">
        <span className="font-semibold text-[14px]">Position size per trade</span>
        <span className="text-[12.5px] text-[var(--color-text-muted)]">
          avg {avg.toFixed(1)}% · size↔R corr {corr != null ? (corr >= 0 ? '+' : '') + corr.toFixed(2) : '—'} · {lossShareTopQ.toFixed(0)}% of losses from biggest quartile
        </span>
      </div>
      <div className="text-[11px] text-[var(--color-text-muted)] mb-2">
        Same order as the RR chart · notional ÷ equity at entry · green = won, red = lost. Corr ≈ 0 means size doesn't predict which trades work — sizing adds no edge.
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 5, right: 8, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" vertical={false} />
          <XAxis dataKey="i" tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }} tickFormatter={() => ''} />
          <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} tickFormatter={v => `${v}%`} width={44} />
          <Tooltip
            cursor={{ fill: 'var(--color-border-light)' }}
            contentStyle={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 8, fontSize: 12 }}
            formatter={(v, n, p) => [`${v}% of equity${p?.payload?.r != null ? ` · ${p.payload.r.toFixed(1)}R` : ''}`, 'Position size']}
            labelFormatter={(i) => data[i]?.ticker + ' · ' + data[i]?.exit}
          />
          <ReferenceLine y={avg} stroke="var(--color-text-muted)" strokeDasharray="4 4" strokeOpacity={0.6} />
          <Bar dataKey="size" isAnimationActive={false}>
            {data.map((d, i) => <Cell key={i} fill={d.pl > 0 ? '#2e9e4f' : '#d0362b'} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
