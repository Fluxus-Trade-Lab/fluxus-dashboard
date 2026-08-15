import { useMemo, useRef, useState } from 'react'
import { SLOT_COLOURS, MAX_COMPARE } from './useThemeCompare'

/**
 * The selection, as three visible slots and a search field — the chip wall's
 * replacement.
 *
 * The wall showed all 79 themes at equal weight and became the largest object
 * on the page; a picker had turned into the subject. This bar is the same
 * capability at a fiftieth of the weight, because the RANKING below is
 * already the browsable list of themes — a second full listing above it was
 * the same information twice.
 *
 * The three slots are drawn even when empty. Empty slots ARE the caption:
 * they say "up to three" without a sentence, they show remaining capacity at
 * a glance, and a pick landing in one is the interaction's receipt — visible
 * in the sticky bar no matter how deep in the list the click happened.
 */
export default function CompareBar({ rows, picks, atLimit, onToggle }) {
  const [q, setQ] = useState('')
  const inputRef = useRef(null)

  const picked = new Set(picks.map((p) => p.name))
  const matches = useMemo(() => {
    const needle = q.trim().toLowerCase()
    if (!needle) return []
    return rows
      .map((r) => r.group)
      .filter((n) => n.toLowerCase().includes(needle) && !picked.has(n))
      .slice(0, 8)
  }, [q, rows, picks])   // eslint-disable-line react-hooks/exhaustive-deps

  const pick = (name) => { onToggle(name); setQ(''); inputRef.current?.focus() }

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <div className="relative">
        <input ref={inputRef} value={q}
               onChange={(e) => setQ(e.target.value)}
               onKeyDown={(e) => {
                 if (e.key === 'Enter' && matches[0]) pick(matches[0])
                 if (e.key === 'Escape') setQ('')
               }}
               disabled={atLimit}
               placeholder={atLimit ? 'full — remove one' : 'Add theme…'}
               className="w-[136px] h-[26px] px-0.5 text-[12.5px] bg-transparent
                          border-0 border-b border-[var(--color-border)] rounded-none
                          text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]
                          focus:outline-none focus:border-[var(--color-text-muted)]
                          disabled:opacity-50 disabled:cursor-not-allowed" />
        {matches.length > 0 && (
          <ul className="absolute left-0 top-[34px] z-30 m-0 p-1 list-none w-[240px]
                         max-h-[264px] overflow-auto rounded border
                         border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg">
            {matches.map((n) => (
              <li key={n}>
                {/* mousedown, not click: click fires after blur has closed the list */}
                <button type="button" onMouseDown={(e) => { e.preventDefault(); pick(n) }}
                        className="w-full text-left px-2 py-1.5 text-[12.5px] rounded-sm
                                   bg-transparent border-0 cursor-pointer
                                   text-[var(--color-text-secondary)]
                                   hover:bg-[var(--color-hover-bg)] hover:text-[var(--color-text)]">
                  {n}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {SLOT_COLOURS.map((colour, i) => {
        const p = picks[i]
        return p ? (
          <button key={colour} type="button" onClick={() => onToggle(p.name)}
                  title={`${p.name} — click to remove`}
                  style={{ color: p.colour }}
                  className="h-[26px] max-w-[190px] px-0.5 bg-transparent border-0
                             cursor-pointer flex items-center gap-1.5 text-[12.5px] font-medium">
            <i className="w-2 h-2 rounded-full shrink-0" style={{ background: p.colour }} />
            <span className="truncate">{p.name}</span>
            <span aria-hidden className="opacity-50">×</span>
          </button>
        ) : (
          /* an empty slot is the caption: a hollow dot says "room for one
             more" without a box or a sentence */
          <span key={colour} aria-hidden
                className="w-2 h-2 rounded-full select-none shrink-0" />
        )
      })}
    </div>
  )
}
