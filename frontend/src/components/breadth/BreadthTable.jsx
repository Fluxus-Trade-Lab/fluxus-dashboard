export default function BreadthTable({ data }) {
  const rows = data?.history?.rows
  if (!rows?.length) return null

  // Deduplicate by date (keep last), reverse so newest is first
  const seen = new Set()
  const deduped = []
  for (let i = rows.length - 1; i >= 0; i--) {
    if (!seen.has(rows[i].date)) {
      seen.add(rows[i].date)
      deduped.unshift(rows[i])
    }
  }
  const sorted = [...deduped].reverse()

  return (
    <div className="bg-[var(--color-surface)] rounded-3xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-[12.5px]">
          <thead>
            <tr className="border-b border-[var(--color-border)] bg-[var(--color-bg)]">
              <Th>Date</Th>
              <Th>Up 4%</Th>
              <Th>Dn 4%</Th>
              <Th>5D Ratio</Th>
              <Th>10D Ratio</Th>
              <ThSep />
              <Th>Up 25% Qtr</Th>
              <Th>Dn 25% Qtr</Th>
              <Th>Up 25% Mo</Th>
              <Th>Dn 25% Mo</Th>
              <Th>Up 50% Mo</Th>
              <Th>Dn 50% Mo</Th>
              <ThSep />
              <Th>T2108</Th>
              <Th>% &gt; 200</Th>
              <Th>% &gt; 50</Th>
              <Th>% &gt; 20</Th>
              <ThSep />
              <Th>Adv</Th>
              <Th>Dec</Th>
              <Th>NH</Th>
              <Th>NL</Th>
              <Th>McCl</Th>
              <ThSep />
              <Th>SPX</Th>
              <Th>Worden</Th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, i) => (
              <tr
                key={row.date}
                className={`border-b border-[var(--color-border-light)] hover:bg-[var(--color-hover-bg)] ${
                  i === 0 ? 'bg-[var(--color-surface-alt)]/50 font-medium' : i % 2 === 1 ? 'bg-[var(--color-surface-alt)]/50' : ''
                }`}
              >
                <Td className="text-[var(--color-text-secondary)] whitespace-nowrap">{fmtDate(row.date)}</Td>
                <Td>{row.up_4pct}</Td>
                <Td>{row.down_4pct}</Td>
                <Td className={ratioColor(row.ratio_5d)}>{row.ratio_5d?.toFixed(2)}</Td>
                <Td className={ratioColor(row.ratio_10d)}>{row.ratio_10d?.toFixed(2)}</Td>
                <TdSep />
                <Td>{row.up_25pct_qtr}</Td>
                <Td>{row.down_25pct_qtr}</Td>
                <Td>{row.up_25pct_month}</Td>
                <Td>{row.down_25pct_month}</Td>
                <Td>{row.up_50pct_month}</Td>
                <Td>{row.down_50pct_month}</Td>
                <TdSep />
                <Td className={pctAboveColor(row.t2108)}>{row.t2108?.toFixed(1)}</Td>
                <Td className={pctAboveColor(row.pct_above_200sma)}>{row.pct_above_200sma?.toFixed(1)}</Td>
                <Td className={pctAboveColor(row.pct_above_50sma)}>{row.pct_above_50sma?.toFixed(1)}</Td>
                <Td className={pctAboveColor(row.pct_above_20sma)}>{row.pct_above_20sma?.toFixed(1)}</Td>
                <TdSep />
                <Td>{row.advances}</Td>
                <Td>{row.declines}</Td>
                <Td>{row.new_highs}</Td>
                <Td>{row.new_lows}</Td>
                <Td className={mcColor(row.mcclellan_osc)}>{row.mcclellan_osc?.toFixed(1)}</Td>
                <TdSep />
                <Td>{row.spx_close?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? '\u2014'}</Td>
                <Td>{row.universe_size?.toLocaleString()}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Helpers ──────────────────────────────────────────────

function Th({ children }) {
  return (
    <th className="px-2 py-1.5 text-right text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] whitespace-nowrap">
      {children}
    </th>
  )
}

function ThSep() {
  return <th className="w-px px-0 bg-[var(--color-border)]" />
}

function Td({ children, className = '' }) {
  return (
    <td className={`px-2 py-1 text-right font-mono tabular-nums text-[11px] ${className}`}>
      {children ?? '\u2014'}
    </td>
  )
}

function TdSep() {
  return <td className="w-px px-0 bg-[var(--color-border-light)]" />
}

function fmtDate(iso) {
  if (!iso) return '\u2014'
  const [, m, d] = iso.split('-')
  return `${parseInt(m)}/${parseInt(d)}`
}

/* Tints, not coloured type. The cell IS the mark and the number sits on it —
 * the same construction rsTone uses in the screener. It read
 * `bg-[color-mix(in_srgb,var(--color-profit)_10%,transparent)] text-[var(--color-profit)]`: raw Tailwind green off the
 * system entirely, plus the money palette on a market-half page. */
function tint(level) {
  if (level === 'high') return 'bg-[color-mix(in_srgb,var(--color-took)_28%,transparent)]'
  if (level === 'mid') return 'bg-[color-mix(in_srgb,var(--color-signal-caution)_20%,transparent)]'
  return 'bg-[color-mix(in_srgb,var(--color-refused)_26%,transparent)]'
}

function ratioColor(val) {
  if (val == null) return ''
  return tint(val >= 1.0 ? 'high' : val >= 0.5 ? 'mid' : 'low')
}

function pctAboveColor(val) {
  if (val == null) return ''
  return tint(val >= 60 ? 'high' : val >= 40 ? 'mid' : 'low')
}

function mcColor(val) {
  if (val == null) return ''
  return tint(val >= 0 ? 'high' : 'low')
}
