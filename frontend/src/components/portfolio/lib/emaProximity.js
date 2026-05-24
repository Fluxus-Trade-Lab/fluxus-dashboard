/**
 * Compute the proximity chips a row should display.
 * @param {{price: number, direction: string, wkClose?: number}} ctx
 * @param {{ema10?: number, ema20?: number, wk_ema10?: number, wk_ema20?: number}} ema
 * @returns {Array<{label: string, tone: string}>}
 */
export function chips(ctx, ema) {
  if (!ema) return []
  const out = []
  const price = ctx.price
  const long = ctx.direction === 'long'

  if (ema.ema10 != null && price > 0) {
    if (Math.abs(price - ema.ema10) / price < 0.015) {
      out.push({ label: '10EMA', tone: 'amber' })
    }
  }

  if (ema.ema20 != null && price > 0) {
    if (Math.abs(price - ema.ema20) / price < 0.02) {
      out.push({ label: '20EMA', tone: 'red' })
    }
  }

  if (ctx.wkClose != null && ema.wk_ema10 != null) {
    const fired = long ? ctx.wkClose < ema.wk_ema10 : ctx.wkClose > ema.wk_ema10
    if (fired) out.push({ label: 'T2', tone: 'orange' })
  }

  if (ctx.wkClose != null && ema.wk_ema20 != null) {
    const fired = long ? ctx.wkClose < ema.wk_ema20 : ctx.wkClose > ema.wk_ema20
    if (fired) out.push({ label: 'STOP', tone: 'red' })
  }

  return out
}
