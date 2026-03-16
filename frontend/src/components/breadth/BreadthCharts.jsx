import { useRef, useEffect, useCallback } from 'react'
import { createChart, ColorType, LineSeries, HistogramSeries } from 'lightweight-charts'

export default function BreadthCharts({ data }) {
  if (!data?.history) return null

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
      <MaChart history={data.history} />
      <McClellanChart history={data.history} />
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

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#78716c',
        fontSize: 10,
      },
      grid: {
        vertLines: { color: '#f5f5f4' },
        horzLines: { color: '#f5f5f4' },
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
    <div className="bg-white border border-stone-200 rounded px-3 py-3">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-stone-500 mb-2">
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
    const mcData = dates.map((d, i) => {
      const val = hist.mcclellan_osc[i] ?? 0
      return { time: d, value: val, color: val >= 0 ? '#22c55e' : '#ef4444' }
    })

    const mcSeries = chart.addSeries(HistogramSeries, { title: 'McClellan' })
    mcSeries.setData(mcData)
  })

  return (
    <div className="bg-white border border-stone-200 rounded px-3 py-3">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-stone-500 mb-2">
        McClellan Oscillator
      </h3>
      <div ref={containerRef} />
    </div>
  )
}
