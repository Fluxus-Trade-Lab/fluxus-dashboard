import { useEffect, useCallback } from 'react'
import { createChart, ColorType } from 'lightweight-charts'

// Theme-aware lightweight-charts factory shared by all breadth charts.
export function useBreadthChart(containerRef, chartRef, deps, setupFn, height) {
  const setup = useCallback(setupFn, [])

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

    setup(chart, deps)
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
  }, [deps, height, setup])
}
