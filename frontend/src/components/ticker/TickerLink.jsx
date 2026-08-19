import { tickerHref } from '../portfolio/lib/tickerUrl'

/**
 * Renders a ticker symbol as a clickable link to the tear-sheet page.
 * Use everywhere a ticker is displayed.
 */
export default function TickerLink({ symbol, className = '', style, title, children }) {
  if (!symbol) return <span className={className}>{children || symbol}</span>
  /* `style` exists for one caller: Today's List paints the ATR reading as the
     ticker's own ground, so the ink has to be chosen against that ground
     instead of inherited. When it is set the accent hover would fight the
     chosen foreground, so only the underline is kept. */
  return (
    <a
      href={tickerHref(symbol)}
      style={style}
      title={title}
      className={`hover:underline decoration-dotted ${
        style ? '' : 'hover:text-[var(--color-accent)]'} ${className}`}
    >
      {children || symbol}
    </a>
  )
}
