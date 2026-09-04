import { derive as deriveLegState } from '../portfolio/lib/legState'
import { suggest as suggestStop } from '../portfolio/lib/stopSuggestion'
import { compute as computeTargets, isHit } from '../portfolio/lib/trimTargets'
import { chips as proximityChipsFn } from '../portfolio/lib/emaProximity'
import LegStateBadge from '../portfolio/ui/LegStateBadge'
import ProximityChips from '../portfolio/ui/ProximityChips'
import { fmtCur } from '../portfolio/lib/portfolioFormat'

/**
 * Status Panel — for the most-recent open layer of this ticker (if any),
 * shows leg state, current/suggested stop, trim targets, EMA references.
 *
 * Falls back to "no open position" with a summary of the most recent closed
 * trade if any.
 */
export default function TickerStatusPanel({ symbol, openTrade, lastClosed, universe, onAcceptStop }) {
  if (!openTrade && !lastClosed) {
    return (
      <div className="bg-[var(--color-bg)] rounded-3xl p-5 h-full">
        <div className="font-semibold mb-3 text-[13px]">Status</div>
        <div className="text-[var(--color-text-muted)] text-[13px]">No record of trading {symbol}.</div>
      </div>
    )
  }
  if (!openTrade) {
    return (
      <div className="bg-[var(--color-bg)] rounded-3xl p-5 h-full">
        <div className="font-semibold mb-3 text-[13px]">Status</div>
        <div className="text-[13px]">No open position.</div>
        <div className="text-[11px] text-[var(--color-text-muted)] mt-1">
          Last trade: {lastClosed.entryDate?.slice(0, 10)} @ {fmtCur(lastClosed.entryPrice)}
        </div>
      </div>
    )
  }

  const t = openTrade
  const legState = deriveLegState({
    currentQty: t.currentQty, originalQty: t.originalQty, trims: t.trims,
  })
  const u = universe || {}
  const px = t.lastPrice || t.entryPrice
  // ATR is already published in dollars; going through a percentage was a
  // detour, and the percentage it used (`adr_pct`) stopped being ATR% on
  // 2026-09-04. A stop distance must respect gaps, so true range is right.
  const atrDollars = u.atr ?? 0
  const stopSugg = suggestStop(
    { state: legState, stopPrice: t.stopPrice, entryPrice: t.entryPrice, direction: t.direction },
    u,
    { atr: atrDollars },
  )
  const targets = computeTargets(t)
  const hit4 = targets && isHit(t.trims, targets.targetR4, t.direction)
  const hit8 = targets && isHit(t.trims, targets.targetR8, t.direction)
  const chipsList = proximityChipsFn(
    { price: px, direction: t.direction, wkClose: px },
    u,
  )

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5 h-full flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="font-semibold text-[13px]">Status</div>
        <LegStateBadge state={legState} />
      </div>
      <ProximityChips chips={chipsList} />

      <div className="border-t border-[var(--color-border-light)] pt-3">
        <div className="text-[11px] uppercase text-[var(--color-text-muted)] tracking-wide mb-1">Stop</div>
        <div className="flex items-baseline justify-between gap-2">
          <span className="tabular-nums text-[17px] font-semibold">{fmtCur(t.stopPrice)}</span>
          {stopSugg?.suggestedStop != null && Math.abs(stopSugg.suggestedStop - t.stopPrice) > 0.01 && (
            <button
              onClick={() => onAcceptStop?.(t.id, stopSugg.suggestedStop)}
              className="text-[11px] text-[var(--color-accent)] hover:underline cursor-pointer"
              title={stopSugg.rationale}
            >
              sug {fmtCur(stopSugg.suggestedStop)} → Accept
            </button>
          )}
        </div>
        {stopSugg?.rationale && (
          <div className="text-[11px] text-[var(--color-text-muted)] mt-1">{stopSugg.rationale}</div>
        )}
      </div>

      {targets && (
        <div className="border-t border-[var(--color-border-light)] pt-3">
          <div className="text-[11px] uppercase text-[var(--color-text-muted)] tracking-wide mb-1">Trim targets</div>
          <div className="text-[13px] flex flex-col gap-0.5">
            <div className={hit4 ? 'line-through text-[var(--color-profit)]' : ''}>
              +4R · {fmtCur(targets.targetR4)}
            </div>
            <div className={hit8 ? 'line-through text-[var(--color-profit)]' : ''}>
              +8R · {fmtCur(targets.targetR8)}
            </div>
          </div>
        </div>
      )}

      <div className="border-t border-[var(--color-border-light)] pt-3">
        <div className="text-[11px] uppercase text-[var(--color-text-muted)] tracking-wide mb-1">EMA references</div>
        <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[11px] tabular-nums">
          {u.ema10 != null && <><span className="text-[var(--color-text-muted)]">10EMA</span><span>{fmtCur(u.ema10)}</span></>}
          {u.ema20 != null && <><span className="text-[var(--color-text-muted)]">20EMA</span><span>{fmtCur(u.ema20)}</span></>}
          {u.wk_ema10 != null && <><span className="text-[var(--color-text-muted)]">wk-10EMA</span><span>{fmtCur(u.wk_ema10)}</span></>}
          {u.wk_ema20 != null && <><span className="text-[var(--color-text-muted)]">wk-20EMA</span><span>{fmtCur(u.wk_ema20)}</span></>}
        </div>
      </div>
    </div>
  )
}
