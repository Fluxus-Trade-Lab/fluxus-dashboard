import { useState, useMemo } from 'react'
import { barStyle } from '../groups/ThemeBars'
import { useLanguage } from '../../i18n/LanguageContext'

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
      className={`bg-transparent border-none p-0 cursor-pointer text-[12.5px] font-inherit
                  pb-[1px] outline-none focus-visible:ring-1
                  ${on ? 'text-[var(--color-text-bold)] border-b border-solid border-[var(--color-text-bold)]'
                       : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'}
                  ${dim ? 'opacity-45' : ''}`}>
      {children}
    </button>
  )
}

/** A count earns ink in exactly three cases: the word is selected (the reader
 *  asked), the count is a measured zero (dimming alone cannot be told apart
 *  from "not loaded"), or the file has not arrived (an em-dash is not a zero).
 *  Thirteen grey numbers at rest were the overflow Andy pointed at — every
 *  positive count now lives in the word's tooltip instead. */
function Count({ n, on }) {
  if (n != null && n > 0 && !on) return null
  return (
    <span className="text-[10px] ml-[3px] text-[var(--color-text-muted)]">
      {n == null ? '—' : n === 0 ? '0' : n}
    </span>
  )
}

/** The chosen theme's ribbon — rendered only when measured, the same
 *  all-or-nothing rule the trajectory panel follows. Five dashed boxes in a
 *  control bar were decoration pretending to be honesty; the unmeasured case
 *  is stated in the theme's tooltip instead. */
function ThemeRibbon({ theme }) {
  const cells = theme?.ribbon?.length ? theme.ribbon : null
  if (!cells) return null
  return (
    <span className="inline-flex gap-[2px] ml-2 align-middle"
          title={`${theme.group} — five fortnights, oldest first: ${cells.map((c) => c.state).join(' · ')}`}>
      {cells.map((c, i) => (
        <i key={i} className="block w-[13px] h-[9px] rounded-[1px]" style={barStyle(c.state)} />
      ))}
    </span>
  )
}

/** One label style, one width, both rows — the bar reads as a grid, not a
 *  sentence. Groups on the second row are separated by hairlines, not labels
 *  floating mid-flow. */
function Lbl({ children }) {
  return (
    <span className="w-11 shrink-0 text-[10px] font-mono font-medium uppercase tracking-[.14em]
                     text-[var(--color-text-muted)]">{children}</span>
  )
}
function Divider() {
  return <span className="self-center h-3 w-px bg-[var(--color-border)]" />
}

