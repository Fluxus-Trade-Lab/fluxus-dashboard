import { tickerHref } from '../portfolio/lib/tickerUrl'

/**
 * Renders a ticker symbol as a clickable link to the tear-sheet page.
 * Use everywhere a ticker is displayed.
 */
export default function TickerLink({ symbol, className = '', children }) {
  if (!symbol) return <span className={className}>{children || symbol}</span>
  return (
    <a
      href={tickerHref(symbol)}
      className={`hover:text-[var(--color-accent)] hover:underline decoration-dotted ${className}`}
    >
      {children || symbol}
    </a>
  )
}
