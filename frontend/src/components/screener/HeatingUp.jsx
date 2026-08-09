import { useState, useEffect } from 'react'

/**
 * Confluence ledger — the v2 screener object.
 *
 * Design: Fluxus_Brand/visual/explorations/2026-08-08/screener.html (scored 92)
 *
 * Two things this replaces, and why:
 *   · chips → countable marks. A chip says "this fired"; a row of marks says how
 *     often, and lets two names be compared without reading a number.
 *   · a badge-sized staleness flag → a drawn one. When the last session in the
 *     ledger is not the last session in the market, that is the first thing to
 *     read, not a chip in the corner.
 *
 * Note on what is NOT drawn: the raw screener files carry only a pipeline run
 * timestamp, not the session they cover, so "how far behind the raw screeners
 * is this?" cannot be answered from the data and is not claimed.
 *
 * The score stays a printed number on purpose: the weighting (quality ×3 against
 * participation ×1, repeats capped) cannot be drawn honestly, and anything that
 * cannot be drawn honestly gets written.
 */

const QUALITY = new Set(['episodic_pivot', 'vcp', 'momentum_97'])

const LABELS = {
  episodic_pivot: 'EP',
  vcp: 'VCP',
  momentum_97: 'MOM',
  gainers_4pct: '4%',
  vol_up_gainers: 'VOL',
  ema21_watch: '21D',
  healthy_charts: 'CHART',
}

/** Counts above this are printed rather than drawn — drawing 40 marks is noise. */
const MAX_MARKS = 8

