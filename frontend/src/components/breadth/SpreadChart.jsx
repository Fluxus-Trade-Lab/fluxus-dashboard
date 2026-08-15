import { useRef } from 'react'
import { BaselineSeries, LineSeries } from 'lightweight-charts'
import { useBreadthChart, chartTokens } from './useBreadthChart'

export default function SpreadChart({ rows }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useBreadthChart(containerRef, chartRef, rows, (chart, data) => {
    // v3: green retires — the spread around zero is the pair's home ground.
    // The spread is the subject (2.4); the two raw counts are context (1).
    const tk = chartTokens()
    const rgba = (h, a) => `rgba(${parseInt(h.slice(1,3),16)}, ${parseInt(h.slice(3,5),16)}, ${parseInt(h.slice(5,7),16)}, ${a})`
    const pts = data.filter((r) => r.up_25pct_qtr != null && r.down_25pct_qtr != null)
    const spread = chart.addSeries(BaselineSeries, {
      baseValue: { type: 'price', price: 0 },
      topLineColor: tk.took, topFillColor1: rgba(tk.took, 0.14),
      topFillColor2: rgba(tk.took, 0.02),
      bottomLineColor: tk.refused, bottomFillColor1: rgba(tk.refused, 0.02),
      bottomFillColor2: rgba(tk.refused, 0.14),
      lineWidth: 2.4,
    })
    spread.setData(pts.map((r) => ({ time: r.date, value: r.up_25pct_qtr - r.down_25pct_qtr })))
    const up = chart.addSeries(LineSeries, { color: rgba(tk.took, 0.45), lineWidth: 1 })
    up.setData(pts.map((r) => ({ time: r.date, value: r.up_25pct_qtr })))
    const down = chart.addSeries(LineSeries, { color: rgba(tk.refused, 0.45), lineWidth: 1 })
    down.setData(pts.map((r) => ({ time: r.date, value: r.down_25pct_qtr })))
  })

  if (!rows?.length) return null
  const last = rows[rows.length - 1]
  const spread = (last?.up_25pct_qtr ?? 0) - (last?.down_25pct_qtr ?? 0)
  return (
    <div className="bg-[var(--color-surface)] rounded-3xl px-3 py-3">
      <div className="flex items-baseline justify-between mb-2">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Quarterly Breadth (stocks moving 25%+ over the quarter)
        </h3>
        <span className={`text-[10px] font-mono ${spread > 0 ? 'text-[var(--color-took)]' : 'text-[var(--color-refused)]'}`}>
          {spread > 0 ? '+' : ''}{spread} spread
        </span>
      </div>
      <div ref={containerRef} />
    </div>
  )
}
