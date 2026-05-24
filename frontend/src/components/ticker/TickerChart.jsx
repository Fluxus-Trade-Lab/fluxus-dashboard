import { useEffect, useRef } from 'react'

/**
 * Embeds the free TradingView Advanced Chart widget for a symbol.
 *
 * Important: the widget's `autosize: true` requires the official nested-div
 * structure to compute height correctly:
 *   <div class="tradingview-widget-container" style="height:Xpx">
 *     <div class="tradingview-widget-container__widget" style="height:100%"></div>
 *     <script src="...embed-widget-advanced-chart.js">{config json}</script>
 *   </div>
 *
 * Without the inner `__widget` div, the widget collapses to ~150px.
 */
export default function TickerChart({ symbol, height = 520 }) {
  const containerRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current || !symbol) return

    const container = containerRef.current
    // Reset previous mount (e.g., on symbol change)
    container.innerHTML = ''

    // Inner div the widget renders into — must have height: 100%
    const widgetDiv = document.createElement('div')
    widgetDiv.className = 'tradingview-widget-container__widget'
    widgetDiv.style.height = '100%'
    widgetDiv.style.width = '100%'
    container.appendChild(widgetDiv)

    const script = document.createElement('script')
    script.type = 'text/javascript'
    script.async = true
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js'
    script.innerHTML = JSON.stringify({
      autosize: true,
      symbol: symbol,
      interval: 'D',
      timezone: 'America/New_York',
      theme: 'dark',
      style: '1',
      locale: 'en',
      enable_publishing: false,
      hide_top_toolbar: false,
      hide_side_toolbar: true,
      allow_symbol_change: false,
      studies: ['MASimple@tv-basicstudies', 'RSI@tv-basicstudies'],
      support_host: 'https://www.tradingview.com',
    })
    container.appendChild(script)

    return () => {
      if (container) container.innerHTML = ''
    }
  }, [symbol])

  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] overflow-hidden">
      <div
        ref={containerRef}
        className="tradingview-widget-container"
        style={{ height: `${height}px`, width: '100%' }}
      />
    </div>
  )
}
