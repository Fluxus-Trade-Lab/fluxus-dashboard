import { useRef } from 'react'
import { BaselineSeries, LineSeries } from 'lightweight-charts'
import { useBreadthChart } from './useBreadthChart'

export default function SpreadChart({ rows }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useBreadthChart(containerRef, chartRef, rows, (chart, data) => {
    const pts = data.filter((r) => r.up_25pct_qtr != null && r.down_25pct_qtr != null)
    const spread = chart.addSeries(BaselineSeries, {
      baseValue: { type: 'price', price: 0 },
      topLineColor: '#4d7c0f', topFillColor1: 'rgba(77, 124, 15, 0.15)',
      topFillColor2: 'rgba(77, 124, 15, 0.02)',
      bottomLineColor: '#b91c1c', bottomFillColor1: 'rgba(185, 28, 28, 0.02)',
      bottomFillColor2: 'rgba(185, 28, 28, 0.15)',
      lineWidth: 1.5,
    })
    spread.setData(pts.map((r) => ({ time: r.date, value: r.up_25pct_qtr - r.down_25pct_qtr })))
    const up = chart.addSeries(LineSeries, { color: 'rgba(77,124,15,0.5)', lineWidth: 1 })
    up.setData(pts.map((r) => ({ time: r.date, value: r.up_25pct_qtr })))
    const down = chart.addSeries(LineSeries, { color: 'rgba(185,28,28,0.5)', lineWidth: 1 })
    down.setData(pts.map((r) => ({ time: r.date, value: r.down_25pct_qtr })))
  })

  if (!rows?.length) return null
  const last = rows[rows.length - 1]
  const spread = (last?.up_25pct_qtr ?? 0) - (last?.down_25pct_qtr ?? 0)
  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-3">
      <div className="flex items-baseline justify-between mb-2">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Quarterly Breadth (stocks moving 25%+ over the quarter)
        </h3>
        <span className={`text-[10px] font-mono ${spread > 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
          {spread > 0 ? '+' : ''}{spread} spread
        </span>
      </div>
      <div ref={containerRef} />
    </div>
  )
}
