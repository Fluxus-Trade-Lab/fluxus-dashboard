import { useState, useEffect, useRef, useCallback } from 'react'
import { createChart, ColorType, CandlestickSeries, LineSeries, HistogramSeries } from 'lightweight-charts'

/* ── Theme helpers (shared with OhlcvChart) ─────────────── */

function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

function getThemeColors() {
  const dark = isDarkMode()
  return {
    background: dark ? '#1c1917' : '#ffffff',
    textColor: dark ? '#a8a29e' : '#78716c',
    gridColor: dark ? '#292524' : '#f5f5f4',
    candleUp: '#16a34a',
    candleDown: '#dc2626',
    wickUp: '#16a34a',
    wickDown: '#dc2626',
    volUp: dark ? 'rgba(22, 163, 74, 0.3)' : 'rgba(22, 163, 74, 0.18)',
    volDown: dark ? 'rgba(220, 38, 38, 0.3)' : 'rgba(220, 38, 38, 0.18)',
  }
}

/* ── MA helpers ─────────────────────────────────────────── */

function computeSMA(closes, period) {
  const result = []
  let sum = 0
  for (let i = 0; i < closes.length; i++) {
    sum += closes[i]
    if (i >= period) sum -= closes[i - period]
    if (i >= period - 1) result.push(sum / period)
    else result.push(null)
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

const MA_CONFIGS = [
  { period: 10, type: 'ema', color: '#22d3ee', width: 1, label: '10E' },
  { period: 21, type: 'ema', color: '#3b82f6', width: 1.5, label: '21E' },
  { period: 50, type: 'sma', color: '#f59e0b', width: 1.5, label: '50' },
  { period: 200, type: 'sma', color: '#a8a29e', width: 1, label: '200' },
]

/* ── GymChart — incremental bar reveal ──────────────────── */

function GymChart({ data, revealIndex, height = 350 }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)
  const candleSeriesRef = useRef(null)
  const volSeriesRef = useRef(null)
  const maSeriesRefs = useRef([])
  const lastRevealRef = useRef(0)

  // Track dark mode
  const [darkMode, setDarkMode] = useState(isDarkMode)
  useEffect(() => {
    const observer = new MutationObserver(() => setDarkMode(isDarkMode()))
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    return () => observer.disconnect()
  }, [])

  // Create chart on mount or when data/dark mode changes
  useEffect(() => {
    if (!containerRef.current || !data?.length) return

    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
    }

    const theme = getThemeColors()
    const w = containerRef.current.clientWidth
    const initialData = data.slice(0, revealIndex)

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
        scaleMargins: { top: 0.02, bottom: 0.18 },
      },
      timeScale: { borderVisible: false },
      crosshair: {
        mode: 0,
        horzLine: { visible: true, labelVisible: true, style: 3, color: isDarkMode() ? '#44403c' : '#d6d3d1' },
        vertLine: { style: 3, color: isDarkMode() ? '#44403c' : '#d6d3d1' },
      },
    })

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: theme.candleUp,
      downColor: theme.candleDown,
      borderUpColor: theme.candleUp,
      borderDownColor: theme.candleDown,
      wickUpColor: theme.wickUp,
      wickDownColor: theme.wickDown,
    })
    candleSeries.setData(initialData)

    const volSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    })
    volSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    })
    volSeries.setData(initialData.map(d => ({
      time: d.time,
      value: d.volume,
      color: d.close >= d.open ? theme.volUp : theme.volDown,
    })))

    // MAs on full initial data
    const closes = initialData.map(d => d.close)
    const times = initialData.map(d => d.time)
    const maSeries = []

    for (const ma of MA_CONFIGS) {
      const values = ma.type === 'ema'
        ? computeEMA(closes, ma.period)
        : computeSMA(closes, ma.period)
      const lineData = []
      for (let i = 0; i < times.length; i++) {
        if (values[i] !== null) lineData.push({ time: times[i], value: values[i] })
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
        maSeries.push({ series, config: ma })
      }
    }

    chart.timeScale().fitContent()
    chartRef.current = chart
    candleSeriesRef.current = candleSeries
    volSeriesRef.current = volSeries
    maSeriesRefs.current = maSeries
    lastRevealRef.current = revealIndex

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
  }, [data, darkMode]) // recreate chart on data change or theme change, NOT on revealIndex

  // Incrementally add bars when revealIndex grows
  useEffect(() => {
    if (!data?.length || !candleSeriesRef.current) return
    const last = lastRevealRef.current
    if (revealIndex <= last) return

    const theme = getThemeColors()

    for (let i = last; i < revealIndex && i < data.length; i++) {
      const bar = data[i]
      candleSeriesRef.current.update(bar)
      if (volSeriesRef.current) {
        volSeriesRef.current.update({
          time: bar.time,
          value: bar.volume,
          color: bar.close >= bar.open ? theme.volUp : theme.volDown,
        })
      }

      // Update MAs — recompute from all revealed data up to this point
      const allCloses = data.slice(0, i + 1).map(d => d.close)
      for (const { series, config } of maSeriesRefs.current) {
        const values = config.type === 'ema'
          ? computeEMA(allCloses, config.period)
          : computeSMA(allCloses, config.period)
        const lastVal = values[values.length - 1]
        if (lastVal !== null) {
          series.update({ time: bar.time, value: lastVal })
        }
      }
    }

    lastRevealRef.current = revealIndex
  }, [revealIndex, data])

  if (!data?.length) {
    return (
      <div className="flex items-center justify-center text-[var(--color-text-muted)] text-xs" style={{ height }}>
        No chart data
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center gap-2.5 px-2 py-1">
        {MA_CONFIGS.map(ma => (
          <span key={ma.label} className="flex items-center gap-1">
            <span className="inline-block w-3 h-0.5 rounded-full" style={{ backgroundColor: ma.color }} />
            <span className="text-[9px] text-[var(--color-text-muted)] font-mono">{ma.label}</span>
          </span>
        ))}
      </div>
      <div ref={containerRef} />
    </div>
  )
}

