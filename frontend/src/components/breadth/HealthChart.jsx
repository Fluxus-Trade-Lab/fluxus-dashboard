import { useRef } from 'react'
import { CandlestickSeries, LineSeries } from 'lightweight-charts'
import { useBreadthChart, chartTokens } from './useBreadthChart'

export default function HealthChart({ title, block, state, t2108, warnCount }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useBreadthChart(containerRef, chartRef, block, (chart, blk) => {
    const candles = chart.addSeries(CandlestickSeries, {
      upColor: chartTokens().took, downColor: chartTokens().refused,
      wickUpColor: chartTokens().took, wickDownColor: chartTokens().refused,
      borderVisible: false,
    })
    candles.setData(blk.candles.map((c) => ({
      time: c.date, open: c.o, high: c.h, low: c.l, close: c.c,
    })))

    const mkLine = (values, color, width) => {
      const s = chart.addSeries(LineSeries, { color, lineWidth: width, priceLineVisible: false })
      s.setData(blk.candles
        .map((c, i) => ({ time: c.date, value: values[i] }))
        .filter((p) => p.value != null))
      return s
    }
    mkLine(blk.sma20, chartTokens().muted, 1)
    mkLine(blk.sma50, chartTokens().secondary, 1)

    if (t2108?.dates?.length) {
      const overlay = chart.addSeries(LineSeries, {
        // dotted: the 20 SMA is the same grey at the same width, and two lines
        // told apart by nothing is two lines nobody can tell apart
        color: chartTokens().muted, lineWidth: 1, lineStyle: 1, priceScaleId: 't2108',
        priceLineVisible: false,
      })
      overlay.setData(t2108.dates.map((d, i) => ({ time: d, value: t2108.values[i] ?? 0 })))
      chart.priceScale('t2108').applyOptions({
        scaleMargins: { top: 0.05, bottom: 0.05 }, visible: false,
      })
      overlay.createPriceLine({ price: 20, color: chartTokens().border, lineWidth: 1, lineStyle: 2 })
      overlay.createPriceLine({ price: 80, color: chartTokens().border, lineWidth: 1, lineStyle: 2 })
    }
  })

  if (!block) return null
  const last = block.candles[block.candles.length - 1]
  const prev = block.candles[block.candles.length - 2]
  const dayPct = prev ? ((last.c / prev.c - 1) * 100).toFixed(2) : null

  return (
    // frameless since 2026-09-11 — BenchmarkPanel's card is the frame, and the
    // five warning cells sit under this chart inside it
    <div>
      <div className="flex items-baseline justify-between mb-2">
        <h3 className="text-[13px] font-semibold text-[var(--color-text)]">
          {title}
          {state && <span className="ml-2 text-[11px] font-normal text-[var(--color-text-muted)]">{state}</span>}
        </h3>
        <span className="text-[11px] font-mono text-[var(--color-text-secondary)]">
          {last.c.toLocaleString()} {dayPct != null ? `(${dayPct}%)` : ''}
          {warnCount != null && <span className="ml-2 text-[var(--color-text-muted)]">{warnCount}/5</span>}
        </span>
      </div>
      <div ref={containerRef} />
      <div className="text-[11px] text-[var(--color-text-muted)] mt-1">
        20 SMA thin · 50 SMA dark · T2108 dotted, 20/80 dashed
      </div>
    </div>
  )
}
