export default function TimeMachineBar({ tm }) {
  const idx = tm.dates.indexOf(tm.date)

  if (!tm.active) {
    return (
      <div className="flex items-center gap-3 bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-4 py-2">
        <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Market Time Machine
        </span>
        <span className="text-[11px] text-[var(--color-text-muted)] flex-1">
          Replay the dashboard using only information available through a past trading date.
        </span>
        <button
          onClick={tm.engage}
          disabled={tm.loading}
          className="text-[11px] px-2 py-1 rounded border border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-hover-bg)] disabled:opacity-50"
        >
          {tm.loading ? 'Loading…' : 'Enable'}
        </button>
        {/* an error is chrome, not a market reading — it leaves the encoding pair */}
        {tm.error && (
          <span className="text-[10px] text-[var(--color-signal-riskoff)]">{tm.error}</span>
        )}
      </div>
    )
  }

  // Defensive: never assert "future observations excluded" without a pinned
  // date to back the claim — show a neutral loading row instead.
  if (!tm.date) {
    return (
      <div className="flex items-center gap-3 bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-4 py-2">
        <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Market Time Machine
        </span>
        <span className="text-[11px] text-[var(--color-text-muted)] flex-1">
          Loading replay data…
        </span>
      </div>
    )
  }

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-signal-caution)] rounded px-4 py-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-signal-caution)]">
          Historical snapshot · {tm.date} · future observations excluded
        </span>
        <div className="flex items-center gap-1">
          <BarButton onClick={() => tm.step(-1)} label="◀" />
          <BarButton onClick={tm.togglePlay} label={tm.playing ? '❚❚ Pause' : '▶ Play'} />
          <BarButton onClick={() => tm.step(1)} label="▶" />
          <BarButton onClick={tm.jumpYtd} label="YTD" />
          <BarButton onClick={tm.exitToLatest} label="Latest" />
        </div>
      </div>
      <input
        type="range"
        min={0}
        max={Math.max(tm.dates.length - 1, 0)}
        value={idx < 0 ? 0 : idx}
        onChange={(e) => tm.setDate(tm.dates[Number(e.target.value)])}
        className="w-full accent-[var(--color-signal-caution)]"
      />
      <div className="flex justify-between text-[10px] font-mono text-[var(--color-text-muted)] mt-1">
        <span>{tm.dates[0]}</span>
        <span>{tm.dates[tm.dates.length - 1]}</span>
      </div>
    </div>
  )
}

function BarButton({ onClick, label }) {
  return (
    <button
      onClick={onClick}
      className="text-[10px] font-mono px-2 py-1 rounded border border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-hover-bg)]"
    >
      {label}
    </button>
  )
}
