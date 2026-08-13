/**
 * Where a theme's three-month lead was actually earned.
 *
 * Design: Fluxus_Brand/visual/2026-08-10_TSF_PAGE_MAP.md §四.4
 *
 * `excess_3m` is one number for a quarter, and one number cannot tell a theme
 * that has been grinding ahead all quarter apart from one that did nothing for
 * two months and gapped last week. The pipeline has always decomposed it into
 * four disjoint windows — 0–1w, 1w–1m, 1m–3m, 3m–6m — and the front end has
 * never drawn them.
 *
 * Four bars on one shared scale, in time order, oldest at the left. Disjoint,
 * so they do not double-count: each is that stretch alone, chained apart from
 * the cumulative figures rather than differenced (see rs_engine).
 *
 * An unmeasured window is drawn as a dashed outline sitting ON the zero rule,
 * not as a gap and not as zero. Fourteen proxy themes have no local bars for
 * the far window, and «no reading» must not look like «flat» — that confusion
 * is the whole reason the column was worth drawing.
 *
 * Scale is shared across every window and every theme on screen, so a bar
 * twice as long is twice the number, in any row and any column.
 */

import { SEGMENTS } from './segments'

function Bar({ v, scale }) {
  if (v == null || !Number.isFinite(v)) {
    return (
      <span className="relative block h-[13px]" title="not measured">
        <i className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-[18px]
                      border border-dashed"
           style={{ borderColor: 'var(--color-untested)' }} />
      </span>
    )
  }
  const frac = Math.max(-1, Math.min(1, v / scale))
  const pos = v > 0
  return (
    <span className="relative block h-[13px]" title={`${(v * 100).toFixed(2)}%`}>
      <i className="absolute top-[-2px] bottom-[-2px] left-1/2 w-px
                    bg-[var(--color-text-muted)]" />
      <i className="absolute inset-y-0" style={{
        background: pos ? 'var(--color-took)' : 'var(--color-untested)',
        left: pos ? '50%' : `${50 + frac * 50}%`,
        width: `${Math.abs(frac) * 50}%`,
      }} />
    </span>
  )
}

export default function RsSegments({ rows, limit = 20 }) {
  if (!rows?.length) return null

  const shown = [...rows]
    .filter((r) => r.excess_3m != null)
    .sort((a, b) => b.excess_3m - a.excess_3m)
    .slice(0, limit)

  const scale = shown.reduce((m, r) =>
    SEGMENTS.reduce((mm, s) => {
      const v = r[s.key]
      return v == null || !Number.isFinite(v) ? mm : Math.max(mm, Math.abs(v))
    }, m), 0) || 1

  const unmeasured = shown.reduce((n, r) =>
    n + SEGMENTS.filter((s) => r[s.key] == null).length, 0)

  return (
    <section>
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1
                      pb-2 border-b border-[var(--color-v2-ink)]">
        <div className="flex items-baseline gap-3">
          <h2 className="text-[17px] font-semibold m-0"
              style={{ fontFamily: 'var(--font-cond)' }}>Where the lead was earned</h2>
          <span className="text-[11px] text-[var(--color-text-muted)]">
            four disjoint windows, oldest first — they do not overlap
          </span>
        </div>
        <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
          scale ±{(scale * 100).toFixed(0)}% · top {shown.length} by 3m
          {unmeasured > 0 && ` · ${unmeasured} windows unmeasured`}
        </span>
      </div>

      <div className="grid grid-cols-[minmax(120px,190px)_repeat(4,1fr)_64px] gap-x-3 gap-y-0
                      pt-2 pb-1 text-[10px] font-mono uppercase tracking-wider
                      text-[var(--color-text-muted)]">
        <span>Theme</span>
        {SEGMENTS.map((s) => (
          <span key={s.key} title={s.note}
                className={`text-center ${s.inQuarter ? '' : 'opacity-70'}`}
                style={s.inQuarter ? undefined
                  : { borderRight: '1px solid var(--color-border)', paddingRight: '10px' }}>
            {s.label}
          </span>
        ))}
        <span className="text-right">3m total</span>
      </div>

      {shown.map((r) => (
        <div key={r.group}
             className="grid grid-cols-[minmax(120px,190px)_repeat(4,1fr)_64px] gap-x-3
                        items-center py-[4px] hover:bg-[var(--color-hover-bg)]">
          <span className="text-[12.5px] truncate" title={r.tickers?.join(' · ')}>
            {r.group}
          </span>
          {SEGMENTS.map((s) => (
            <span key={s.key}
                  style={s.inQuarter ? undefined
                    : { borderRight: '1px solid var(--color-border)', paddingRight: '10px' }}>
              <Bar v={r[s.key]} scale={scale} />
            </span>
          ))}
          <span className="text-[12.5px] font-mono tabular-nums text-right">
            {r.excess_3m > 0 ? '+' : ''}{(r.excess_3m * 100).toFixed(1)}%
          </span>
        </div>
      ))}

      <div className="flex flex-wrap gap-x-5 gap-y-1 pt-3 text-[10px]
                      text-[var(--color-text-muted)]">
        <span className="flex items-center gap-1.5">
          <i className="block w-3 h-[9px]" style={{ background: 'var(--color-took)' }} />ahead of SPY
        </span>
        <span className="flex items-center gap-1.5">
          <i className="block w-3 h-[9px]" style={{ background: 'var(--color-untested)' }} />behind
        </span>
        <span className="flex items-center gap-1.5">
          <i className="block w-3 h-[9px] border border-dashed"
             style={{ borderColor: 'var(--color-untested)' }} />not measured
        </span>
        <span>
          · one scale across all four columns — a bar twice as long is twice the number.
          The windows do not overlap, but they do not sum either: excess returns compound
          rather than add, and <b>3–6m sits outside the three-month total</b> — that is what
          the rule after it marks. Read each bar as its own stretch, not as a term in an
          addition.
        </span>
      </div>
    </section>
  )
}
