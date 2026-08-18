import { useEffect, useMemo, useRef, useState } from 'react'
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

/**
 * A vocabulary, collapsed.
 *
 * Andy, 2026-08-18: 这些变成 dropdown 占的空间太多了. The bar spent two full
 * rows printing nine scan words and six filter words that are, on any given
 * morning, mostly not the one you want — and it sits above the chart and the
 * table, so those two rows cost every page view. A menu spends one line on the
 * word you HAVE chosen and none on the eight you have not.
 *
 * WHAT THE COLLAPSE MUST NOT COST is the counts. The number beside a word is
 * the whole reason these are selectors and not a query builder: it answers
 * "what does turning this on cost me" before it is on. They survive inside the
 * panel, where there is now room to print every one of them rather than only
 * the selected and the zeroes.
 *
 * The trigger states its current value, so a bar at rest still says what it is
 * filtering by — a collapsed control that shows only its label would hide the
 * filter, which is the failure mode this page has been careful about all round.
 */
function Menu({ label, summary, dim, children }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    if (!open) return
    const away = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    const esc = (e) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', away)
    document.addEventListener('keydown', esc)
    return () => {
      document.removeEventListener('mousedown', away)
      document.removeEventListener('keydown', esc)
    }
  }, [open])

  return (
    <span className="relative" ref={ref}>
      <button type="button" onClick={() => setOpen((o) => !o)}
              aria-expanded={open} aria-haspopup="true"
              className="flex items-baseline gap-1.5 bg-transparent border-none p-0 cursor-pointer
                         outline-none focus-visible:ring-1">
        <span className="text-[10px] font-mono font-medium uppercase tracking-[.14em]
                         text-[var(--color-text-muted)]">{label}</span>
        <span className={`text-[12.5px] pb-[1px] border-b border-solid
                          ${dim ? 'text-[var(--color-text-muted)] border-[var(--color-border)]'
                                : 'text-[var(--color-text-bold)] border-[var(--color-text-bold)]'}`}>
          {summary}
        </span>
        {/* 10px, not 9 — the type floor applies to a caret as much as to a
            word, and this is the same glyph idiom the table's evidence toggle
            already uses. */}
        <span className="text-[10px] leading-none text-[var(--color-text-muted)]" aria-hidden="true">
          {open ? '\u25b4' : '\u25be'}
        </span>
      </button>
      {open && (
        <div className="absolute left-0 top-full mt-1.5 z-30 min-w-[236px] max-h-[340px] overflow-auto
                        rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]
                        py-1 shadow-lg"
             onClick={(e) => { if (e.target.closest('[data-close]')) setOpen(false) }}>
          {children}
        </div>
      )}
    </span>
  )
}

/**
 * One row of a menu: the word, its mark, and its count — always the count,
 * because in here there is room and the number is the point.
 */
function Item({ on, dim, onClick, title, mark, children, n, close }) {
  return (
    <button type="button" onClick={onClick} title={title} data-close={close ? '' : undefined}
            className={`w-full flex items-baseline gap-2 px-3 py-[5px] text-left text-[12.5px]
                        bg-transparent border-none cursor-pointer font-inherit
                        hover:bg-[var(--color-hover-bg)]
                        ${on ? 'text-[var(--color-text-bold)] font-semibold'
                             : 'text-[var(--color-text-secondary)]'}
                        ${dim ? 'opacity-45' : ''}`}>
      {/* the tick takes the row's own colour rather than the muted grey it
          started in: a mark fainter than the word it marks reads as
          decoration. The width is reserved either way, so the labels stay in
          one column whether or not anything is selected. */}
      <span className="w-3 shrink-0 text-[10px] leading-none">{on ? '\u2713' : ''}</span>
      {mark}
      <span className="min-w-0 flex-1 truncate">{children}</span>
      <span className="shrink-0 text-[10px] font-mono tabular-nums text-[var(--color-text-muted)]">
        {n == null ? '\u2014' : n}
      </span>
    </button>
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

  const activeScan = scans.find((x) => x.key === scan) ?? scans[0]

  /** the chosen themes as rows; a name with no row is dropped upstream */
  const picked = chosen?.size ? themes.filter((t) => chosen.has(t.group)) : []

  return (
    // z-30, not z-10. The table's own sticky header is z-10 inside its scroll
    // box and comes LATER in the document, so at equal weight it painted over
    // this bar's open menu — the first row of the state list disappeared under
    // the column names. A control that opens over the thing it controls has to
    // outrank it, and the bar is the outer stacking context, so the number has
    // to live here rather than on the panel inside it.
    <div className="sticky top-0 z-30 mb-4 border-b border-[var(--color-border)]
                    bg-[color-mix(in_srgb,var(--color-bg)_88%,transparent)] backdrop-blur-sm">
      {/* ONE ROW. Scan, state and gate are menus; theme keeps its chips
          because a chosen theme is a thing you need to see, not a value you
          need to recall, and the ticker search stays open because it is the
          one control with nothing to choose from. */}
      <div className="flex items-baseline gap-x-5 gap-y-2 flex-wrap py-2">
        <Menu label={tr('scr.bar.scan')} summary={activeScan?.label ?? '\u2014'}>
          {scans.map((s) => (
            <Item key={s.key} on={scan === s.key} dim={s.count === 0} close
                  onClick={() => onScan(s.key)} n={s.count}
                  title={s.count === 0 ? `${s.label} \u2014 0 today`
                       : s.count == null ? `${s.label} \u2014 not loaded yet`
                       : `${s.label} \u2014 ${s.count} names`}>
              {s.label}
            </Item>
          ))}
        </Menu>

        <Menu label={tr('scr.bar.state')} dim={!states.size}
              summary={states.size
                ? [...STATE_ORDER].filter((x) => states.has(x)).map((x) => tr(`state.${x}`)).join(' + ')
                : tr('scr.bar.anyState') === 'scr.bar.anyState' ? 'any' : tr('scr.bar.anyState')}>
          {STATE_ORDER.map((st) => {
            const n = stateCounts ? (stateCounts[st] ?? 0) : null
            return (
              <Item key={st} on={states.has(st)} onClick={() => onToggleState(st)} n={n}
                    title={n == null ? `${st} \u2014 not loaded yet` : `${st} \u2014 ${n} in this cut`}
                    mark={<i className="inline-block w-[8px] h-[8px] rounded-[1px] shrink-0"
                             style={barStyle(st)} />}>
                {tr(`state.${st}`)}
              </Item>
            )
          })}
        </Menu>

        {/* The two gates the retired preset lists all shared. The count is what
            the gate would KEEP, shown before it is on. */}
        <Menu label={tr('scr.bar.gate')} dim={!gates?.size}
              summary={gates?.size
                ? ['liquid', 'exHealth'].filter((g) => gates.has(g)).map((g) => tr(`scr.gate.${g}`)).join(' + ')
                : tr('scr.bar.anyGate') === 'scr.bar.anyGate' ? 'none' : tr('scr.bar.anyGate')}>
          {['liquid', 'exHealth'].map((g) => (
            <Item key={g} on={gates?.has(g)} onClick={() => onToggleGate(g)}
                  n={gateCounts?.[g] ?? null} title={tr(`scr.gate.${g}.why`)}>
              {tr(`scr.gate.${g}`)}
            </Item>
          ))}
        </Menu>

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
