import { useRef, useEffect, useCallback } from 'react'
import { createChart, ColorType, LineSeries } from 'lightweight-charts'

// Deduplicate history by date (keep last occurrence) to prevent
// lightweight-charts from crashing on duplicate timestamps.
function dedupeHistory(history) {
  if (!history?.dates?.length) return history
  const seen = new Set()
  const indices = []
  for (let i = history.dates.length - 1; i >= 0; i--) {
    if (!seen.has(history.dates[i])) {
      seen.add(history.dates[i])
      indices.unshift(i)
    }
  }
  const pick = (arr) => indices.map((i) => arr[i])
  return {
    ...history,
    dates: pick(history.dates),
    pct_above_200sma: pick(history.pct_above_200sma),
    pct_above_50sma: pick(history.pct_above_50sma),
    pct_above_20sma: pick(history.pct_above_20sma),
    mcclellan_osc: pick(history.mcclellan_osc),
  }
}

export default function BreadthCharts({ data }) {
  if (!data?.history) return null

  const history = dedupeHistory(data.history)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
      <MaChart history={history} />
      <McClellanChart history={history} />
    </div>
  )
}

function useChart(containerRef, chartRef, history, setupFn, height) {
  const setup = useCallback(setupFn, [])

  useEffect(() => {
    if (!containerRef.current || !history?.dates?.length) return

    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
    }

    const w = containerRef.current.clientWidth
    const h = height ?? Math.max(160, Math.round(w * 0.35))

    const root = getComputedStyle(document.documentElement)
    const bgColor = root.getPropertyValue('--color-surface').trim() || '#ffffff'
    const txtColor = root.getPropertyValue('--color-text-secondary').trim() || '#78716c'
    const gridColor = root.getPropertyValue('--color-border-light').trim() || '#f5f5f4'

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: bgColor },
        textColor: txtColor,
        fontSize: 10,
      },
      grid: {
        vertLines: { color: gridColor },
        horzLines: { color: gridColor },
      },
      width: w,
      height: h,
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false },
      crosshair: { horzLine: { visible: false, labelVisible: false } },
    })

    setup(chart, history)
    chart.timeScale().fitContent()
    chartRef.current = chart

    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        const newW = containerRef.current.clientWidth
        const newH = height ?? Math.max(160, Math.round(newW * 0.35))
        chartRef.current.applyOptions({ width: newW, height: newH })
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (chartRef.current) {
        chartRef.current.remove()
        chartRef.current = null
      }
    }
  }, [history, height, setup])
}

function MaChart({ history }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useChart(containerRef, chartRef, history, (chart, hist) => {
    const dates = hist.dates

    const sma200 = chart.addSeries(LineSeries, { color: '#3b82f6', lineWidth: 1.5, title: '200 SMA' })
    sma200.setData(dates.map((d, i) => ({ time: d, value: hist.pct_above_200sma[i] ?? 0 })))

    const sma50 = chart.addSeries(LineSeries, { color: '#f59e0b', lineWidth: 1.5, title: '50 SMA' })
    sma50.setData(dates.map((d, i) => ({ time: d, value: hist.pct_above_50sma[i] ?? 0 })))

    const sma20 = chart.addSeries(LineSeries, { color: '#a8a29e', lineWidth: 1, title: '20 SMA' })
    sma20.setData(dates.map((d, i) => ({ time: d, value: hist.pct_above_20sma[i] ?? 0 })))
  })

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-3">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
        % Above Moving Averages
      </h3>
      <div ref={containerRef} />
    </div>
  )
}

function McClellanChart({ history }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useChart(containerRef, chartRef, history, (chart, hist) => {
    const dates = hist.dates
    const mcData = dates.map((d, i) => ({
      time: d,
      value: hist.mcclellan_osc[i] ?? 0,
    }))

    const mcSeries = chart.addSeries(LineSeries, {
      color: '#78716c',
      lineWidth: 1.5,
      title: 'McClellan',
      crosshairMarkerRadius: 3,
    })
    mcSeries.setData(mcData)

    // Zero line baseline
    mcSeries.createPriceLine({
      price: 0,
      color: '#d6d3d1',
      lineWidth: 1,
      lineStyle: 2, // dashed
    })
  })

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-3">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
        McClellan Oscillator
      </h3>
      <div ref={containerRef} />
    </div>
  )
}
