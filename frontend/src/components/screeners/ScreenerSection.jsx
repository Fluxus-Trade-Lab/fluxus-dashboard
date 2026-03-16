import { useState } from 'react'

export default function ScreenerSection({ title, count, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-3 py-2 text-left"
      >
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
            {title}
          </span>
          {count != null && (
            <span className="text-[10px] font-mono bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] px-1.5 rounded-full">
              {count}
            </span>
          )}
        </div>
        <span className="text-[10px] text-[var(--color-text-muted)]">
          {open ? '▾' : '▸'}
        </span>
      </button>
      {open && (
        <div className="px-3 pb-3">
          {children}
        </div>
      )}
    </div>
  )
}
