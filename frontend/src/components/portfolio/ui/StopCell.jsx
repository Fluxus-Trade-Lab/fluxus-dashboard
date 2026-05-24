import EditablePrice from './EditablePrice'

export default function StopCell({ stopPrice, suggestion, onChange }) {
  const sug = suggestion?.suggestedStop
  const showSuggestion = sug != null && Math.abs(sug - stopPrice) > 0.01
  return (
    <div className="flex flex-col gap-0.5">
      <EditablePrice value={stopPrice} onChange={onChange} />
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
      {suggestion?.basis === 'no-data' && (
        <div className="text-[10px] text-[var(--color-text-muted)]" title={suggestion.rationale}>
          no wk-20EMA data
        </div>
      )}
    </div>
  )
}
