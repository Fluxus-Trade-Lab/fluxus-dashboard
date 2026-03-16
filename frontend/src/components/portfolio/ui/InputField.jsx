export default function InputField({ label, className = '', ...props }) {
  return (
    <div className="flex flex-col gap-0.5">
      {label && (
        <label className="text-[11px] text-[var(--color-text-secondary)] font-medium tracking-wide">
          {label}
        </label>
      )}
      <input
        className={`px-2 py-1.5 border border-[var(--color-input-border)] rounded text-sm bg-[var(--color-input-bg)]
          outline-none focus:border-[var(--color-accent)] font-sans ${className}`}
        {...props}
      />
    </div>
  )
}

export function SelectField({ label, children, className = '', ...props }) {
  return (
    <div className="flex flex-col gap-0.5">
      {label && (
        <label className="text-[11px] text-[var(--color-text-secondary)] font-medium tracking-wide">
          {label}
        </label>
      )}
      <select
        className={`px-2 py-1.5 border border-[var(--color-input-border)] rounded text-sm bg-[var(--color-input-bg)]
          outline-none focus:border-[var(--color-accent)] font-sans ${className}`}
        {...props}
      >
        {children}
      </select>
    </div>
  )
}
