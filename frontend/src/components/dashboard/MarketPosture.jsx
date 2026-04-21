import { signalLabel } from '../../lib/format'

const SIGNAL_SCORE = { POWER_3: 3, CAUTION: 2, WARNING: 1, RISK_OFF: 0 }
const TICKERS = ['SPY', 'QQQ', 'IWM', 'RSP']

function derivePosture(signals) {
  if (!signals) return null

  let total = 0
  let count = 0
  for (const t of TICKERS) {
    const s = signals[t]
    if (s?.signal && SIGNAL_SCORE[s.signal] != null) {
      total += SIGNAL_SCORE[s.signal]
      count++
    }
  }
  if (count === 0) return null

  const avg = total / count
  // 2.5+ = green, 1.5-2.49 = yellow, <1.5 = red
  if (avg >= 2.5) return { level: 'green', label: 'Full Size', desc: 'All strategies go. Normal position sizing.' }
  if (avg >= 1.5) return { level: 'yellow', label: 'Selective', desc: 'Reduce size. Only A+ setups.' }
  return { level: 'red', label: 'Defensive', desc: 'Cash heavy. Protect capital.' }
}

const LIGHT_STYLES = {
  green: {
    active: 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]',
    ring: 'ring-green-500/20',
  },
  yellow: {
    active: 'bg-amber-500 shadow-[0_0_8px_rgba(234,179,8,0.5)]',
    ring: 'ring-amber-500/20',
  },
  red: {
    active: 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]',
    ring: 'ring-red-500/20',
  },
}

export default function MarketPosture({ signals }) {
  const posture = derivePosture(signals)

  if (!posture) return null

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-5 py-4">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
        Market Posture
      </h3>

      {/* Traffic light */}
      <div className="flex items-center gap-4">
        <div className={`flex flex-col gap-1.5 p-2 rounded-lg ring-1 ${LIGHT_STYLES[posture.level].ring}`}>
          {['red', 'yellow', 'green'].map((color) => (
            <div
              key={color}
              className={`w-5 h-5 rounded-full transition-all ${
                color === posture.level
                  ? LIGHT_STYLES[color].active
                  : 'bg-[var(--color-surface-raised)]'
              }`}
            />
          ))}
        </div>
        <div>
          <div className="text-base font-bold text-[var(--color-text-bold)]">
            {posture.label}
          </div>
          <div className="text-xs text-[var(--color-text-secondary)] mt-0.5">
            {posture.desc}
          </div>
        </div>
      </div>

      {/* Signal breakdown */}
      <div className="flex gap-3 flex-wrap mt-3 pt-3 border-t border-[var(--color-border-light)]">
        {TICKERS.map((t) => {
          const s = signals?.[t]
          if (!s) return null
          const colorMap = { green: 'text-green-600', yellow: 'text-amber-600', orange: 'text-orange-500', red: 'text-red-500' }
          return (
            <div key={t} className="flex items-center gap-1.5">
              <span className="font-mono text-[11px] text-[var(--color-text-secondary)]">{t}</span>
              <span className={`text-[10px] font-medium uppercase ${colorMap[s.color] || 'text-[var(--color-text-muted)]'}`}>
                {signalLabel(s.signal)}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
