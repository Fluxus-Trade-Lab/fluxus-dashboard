import { fmtPctRaw, pctColor } from '../../lib/format'

export default function EpisodicPivot({ data }) {
  if (!data?.results || data.results.length === 0) return null

  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          <th className="text-left py-1 pr-2">Ticker</th>
          <th className="text-right py-1 px-2">Contractions</th>
          <th className="text-right py-1 px-2">Depth</th>
          <th className="text-right py-1 px-2">Pivot</th>
          <th className="text-right py-1 pl-2">% to Pivot</th>
        </tr>
      </thead>
      <tbody>
        {data.results.map((r, i) => (
          <tr key={`${r.ticker}-${i}`} className={`border-b border-[var(--color-border-light)] ${i % 2 === 1 ? 'bg-[var(--color-surface-alt)]/50' : ''}`}>
            <td className="font-mono text-xs font-medium text-[var(--color-text-bold)] py-1 pr-2">
              {r.ticker}
            </td>
            <td className="font-mono text-right py-1 px-2 text-[var(--color-text-secondary)]">
              {r.num_contractions}
            </td>
            <td className="font-mono text-right py-1 px-2 text-[var(--color-text-secondary)]">
              {r.max_depth != null && r.last_depth != null
                ? `${Number(r.max_depth).toFixed(1)}\u2192${Number(r.last_depth).toFixed(1)}`
                : '\u2014'}
            </td>
            <td className="font-mono text-right py-1 px-2 text-[var(--color-text-secondary)]">
              {r.pivot != null ? Number(r.pivot).toFixed(2) : '\u2014'}
            </td>
            <td className={`font-mono text-right py-1 pl-2 ${pctColor(r.pct_to_pivot)}`}>
              {fmtPctRaw(r.pct_to_pivot)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
