/**
 * Wraps an unfinished/unreviewed section. Locked for everyone, including
 * verified members (Andy 2026-09-25: "我没有再完成确认审核的板块 那现在只是
 * 不对他们开放 只是写这是一个Beta") — this component doesn't take an
 * "isMember" prop on purpose, because the rule is nobody gets in yet.
 *
 * Which sections actually qualify isn't decided here — that's a per-page
 * call for whoever owns the section, not something to guess in the wrapper.
 */
export default function BetaLock({ label, children }) {
  return (
    <div className="relative" data-beta-lock={label ?? true}>
      <div aria-hidden className="pointer-events-none opacity-30 blur-[1px] select-none">
        {children}
      </div>
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-[var(--color-surface)]/85 backdrop-blur-sm rounded text-center px-4">
        <span className="text-xl" aria-hidden>🔒</span>
        <span className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-secondary)]">
          Beta — opening soon
        </span>
        {label && (
          <span className="text-[11px] text-[var(--color-text-muted)]">{label}</span>
        )}
      </div>
    </div>
  )
}
