import { useRef } from 'react'
import { LineSeries } from 'lightweight-charts'
import { useBreadthChart, chartTokens } from './useBreadthChart'

export default function RatioChart({ rows }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useBreadthChart(containerRef, chartRef, rows, (chart, data) => {
    const tk = chartTokens()
    const r5 = chart.addSeries(LineSeries, { color: tk.ink, lineWidth: 2.4, title: '5D' })
    r5.setData(data.filter((r) => r.ratio_5d != null)
      .map((r) => ({ time: r.date, value: r.ratio_5d })))
    const r10 = chart.addSeries(LineSeries, {
      color: '#78716c', lineWidth: 1, lineStyle: 2, title: '10D',
    })
    r10.setData(data.filter((r) => r.ratio_10d != null)
      .map((r) => ({ time: r.date, value: r.ratio_10d })))
    r5.createPriceLine({ price: 1.0, color: '#d6d3d1', lineWidth: 1, lineStyle: 2 })
  })

  if (!rows?.length) return null
  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-3">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
        Breadth Ratios (dashed reference = 1, up days equal down days)
      </h3>
      <div ref={containerRef} />
    </div>
  )
}
