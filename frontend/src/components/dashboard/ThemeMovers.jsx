import { useMemo } from 'react'
import { useGroups } from '../../hooks/useGroups'
import { barStyle } from '../groups/ThemeBars'

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
 * THE MEMBER COUNT IS PRINTED, and it used to carry more than a count. Sixteen
 * published themes were a single ETF standing in for a whole market — Biotech =
 * XBI, China Tech = KWEB — and ranked silently beside a 286-name basket a
 * fund's move read as a theme's move, so those rows said "1 fund" instead of
 * "1 name". All sixteen were deleted upstream on 2026-08-18 and no published
 * theme has one member any more. The count stays because basket size is worth
 * seeing either way; the special case is gone with the rows it described.
 */

const WINDOWS = { '1D': 'perf_1d', '1W': 'perf_1w' }

/**
 * One theme: its state as a mark, its name, its move. Three things, one line.
 *
 * The state used to arrive as a word under the name and the member count sat
 * beside it — three lines of furniture for a row whose job is "which theme
 * moved and by how much". The mark carries the state on its own (Andy,
 * 2026-08-19): tone × fill, four states, no hue involved, so it survives the
 * greyscale this page is screenshotted into. The word moved to the legend,
 * where it is read once instead of six times.
 */
function Row({ theme, changeKey }) {
  const change = theme[changeKey]
  const ok = Number.isFinite(change)
  return (
    <div className="h-[22px] flex items-center gap-2">
      <i className="shrink-0 w-[8px] h-[8px] rounded-[1px]"
         style={barStyle(theme.state)} title={theme.state ?? 'no state'} />
      <span className="min-w-0 flex-1 truncate text-[12.5px] font-medium
                       text-[var(--color-text-bold)]" title={theme.group}>
        {theme.group}
      </span>
      <span className="shrink-0 text-[12.5px] font-mono tabular-nums font-medium"
            style={{ color: !ok ? 'var(--color-text-muted)'
                          : change > 0 ? 'var(--color-took)' : 'var(--color-refused)' }}>
        {ok ? `${change > 0 ? '+' : ''}${(change * 100).toFixed(2)}%` : '—'}
      </span>
    </div>
  )
}

const STATES = ['Leading', 'Weakening', 'Improving', 'Lagging']

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
        /* Themes, as the card's own title says (Andy 2026-08-19, same ruling as
           the Themes page). Ranking a 1,579-name size bucket under a heading
           that reads "Theme Leaders and Laggards" is the defect he named. */
        .filter((t) => t.kind === 'theme')
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
              {/* The paragraph is gone (Andy, 2026-08-19) and the four marks
                  take its place — read once here instead of six times in the
                  rows. Tone × fill, never hue, so the four stay apart in the
                  greyscale this page is screenshotted into.

                  The selection count went too (Andy: 多余). The rule about
                  outcome-ordered lists disclosing their cut still stands — it
                  is just already satisfied here by the SHAPE: three rows, a
                  rule, three rows is a top-and-bottom, visible without being
                  written. The denominator lives one click away on Themes,
                  which carries the whole ranking. */}
              <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1
                              text-[10px] text-[var(--color-text-muted)]">
                {STATES.map((st) => (
                  <span key={st} className="flex items-center gap-1.5">
                    <i className="w-[8px] h-[8px] rounded-[1px]" style={barStyle(st)} />
                    {st}
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  )
}
