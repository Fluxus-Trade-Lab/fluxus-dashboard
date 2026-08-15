import { useRef, useEffect, useState } from 'react'
import { createChart, ColorType, CandlestickSeries, LineSeries, HistogramSeries } from 'lightweight-charts'

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

/* ── Weekly aggregation ─────────────────────────────────── */

function toWeekly(daily) {
  if (!daily?.length) return []
  const weeks = []
  let current = null

  for (const bar of daily) {
    // Parse ISO date to get week start (Monday)
    const d = new Date(bar.time + 'T00:00:00')
    const day = d.getDay()
    const diff = d.getDate() - day + (day === 0 ? -6 : 1) // Monday
    const weekStart = new Date(d)
    weekStart.setDate(diff)
    const weekKey = weekStart.toISOString().slice(0, 10)

    if (!current || current._week !== weekKey) {
      if (current) weeks.push(current)
      current = {
        _week: weekKey,
        time: bar.time, // Use first bar's date as the week time
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
        volume: bar.volume,
      }
    } else {
      current.high = Math.max(current.high, bar.high)
      current.low = Math.min(current.low, bar.low)
      current.close = bar.close
      current.volume += bar.volume
    }
  }
  if (current) weeks.push(current)

  // Strip internal _week key
  return weeks.map(({ _week, ...rest }) => rest)
}

/* ── MA config ──────────────────────────────────────────── */

const MA_CONFIGS = [
  { period: 10, type: 'ema', color: null, tone: '--color-untested', width: 1,   label: '10E' },
  { period: 21, type: 'ema', color: null, tone: '--color-text-muted', width: 1.5, label: '21E' },
  { period: 50, type: 'sma', color: null, tone: '--color-text-secondary', width: 1.5, label: '50' },
  { period: 200, type: 'sma', color: null, tone: '--color-text-bold', width: 1.5,  label: '200' },
]

/** MA line colours resolve at call time: lightweight-charts takes literals,
 *  and the ladder must follow the theme. */
const maColor = (ma) =>
  ma.color ?? getComputedStyle(document.documentElement).getPropertyValue(ma.tone).trim()


/* ── Theme helpers ───────────────────────────────────────── */

function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

function getThemeColors() {
  // lightweight-charts cannot read CSS variables, so the v3 tokens are
  // resolved to literals here; a theme flip re-resolves on chart rebuild.
  const g = (n, fb) => getComputedStyle(document.documentElement).getPropertyValue(n).trim() || fb
  const rgba = (h, a) => `rgba(${parseInt(h.slice(1,3),16)}, ${parseInt(h.slice(3,5),16)}, ${parseInt(h.slice(5,7),16)}, ${a})`
  const took = g('--color-took', '#1f5288'), refused = g('--color-refused', '#d94032')
  return {
    background: g('--color-surface', '#ffffff'),
    textColor: g('--color-text-muted', '#78716c'),
    gridColor: g('--color-border-light', '#f5f5f4'),
    candleUp: took, candleDown: refused,
    wickUp: took, wickDown: refused,
    volUp: rgba(took, 0.22), volDown: rgba(refused, 0.22),
  }
}

/* ── MA Legend ───────────────────────────────────────────── */

function MaLegend({ showMAs, spyData }) {
  if (!showMAs) return null
  return (
    <div className="flex items-center gap-2.5 px-2 py-1">
      {MA_CONFIGS.map(ma => (
        <span key={ma.label} className="flex items-center gap-1">
          <span className="inline-block w-3 h-0.5 rounded-full" style={{ backgroundColor: maColor(ma) }} />
          <span className="text-[10px] text-[var(--color-text-muted)] font-mono">{ma.label}</span>
        </span>
      ))}
      {spyData?.length > 0 && (
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-0.5 rounded-full border-b border-dashed" style={{ borderColor: 'var(--color-text-muted)' }} />
          <span className="text-[10px] text-[var(--color-text-muted)] font-mono">SPY</span>
        </span>
      )}
    </div>
  )
}

