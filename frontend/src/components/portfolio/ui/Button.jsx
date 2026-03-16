const variants = {
  primary: 'bg-[var(--color-accent)] text-white hover:opacity-90',
  danger: 'bg-red-600 text-white hover:bg-red-700',
  ghost: 'bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:bg-[var(--color-hover-bg)]',
}

export default function Button({ children, variant = 'primary', className = '', ...props }) {
  return (
    <button
      className={`px-3 py-1.5 rounded text-xs font-semibold cursor-pointer
        disabled:opacity-50 disabled:cursor-not-allowed transition-colors
        ${variants[variant] || variants.primary} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
