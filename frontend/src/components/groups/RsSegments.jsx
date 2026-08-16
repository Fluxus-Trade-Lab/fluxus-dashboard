/**
 * Where a theme's three-month lead was actually earned.
 *
 * Design: Fluxus_Brand/visual/2026-08-10_TSF_PAGE_MAP.md §四.4
 *
 * `excess_3m` is one number for a quarter, and one number cannot tell a theme
 * that has been grinding ahead all quarter apart from one that did nothing for
 * two months and gapped last week. The pipeline decomposes it into disjoint
 * windows; this draws the three that fall inside the quarter — 1m–3m, 1w–1m,
 * 0–1w. The fourth, 3m–6m, is outside the total this page ranks on and is not
 * drawn here or in the trajectory panel.
 *
 * Three bars on one shared scale, in time order, oldest at the left. Disjoint,
 * so they do not double-count: each is that stretch alone, chained apart from
 * the cumulative figures rather than differenced (see rs_engine).
 *
 * 2026-08-16 — SAME UNITS AS THE TRAJECTORY PANEL. This drew the stretches'
 * raw totals over four windows while Compare drew three windows as excess per
 * session, so one page said High Octane's 1–3m was +34.7% in one place and
 * +0.83% in another, with nothing connecting them. Both are now per session,
 * and 3–6m is gone from both: segments.js has always marked it outside the
 * quarter this page ranks on.
 *
 * That makes the two views the same sentence at two volumes — Compare reads
 * three themes closely, this reads ten at a glance — rather than two claims a
 * reader has to reconcile.
 *
 * An unmeasured window is drawn as a dashed outline sitting ON the zero rule,
 * not as a gap and not as zero. Fourteen proxy themes have no local bars for
 * the far window, and «no reading» must not look like «flat» — that confusion
 * is the whole reason the column was worth drawing.
 *
 * Scale is shared across every window and every theme on screen, so a bar
 * twice as long is twice the number, in any row and any column.
 */

import { QUARTER_SEGMENTS, ratePerSession } from './segments'

function Bar({ v, scale, raw, sessions }) {
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
    <span className="relative block h-[13px]"
          title={`${(v * 100).toFixed(2)}% per session`
            + (Number.isFinite(raw) ? ` · ${sessions} sessions, ${raw > 0 ? '+' : ''}${(raw * 100).toFixed(1)}% over the stretch` : '')}>
      <i className="absolute top-[-2px] bottom-[-2px] left-1/2 w-px
                    bg-[var(--color-text-muted)]" />
      <i className="absolute inset-y-0" style={{
        background: pos ? 'var(--color-took)' : 'var(--color-refused)',
        left: pos ? '50%' : `${50 + frac * 50}%`,
        width: `${Math.abs(frac) * 50}%`,
      }} />
    </span>
  )
}

export default function RsSegments({ rows, limit = 10 }) {
  if (!rows?.length) return null

  const shown = [...rows]
    .filter((r) => r.excess_3m != null)
    .sort((a, b) => b.excess_3m - a.excess_3m)
    .slice(0, limit)

  const scale = shown.reduce((m, r) =>
    QUARTER_SEGMENTS.reduce((mm, s) => {
      const v = ratePerSession(r, s)
      return v == null ? mm : Math.max(mm, Math.abs(v))
    }, m), 0) || 1

  const unmeasured = shown.reduce((n, r) =>
    n + QUARTER_SEGMENTS.filter((s) => ratePerSession(r, s) == null).length, 0)

  return (
    <section>
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1
                      pb-2 border-b border-[var(--color-v2-ink)]">
        <div className="flex items-baseline gap-3">
          <h2 className="text-[17px] font-semibold m-0"
              style={{ fontFamily: 'var(--font-cond)' }}>Where the lead was earned</h2>
          <span className="text-[11px] text-[var(--color-text-muted)]">
            the quarter's three disjoint stretches, oldest first · excess per session
          </span>
        </div>
        <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
          scale ±{(scale * 100).toFixed(2)}%/session · top {shown.length} by 3m
          {unmeasured > 0 && ` · ${unmeasured} windows unmeasured`}
        </span>
      </div>

      <div className="grid grid-cols-[minmax(120px,190px)_repeat(4,1fr)_64px] gap-x-3 gap-y-0
                      pt-2 pb-1 text-[10px] font-mono uppercase tracking-wider
                      text-[var(--color-text-muted)]">
        <span>Theme</span>
        {QUARTER_SEGMENTS.map((s) => (
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
          {QUARTER_SEGMENTS.map((s) => (
            <span key={s.key}>
              {/* the rate, not the stretch's total — the same number the
                  trajectory panel plots, so the two cannot disagree */}
              <Bar v={ratePerSession(r, s)} scale={scale}
                   raw={r[s.key]} sessions={s.sessions} />
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
          <i className="block w-3 h-[9px] ml-3" style={{ background: 'var(--color-refused)' }} />behind
        </span>
        <span className="flex items-center gap-1.5">
          <i className="block w-3 h-[9px]" style={{ background: 'var(--color-untested)' }} />behind
        </span>
        <span className="flex items-center gap-1.5">
          <i className="block w-3 h-[9px] border border-dashed"
             style={{ borderColor: 'var(--color-untested)' }} />not measured
        </span>
        <span>
          · one scale across all three columns — a bar twice as long is twice the number.
          Each bar is that stretch&rsquo;s excess <b>divided by its own length</b>, which is
          the only way a five-session week and a forty-two-session run compare: on the
          totals the short stretch is always the small bar, and every theme looks like it
          is fading. Same units as the trajectory panel above. The stretches do not
          overlap, and they do not sum either — excess returns compound rather than add,
          so read each bar as its own stretch, not as a term in an addition.
        </span>
      </div>
    </section>
  )
}
