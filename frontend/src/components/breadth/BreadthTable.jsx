import { orig } from './origCols'

/**
 * The archive — and, since 2026-09-11, the only place today's raw counts are
 * printed. Market monitor (15 tiles) and Classic breadth (9 tiles) were this
 * table's first row drawn a second and third time; Andy merged them here:
 * "并成一张表：今天钉在第一行、加粗；不上色，仍然按照原有的上色方式".
 * So today's row is pinned under the header and bold, the cell tints below
 * are the table's own, unchanged, and A/D line — the one number Classic
 * breadth carried that this table did not — is now a column.
 */
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
    <div className="bg-[var(--color-bg)] rounded-2xl overflow-hidden">
      {/* one scroll box for both axes, so the header and today's row can stick
          while the history scrolls under them */}
      <p className="px-3 pt-2 pb-1 m-0 text-[11px] text-[var(--color-text-muted)]">
        4%, ratio, 25%/qtr, month and NH/NL columns print Stockbee's own scans (NH/NL: common stocks).
        <span className="italic"> Grey italic</span> = the older count, shown where the author's column
        does not exist yet; it is never tinted and no vote reads it.
      </p>
      <div className="overflow-auto max-h-[460px]">
        <table className="w-full text-[13px] border-separate border-spacing-0">
          <thead className="sticky top-0 z-20">
            <tr className="bg-[var(--color-bg)]">
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
              <Th title="Nasdaq-100 pool, T-0923-03 -- the standard reading; McCl above is the legacy full-universe column, kept for archive continuity">McCl (NDX)</Th>
              <Th title="McClellan Summation Index, Nasdaq-100 pool">MCSI</Th>
              <Th>A/D line</Th>
              <ThSep />
              <Th>SPX</Th>
              <Th>Worden</Th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, i) => (
              <tr
                key={row.date}
                className={`hover:bg-[var(--color-hover-bg)] ${
                  i === 0 ? 'today sticky top-[29px] z-10 bg-[var(--color-bg)] font-semibold text-[var(--color-text-bold)]'
                    : i % 2 === 1 ? 'bg-[var(--color-surface-alt)]/50' : ''
                }`}
              >
                <Td className="text-[var(--color-text-secondary)] whitespace-nowrap">{fmtDate(row.date)}</Td>
                <OTd row={row} k="up_4pct" />
                <OTd row={row} k="down_4pct" />
                <OTd row={row} k="ratio_5d" fmt={(v) => v.toFixed(2)} tone={(v) => ratioColor(v, i === 0, ENGINE_LINES.ratio5)} />
                <OTd row={row} k="ratio_10d" fmt={(v) => v.toFixed(2)} tone={(v) => ratioColor(v, i === 0, ENGINE_LINES.ratio10)} />
                <TdSep />
                <OTd row={row} k="up_25pct_qtr" />
                <OTd row={row} k="down_25pct_qtr" />
                <OTd row={row} k="up_25pct_month" />
                <OTd row={row} k="down_25pct_month" />
                <OTd row={row} k="up_50pct_month" />
                <OTd row={row} k="down_50pct_month" />
                <TdSep />
                <Td className={t2108Color(row.t2108, i === 0)}>{row.t2108?.toFixed(1)}</Td>
                <Td className={pct200Color(row.pct_above_200sma, i === 0)}>{row.pct_above_200sma?.toFixed(1)}</Td>
                <Td>{row.pct_above_50sma?.toFixed(1)}</Td>
                <Td>{row.pct_above_20sma?.toFixed(1)}</Td>
                <TdSep />
                <Td>{row.advances}</Td>
                <Td>{row.declines}</Td>
                <OTd row={row} k="new_highs" />
                <OTd row={row} k="new_lows" />
                <Td className={mcColor(row.mcclellan_osc, i === 0)}>{row.mcclellan_osc?.toFixed(1)}</Td>
                <Td className={mcColor(row.mcclellan_osc_ndx, i === 0)}>{row.mcclellan_osc_ndx?.toFixed(1)}</Td>
                <Td className={mcColor(row.mcclellan_summation_ndx, i === 0)}>{row.mcclellan_summation_ndx?.toFixed(0)}</Td>
                <Td>{row.ad_line?.toLocaleString()}</Td>
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
    <th className="px-2 py-1.5 text-right text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] whitespace-nowrap
                   bg-[var(--color-bg)] border-b border-[var(--color-text)]">
      {children}
    </th>
  )
}

