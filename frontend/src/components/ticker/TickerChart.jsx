import { useEffect, useRef } from 'react'

/**
 * Embeds the free TradingView Advanced Chart widget for a symbol.
 * One-time script injection per mount; re-mounts when symbol changes.
 */
export default function TickerChart({ symbol }) {
  const containerRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current || !symbol) return
    // Clear any previous widget content
    containerRef.current.innerHTML = ''

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
    containerRef.current.appendChild(script)

    return () => {
      if (containerRef.current) containerRef.current.innerHTML = ''
    }
  }, [symbol])

  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] overflow-hidden">
      <div
        ref={containerRef}
        className="tradingview-widget-container"
        style={{ height: 440, width: '100%' }}
      />
    </div>
  )
}