export default function HeatingUp({ limit = 25, compact = false }) {
  const [data, setData] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetch('/data/output/heating_up.json')
      .then((r) => (r.ok ? r.json() : null))
      .then((json) => { if (!cancelled) setData(json) })
      .catch(() => { if (!cancelled) setData(null) })
    return () => { cancelled = true }
  }, [])

  if (!data?.rows?.length) return null
  const rows = data.rows.slice(0, limit)

  if (compact) {
    return (
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3">
        <div className="flex items-baseline justify-between mb-1">
          <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
            Heating Up
          </h3>
          <AsOf data={data} />
        </div>
        {/* the key travels with the marks — an isotype set without one is decoration */}
        <div className="flex items-center gap-3 mb-2 text-[9px] text-[var(--color-text-muted)]">
          <span className="flex items-center gap-1">
            <i className="block w-2 h-2" style={{ background: 'var(--color-took)' }} />quality
          </span>
          <span className="flex items-center gap-1">
            <i className="block w-2 h-2"
               style={{ boxShadow: 'inset 0 0 0 1.2px var(--color-untested)' }} />participation
          </span>
          <span>one mark = one appearance</span>
        </div>
        <ul className="space-y-1.5">
          {rows.map((r) => (
            <li key={r.ticker} className="flex items-center gap-2 text-xs">
              <a href={`#/ticker/${r.ticker}`}
                 className="font-mono font-medium text-[var(--color-text)] hover:underline w-14 shrink-0">
                {r.ticker}
              </a>
              <span className="font-mono tabular-nums text-[var(--color-text-secondary)]
                               w-10 shrink-0 text-right">{r.score.toFixed(1)}</span>
              <Marks screeners={r.screeners} dense />
            </li>
          ))}
        </ul>
      </div>
    )
  }

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
      <div className="flex items-baseline justify-between pb-2 border-b border-[var(--color-v2-ink)]">
        <h3 className="text-[10px] font-mono uppercase tracking-[.24em] text-[var(--color-text-muted)]">
          Confluence ledger
        </h3>
        <span className="text-[11px] text-[var(--color-text-secondary)]">
          One mark is one appearance — quality solid, participation outlined
        </span>
      </div>

      {/* The last session counted is the frame everything below sits in, so it is
          drawn at reading size instead of shrunk into a corner badge. */}
      <div className="flex items-baseline gap-3 mt-3 pb-3 border-b border-[var(--color-border-light)]">
        <span className="text-[9px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)]">
          Counted through
        </span>
        <span className="text-[17px] tabular-nums leading-none text-[var(--color-text)]"
              style={{ fontFamily: 'var(--font-cond)' }}>{data.as_of}</span>
        {data.stale && (
          <span className="text-[11px] text-[var(--color-signal-caution)]">
            — {data.stale_reason ?? 'stale'}; nothing after that session is in here
          </span>
        )}
      </div>

      <div className="overflow-x-auto">
        <div className="grid grid-cols-[62px_54px_1fr_92px_120px] gap-3 items-center
                        text-[9px] font-mono uppercase tracking-[.16em]
                        text-[var(--color-text-muted)] pt-4 pb-2
                        border-b border-[var(--color-v2-ink)] min-w-[720px]">
          <span>Ticker</span><span>Score</span><span>Where it appeared</span>
          <span>Span</span><span>Sector</span>
        </div>
        {rows.map((r) => (
          <div key={r.ticker}
               className="grid grid-cols-[62px_54px_1fr_92px_120px] gap-3 items-center py-2.5
                          border-b border-[var(--color-border-light)] min-w-[720px]
                          hover:bg-[var(--color-hover-bg)]">
            <a href={`#/ticker/${r.ticker}`}
               className="font-mono text-[15px] font-medium text-[var(--color-text)] hover:underline">
              {r.ticker}
            </a>
            <span className="text-[20px] font-bold tabular-nums leading-none"
                  style={{ fontFamily: 'var(--font-cond)' }}>{r.score.toFixed(1)}</span>
            <Marks screeners={r.screeners} />
            <span className="font-mono text-[11px] text-[var(--color-text-secondary)]">
              {r.days_span} sessions
            </span>
            <span className="text-[11px] text-[var(--color-text-secondary)]">{r.sector ?? '—'}</span>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-x-6 gap-y-2 pt-3 text-[11px] text-[var(--color-text-secondary)]">
        <span><i className="inline-block w-[11px] h-[11px] align-[-1px] mr-1.5"
                 style={{ background: 'var(--color-took)' }} />quality — EP · VCP · MOM · weight ×3</span>
        <span><i className="inline-block w-[11px] h-[11px] align-[-1px] mr-1.5"
                 style={{ boxShadow: 'inset 0 0 0 1.2px var(--color-untested)' }} />
          participation — weight ×1</span>
        <span className="text-[var(--color-text-muted)]">
          counts above {MAX_MARKS} are printed, not drawn
        </span>
      </div>

      {/* Any list ordered by outcome has to say how the sample chose itself. */}
      <p className="text-[11px] leading-relaxed text-[var(--color-text-secondary)] mt-3 pl-3
                    border-l-2 border-dashed border-[var(--color-untested)]">
        This list ranks by what has already stacked, so <b>every name on it is a survivor</b>.
        Read it for what is confluent right now, not as evidence that confluence pays — the
        measured answer to that is a separate matched study, and it came back <b>0 of 42</b>.
      </p>
    </div>
  )
}

/** Isotype: one mark is one appearance, so two names compare without reading. */
function Marks({ screeners, dense = false }) {
  const groups = [...screeners].sort(
    (a, b) => (QUALITY.has(b.name) ? 1 : 0) - (QUALITY.has(a.name) ? 1 : 0)
      || a.name.localeCompare(b.name),
  )
  const size = dense ? 8 : 11
  return (
    <span className="flex flex-wrap gap-x-3 gap-y-1 items-center">
      {groups.map((s) => {
        const quality = QUALITY.has(s.name)
        const shown = Math.min(s.hits, MAX_MARKS)
        return (
          <span key={s.name} className="flex gap-[2px] items-center"
                title={`${s.name} · ${s.hits}× · last ${s.last_date}`}>
            <span className="text-[9px] text-[var(--color-text-muted)] mr-1">
              {LABELS[s.name] ?? s.name}
            </span>
            {Array.from({ length: shown }, (_, i) => (
              <i key={i} className="block" style={{
                width: size, height: size,
                background: quality ? 'var(--color-took)' : 'transparent',
                boxShadow: quality ? undefined : 'inset 0 0 0 1.2px var(--color-untested)',
              }} />
            ))}
            {s.hits > MAX_MARKS && (
              <span className="text-[9px] text-[var(--color-text-muted)] ml-0.5">
                +{s.hits - MAX_MARKS}
              </span>
            )}
          </span>
        )
      })}
    </span>
  )
}

function AsOf({ data }) {
  return (
    <span className="flex items-baseline gap-1.5">
      {data.stale && (
        <span title={data.stale_reason ?? 'Stale data'}
              className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10
                         text-[var(--color-signal-caution)] uppercase tracking-wide">
          Stale
        </span>
      )}
      <span className="text-[10px] font-mono text-[var(--color-text-muted)]">
        as of {data.as_of}
      </span>
    </span>
  )
}
