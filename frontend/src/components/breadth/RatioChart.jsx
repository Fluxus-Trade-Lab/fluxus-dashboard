import { useRef } from 'react'
import { LineSeries } from 'lightweight-charts'
import { useBreadthChart, chartTokens } from './useBreadthChart'
import { ORIG_COLS } from './origCols'

export default function RatioChart({ rows }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useBreadthChart(containerRef, chartRef, rows, (chart, data) => {
    const tk = chartTokens()
    const line = (key, opts) => {
      const ser = chart.addSeries(LineSeries, opts)
      ser.setData(data.filter((r) => r[key] != null).map((r) => ({ time: r.date, value: r[key] })))
      return ser
    }
    // Stockbee's own ratios (what votes) solid; the older point-to-point
    // ratios dotted and muted, kept so the history does not vanish while the
    // author's columns are only days old.
    line('ratio_5d', { color: tk.muted, lineWidth: 1, lineStyle: 1, title: '5D old' })
    line('ratio_10d', { color: tk.muted, lineWidth: 1, lineStyle: 1, title: '10D old' })
    const r5 = line(ORIG_COLS.ratio_5d, { color: tk.ink, lineWidth: 2.4, title: '5D' })
    line(ORIG_COLS.ratio_10d, { color: tk.ink, lineWidth: 1.2, lineStyle: 2, title: '10D' })
    r5.createPriceLine({ price: 1.0, color: tk.border, lineWidth: 1, lineStyle: 2 })
    r5.createPriceLine({ price: 2.0, color: tk.border, lineWidth: 1, lineStyle: 2, title: '10D thrust >2' })
  })

  if (!rows?.length) return null
  return (
    <div className="bg-[var(--color-bg)] rounded-2xl px-3 py-3">
      <h3 className="text-[11px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] mb-2">
        Up/down ratio · 5D / 10D · Stockbee solid · old count dotted
      </h3>
      <div ref={containerRef} />
    </div>
  )
}
