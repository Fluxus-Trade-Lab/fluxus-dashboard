import { useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Cell, ResponsiveContainer } from 'recharts'
import { rMultiple } from './lib/diagnosticsR'

/**
 * RR chart — every closed trade by its R-multiple (realizedPL ÷ initial risk).
 * Green = win, red = loss, ordered by exit date. The signature momentum shape:
 * a floor of small losses with a few towering right-tail winners.
 */
export default function RRChart({ enrichedTrades }) {
  const { data, avgWin, avgLoss, sumR, wr } = useMemo(() => {
    const rows = (enrichedTrades || [])
      .filter(t => t.isClosed)
      .map(t => {
        const exit = (t.trims?.length ? t.trims[t.trims.length - 1].date : t.entryDate) || ''
        return { r: rMultiple(t), ticker: t.ticker, exit: exit.slice(0, 10) }
      })
      .filter(d => d.r != null)
      .sort((a, b) => (a.exit < b.exit ? -1 : 1))
      .map((d, i) => ({ ...d, i, r: Math.round(d.r * 100) / 100 }))
    const wins = rows.filter(d => d.r > 0)
    const losses = rows.filter(d => d.r < 0)
    return {
      data: rows,
      avgWin: wins.length ? wins.reduce((s, d) => s + d.r, 0) / wins.length : 0,
      avgLoss: losses.length ? losses.reduce((s, d) => s + d.r, 0) / losses.length : 0,
      sumR: rows.reduce((s, d) => s + d.r, 0),
      wr: rows.length ? (wins.length / rows.length) * 100 : 0,
    }
  }, [enrichedTrades])

  if (data.length < 3) return null

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5">
      <div className="flex items-center justify-between mb-1">
        <span className="font-semibold text-[14px]">Every trade by R-multiple</span>
        <span className="text-[12.5px] text-[var(--color-text-muted)]">
          {data.length} trades · {wr.toFixed(0)}% win · +{sumR.toFixed(0)}R · avg win +{avgWin.toFixed(1)}R / loss {avgLoss.toFixed(1)}R
        </span>
      </div>
      <div className="text-[11px] text-[var(--color-text-muted)] mb-2">Green = win, red = loss · profit ÷ initial risk (1R)</div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 5, right: 8, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" vertical={false} />
          <XAxis dataKey="i" tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }} tickFormatter={() => ''} />
          <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} tickFormatter={v => `${v}R`} width={44} />
          <Tooltip
            cursor={{ fill: 'var(--color-border-light)' }}
            contentStyle={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 8, fontSize: 12 }}
            formatter={(v) => [`${v}R`, 'R-multiple']}
            labelFormatter={(i) => data[i]?.ticker + ' · ' + data[i]?.exit}
          />
          <ReferenceLine y={0} stroke="var(--color-text-muted)" />
          <ReferenceLine y={avgWin} stroke="var(--color-profit)" strokeDasharray="4 4" strokeOpacity={0.6} />
          <ReferenceLine y={avgLoss} stroke="var(--color-loss)" strokeDasharray="4 4" strokeOpacity={0.6} />
          <Bar dataKey="r" isAnimationActive={false}>
            {data.map((d, i) => <Cell key={i} fill={d.r > 0 ? '#2e9e4f' : '#d0362b'} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
