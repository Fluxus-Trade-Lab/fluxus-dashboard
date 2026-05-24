/**
 * Suggest a trail stop based on the position's leg state and per-ticker EMA data.
 *
 * Rules (v3 optimizer defaults):
 *   PRE_TRIM                → CSV initial stop (don't override user's risk decision)
 *   POST_T1/POST_T2/POST_T3 → max(entry, wk_ema20 - 0.25 ATR)  for longs
 *                              min(entry, wk_ema20 + 0.25 ATR)  for shorts
 *
 * @param {{state: string, stopPrice: number, entryPrice: number, direction: string}} trade
 * @param {{ema10?: number, ema20?: number, wk_ema10?: number, wk_ema20?: number}} ema
 * @param {{atr: number}} stats
 * @returns {{suggestedStop: number|null, basis: string, rationale: string}|null}
 */
export function suggest(trade, ema, stats) {
  if (trade.state === 'CLOSED') return null

  if (trade.state === 'PRE_TRIM') {
    return {
      suggestedStop: trade.stopPrice,
      basis: 'csv-initial',
      rationale: 'Initial risk stop from trade entry',
    }
  }

  const wk20 = ema?.wk_ema20
  if (wk20 == null || !Number.isFinite(wk20)) {
    return {
      suggestedStop: null,
      basis: 'no-data',
      rationale: 'No weekly-20EMA data — set manually',
    }
  }

  const atr = stats?.atr ?? 0
  const buffer = 0.25 * atr

  if (trade.direction === 'long') {
    const wk20Stop = wk20 - buffer
    if (wk20Stop > trade.entryPrice) {
      return {
        suggestedStop: round2(wk20Stop),
        basis: 'wk20ema',
        rationale: `wk-20EMA ($${round2(wk20)}) − 0.25×ATR buffer`,
      }
    }
    return {
      suggestedStop: trade.entryPrice,
      basis: 'breakeven',
      rationale: 'wk-20EMA below entry — hold breakeven floor',
    }
  }

  // short
  const wk20Stop = wk20 + buffer
  if (wk20Stop < trade.entryPrice) {
    return {
      suggestedStop: round2(wk20Stop),
      basis: 'wk20ema',
      rationale: `wk-20EMA ($${round2(wk20)}) + 0.25×ATR buffer`,
    }
  }
  return {
    suggestedStop: trade.entryPrice,
    basis: 'breakeven',
    rationale: 'wk-20EMA above entry — hold breakeven floor',
  }
}

function round2(n) { return Math.round(n * 100) / 100 }
