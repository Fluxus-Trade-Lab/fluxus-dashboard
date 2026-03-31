import { useRef, useEffect } from 'react'
import { createChart, ColorType, CandlestickSeries, LineSeries } from 'lightweight-charts'

/* ── MA helpers ──────────────────────────────────────────── */

function computeSMA(closes, period) {
  const result = []
  let sum = 0
  for (let i = 0; i < closes.length; i++) {
    sum += closes[i]
    if (i >= period) sum -= closes[i - period]
    if (i >= period - 1) {
      result.push(sum / period)
    } else {
      result.push(null)
    }
  }
  return result
}

function computeEMA(closes, period) {
  const k = 2 / (period + 1)
  const result = []
  let ema = null
  // Seed with SMA of first `period` values
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) {
      result.push(null)
    } else if (i === period - 1) {
      let sum = 0
      for (let j = 0; j <= i; j++) sum += closes[j]
      ema = sum / period
      result.push(ema)
    } else {
      ema = closes[i] * k + ema * (1 - k)
      result.push(ema)
    }
  }
  return result
}

/* ── Theme helpers ───────────────────────────────────────── */

function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

function getThemeColors() {
  const dark = isDarkMode()
  return {
    background: dark ? '#292524' : '#ffffff',
    textColor: dark ? '#a8a29e' : '#78716c',
    gridColor: dark ? '#3a3733' : '#f5f5f4',
    candleUp: '#16a34a',
    candleDown: '#dc2626',
    wickUp: '#16a34a',
    wickDown: '#dc2626',
  }
}

/* ── Component ───────────────────────────────────────────── */

export default function OhlcvChart({
  data,
  showMAs = true,
  height = 350,
  spyData,
}) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current || !data?.length) return

    // Clean up previous chart
    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
    }

    const theme = getThemeColors()
    const w = containerRef.current.clientWidth

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: theme.background },
        textColor: theme.textColor,
        fontSize: 10,
      },
      grid: {
        vertLines: { color: theme.gridColor },
        horzLines: { color: theme.gridColor },
      },
      width: w,
      height,
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false },
      crosshair: { horzLine: { visible: false, labelVisible: false } },
    })

    // Candlestick series
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: theme.candleUp,
      downColor: theme.candleDown,
      borderUpColor: theme.candleUp,
      borderDownColor: theme.candleDown,
      wickUpColor: theme.wickUp,
      wickDownColor: theme.wickDown,
    })
    candleSeries.setData(data)

    // MA overlays
    if (showMAs) {
      const closes = data.map((d) => d.close)
      const times = data.map((d) => d.time)

      const maConfigs = [
        { values: computeEMA(closes, 21), color: '#3b82f6', width: 1.5 },  // blue
        { values: computeSMA(closes, 50), color: '#f59e0b', width: 1.5 },  // amber
        { values: computeSMA(closes, 200), color: '#a8a29e', width: 1 },   // gray
      ]

      for (const ma of maConfigs) {
        const lineData = []
        for (let i = 0; i < times.length; i++) {
          if (ma.values[i] !== null) {
            lineData.push({ time: times[i], value: ma.values[i] })
          }
        }
        if (lineData.length > 0) {
          const series = chart.addSeries(LineSeries, {
            color: ma.color,
            lineWidth: ma.width,
            crosshairMarkerVisible: false,
            priceLineVisible: false,
            lastValueVisible: false,
          })
          series.setData(lineData)
        }
      }
    }

    // SPY overlay (normalized to % change from first bar)
    if (spyData?.length > 0) {
      const base = spyData[0].close
      const spyLine = spyData.map(d => ({
        time: d.time,
        value: ((d.close - base) / base) * 100,
      }))

      const spySeries = chart.addSeries(LineSeries, {
        color: '#6366f1',
        lineWidth: 1.5,
        lineStyle: 2, // dashed
        crosshairMarkerVisible: false,
        priceLineVisible: false,
        lastValueVisible: true,
        title: 'SPY %',
        priceScaleId: 'spy',
      })
      spySeries.setData(spyLine)

      chart.priceScale('spy').applyOptions({
        scaleMargins: { top: 0.7, bottom: 0 },
        borderVisible: false,
      })
    }

    chart.timeScale().fitContent()
    chartRef.current = chart

    // Resize handler
    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
        })
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
  }, [data, showMAs, height, spyData])

  // Fallback
  if (!data?.length) {
    return (
      <div
        className="flex items-center justify-center text-[var(--color-text-muted)] text-xs"
        style={{ height }}
      >
        No chart data
      </div>
    )
  }

  return <div ref={containerRef} />
}