export default function ScanBar({
  scans, scan, onScan,
  stateCounts, states, onToggleState,
  gates, gateCounts, onToggleGate,
  themes, chosen, onTheme, handoff,
  search, onSearch,
  receipt, hiddenNote, gateNote, gateOn, wideNote,
}) {
  const { t: tr } = useLanguage()
  const [themeQuery, setThemeQuery] = useState('')
  const [themeOpen, setThemeOpen] = useState(false)
  const [themeIdx, setThemeIdx] = useState(0)

  const themeMatches = useMemo(() => {
    const q = themeQuery.trim().toLowerCase()
    const list = q ? themes.filter((t) => t.group.toLowerCase().includes(q)) : themes
    return list.slice(0, 12)
  }, [themes, themeQuery])

  /** the chosen themes as rows; a name with no row is dropped upstream */
  const picked = chosen?.size ? themes.filter((t) => chosen.has(t.group)) : []

  return (
    <div className="sticky top-0 z-10 mb-4 border-b border-[var(--color-border)]
                    bg-[color-mix(in_srgb,var(--color-bg)_88%,transparent)] backdrop-blur-sm">
      <div className="flex items-baseline gap-x-4 gap-y-1 flex-wrap py-2">
        <Lbl>{tr('scr.bar.scan')}</Lbl>
        {scans.map((s) => (
          <Seg key={s.key} on={scan === s.key} dim={s.count === 0}
               onClick={() => onScan(s.key)}
               title={s.count === 0 ? `${s.label} — 0 today`
                    : s.count == null ? `${s.label} — not loaded yet`
                    : `${s.label} — ${s.count} names`}>
            {s.label}<Count n={s.count} on={scan === s.key} />
          </Seg>
        ))}
      </div>
      <div className="flex items-baseline gap-x-4 gap-y-1 flex-wrap pb-2">
        <Lbl>{tr('scr.bar.state')}</Lbl>
        {STATE_ORDER.map((st) => {
          const n = stateCounts ? (stateCounts[st] ?? 0) : null
          return (
            <Seg key={st} on={states.has(st)} onClick={() => onToggleState(st)}
                 title={n == null ? `${st} — not loaded yet` : `${st} — ${n} in this cut`}>
              <i className="inline-block w-[8px] h-[8px] rounded-[1px] mr-[5px] align-[-1px]"
                 style={barStyle(st)} />
              {tr(`state.${st}`)}<Count n={n} on={states.has(st)} />
            </Seg>
          )
        })}

        {/* The two gates the retired preset lists all shared. Same chip as the
            state words because they do the same job — narrow the cut — and a
            second control idiom for the same job is one idiom too many. The
            count is what the gate would KEEP, shown before it is on. */}
        <Divider />
        <Lbl>{tr('scr.bar.gate')}</Lbl>
        {['liquid', 'exHealth'].map((g) => (
          <Seg key={g} on={gates?.has(g)} onClick={() => onToggleGate(g)}
               title={tr(`scr.gate.${g}.why`)}>
            {tr(`scr.gate.${g}`)}<Count n={gateCounts?.[g] ?? null} on={gates?.has(g)} />
          </Seg>
        ))}

        <Divider />
        <span className="text-[10px] font-mono font-medium uppercase tracking-[.14em] text-[var(--color-text-muted)]">{tr('scr.bar.theme')}</span>
        {picked.length > 0 && picked.map((t) => (
          <span key={t.group} className="text-[12.5px] text-[var(--color-text-bold)]">
            {t.group}
            {/* the ribbon belongs to ONE theme, so it is drawn only when one is
                chosen — five fortnights of two themes side by side would read
                as one sequence */}
            {picked.length === 1 && <ThemeRibbon theme={t} />}
            <button type="button" onClick={() => onTheme(t.group)}
              className="bg-transparent border-none cursor-pointer text-[var(--color-text-muted)]
                         hover:text-[var(--color-text)] ml-1.5 p-0 text-[11px]"
              aria-label={tr('scr.bar.clearTheme')}>&times;</button>
          </span>
        ))}
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
              placeholder={picked.length
                ? tr('scr.bar.addTheme') === 'scr.bar.addTheme' ? '+ another' : tr('scr.bar.addTheme')
                : `${tr('scr.bar.allThemes')} · ${themes.length}`}
              className="bg-transparent border-none border-b border-solid border-[var(--color-border)]
                         text-[12.5px] text-[var(--color-text)] w-[130px] px-0.5 outline-none
                         placeholder:text-[var(--color-text-secondary)]" />
            {themeOpen && themeMatches.length > 0 && (
              <div className="absolute left-0 top-full mt-1 z-20 min-w-[220px] max-h-[300px] overflow-auto
                              bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg shadow-lg">
                {themeMatches.map((t, i) => (
                  // mousedown, not click — click fires after the input's blur closes the list
                  <div key={t.group}
                    onMouseDown={() => { onTheme(t.group); setThemeQuery(''); setThemeOpen(false); setThemeIdx(0) }}
                    onMouseEnter={() => setThemeIdx(i)}
                    className={`px-2.5 py-1 text-[12.5px] cursor-pointer flex items-baseline gap-2
                                ${chosen?.has(t.group) ? 'font-semibold' : ''}
                                ${i === themeIdx ? 'bg-[var(--color-hover-bg)]' : ''}`}>
                    <span>{t.group}</span>
                    <span className="text-[10px] text-[var(--color-text-muted)] ml-auto">{t.members}</span>
                  </div>
                ))}
              </div>
            )}
        </span>

        <Divider />
        <input value={search} onChange={(e) => onSearch(e.target.value)}
          placeholder="find ticker…"
          className="bg-transparent border-none border-b border-solid border-[var(--color-border)]
                     text-[12.5px] font-mono text-[var(--color-text)] w-[104px] px-0.5 outline-none
                     placeholder:text-[var(--color-text-muted)]" />

        <span className="ml-auto text-[11px] text-[var(--color-text-muted)]"
              title={hiddenNote || undefined}>{receipt}</span>
        {/* Whether the tradeable gate is in force. Stated either way: a filter
            the reader assumes is on, and is not, is worse than no filter. */}
        {gateNote && (
          <span className={`text-[10px] font-mono ${gateOn
            ? 'text-[var(--color-text-muted)]'
            : 'text-[var(--color-signal-caution)]'}`}>· {gateNote}</span>
        )}
      </div>

      {/* A filter this page did not set has to introduce itself. The chips
          above are already visible and already clearable — this only answers
          the question those chips raise on a page you have just arrived at:
          who chose these? It appears once, for the set it carried in, and
          never again for the same set. */}
      {handoff?.length > 0 && (
        <p className="m-0 mt-1.5 pl-3 text-[11px] leading-relaxed text-[var(--color-text-secondary)]
                      border-l border-dashed border-[var(--color-text-muted)]">
          Narrowed to the {handoff.length === 1 ? 'theme' : `${handoff.length} themes`} you were
          comparing on <a href="#/groups" className="text-inherit">Themes</a> &mdash;{' '}
          <b className="text-[var(--color-text-bold)]">{handoff.join(' · ')}</b>. Clear a chip above
          to widen it; this will not come back unless the picks over there change.
        </p>
      )}

      {/* An empty intersection is a reading, and this page will not swap the
          scan to make it non-empty. It says what the wider view holds and
          leaves the switch to the reader. */}
      {wideNote && (
        <p className="m-0 mt-1.5 text-[11px] leading-relaxed text-[var(--color-text-muted)]">
          These themes hold <b className="text-[var(--color-text-secondary)]">{wideNote.n}</b> tradeable
          names in all &mdash; the scan on top is what empties it.{' '}
          <button type="button" onClick={wideNote.onWiden}
                  className="bg-transparent border-none p-0 cursor-pointer underline
                             text-[var(--color-text-secondary)] hover:text-[var(--color-text)]">
            drop the scan
          </button>
        </p>
      )}
    </div>
  )
}
