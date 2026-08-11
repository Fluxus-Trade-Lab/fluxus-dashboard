import { useState, useMemo } from 'react'
import { barStyle } from '../groups/ThemeBars'

/**
 * The control bar: four vocabularies, all selection, no query construction.
 *
 * Scan, state, theme, name — each selector offers only words the pipeline
 * already speaks, and the row set is their intersection. There is nothing to
 * type except a ticker, which is itself a word from the universe. The min/max
 * filter panel this replaces let a reader build a question the pipeline had
 * never answered; this bar only lets them choose between answers that already
 * exist.
 *
 * When a theme is chosen, its fortnight ribbon appears here — on the bar, not
 * in every row. The ribbon is a property of the theme, and a stock belongs to
 * 2-3 themes at the median, so a per-row copy would need a tie-break rule the
 * pipeline has not defined. One ribbon beside the theme's name says the same
 * thing once, honestly.
 */

const STATE_ORDER = ['Leading', 'Weakening', 'Improving', 'Lagging']

function Seg({ on, dim, onClick, children, title }) {
  return (
    <button type="button" onClick={onClick} title={title}
      className={`bg-transparent border-none p-0 cursor-pointer text-[11.5px] font-inherit
                  pb-[1px] outline-none focus-visible:ring-1
                  ${on ? 'text-[var(--color-text-bold)] border-b border-solid border-[var(--color-text-bold)]'
                       : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'}
                  ${dim ? 'opacity-45' : ''}`}>
      {children}
    </button>
  )
}

/** null = the file has not arrived; 0 = it arrived and found nothing.
 *  Different claims, different marks — an em-dash is not a zero. "0 today"
 *  belongs to scans (a session reading); a facet count's zero is just 0. */
function Count({ n, zeroLabel = '0' }) {
  return (
    <span className="text-[10px] ml-[3px] text-[var(--color-text-muted)]">
      {n == null ? '—' : n === 0 ? zeroLabel : n}
    </span>
  )
}

/** Five ribbon cells for the chosen theme — dashed while the archive is short. */
function ThemeRibbon({ theme }) {
  const cells = theme?.ribbon?.length ? theme.ribbon : null
  return (
    <span className="inline-flex gap-[2px] ml-2 align-middle"
          title={cells
            ? `${theme.group} — five fortnights, oldest first: ${cells.map((c) => c.state).join(' · ')}`
            : `${theme?.group} — state history not measured yet; the archive is still accumulating`}>
      {(cells ?? Array.from({ length: 5 })).map((c, i) => (
        <i key={i} className="block w-[13px] h-[9px] rounded-[1px]"
           style={c ? barStyle(c.state)
                    : { border: '1px dashed var(--color-text-muted)', opacity: 0.5 }} />
      ))}
    </span>
  )
}