/* ── TradingGym ─────────────────────────────────────────── */

export default function TradingGym({ cards }) {
  const [difficulty, setDifficulty] = useState('mixed') // 'easy' | 'mixed'
  const [ohlcv, setOhlcv] = useState(null)
  const [entry, setEntry] = useState(null)
  const [loading, setLoading] = useState(true)

  // Game state
  const [revealIndex, setRevealIndex] = useState(0)
  const [splitIndex, setSplitIndex] = useState(0)
  const [choice, setChoice] = useState(null) // 'buy' | 'pass' | 'fade'
  const [animating, setAnimating] = useState(false)
  const [showResult, setShowResult] = useState(false)
  const intervalRef = useRef(null)

  // Score tracking
  const [round, setRound] = useState(0)
  const [correct, setCorrect] = useState(0)
  const [streak, setStreak] = useState(0)
  const [bestStreak, setBestStreak] = useState(() => {
    try { return parseInt(localStorage.getItem('gym-best-streak') || '0', 10) }
    catch { return 0 }
  })

  // Streak animation
  const [streakBump, setStreakBump] = useState(false)

  const eligible = useCallback(() => {
    let pool = cards.filter(c => c.ohlcv_file)
    if (difficulty === 'easy') pool = pool.filter(c => (c.gain_pct || 0) >= 100)
    return pool
  }, [cards, difficulty])

  const loadRandom = useCallback(async () => {
    setLoading(true)
    setChoice(null)
    setAnimating(false)
    setShowResult(false)
    if (intervalRef.current) clearInterval(intervalRef.current)

    const pool = eligible()
    if (!pool.length) { setLoading(false); return }

    const pick = pool[Math.floor(Math.random() * pool.length)]
    setEntry(pick)

    try {
      const res = await fetch(`/data/modelbooks/${pick.ohlcv_file}`)
      const data = await res.json()
      const split = Math.floor(data.length * 0.7)
      setOhlcv(data)
      setSplitIndex(split)
      setRevealIndex(split)
      setRound(r => r + 1)
    } catch {
      setOhlcv(null)
    }
    setLoading(false)
  }, [eligible])

  // Load first entry
  useEffect(() => { loadRandom() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Handle player choice
  const handleChoice = (c) => {
    if (animating || choice) return
    setChoice(c)
    setAnimating(true)

    let idx = splitIndex
    intervalRef.current = setInterval(() => {
      idx += 1
      if (idx >= ohlcv.length) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
        setRevealIndex(ohlcv.length)
        setAnimating(false)
        setShowResult(true)
      } else {
        setRevealIndex(idx)
      }
    }, 80)
  }

  // Compute result
  const computeResult = () => {
    if (!ohlcv || !choice) return null
    const decisionClose = ohlcv[splitIndex - 1].close
    const finalClose = ohlcv[ohlcv.length - 1].close
    const changePct = ((finalClose - decisionClose) / decisionClose) * 100

    let isCorrect = false
    if (choice === 'buy' && changePct >= 20) isCorrect = true
    else if (choice === 'pass' && changePct < 20) isCorrect = true
    else if (choice === 'fade' && changePct < 0) isCorrect = true

    return { changePct, isCorrect }
  }

  // Update score when result is shown
  useEffect(() => {
    if (!showResult) return
    const result = computeResult()
    if (!result) return

    if (result.isCorrect) {
      setCorrect(c => c + 1)
      setStreak(s => {
        const newStreak = s + 1
        if (newStreak > bestStreak) {
          setBestStreak(newStreak)
          try { localStorage.setItem('gym-best-streak', String(newStreak)) } catch {}
        }
        return newStreak
      })
      setStreakBump(true)
      setTimeout(() => setStreakBump(false), 300)
    } else {
      setStreak(0)
    }
  }, [showResult]) // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup interval on unmount
  useEffect(() => {
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [])

  const result = showResult ? computeResult() : null

  if (!eligible().length) {
    return (
      <div className="text-xs text-[var(--color-text-muted)] py-8 text-center">
        No entries with chart data{difficulty === 'easy' ? ' and 100%+ gains' : ''}.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Header: score + difficulty */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-[10px] font-mono text-[var(--color-text-secondary)]">
          <span>Round {round}{round > 0 ? ` \u2014 ${correct}/${round}${showResult ? '' : ' so far'}` : ''}</span>
          <span>
            Streak:{' '}
            <span
              className={`inline-block transition-transform duration-200 ${streakBump ? 'scale-125' : 'scale-100'}`}
              style={{ fontVariantNumeric: 'tabular-nums' }}
            >
              {streak}
            </span>
          </span>
          <span className="text-[var(--color-text-muted)]">Best: {bestStreak}</span>
        </div>
        <div className="flex gap-1">
          {['easy', 'mixed'].map(d => (
            <button
              key={d}
              onClick={() => { setDifficulty(d); }}
              className={`px-2 py-1 text-[9px] font-medium rounded cursor-pointer transition-colors ${
                difficulty === d
                  ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] bg-[var(--color-surface-raised)]'
              }`}
            >
              {d === 'easy' ? 'Easy' : 'Mixed'}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      {loading ? (
        <div className="flex items-center justify-center h-[350px] text-xs text-[var(--color-text-muted)] animate-pulse">
          Loading chart...
        </div>
      ) : ohlcv ? (
        <div className="border border-[var(--color-border)] rounded-lg overflow-hidden bg-[var(--color-surface)]">
          <GymChart data={ohlcv} revealIndex={revealIndex} height={350} />
        </div>
      ) : (
        <div className="flex items-center justify-center h-[350px] text-xs text-[var(--color-text-muted)]">
          Failed to load chart data
        </div>
      )}

      {/* Action buttons */}
      {!showResult && ohlcv && !loading && (
        <div className="flex items-center justify-center gap-3 py-2">
          <span className="text-[10px] text-[var(--color-text-muted)] mr-2">What's your call?</span>
          <button
            onClick={() => handleChoice('buy')}
            disabled={animating || !!choice}
            className="px-4 py-1.5 text-[11px] font-medium rounded bg-green-600 text-white cursor-pointer transition-opacity disabled:opacity-40 disabled:cursor-not-allowed hover:bg-green-700"
          >
            Buy
          </button>
          <button
            onClick={() => handleChoice('pass')}
            disabled={animating || !!choice}
            className="px-4 py-1.5 text-[11px] font-medium rounded bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] cursor-pointer transition-opacity disabled:opacity-40 disabled:cursor-not-allowed hover:brightness-110"
          >
            Pass
          </button>
          <button
            onClick={() => handleChoice('fade')}
            disabled={animating || !!choice}
            className="px-4 py-1.5 text-[11px] font-medium rounded bg-red-600 text-white cursor-pointer transition-opacity disabled:opacity-40 disabled:cursor-not-allowed hover:bg-red-700"
          >
            Fade
          </button>
        </div>
      )}

      {/* Animating indicator */}
      {animating && (
        <div className="text-center text-[10px] text-[var(--color-text-muted)] animate-pulse py-1">
          Revealing...
        </div>
      )}

      {/* Result card */}
      {showResult && result && (
        <div className="border border-[var(--color-border)] rounded-lg p-4 bg-[var(--color-surface)]">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[9px] uppercase tracking-wide text-[var(--color-text-muted)] mb-1">Result</div>
              <div className="flex items-center gap-3">
                <span className={`text-sm font-mono font-semibold ${result.changePct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {result.changePct >= 0 ? '+' : ''}{result.changePct.toFixed(1)}%
                </span>
                <span className={`text-[11px] font-medium px-2 py-0.5 rounded ${
                  result.isCorrect
                    ? 'bg-green-600/15 text-green-500'
                    : 'bg-red-600/15 text-red-500'
                }`}>
                  {result.isCorrect ? 'CORRECT' : 'WRONG'}
                </span>
                <span className="text-[10px] text-[var(--color-text-muted)]">
                  You chose <span className="font-medium text-[var(--color-text-secondary)]">{choice?.toUpperCase()}</span>
                </span>
              </div>
              {entry && (
                <div className="text-[9px] text-[var(--color-text-muted)] mt-2">
                  {entry.ticker} ({entry.year}) — {entry.source}
                  {entry.patterns?.length > 0 && (
                    <span className="ml-2">{entry.patterns.join(', ')}</span>
                  )}
                </div>
              )}
            </div>
            <button
              onClick={loadRandom}
              className="px-4 py-1.5 text-[11px] font-medium rounded bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)] cursor-pointer hover:brightness-110 transition-all"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