/* ── Component ───────────────────────────────────────────── */

export default function OhlcvChart({
  data,
  showMAs = true,
  showVolume = true,
  height = 350,
  spyData,
  showControls = false,
}) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)
  const [logScale, setLogScale] = useState(false)
  const [timeframe, setTimeframe] = useState('D') // 'D' or 'W'

  // Watch for dark mode changes via MutationObserver
  const [darkMode, setDarkMode] = useState(isDarkMode)
  useEffect(() => {
    const observer = new MutationObserver(() => setDarkMode(isDarkMode()))
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    if (!containerRef.current || !data?.length) return

    // Clean up previous chart
    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
    }

    const theme = getThemeColors()
    const w = containerRef.current.clientWidth
    const chartData = timeframe === 'W' ? toWeekly(data) : data

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
      rightPriceScale: {
        borderVisible: false,
        scaleMargins: { top: 0.02, bottom: showVolume ? 0.18 : 0.02 },
        mode: logScale ? 1 : 0, // 1 = logarithmic
      },
      timeScale: { borderVisible: false },
      crosshair: {
        mode: 0, // Normal crosshair
        horzLine: { visible: true, labelVisible: true, style: 3, color: isDarkMode() ? '#44403c' : '#d6d3d1' },
        vertLine: { style: 3, color: isDarkMode() ? '#44403c' : '#d6d3d1' },
      },
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
    candleSeries.setData(chartData)

    // Volume histogram (occupies bottom 15% of chart)
    if (showVolume) {
      const volSeries = chart.addSeries(HistogramSeries, {
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
      })
      volSeries.priceScale().applyOptions({
        scaleMargins: { top: 0.85, bottom: 0 },
      })
      const volData = chartData.map(d => ({
        time: d.time,
        value: d.volume,
        color: d.close >= d.open ? theme.volUp : theme.volDown,
      }))
      volSeries.setData(volData)
    }

    // MA overlays
    if (showMAs) {
      const closes = chartData.map((d) => d.close)
      const times = chartData.map((d) => d.time)

      for (const ma of MA_CONFIGS) {
        const values = ma.type === 'ema'
          ? computeEMA(closes, ma.period)
          : computeSMA(closes, ma.period)
        const lineData = []
        for (let i = 0; i < times.length; i++) {
          if (values[i] !== null) {
            lineData.push({ time: times[i], value: values[i] })
          }
        }
        if (lineData.length > 0) {
          const series = chart.addSeries(LineSeries, {
            color: maColor(ma),
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
        color: getComputedStyle(document.documentElement).getPropertyValue('--color-text-muted').trim(),
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
  }, [data, showMAs, showVolume, height, spyData, darkMode, logScale, timeframe])

  // Fallback
  if (!data?.length) {
    return (
      <div
        className="flex items-center justify-center text-[var(--color-text-muted)] text-[12.5px]"
        style={{ height }}
      >
        No chart data
      </div>
    )
  }

  return (
    <div>
      {/* Toolbar: legend + controls */}
      <div className="flex items-center justify-between">
        <MaLegend showMAs={showMAs} spyData={spyData} />
        {showControls && (
          <div className="flex items-center gap-1 px-2 py-1">
            {['D', 'W'].map(tf => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`text-[10px] font-mono px-1.5 py-0.5 rounded transition-colors cursor-pointer ${
                  timeframe === tf
                    ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'
                }`}
              >
                {tf}
              </button>
            ))}
            <span className="w-px h-3 bg-[var(--color-border)] mx-0.5" />
            <button
              onClick={() => setLogScale(s => !s)}
              className={`text-[10px] font-mono px-1.5 py-0.5 rounded transition-colors cursor-pointer ${
                logScale
                  ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'
              }`}
            >
              {logScale ? 'LOG' : 'LIN'}
            </button>
          </div>
        )}
      </div>
      <div ref={containerRef} />
    </div>
  )
}
