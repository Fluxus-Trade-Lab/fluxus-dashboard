export default function StatCard({ label, value, sub, colorClass }) {
  return (
    <div className="px-4 py-3 bg-[var(--color-bg)] rounded-md border border-[var(--color-border)] min-w-[140px]">
      <div className="text-[11px] text-[var(--color-text-muted)] font-medium uppercase tracking-wider mb-1">
        {label}
      </div>
      <div className={`text-xl font-bold tabular-nums ${colorClass || 'text-[var(--color-text)]'}`}>
        {value}
      </div>
      {sub && <div className="text-[11px] text-[var(--color-text-muted)] mt-0.5">{sub}</div>}
    </div>
  )
}
