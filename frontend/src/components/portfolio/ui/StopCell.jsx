import EditablePrice from './EditablePrice'
import { stopNotMoved, stopBufferPct } from '../lib/stopDiscipline'

/**
 * One column, four things, and only one of them shouting.
 *
 * Andy, 2026-09-01: 「四个内容都挤在了一个 CELL 里面」. He tried V3 (buffer drawn
 * as a bar, every number faded) and came back to **V2 with init on hover** —
 * the version below. The difference is worth naming: V3 spent a line on a bar
 * so it would not have to print a number; V2 prints the number and puts it
 * where it belongs.
 *
 *   LINE 1        the stop, and the buffer beside it — `$100.00 · 3.4%`.
 *                 The buffer is a PROPERTY of this price ("how far away is
 *                 it"), not a second fact, so it reads as one line.
 *   LINE 2        the suggestion, always legible — it is the only thing here
 *                 you can act on. `init` shares the line but stays hidden
 *                 until the row is under the cursor: it is reference, wanted
 *                 maybe once a week, and it was costing a permanent line.
 *   NEVER FADES   the red "up N R and the stop has not moved" mark. That is
 *                 the whole reason this column was rebuilt: all 373 historical
 *                 trades still sit on their entry stop, and that is where the
 *                 −17.9% drawdown came from (DATA_CONTRACTS §十四).
 *
 * `group` on the <tr> drives the hover; `group-focus-within` covers the
 * keyboard, which has no hover at all.
 */
export default function StopCell({ stopPrice, initialStop, suggestion, onChange, trade }) {
  const sug = suggestion?.suggestedStop
  const showSuggestion = sug != null && Math.abs(sug - stopPrice) > 0.01
  const trailed = initialStop != null && Math.abs(initialStop - stopPrice) > 0.01
  const nudge = stopNotMoved(trade)
  const buffer = stopBufferPct(trade)
  const crossed = buffer != null && buffer < 0

  return (
    <div className="flex flex-col gap-0.5">
      {/* LINE 1 — the price, and how far it is. Absent rather than 0 when
          unmeasured: `stopBufferPct` returns null, and 0% would say "the stop
          is exactly here", which is a different sentence. */}
      <div className="flex items-baseline gap-1 flex-wrap">
        <EditablePrice value={stopPrice} onChange={onChange}
                       title={suggestion?.basis === 'no-data' ? suggestion.rationale : undefined} />
        {buffer != null && (
          <span className="text-[11px] tabular-nums text-[var(--color-text-muted)] whitespace-nowrap"
                title="How far price can move against you before the current stop is hit.">
            · {crossed ? `crossed ${Math.abs(buffer).toFixed(1)}%` : `${buffer.toFixed(1)}%`}
          </span>
        )}
      </div>

      {nudge && (
        <div className="text-[11px] font-medium tabular-nums"
             style={{ color: 'var(--color-refused)' }}
             title={`Up ${trade.rr.toFixed(1)}R and the stop is still at entry risk. `
                    + `Moving it does NOT change this trade's R — the denominator is `
                    + `locked to the initial stop ($${initialStop?.toFixed(2)}).`}>
          {trade.rr.toFixed(1)}R · stop not moved
        </div>
      )}

      {/* LINE 2 — what you can act on, and what you might look up. */}
      {(showSuggestion || trailed) && (
        <div className="text-[11px] tabular-nums leading-[1.5] text-[var(--color-text-muted)]">
          {showSuggestion && (
            <>
              <span title={suggestion.rationale}>sug ${sug.toFixed(2)} </span>
              <button onClick={() => onChange(sug)}
                      className="text-[var(--color-accent)] hover:underline cursor-pointer">
                Accept
              </button>
            </>
          )}
          {trailed && (
            <span className="opacity-0 transition-opacity group-hover:opacity-100
                             group-focus-within:opacity-100 whitespace-nowrap"
                  title={`Locked at entry — 1R anchored here. Current stop is trailed ${
                    stopPrice > initialStop ? 'up' : 'down'
                  } by $${Math.abs(stopPrice - initialStop).toFixed(2)}.`}>
              {showSuggestion && <span className="opacity-40"> · </span>}
              init ${initialStop.toFixed(2)}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
