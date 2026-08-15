import { useEffect, useLayoutEffect, useRef } from 'react'
import { createChart, ColorType } from 'lightweight-charts'

/** v3 pair + greys, resolved to literals because lightweight-charts cannot
 *  read CSS variables. Resolved at call time, so a theme flip re-resolves on
 *  the next chart rebuild. */
export function chartTokens() {
  const g = (n, fb) => getComputedStyle(document.documentElement).getPropertyValue(n).trim() || fb
  return {
    took: g('--color-took', '#1f5288'),
    refused: g('--color-refused', '#d94032'),
    ink: g('--color-text', '#1c1917'),
    inkBold: g('--color-text-bold', '#292524'),
    secondary: g('--color-text-secondary', '#5f584f'),
    muted: g('--color-text-muted', '#7d766d'),
    border: g('--color-border', '#e2dcd0'),
  }
}

// Theme-aware lightweight-charts factory shared by all breadth charts.
//
// `setupFn` is held in a ref that is refreshed on EVERY render, and is
// deliberately NOT an effect dependency. Callers pass inline closures that
// capture props (e.g. HealthChart's t2108 overlay); memoising the closure once
// on first render — as `useCallback(setupFn, [])` did — froze those captured
// props forever, so a Time Machine pin redrew the chart with the ORIGINAL
// (live, future-extending) overlay data under a "future observations excluded"
// banner. Reading through a ref keeps the redraw on `[deps, height]` while
// always running the current closure.
export function useBreadthChart(containerRef, chartRef, deps, setupFn, height) {
  const setupRef = useRef(setupFn)
  // In a layout effect, not during render: writing a ref while rendering is
  // the thing that breaks under a re-entrant render. Layout effects run
  // before the redraw effect below, so it still reads the current closure.
  useLayoutEffect(() => { setupRef.current = setupFn })

  useEffect(() => {
    if (!containerRef.current || !deps) return

    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
    }

    const w = containerRef.current.clientWidth
    const h = height ?? Math.max(160, Math.round(w * 0.35))

    const root = getComputedStyle(document.documentElement)
    const bgColor = root.getPropertyValue('--color-surface').trim() || '#ffffff'
    const txtColor = root.getPropertyValue('--color-text-secondary').trim() || '#78716c'
    const gridColor = root.getPropertyValue('--color-border-light').trim() || '#f5f5f4'

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: bgColor },
        textColor: txtColor,
        fontSize: 10,
      },
      grid: {
        vertLines: { color: gridColor },
        horzLines: { color: gridColor },
      },
      width: w,
      height: h,
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false },
      crosshair: { horzLine: { visible: false, labelVisible: false } },
    })

    setupRef.current(chart, deps)
    chart.timeScale().fitContent()
    chartRef.current = chart

    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        const newW = containerRef.current.clientWidth
        const newH = height ?? Math.max(160, Math.round(newW * 0.35))
        chartRef.current.applyOptions({ width: newW, height: newH })
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
  }, [deps, height])
}
