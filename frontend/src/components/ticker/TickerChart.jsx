import { useEffect, useRef, useState } from 'react'

/**
 * Embeds the free TradingView Advanced Chart widget for a symbol.
 *
 * Important: TradingView's embed script takes over the div it's attached to —
 * on init it overwrites that div's inline style to `height:100%; width:100%`
 * and replaces its children (including our inner `__widget` mount div) with
 * its own iframe. So the fixed pixel height must live on an ANCESTOR that
 * TradingView doesn't touch (the outer wrapper below), not on the
 * `.tradingview-widget-container` div itself — anything set there gets
 * clobbered. Without a definite height somewhere in the chain, the 100%
 * resolves to `auto` and the iframe collapses to the browser's default
 * iframe height (150px).
 */
export default function TickerChart({ symbol, height = 520, interval = 'D' }) {
  const containerRef = useRef(null)
  const outerRef = useRef(null)
  // The widget's theme was hardcoded to dark, so on the light paper this was
  // a black rectangle in the middle of the page. It is a third-party iframe
  // and cannot read our tokens, but it does take a theme on init — and it
  // has to be re-initialised when ours changes, since the iframe will not
  // repaint on its own.
  const [dark, setDark] = useState(() =>
    document.documentElement.classList.contains('dark'))

  useEffect(() => {
    const el = document.documentElement
    const obs = new MutationObserver(() => setDark(el.classList.contains('dark')))
    obs.observe(el, { attributes: true, attributeFilter: ['class'] })
    return () => obs.disconnect()
  }, [])

  /**
   * MOUNT ON DEMAND. This widget is a third-party iframe, and the pages that
   * now carry it are pages of names — one chart per name would be dozens of
   * iframes on a screen that has to open in the morning. So it does not load
   * until it is actually in view, and once loaded it stays: re-tearing a chart
   * every time it scrolls off would cost more than it saves.
   */
  const [near, setNear] = useState(false)
  useEffect(() => {
    if (near) return
    const el = outerRef.current
    if (!el) return

    // The measurement, and the only thing actually deciding this. A rect
    // against the viewport answers "is this on screen" with no dependency on
    // anything firing.
    const check = () => {
      const r = el.getBoundingClientRect()
      if (r.bottom > -200 && r.top < (window.innerHeight || 0) + 200) setNear(true)
    }
    check()

    // IntersectionObserver only makes the later scrolls cheap; it is NOT the
    // gate. It was, and in an embedded browser where the observer never fires
    // the chart simply never loaded — a silent empty frame, which is the exact
    // failure the offline state below exists to prevent. An optimisation is
    // allowed to be absent; a gate is not.
    let io = null
    if (typeof IntersectionObserver === 'function') {
      io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) setNear(true) },
                                    { rootMargin: '200px' })
      io.observe(el)
    }
    window.addEventListener('scroll', check, { passive: true })
    window.addEventListener('resize', check)
    return () => {
      io?.disconnect()
      window.removeEventListener('scroll', check)
      window.removeEventListener('resize', check)
    }
  }, [near])

  /**
   * OFFLINE IS A STATE, NOT A BLANK. The widget is an external request; with
   * no network — or with the script blocked — the container simply stays
   * empty, and an empty box on this page is indistinguishable from a chart
   * that found nothing. So the load is watched and its failure is said out
   * loud, in the same grammar the rest of the site uses for "not measured".
   */
  const [status, setStatus] = useState('idle')   // idle | loading | ok | failed
  const [online, setOnline] = useState(() => navigator.onLine)
  useEffect(() => {
    const up = () => setOnline(true), down = () => setOnline(false)
    window.addEventListener('online', up)
    window.addEventListener('offline', down)
    return () => { window.removeEventListener('online', up); window.removeEventListener('offline', down) }
  }, [])

  useEffect(() => {
    if (!containerRef.current || !symbol || !near || !online) return

    const container = containerRef.current
    setStatus('loading')
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
    script.onload = () => setStatus('ok')
    script.onerror = () => setStatus('failed')
    script.innerHTML = JSON.stringify({
      autosize: true,
      symbol: symbol,
      interval,
      timezone: 'America/New_York',
      theme: dark ? 'dark' : 'light',
      style: '1',
      locale: 'en',
      enable_publishing: false,
      hide_top_toolbar: false,
      hide_side_toolbar: true,
      allow_symbol_change: false,
      /**
       * Andy's overlay set, 2026-08-18: 10 EMA, 21 EMA, 50 SMA. RSI is gone —
       * a second pane taking a third of the height to say something the price
       * and the averages already position you for.
       *
       * OBJECT FORM, AND IT IS LOAD-BEARING. `studies_overrides` is keyed by
       * study TYPE rather than by instance, so it cannot give two exponential
       * averages two different lengths — both would come out the same. Each
       * study carrying its own `inputs` is the only form that expresses 10 and
       * 21 at once, and it is confirmed working on the live chart.
       *
       * Do not "fix" this into strings plus overrides. That swap was made once,
       * on 2026-08-18, off a screenshot that predated this block — the legend
       * in it read "MA 9 close", which was the OLD config, not evidence against
       * this one. Verified by Andy's eye on the legend; the chart is a
       * cross-origin iframe, so no probe on this side can read it back.
       */
      studies: [
        { id: 'MAExp@tv-basicstudies', inputs: { length: 10 } },
        { id: 'MAExp@tv-basicstudies', inputs: { length: 21 } },
        { id: 'MASimple@tv-basicstudies', inputs: { length: 50 } },
      ],
      support_host: 'https://www.tradingview.com',
    })
    container.appendChild(script)

    return () => {
      if (container) container.innerHTML = ''
    }
  }, [symbol, dark, interval, near, online])

  const down = !online || status === 'failed'

  /**
   * The message and the widget are SIBLINGS, both always mounted.
   *
   * They shared one slot at first and the offline state came out as an empty
   * hatched box: the embed script owns whatever node it was appended to and
   * clears it asynchronously, so when React swapped the widget out for the
   * message, a script still in flight wiped the message instead. Two nodes,
   * and the widget's node carries a key on its whole configuration — a stale
   * script can then only ever clear a node React has already detached.
   */
  return (
    <div
      ref={outerRef}
      className="bg-[var(--color-bg)] rounded-3xl overflow-hidden relative"
      style={{ height: `${height}px`, width: '100%' }}
    >
      {/* hatched, so it cannot be read as a chart that rendered nothing, and
          it names which of the two failures this is */}
      <div className="absolute inset-0 items-center justify-center p-6"
           style={{ display: down ? 'flex' : 'none',
                    backgroundImage:
             'repeating-linear-gradient(45deg,var(--color-border-light) 0 1px,transparent 1px 7px)' }}>
        <p className="m-0 max-w-[42ch] text-center text-[11px] leading-relaxed
                      text-[var(--color-text-muted)] bg-[var(--color-bg)] px-3 py-2 rounded-lg">
          <b className="text-[var(--color-text-secondary)]">Chart unavailable.</b>{' '}
          {!online
            ? 'This browser is offline; the chart is drawn by TradingView over the network.'
            : 'TradingView\u2019s embed script did not load \u2014 blocked, or its host is unreachable.'}
          {' '}Everything else on this page is served from the nightly file and is unaffected.
        </p>
      </div>
      <div
        key={`${symbol}|${interval}|${dark ? 'd' : 'l'}`}
        ref={containerRef}
        className="tradingview-widget-container"
        style={{ height: '100%', width: '100%', visibility: down ? 'hidden' : 'visible' }}
      />
    </div>
  )
}