export default function ScanBar({
  scans, scan, onScan,
  stateCounts, states, onToggleState,
  themes, theme, onTheme,
  search, onSearch,
  receipt,
}) {
  const [themeQuery, setThemeQuery] = useState('')
  const [themeOpen, setThemeOpen] = useState(false)
  const [themeIdx, setThemeIdx] = useState(0)

  const themeMatches = useMemo(() => {
    const q = themeQuery.trim().toLowerCase()
    const list = q ? themes.filter((t) => t.group.toLowerCase().includes(q)) : themes
    return list.slice(0, 12)
  }, [themes, themeQuery])

  const chosen = theme ? themes.find((t) => t.group === theme) : null

  return (
    <div className="sticky top-0 z-10 mb-4 border-b border-[var(--color-border)]
                    bg-[color-mix(in_srgb,var(--color-bg)_88%,transparent)] backdrop-blur-sm">
      <div className="flex items-baseline gap-x-5 gap-y-1 flex-wrap py-2">
        <span className="text-[9px] font-mono uppercase tracking-[.14em] text-[var(--color-text-muted)]">Scan</span>
        {scans.map((s) => (
          <Seg key={s.key} on={scan === s.key} dim={s.count === 0}
               onClick={() => onScan(s.key)}
               title={s.count === 0 ? `${s.label} found nothing this session`
                    : s.count == null ? `${s.label} has not loaded yet` : undefined}>
            {s.label}<Count n={s.count} zeroLabel="0 today" />
          </Seg>
        ))}
      </div>
      <div className="flex items-baseline gap-x-5 gap-y-1 flex-wrap pb-2">
        <span className="text-[9px] font-mono uppercase tracking-[.14em] text-[var(--color-text-muted)]">State</span>
        {STATE_ORDER.map((st) => (
          <Seg key={st} on={states.has(st)} onClick={() => onToggleState(st)}>
            <i className="inline-block w-[8px] h-[8px] rounded-[1px] mr-[5px] align-[-1px]"
               style={barStyle(st)} />
            {st}<Count n={stateCounts ? (stateCounts[st] ?? 0) : null} />
          </Seg>
        ))}

        <span className="text-[9px] font-mono uppercase tracking-[.14em] text-[var(--color-text-muted)] ml-2">Theme</span>
        {chosen ? (
          <span className="text-[11.5px] text-[var(--color-text-bold)]">
            {chosen.group}
            <ThemeRibbon theme={chosen} />
            <button type="button" onClick={() => onTheme(null)}
              className="bg-transparent border-none cursor-pointer text-[var(--color-text-muted)]
                         hover:text-[var(--color-text)] ml-1.5 p-0 text-[11px]"
              aria-label="clear theme">×</button>
          </span>
        ) : (
          <span className="relative">
            <input value={themeQuery}
              onChange={(e) => { setThemeQuery(e.target.value); setThemeOpen(true); setThemeIdx(0) }}
              onFocus={() => setThemeOpen(true)}
              onBlur={() => setThemeOpen(false)}
              onKeyDown={(e) => {
                if (e.key === 'ArrowDown') {
                  e.preventDefault(); setThemeIdx((i) => Math.min(i + 1, themeMatches.length - 1))
                } else if (e.key === 'ArrowUp') {
                  e.preventDefault(); setThemeIdx((i) => Math.max(i - 1, 0))
                } else if (e.key === 'Escape') {
                  setThemeOpen(false)
                } else if (e.key === 'Enter' && themeOpen && themeMatches.length &&
                           (themeQuery.trim() || themeIdx > 0)) {
                  // an empty query with no arrowing has expressed no choice —
                  // Enter must not commit the alphabetically first theme
                  const pick = themeMatches[Math.min(themeIdx, themeMatches.length - 1)]
                  onTheme(pick.group); setThemeQuery(''); setThemeOpen(false); setThemeIdx(0)
                }
              }}
              placeholder={`all themes · ${themes.length}`}
              className="bg-transparent border-none border-b border-solid border-[var(--color-border)]
                         text-[11.5px] text-[var(--color-text)] w-[130px] px-0.5 outline-none
                         placeholder:text-[var(--color-text-muted)]" />
            {themeOpen && themeMatches.length > 0 && (
              <div className="absolute left-0 top-full mt-1 z-20 min-w-[220px] max-h-[300px] overflow-auto
                              bg-[var(--color-surface)] border border-[var(--color-border)] rounded shadow-lg">
                {themeMatches.map((t, i) => (
                  // mousedown, not click — click fires after the input's blur closes the list
                  <div key={t.group}
                    onMouseDown={() => { onTheme(t.group); setThemeQuery(''); setThemeOpen(false); setThemeIdx(0) }}
                    onMouseEnter={() => setThemeIdx(i)}
                    className={`px-2.5 py-1 text-[11.5px] cursor-pointer flex items-baseline gap-2
                                ${i === themeIdx ? 'bg-[var(--color-hover-bg)]' : ''}`}>
                    <span>{t.group}</span>
                    <span className="text-[9.5px] text-[var(--color-text-muted)] ml-auto">{t.members}</span>
                  </div>
                ))}
              </div>
            )}
          </span>
        )}

        <span className="text-[9px] font-mono uppercase tracking-[.14em] text-[var(--color-text-muted)] ml-2">Find</span>
        <input value={search} onChange={(e) => onSearch(e.target.value)}
          placeholder="ticker…"
          className="bg-transparent border-none border-b border-solid border-[var(--color-border)]
                     text-[11.5px] font-mono text-[var(--color-text)] w-[90px] px-0.5 outline-none
                     placeholder:text-[var(--color-text-muted)]" />

        <span className="ml-auto text-[10.5px] text-[var(--color-text-muted)]">{receipt}</span>
      </div>
    </div>
  )
}
