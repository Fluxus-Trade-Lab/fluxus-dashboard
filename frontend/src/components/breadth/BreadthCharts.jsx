import { useRef, useEffect } from 'react'
import { createChart, ColorType } from 'lightweight-charts'

export default function BreadthCharts({ data }) {
  if (!data?.history) return null

  return (
    <div className="space-y-3">
      <MaChart history={data.history} />
      <McClellanChart history={data.history} />
    </div>
  )
}

function MaChart({ history }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current || !history?.dates?.length) return

    // Clean up previous chart
    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
    }

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
      width: containerRef.current.clientWidth,
      height: 200,
      rightPriceScale: {
        borderVisible: false,
      },
      timeScale: {
        borderVisible: false,
      },
      crosshair: {
        horzLine: { visible: false, labelVisible: false },
      },
    })

    const dates = history.dates

    // % above 200 SMA (blue)
    const sma200Series = chart.addLineSeries({
      color: '#3b82f6',
      lineWidth: 1.5,
      title: '200 SMA',
    })
    sma200Series.setData(
      dates.map((d, i) => ({ time: d, value: history.pct_above_200sma[i] ?? 0 }))
    )

    // % above 50 SMA (amber)
    const sma50Series = chart.addLineSeries({
      color: '#f59e0b',
      lineWidth: 1.5,
      title: '50 SMA',
    })
    sma50Series.setData(
      dates.map((d, i) => ({ time: d, value: history.pct_above_50sma[i] ?? 0 }))
    )

    // % above 20 SMA (stone)
    const sma20Series = chart.addLineSeries({
      color: '#a8a29e',
      lineWidth: 1,
      title: '20 SMA',
    })
    sma20Series.setData(
      dates.map((d, i) => ({ time: d, value: history.pct_above_20sma[i] ?? 0 }))
    )

    chart.timeScale().fitContent()
    chartRef.current = chart

    // Resize handler
    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: containerRef.current.clientWidth })
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
  }, [history])

  return (
    <div className="bg-white border border-stone-200 rounded px-3 py-3">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-stone-500 mb-2">
        % Above Moving Averages — 100 Day
      </h3>
      <div ref={containerRef} />
    </div>
  )
}

function McClellanChart({ history }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current || !history?.dates?.length) return

    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
    }

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
      width: containerRef.current.clientWidth,
      height: 150,
      rightPriceScale: {
        borderVisible: false,
      },
      timeScale: {
        borderVisible: false,
      },
      crosshair: {
        horzLine: { visible: false, labelVisible: false },
      },
    })

    const dates = history.dates
    const mcData = dates.map((d, i) => {
      const val = history.mcclellan_osc[i] ?? 0
      return {
        time: d,
        value: val,
        color: val >= 0 ? '#22c55e' : '#ef4444',
      }
    })

    const mcSeries = chart.addHistogramSeries({
      title: 'McClellan',
    })
    mcSeries.setData(mcData)

    chart.timeScale().fitContent()
    chartRef.current = chart

    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: containerRef.current.clientWidth })
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
  }, [history])

  return (
    <div className="bg-white border border-stone-200 rounded px-3 py-3">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-stone-500 mb-2">
        McClellan Oscillator — 100 Day
      </h3>
      <div ref={containerRef} />
    </div>
  )
}
