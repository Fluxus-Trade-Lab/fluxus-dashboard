import { useRef } from 'react'
import { LineSeries } from 'lightweight-charts'
import { useBreadthChart, chartTokens } from './useBreadthChart'

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
  const pick = (arr) => (arr ? indices.map((i) => arr[i]) : arr)
  return {
    ...history,
    dates: pick(history.dates),
    pct_above_200sma: pick(history.pct_above_200sma),
    pct_above_50sma: pick(history.pct_above_50sma),
    pct_above_20sma: pick(history.pct_above_20sma),
    mcclellan_osc: pick(history.mcclellan_osc),
    // Nasdaq-100 pool (T-0923-03) -- the standard reading going forward;
    // mcclellan_osc above is kept only for archive continuity.
    mcclellan_osc_ndx: pick(history.mcclellan_osc_ndx),
    mcclellan_summation_ndx: pick(history.mcclellan_summation_ndx),
    mcclellan_summation_ndx_ma10: pick(history.mcclellan_summation_ndx_ma10),
  }
}

export default function BreadthCharts({ data }) {
  if (!data?.history) return null

  const history = dedupeHistory(data.history)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
      <MaChart history={history} />
      <McClellanChart history={history} />
      <McSummationChart history={history} />
    </div>
  )
}

function MaChart({ history }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useBreadthChart(containerRef, chartRef, history, (chart, hist) => {
    const dates = hist.dates

    const tk = chartTokens()
    const sma200 = chart.addSeries(LineSeries, { color: tk.inkBold, lineWidth: 2.4, title: '200 SMA' })
    sma200.setData(dates.map((d, i) => ({ time: d, value: hist.pct_above_200sma[i] ?? 0 })))

    const sma50 = chart.addSeries(LineSeries, { color: tk.secondary, lineWidth: 1.5, title: '50 SMA' })
    sma50.setData(dates.map((d, i) => ({ time: d, value: hist.pct_above_50sma[i] ?? 0 })))

    const sma20 = chart.addSeries(LineSeries, { color: tk.muted, lineWidth: 1, title: '20 SMA' })
    sma20.setData(dates.map((d, i) => ({ time: d, value: hist.pct_above_20sma[i] ?? 0 })))
  })

  return (
    <div className="bg-[var(--color-bg)] rounded-2xl px-3 py-3">
      <h3 className="text-[11px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] mb-2">
        % above 20 / 50 / 200 SMA
      </h3>
      <div ref={containerRef} />
    </div>
  )
}

function McClellanChart({ history }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useBreadthChart(containerRef, chartRef, history, (chart, hist) => {
    const dates = hist.dates
    // Nasdaq-100 pool (T-0923-03) -- rows before the rollout have no value
    // yet (membership tracking + the 19/39-day EMA warm-up), so those plot
    // as a flat 0 rather than a fabricated reading; the line only becomes
    // meaningful from the first real value forward.
    const mcData = dates.map((d, i) => ({
      time: d,
      value: hist.mcclellan_osc_ndx?.[i] ?? 0,
    }))

    const mcSeries = chart.addSeries(LineSeries, {
      color: chartTokens().muted,
      lineWidth: 1.5,
      title: 'McClellan (NDX)',
      crosshairMarkerRadius: 3,
    })
    mcSeries.setData(mcData)

    // ChartSchool's own overbought/oversold band (breadth_signals.py
    // THRESHOLDS['mcclellan']['extreme'] = 100).
    for (const level of [100, -100]) {
      mcSeries.createPriceLine({
        price: level,
        color: chartTokens().border,
        lineWidth: 1,
        lineStyle: 3, // dotted
      })
    }

    // Zero line baseline
    mcSeries.createPriceLine({
      price: 0,
      color: chartTokens().border,
      lineWidth: 1,
      lineStyle: 2, // dashed
    })
  })

  return (
    <div className="bg-[var(--color-bg)] rounded-2xl px-3 py-3">
      <h3 className="text-[11px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] mb-2">
        McClellan Oscillator (Nasdaq-100)
      </h3>
      <div ref={containerRef} />
    </div>
  )
}

function McSummationChart({ history }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useBreadthChart(containerRef, chartRef, history, (chart, hist) => {
    const dates = hist.dates
    const msiData = dates.map((d, i) => ({
      time: d,
      value: hist.mcclellan_summation_ndx?.[i] ?? 0,
    }))
    const ma10Data = dates.map((d, i) => ({
      time: d,
      value: hist.mcclellan_summation_ndx_ma10?.[i] ?? 0,
    }))

    const msiSeries = chart.addSeries(LineSeries, {
      color: chartTokens().inkBold,
      lineWidth: 1.5,
      title: 'McClellan Summation (NDX)',
      crosshairMarkerRadius: 3,
    })
    msiSeries.setData(msiData)

    const ma10Series = chart.addSeries(LineSeries, {
      color: chartTokens().secondary,
      lineWidth: 1,
      title: '10D avg',
    })
    ma10Series.setData(ma10Data)

    // McClellan's own Ratio-Adjusted Summation Index note: "a strong uptrend
    // can be signified by index values going from below -500 to well above
    // +500" (mcoscillator.com; breadth_signals.py THRESHOLDS
    // ['mcclellan_summation']['extreme']).
    for (const level of [500, -500]) {
      msiSeries.createPriceLine({
        price: level,
        color: chartTokens().border,
        lineWidth: 1,
        lineStyle: 3, // dotted
      })
    }

    msiSeries.createPriceLine({
      price: 0,
      color: chartTokens().border,
      lineWidth: 1,
      lineStyle: 2, // dashed
    })
  })

  return (
    <div className="bg-[var(--color-bg)] rounded-2xl px-3 py-3">
      <h3 className="text-[11px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] mb-2">
        McClellan Summation Index (Nasdaq-100)
      </h3>
      <div ref={containerRef} />
    </div>
  )
}