function ThSep() {
  return <th className="w-px px-0 bg-[var(--color-border)] border-b border-[var(--color-text)]" />
}

function Td({ children, className = '' }) {
  return (
    <td className={`px-2 py-1 text-right font-mono tabular-nums text-[11px] border-b border-[var(--color-border-light)]
                    [tr.today_&]:border-b-[var(--color-text)] ${className}`}>
      {children ?? '\u2014'}
    </td>
  )
}

/** A count with an author-definition column: that value, or the old one greyed. */
function OTd({ row, k, fmt = (v) => v, tone }) {
  const { v, old } = orig(row, k)
  if (v == null) return <Td />
  if (old) {
    return (
      <Td className="italic text-[var(--color-text-muted)] font-normal">
        <span title="older count — the author's column starts later">{fmt(v)}</span>
      </Td>
    )
  }
  return <Td className={tone ? tone(v) : ''}>{fmt(v)}</Td>
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
function tint(level, solid) {
  // The pinned row sits over rows scrolling beneath it, so its tints are mixed
  // onto the ground colour instead of onto transparent — same hue and weight,
  // just opaque. Every other row keeps the translucent tint it always had.
  if (solid) {
    if (level === 'high') return 'bg-[color-mix(in_srgb,var(--color-took)_28%,var(--color-bg))]'
    if (level === 'mid') return 'bg-[color-mix(in_srgb,var(--color-signal-caution)_20%,var(--color-bg))]'
    return 'bg-[color-mix(in_srgb,var(--color-refused)_26%,var(--color-bg))]'
  }
  if (level === 'high') return 'bg-[color-mix(in_srgb,var(--color-took)_28%,transparent)]'
  if (level === 'mid') return 'bg-[color-mix(in_srgb,var(--color-signal-caution)_20%,transparent)]'
  return 'bg-[color-mix(in_srgb,var(--color-refused)_26%,transparent)]'
}

/* Each tint is the engine's own vote on that column, not a ruler of ours:
 * `pipeline/screeners/breadth_signals.py::THRESHOLDS`, copied here because the
 * votes ship for today only and the table colours a hundred rows. The copy is
 * pinned by breadthTableLines.test.js, which reads the Python file — before
 * that, one 60/40 ruler painted all four %-columns and %>200 (engine 50/30)
 * disagreed with the engine on 33 of 100 rows. Columns the engine has no rule
 * for (%>50, %>20) carry no tint. */
export const ENGINE_LINES = {
  // 5-day: 1.0/0.5 (Stockbee gives no 5-day line; ours). 10-day: Stockbee 2010-05,
  // "goes above 2 ... bullish breadth thrust", "below .5 ... bearish" -- strict.
  ratio5: { bull: 1.0, bear: 0.5 },
  ratio10: { bull: 2.0, bear: 0.5, strict: true },
  pct200: { bull: 50, bear: 30 },
  t2108: { strongLo: 60, weakHi: 40, oversold: 20, overbought: 80 },
}

function ratioColor(val, solid, t) {
  if (val == null) return ''
  const bull = t.strict ? val > t.bull : val >= t.bull
  return tint(bull ? 'high' : val < t.bear ? 'low' : 'mid', solid)
}

function pct200Color(val, solid) {
  if (val == null) return ''
  const t = ENGINE_LINES.pct200
  return tint(val >= t.bull ? 'high' : val < t.bear ? 'low' : 'mid', solid)
}

// Engine: 60–80 bull, 20–40 bear, anything else neutral (the <20 / >80
// extremes are overrides, not zone votes).
export function t2108Level(val) {
  const z = ENGINE_LINES.t2108
  if (val < z.oversold || val > z.overbought) return 'mid'
  if (val >= z.strongLo) return 'high'
  if (val <= z.weakHi) return 'low'
  return 'mid'
}

function t2108Color(val, solid) {
  if (val == null) return ''
  return tint(t2108Level(val), solid)
}

function mcColor(val, solid) {
  if (val == null) return ''
  return tint(val >= 0 ? 'high' : 'low', solid)
}
