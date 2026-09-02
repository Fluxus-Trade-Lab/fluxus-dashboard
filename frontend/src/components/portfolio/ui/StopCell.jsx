import EditablePrice from './EditablePrice'
import { stopNotMoved, stopBufferPct } from '../lib/stopDiscipline'

/** The bar is full at 20%. A fixed ceiling, not the row set's own max: the
 *  point of the bar is that today's row is comparable to yesterday's, and a
 *  scale that re-fits itself every render is not. Past 20% it simply saturates
 *  — the difference between "far" and "very far" is not a decision anyone
 *  makes from this column. */
const BAR_FULL_AT = 20

/**
 * One column, four things, and only one of them shouting.
 *
 * Andy, 2026-09-01, on the first version: 「四个内容都挤在了一个 CELL 里面」.
 * He picked this layout out of four. The rule it follows: what you must not
 * miss is always solid; what you look up when you are already interested fades
 * back until the row is under the cursor.
 *
 *   ALWAYS SOLID   the stop itself, and the red "you are up N R and this has
 *                  not moved" mark — that one is the whole reason this column
 *                  was touched (DATA_CONTRACTS §十四), so it never fades.
 *   ALWAYS DRAWN   the buffer, as a bar. A length is read without being read;
 *                  it is the one thing here you can scan a whole table for.
 *   FADED AT REST  the numbers behind the bar, the initial stop, the
 *                  suggestion. Still legible at 45% — Andy reads this page by
 *                  screenshotting it, and a screenshot has no hover.
 *
 * `group` on the <tr> is what makes the hover work; `group-focus-within` is
 * what makes it work for a keyboard, which has no hover at all.
 */
export default function StopCell({ stopPrice, initialStop, suggestion, onChange, trade }) {
  const sug = suggestion?.suggestedStop
  const showSuggestion = sug != null && Math.abs(sug - stopPrice) > 0.01
  const trailed = initialStop != null && Math.abs(initialStop - stopPrice) > 0.01
  const nudge = stopNotMoved(trade)
  const buffer = stopBufferPct(trade)
  const crossed = buffer != null && buffer < 0
  const fill = buffer == null ? 0 : Math.max(0, Math.min(1, buffer / BAR_FULL_AT)) * 100

  return (
    <div className="flex flex-col gap-0.5">
      <EditablePrice value={stopPrice} onChange={onChange}
                     title={suggestion?.basis === 'no-data' ? suggestion.rationale : undefined} />

      {/* Never fades. All 373 historical trades still sit on their entry stop
          and that is where the −17.9% drawdown came from; this mark is the
          only reason the column was rebuilt. Red with no blue near it is this
          site's mark for a binding constraint. */}
      {nudge && (
        <div className="text-[10px] font-medium tabular-nums"
             style={{ color: 'var(--color-refused)' }}
             title={`Up ${trade.rr.toFixed(1)}R and the stop is still at entry risk. `
                    + `Moving it does NOT change this trade's R — the denominator is `
                    + `locked to the initial stop ($${initialStop?.toFixed(2)}).`}>
          {trade.rr.toFixed(1)}R · stop not moved
        </div>
      )}

      {/* Absent when unmeasured, rather than a zero-length bar — an empty
          track would read as "no room left", which is a different sentence
          from "we do not have today's price". */}
      {buffer != null && (
        <div className="relative h-[4px] rounded-sm mt-[3px]"
             style={{ background: 'var(--color-border-light)' }}
             title={`Room to the current stop: ${buffer.toFixed(1)}%. Bar is full at ${BAR_FULL_AT}%.`}>
          {!crossed && (
            <i className="absolute left-0 top-0 bottom-0 rounded-sm"
               style={{ width: `${fill}%`, background: 'var(--color-text-secondary)' }} />
          )}
          {crossed && (
            <i className="absolute left-0 top-[-2px] bottom-[-2px] w-[2px] rounded-sm"
               style={{ background: 'var(--color-refused)' }} />
          )}
        </div>
      )}

      {(buffer != null || trailed || showSuggestion) && (
        <div className="text-[10px] tabular-nums leading-[1.5] opacity-45 transition-opacity
                        group-hover:opacity-100 group-focus-within:opacity-100
                        text-[var(--color-text-muted)]">
          {buffer != null && (
            <span>{crossed ? `stop crossed ${Math.abs(buffer).toFixed(1)}%` : `buffer ${buffer.toFixed(1)}%`}</span>
          )}
          {trailed && (
            <>
              {buffer != null && <span className="opacity-40"> · </span>}
              <span title={`Locked at entry — 1R anchored here. Current stop is trailed ${
                stopPrice > initialStop ? 'up' : 'down'
              } by $${Math.abs(stopPrice - initialStop).toFixed(2)}.`}>
                init ${initialStop.toFixed(2)}
              </span>
            </>
          )}
          {showSuggestion && (
            <>
              {(buffer != null || trailed) && <span className="opacity-40"> · </span>}
              <span title={suggestion.rationale}>sug ${sug.toFixed(2)} </span>
              <button onClick={() => onChange(sug)}
                      className="text-[var(--color-accent)] hover:underline cursor-pointer">
                Accept
              </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}
