import { useState } from 'react'
import { DEFAULT_RULES } from '../../portfolio/lib/demonFinder'

const FIELDS = [
  { key: 'capital', label: 'Starting Capital', prefix: '$', format: v => v.toLocaleString(), parse: v => Number(v.replace(/,/g, '')) },
  { key: 'riskPerTrade', label: 'Risk Per Trade', suffix: '%', format: v => (v * 100).toFixed(2), parse: v => Number(v) / 100 },
  { key: 'minRR', label: 'Min R/R', suffix: ':1', format: v => v, parse: Number },
  { key: 'overtradingMax', label: 'Max Entries / 5 Days', format: v => v, parse: Number },
  { key: 'maxTotalHeat', label: 'Max Total Heat', suffix: '%', format: v => (v * 100).toFixed(1), parse: v => Number(v) / 100 },
  { key: 'maxSectorHeat', label: 'Max Sector Heat', suffix: '%', format: v => (v * 100).toFixed(1), parse: v => Number(v) / 100 },
  { key: 'circuitBreakerStreak', label: 'Circuit Breaker', format: v => v, parse: Number },
]

export default function DemonRulesConfig({ rules, onUpdate }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="bg-[var(--color-surface)] rounded-3xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="w-full flex items-center justify-between px-4 py-2.5 text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] hover:bg-[var(--color-hover-bg)] cursor-pointer bg-transparent border-none text-left"
      >
        <span>Trading Rules</span>
        <span className="text-[var(--color-text-muted)]">{open ? '\u25B2' : '\u25BC'}</span>
      </button>

      {open && (
        <div className="px-4 pb-3 border-t border-[var(--color-border-light)]">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-3">
            {FIELDS.map(({ key, label, prefix, suffix, format, parse }) => (
              <div key={key}>
                <label className="text-[11px] text-[var(--color-text-muted)] uppercase tracking-wide block mb-1">
                  {label}
                </label>
                <div className="flex items-center gap-1">
                  {prefix && <span className="text-[13px] text-[var(--color-text-muted)]">{prefix}</span>}
                  <input
                    type="text"
                    value={format(rules[key])}
                    onChange={e => {
                      const val = parse(e.target.value)
                      if (!isNaN(val) && val > 0) onUpdate({ ...rules, [key]: val })
                    }}
                    className="w-full px-2 py-1 text-[13px] font-mono bg-[var(--color-bg)] rounded-3xl outline-none focus:border-[var(--color-text-muted)] text-[var(--color-text)]"
                  />
                  {suffix && <span className="text-[13px] text-[var(--color-text-muted)]">{suffix}</span>}
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={() => onUpdate(DEFAULT_RULES)}
            className="mt-2 text-[11px] text-[var(--color-accent)] hover:underline cursor-pointer bg-transparent border-none"
          >
            Reset to defaults
          </button>
        </div>
      )}
    </div>
  )
}
