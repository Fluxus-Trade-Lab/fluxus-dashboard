export default function SortableHeader({ label, sortKey, sortConfig, onSort, className = '' }) {
  const sortable = Boolean(sortKey)
  const active = sortable && sortConfig.key === sortKey
  const arrow = !sortable ? '' : active ? (sortConfig.direction === 'asc' ? '▲' : '▼') : '↕'

  return (
    <th
      onClick={sortable ? () => onSort(sortKey) : undefined}
      className={`text-left px-2.5 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[11px] uppercase tracking-wide whitespace-nowrap ${sortable ? 'cursor-pointer select-none hover:text-[var(--color-text)]' : ''} ${className}`}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {sortable && (
          <span className={`text-[11px] leading-none ${active ? 'text-[var(--color-accent)]' : 'text-[var(--color-text-muted)] opacity-50'}`}>
            {arrow}
          </span>
        )}
      </span>
    </th>
  )
}
