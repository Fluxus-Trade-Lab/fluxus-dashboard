import { useMemo } from 'react'
import { useGroups } from '../../hooks/useGroups'
import StateBadge from '../groups/StateBadge'

/**
 * Themes, moved today and this week.
 *
 * The brief asks this page for "the one-day and one-week change in sectors AND
 * themes"; only the sectors half existed. Themes come from groups.json, which
 * this page did not load — it is 1.5MB against breadth.json's 140KB, so it
 * arrives on its own through useGroups rather than inside the blocking payload
 * every route waits on.
 *
 * Deliberately built on the Leaders-and-Laggards grammar rather than a new one:
 * on this page a theme and a sector answer the same question at two grains, and
 * two shapes for one question would claim a difference that is not there.
 *
 * ONE THING THE SECTOR CARD DOES NOT HAVE TO SAY. Three of the published
 * themes have `members == 1`: they are one ETF standing in for a whole theme
 * (Biotech = XBI, Taiwan = EWT, Healthcare = XLV). Ranked silently beside a
 * 286-name basket, a fund's move reads as a theme's move. The member count
 * carries that, and a single-fund row says "1 fund" rather than "1 name".
 */

const WINDOWS = { '1D': 'perf_1d', '1W': 'perf_1w' }

function Row({ theme, changeKey }) {
  const change = theme[changeKey]
  const ok = Number.isFinite(change)
  const proxy = theme.members === 1

  return (
    <div className="h-[34px] flex items-center gap-2.5">
      <span className="min-w-0 flex-1">
        <span className="block text-[12.5px] font-medium leading-[13px] truncate
                         text-[var(--color-text-bold)]" title={theme.group}>
          {theme.group}
        </span>
        <span className="flex items-center gap-2 text-[10px] leading-[13px]
                         text-[var(--color-text-muted)]">
          {/* the second channel on the proxy problem: not a colour, a noun */}
          <span title={proxy
            ? 'One fund standing in for the whole theme — its reading is the fund’s, exact by construction but not a basket'
            : `${theme.members} names in this basket`}>
            {proxy ? '1 fund' : `${theme.members} names`}
          </span>
          <StateBadge state={theme.state} />
        </span>
      </span>
      <span className="shrink-0 text-[12.5px] font-mono tabular-nums font-medium"
            style={{ color: !ok ? 'var(--color-text-muted)'
                          : change > 0 ? 'var(--color-took)' : 'var(--color-refused)' }}>
        {ok ? `${change > 0 ? '+' : ''}${(change * 100).toFixed(2)}%` : '—'}
      </span>
    </div>
  )
}

function Column({ label, rows, changeKey }) {
  return (
    <div>
      {label && (
        <h4 className="text-[10px] font-mono font-medium uppercase tracking-[.2em]
                       text-[var(--color-text-muted)] mb-1.5">{label}</h4>
      )}
      {rows.map((t) => <Row key={t.group} theme={t} changeKey={changeKey} />)}
    </div>
  )
}

export default function ThemeMovers({ limit = 3 }) {
  const { themes, loading, error } = useGroups()

  const cols = useMemo(() => {
    return Object.entries(WINDOWS).map(([w, changeKey]) => {
      const sorted = themes
        .filter((t) => t.measurable && Number.isFinite(t[changeKey]))
        .sort((a, b) => b[changeKey] - a[changeKey])
      return {
        w, changeKey, ranked: sorted.length,
        leaders: sorted.slice(0, limit),
        laggards: sorted.slice(-limit).reverse(),
      }
    })
  }, [themes, limit])

  const ranked = cols[0]?.ranked ?? 0

  return (
    <div className="flex flex-col min-w-0">
      <div className="text-[17px] font-semibold leading-tight text-[var(--color-text-bold)]
                      mt-4 mb-3 px-1">
        Theme Leaders and Laggards
      </div>
      <section className="bg-[var(--color-surface)] rounded-3xl overflow-hidden
                          flex flex-col flex-1 pt-4">
        <div className="px-5 pb-4 flex-1 flex flex-col">
          {loading ? (
            <p className="m-0 py-6 text-[11px] text-[var(--color-text-muted)]">
              Loading the theme layer&hellip;
            </p>
          ) : error || !ranked ? (
            /* not zero, and not an empty grid pretending to be a full one */
            <p className="m-0 py-6 text-[11px] leading-relaxed text-[var(--color-text-muted)]">
              {error ? 'groups.json did not load — themes not measured this session.'
                     : 'No theme carried a measurable move for these windows — not measured.'}
            </p>
          ) : (
            <>
              <div className="grid gap-x-4"
                   style={{ gridTemplateColumns: `repeat(${cols.length}, minmax(0, 1fr))` }}>
                {cols.map((c) => (
                  <Column key={`${c.w}-lead`} label={c.w} rows={c.leaders}
                          changeKey={c.changeKey} />
                ))}
              </div>
              <i className="block h-px bg-[var(--color-border-light)] my-3" />
              <div className="grid gap-x-4"
                   style={{ gridTemplateColumns: `repeat(${cols.length}, minmax(0, 1fr))` }}>
                {cols.map((c) => (
                  <Column key={`${c.w}-lag`} label={null} rows={c.laggards}
                          changeKey={c.changeKey} />
                ))}
              </div>
              {/* a list sorted by outcome discloses its own selection —
                  six of N, and N is stated */}
              <p className="m-0 mt-3 text-[10px] leading-snug text-[var(--color-text-muted)]">
                Top and bottom {limit} of {ranked} published themes, ranked on each window
                separately. Provisional themes — the ones whose members have not been shown
                to co-move — are not ranked here.
              </p>
            </>
          )}
        </div>
      </section>
    </div>
  )
}
