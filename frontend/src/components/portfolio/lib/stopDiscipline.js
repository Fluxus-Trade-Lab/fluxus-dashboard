/**
 * The two readings that turn "I meant to move my stop" into something visible.
 *
 * WHY THIS EXISTS. The review lane went through all 373 historical trades and
 * found the `Stop Price` had never once been updated — every one of them still
 * equals its initial stop (DATA_CONTRACTS §十四, 2026-09-01). Andy's own words
 * for the cause: 「没动止损是因为没有在 dashboard 更新」. The cost is measured,
 * not assumed: open exposure ran to an upper bound of 30% at the peak, and that
 * is where the −17.9% drawdown came from.
 *
 * So this is not a nag. It is the one number the table was never showing: how
 * far a winner has run WITHOUT the risk behind it being moved.
 *
 * ⚠️ MOVING THE STOP DOES NOT REWRITE R. The R denominator is locked to
 * `initialStop` (`calculations.js` says so in its own comment and refuses to
 * fall back to the live stop). The review lane re-verified it before asking.
 * That matters because the fear of "ruining my stats" is exactly what stops
 * people trailing, and it is unfounded here.
 */

/** Open gain, in R, at which an un-moved stop starts being called out.
 *  A constant rather than a literal because §十四 asked for it to be tunable. */
export const NUDGE_AT_R = 1

/** Prices are stored to the cent; anything under this is the same number. */
const CENT = 0.01

/**
 * Has this position earned its stop being moved, and has it not been?
 *
 * Both halves have to be true and BOTH are refusals to guess:
 *   - `rr` is null when the trade carries no initial stop, and a position with
 *     no anchor has no R to be up. It returns false rather than treating
 *     "unknown" as "fine".
 *   - the comparison is against `initialStop`, not against some remembered
 *     earlier value: "never moved" is the claim §十四 made about all 373.
 *
 * @returns {boolean} true only for an OPEN position, up at least `atR`, whose
 *   stop is still sitting exactly where it started.
 */
export function stopNotMoved(trade, atR = NUDGE_AT_R) {
  if (!trade || trade.isClosed) return false
  const { rr, stopPrice, initialStop } = trade
  if (initialStop == null || stopPrice == null) return false
  if (typeof rr !== 'number' || !Number.isFinite(rr)) return false
  if (rr < atR) return false
  return Math.abs(stopPrice - initialStop) <= CENT
}

/**
 * How far price can travel against you before the CURRENT stop is hit, as a
 * percentage of the last price.
 *
 * §十四 asked for this because the table only ever showed distance from the
 * INITIAL stop, which stops meaning anything the moment you trail. Positive =
 * the stop is still behind price (room left). Negative = price has already
 * crossed it — which is a real state worth seeing, not an error, so it is
 * returned rather than clamped.
 *
 * @returns {number|null} null when either price is missing — never 0, because
 *   0% buffer means "the stop is exactly here", a very different sentence.
 */
export function stopBufferPct(trade) {
  if (!trade || trade.isClosed) return null
  const { lastPrice, stopPrice, direction } = trade
  if (lastPrice == null || stopPrice == null) return null
  if (!Number.isFinite(lastPrice) || !Number.isFinite(stopPrice) || lastPrice <= 0) return null
  const dir = direction === 'short' ? -1 : 1
  return ((lastPrice - stopPrice) / lastPrice) * dir * 100
}
