import EditablePrice from './EditablePrice'
import { stopNotMoved, stopBufferPct } from '../lib/stopDiscipline'

export default function StopCell({ stopPrice, initialStop, suggestion, onChange, trade }) {
  const sug = suggestion?.suggestedStop
  const showSuggestion = sug != null && Math.abs(sug - stopPrice) > 0.01
  const trailed = initialStop != null && Math.abs(initialStop - stopPrice) > 0.01
  const nudge = stopNotMoved(trade)
  const buffer = stopBufferPct(trade)
  return (
    <div className="flex flex-col gap-0.5">
      <EditablePrice value={stopPrice} onChange={onChange}
                     title={suggestion?.basis === 'no-data' ? suggestion.rationale : undefined} />

      {/* THE ONE THING THIS TABLE NEVER SAID (DATA_CONTRACTS §十四, 2026-09-01).
          All 373 historical trades still carry their entry stop; Andy's reason
          was that the dashboard never surfaced it. Red with no blue anywhere
          near it is this site's mark for a BINDING constraint, and that is
          exactly what this is: the position has earned a move and the risk
          behind it has not been moved. The tooltip carries the fact that
          usually stops people — trailing does not touch R. */}
      {nudge && (
        <div className="text-[10px] font-medium tabular-nums"
             style={{ color: 'var(--color-refused)' }}
             title={`Up ${trade.rr.toFixed(1)}R and the stop is still at entry risk. `
                    + `Moving it does NOT change this trade's R — the denominator is `
                    + `locked to the initial stop ($${initialStop?.toFixed(2)}).`}>
          {trade.rr.toFixed(1)}R · stop not moved
        </div>
      )}

      {/* Distance to the stop you ACTUALLY have. The line below shows the
          initial stop, which stops meaning anything the moment you trail. */}
      {buffer != null && (
        <div className="text-[10px] text-[var(--color-text-muted)] tabular-nums"
             title="How far price can move against you before the current stop is hit.">
          {buffer < 0 ? `stop crossed ${Math.abs(buffer).toFixed(1)}%` : `buffer ${buffer.toFixed(1)}%`}
        </div>
      )}
      {trailed && (
        <div
          className="text-[10px] text-[var(--color-text-muted)] tabular-nums"
          title={`Locked at entry — 1R anchored here. Current stop is trailed ${
            stopPrice > initialStop ? 'up' : 'down'
          } by $${Math.abs(stopPrice - initialStop).toFixed(2)}.`}
        >
          init ${initialStop.toFixed(2)}
        </div>
      )}
      {showSuggestion && (
        <div className="text-[10px] text-[var(--color-text-muted)] flex items-center gap-1.5" title={suggestion.rationale}>
          <span>sug ${sug.toFixed(2)}</span>
          <button
            onClick={() => onChange(sug)}
            className="text-[var(--color-accent)] hover:underline cursor-pointer"
          >
            Accept
          </button>
        </div>
      )}
      {/* "no wk-20EMA data" used to print here as a fourth line. Andy took it
          off on 2026-09-01: it is an explanation for an ABSENT suggestion, not
          a reading, and it was costing a line in a 96px cell on every row that
          had no weekly EMA. It is not lost — the same sentence is the price
          field's tooltip, where a reader who wonders "why is there no sug
          here" will look. */}
    </div>
  )
}
