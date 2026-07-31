import { useState, useEffect } from 'react'

const QUALITY = new Set(['episodic_pivot', 'vcp', 'momentum_97'])

const LABELS = {
  episodic_pivot: 'EP',
  vcp: 'VCP',
  momentum_97: 'MOM',
  gainers_4pct: '4%',
  vol_up_gainers: 'VOL',
  ema21_watch: '21EMA',
  healthy_charts: 'HLTH',
}

export default function HeatingUp({ limit = 25 }) {
  const [data, setData] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetch('/data/output/heating_up.json')
      .then((r) => (r.ok ? r.json() : null))
      .then((json) => { if (!cancelled) setData(json) })
      .catch(() => { if (!cancelled) setData(null) })
    return () => { cancelled = true }
  }, [])

  if (!data?.rows?.length) return null
  const rows = data.rows.slice(0, limit)

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
      <div className="flex items-baseline justify-between mb-3">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Heating Up · signals stacking
        </h3>
        <span className="text-[10px] font-mono text-[var(--color-text-muted)]">
          as of {data.as_of}
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[var(--color-border)]">
              <Th align="left">Ticker</Th>
              <Th>Heat</Th>
              <Th align="left">Signals</Th>
              <Th>Span</Th>
              <Th align="left">Sector</Th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.ticker} className="border-b border-[var(--color-border-light)] hover:bg-[var(--color-hover-bg)]">
                <td className="px-2 py-1.5">
                  <a href={`#/ticker/${r.ticker}`} className="font-mono font-medium text-[var(--color-text)] hover:underline">
                    {r.ticker}
                  </a>
                </td>
                <td className="px-2 py-1.5 text-right font-mono tabular-nums text-[var(--color-text)]">
                  {r.score.toFixed(2)}
                </td>
                <td className="px-2 py-1.5">
                  <span className="flex flex-wrap gap-1">
                    {r.screeners.map((s) => (
                      <span
                        key={s.name}
                        title={`${s.name} · ${s.hits}× · last ${s.last_date}`}
                        className={`text-[9px] font-mono px-1 py-0.5 rounded border ${
                          QUALITY.has(s.name)
                            ? 'border-[var(--color-profit)] text-[var(--color-profit)]'
                            : 'border-[var(--color-border)] text-[var(--color-text-secondary)]'
                        }`}
                      >
                        {LABELS[s.name] ?? s.name}{s.hits > 1 ? `×${s.hits}` : ''}
                      </span>
                    ))}
                  </span>
                </td>
                <td className="px-2 py-1.5 text-right font-mono tabular-nums text-[var(--color-text-secondary)]">
                  {r.days_span}d
                </td>
                <td className="px-2 py-1.5 text-[var(--color-text-secondary)]">{r.sector ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Th({ children, align = 'right' }) {
  return (
    <th className={`px-2 py-1.5 text-${align} text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] whitespace-nowrap`}>
      {children}
    </th>
  )
}
