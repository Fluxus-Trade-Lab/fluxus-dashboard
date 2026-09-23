/**
 * The morning walk's table — the register Andy asked for on 2026-09-23:
 * 「我们这个页面要求完全复刻traderslab，所以走的是卡片+表格。数据信息要多。」
 *
 * What that means here, taken from TradersLab's own Daily Market Breadth
 * Snapshot: small caps-and-tracking column heads, tabular figures, tight rows,
 * and the cell itself tinted by its reading — so a column is scanned rather
 * than read. Prose does not live in the table; a column that needs a sentence
 * to be understood carries a `title` instead.
 *
 * Tints use the site's own took/refused pair mixed onto the ground, the same
 * construction BreadthTable settled on, never raw green/red.
 */

/** Tint for a signed reading; `scale` is the value that earns a full tint. */
export function signTint(v, scale = 1) {
  if (v == null || !Number.isFinite(v) || !scale) return undefined
  const k = Math.max(-1, Math.min(1, v / scale))
  if (Math.abs(k) < 0.08) return undefined
  const pct = (8 + Math.abs(k) * 22).toFixed(0)
  const ink = k > 0 ? 'var(--color-took)' : 'var(--color-refused)'
  return { background: `color-mix(in srgb, ${ink} ${pct}%, transparent)` }
}

/** Tint for a 0–100 reading against a neutral mid-point. */
export function bandTint(v, mid = 50, span = 50) {
  if (v == null || !Number.isFinite(v)) return undefined
  return signTint(v - mid, span)
}

export const fmtPct = (v, d = 1) => (v == null || !Number.isFinite(v) ? '—' : `${v > 0 ? '+' : ''}${(v * 100).toFixed(d)}%`)
export const fmtNum = (v, d = 0) => (v == null || !Number.isFinite(v) ? '—' : v.toFixed(d))

/**
 * @param {{key:string,label:string,title?:string,align?:'left'|'right',
 *          get:(row:object)=>any, fmt?:(v:any,row:object)=>any,
 *          tint?:(v:any,row:object)=>object|undefined, cls?:string}[]} columns
 */
export default function ReadTable({ columns, rows, caption, empty = 'not measured', rowKey = (r, i) => i, dense, maxHeight }) {
  if (!rows?.length) return <p className="m-0 text-[13px] italic text-[var(--color-text-muted)]">{empty}</p>
  const pad = dense ? 'px-2 py-[3px]' : 'px-2 py-1'
  return (
    <div className="overflow-auto" style={maxHeight ? { maxHeight } : undefined}>
      <table className="w-full border-collapse text-[13px]">
        <thead className={maxHeight ? 'sticky top-0 z-10 bg-[var(--color-bg)]' : undefined}>
          <tr>
            {columns.map((c) => (
              <th key={c.key} title={c.title}
                  className={`${pad} text-[11px] font-mono font-medium uppercase tracking-[.08em] whitespace-nowrap
                              text-[var(--color-text-muted)] border-b border-[var(--color-text)]
                              ${c.align === 'right' ? 'text-right' : 'text-left'}`}>
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={rowKey(r, i)} className="border-b border-[var(--color-border-light)] hover:bg-[var(--color-hover-bg)]">
              {columns.map((c) => {
                const v = c.get(r)
                return (
                  <td key={c.key} style={c.tint?.(v, r)}
                      className={`${pad} whitespace-nowrap ${c.align === 'right' ? 'text-right tabular-nums' : ''} ${c.cls ?? ''}`}>
                    {c.fmt ? c.fmt(v, r) : (v ?? '—')}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      {caption && <p className="m-0 mt-1 text-[11px] text-[var(--color-text-muted)]">{caption}</p>}
    </div>
  )
}
