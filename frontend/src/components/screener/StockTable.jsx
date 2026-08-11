import { useState } from 'react'
import Squares from '../Squares'
import { barStyle } from '../groups/ThemeBars'
import { tickerHref } from '../portfolio/lib/tickerUrl'

/**
 * One table, whatever the vocabularies selected. Changing a scan or a state
 * changes the row set and nothing else — no column appears, disappears, or
 * re-encodes, so a value seen under one selection means the same thing under
 * every other.
 *
 * Column notes that are constraints rather than descriptions:
 *
 *   Heat        only names on the confluence ledger have one. A stock that
 *               never stacked screens prints — , because "not on a top-50
 *               ledger" is not a heat of zero.
 *   Align       two lights, never a composite. Left: own RS 3M in the top
 *               third of the universe scale (the rsTone threshold the site
 *               already uses). Right: its industry's state, in the state
 *               grammar. Adding them into one score would need a weight
 *               nobody measured.
 *   Group trend five dashed cells — the home group's state history, not
 *               measured yet. The pipeline owes one membership pointer per
 *               stock (confirmed 2026-08-11); the cells light up when it
 *               lands. Unmeasured ≠ zero, so they are drawn, not omitted.
 *   Vol 5d/50d  same status: field confirmed, data not yet supplied.
 *   Rel vol     today's volume over the 3-month average (Finviz construction)
 *               — a different measurement from 5d/50d and labelled as such,
 *               not a stand-in for it.
 *
 * Rows navigate to the ticker page; the caret expands evidence in place and
 * must not navigate, hence stopPropagation.
 */

const HEAD = 25
const STEP = 100

/** The state word carries the grammar's glyph, not its own colour scheme —
 *  the same square the control bar's chips wear, so one state never makes
 *  two different colour claims on one screen. */
function StateWord({ state, fallback }) {
  if (!state) return <span className="text-[var(--color-text-muted)]">{fallback}</span>
  return (
    <span className="text-[var(--color-text-secondary)] whitespace-nowrap">
      <i className="inline-block w-[7px] h-[7px] rounded-[1px] mr-[5px] align-[-0.5px]"
         style={barStyle(state)} />
      {state}
    </span>
  )
}

const fmtPct = (v) =>
  v == null || !Number.isFinite(v) ? '—' : `${v > 0 ? '+' : ''}${(v * 100).toFixed(1)}%`

function RsCell({ v }) {
  if (v == null || !Number.isFinite(v)) return <td className="py-[4px] pr-2.5 text-right tabular-nums text-[var(--color-text-muted)]">—</td>
  const style = v >= 67
    ? { background: 'color-mix(in srgb, var(--color-took) 30%, transparent)' }
    : v <= 33
      ? { background: 'color-mix(in srgb, var(--color-refused) 26%, transparent)' }
      : undefined
  return (
    <td className="py-[4px] pr-2.5 text-right tabular-nums">
      <span className="rounded-sm px-1" style={style}>{Math.round(v)}</span>
    </td>
  )
}

function AlignDots({ rs3, indState, indName }) {
  const stockKnown = Number.isFinite(rs3)
  return (
    <td className="py-[4px] pr-2.5 text-center whitespace-nowrap">
      <i className="inline-block w-[7px] h-[7px] rounded-full mx-[1.5px] align-middle"
         title={stockKnown ? `own RS 3M ${Math.round(rs3)} of 99` : 'no RS reading'}
         style={!stockKnown
           ? { border: '1px dashed var(--color-text-muted)' }
           : rs3 >= 67
             ? { background: 'var(--color-took)' }
             : { border: '1px solid var(--color-untested)' }} />
      <i className="inline-block w-[7px] h-[7px] rounded-[1px] mx-[1.5px] align-middle"
         title={indState ? `${indName}: ${indState}` : 'industry state not measured'}
         style={indState ? barStyle(indState) : { border: '1px dashed var(--color-text-muted)' }} />
    </td>
  )
}

/** Five dashed cells: the home group's state history, awaiting its pointer. */
function GroupTrendCell() {
  return (
    <td className="py-[4px] pr-2.5 opacity-40 group-hover:opacity-100 transition-opacity">
      <span className="inline-flex gap-[2px]"
            title="group state history — not measured yet">
        {Array.from({ length: 5 }, (_, i) => (
          <i key={i} className="block w-[10px] h-[8px] rounded-[1px] opacity-50"
             style={{ border: '1px dashed var(--color-text-muted)' }} />
        ))}
      </span>
    </td>
  )
}

function HeatCell({ heat }) {
  if (!heat) {
    return <td className="py-[4px] pr-2.5 text-[var(--color-text-muted)]"
               title="not on the confluence ledger">—</td>
  }
  const marks = heat.screeners.map((s) => '|'.repeat(s.hits)).join(' ')
  return (
    <td className="py-[4px] pr-2.5 whitespace-nowrap">
      <span className="tabular-nums font-mono">{heat.score.toFixed(1)}</span>
      <span className="text-[8.5px] tracking-[1px] text-[var(--color-text-muted)] opacity-0 group-hover:opacity-60 transition-opacity ml-1.5">{marks}</span>
    </td>
  )
}

function EvidenceFold({ row }) {
  return (
    <tr>
      <td colSpan={15} className="pb-2 pt-0 pl-9 border-none">
        <div className="border border-[var(--color-border-light)] rounded-md bg-[var(--color-surface)]
                        px-3.5 py-2 text-[12px] text-[var(--color-text-secondary)] flex flex-wrap gap-x-5 gap-y-1">
          {row.heat && row.heat.screeners.map((s) => (
            <span key={s.name}>
              <b className="font-semibold text-[var(--color-text)]">{s.name}</b>
              {' '}×{s.hits} · {s.last_date?.slice(5)}
            </span>
          ))}
          {row.indPct != null && (
            <span title="percentile within its own industry">Ind pct <b className="font-semibold text-[var(--color-text)]">{Math.round(row.indPct)}</b></span>
          )}
          {row.perf1w != null && <span>1W <b className="font-semibold text-[var(--color-text)]">{fmtPct(row.perf1w)}</b></span>}
          {row.sector && <span className="text-[var(--color-text-muted)]">{row.sector}{row.ind ? ` · ${row.ind}` : ''}</span>}
        </div>
      </td>
    </tr>
  )
}

export default function StockTable({ rows }) {
  const [shown, setShown] = useState(HEAD)
  const [open, setOpen] = useState(() => new Set())

  const visible = rows.slice(0, shown)
  const hidden = rows.length - visible.length

  const toggle = (t) => setOpen((prev) => {
    const next = new Set(prev)
    if (next.has(t)) next.delete(t); else next.add(t)
    return next
  })

  if (!rows.length) {
    return (
      <p className="m-0 py-8 text-center text-[12px] text-[var(--color-text-muted)]">
        0 names match this selection.
      </p>
    )
  }

  return (
    <div>
      <table className="w-full text-[12.5px] border-collapse">
        <thead>
          <tr className="text-[9.5px] font-mono uppercase tracking-wider text-[var(--color-text-muted)]">
            <th className="text-right py-1 pr-2.5 font-medium w-7">#</th>
            <th className="text-left py-1 pr-2.5 font-medium">Ticker</th>
            <th className="text-left py-1 pr-2.5 font-medium"
                title="confluence score — how many screens stacked, quality tier ×3">Heat</th>
            <th className="text-center py-1 pr-2.5 font-medium"
                title="left dot: own RS 3M ≥ 67 · right dot: industry state">Align</th>
            <th className="text-left py-1 pr-2.5 font-medium">State</th>
            <th className="text-left py-1 pr-2.5 font-medium"
                title="home-group state history — awaiting the per-stock membership pointer">Group trend</th>
            <th className="text-right py-1 pr-2.5 font-medium">RS 1M</th>
            <th className="text-right py-1 pr-2.5 font-medium">RS 3M</th>
            <th className="text-right py-1 pr-2.5 font-medium">RS 6M</th>
            <th className="text-right py-1 pr-2.5 font-medium"
                title="rs_accel — the same number the state machine reads">Accel</th>
            <th className="text-right py-1 pr-2.5 font-medium">From 52wH</th>
            <th className="text-right py-1 pr-2.5 font-medium"
                title="today's volume ÷ 3-month average (Finviz construction)">Rel vol</th>
            <th className="text-right py-1 pr-2.5 font-medium"
                title="5-day ÷ 50-day average volume — not measured yet">Vol 5d/50d</th>
            <th className="text-left py-1 pr-2.5 font-medium"
                title="windows spent in the top quartile of its own cohort">Top quartile</th>
            <th className="py-1 font-medium w-5"></th>
          </tr>
        </thead>
        <tbody>
          {visible.map((r, i) => (
            <RowPair key={r.ticker} r={r} i={i} open={open.has(r.ticker)} onToggle={toggle} />
          ))}
        </tbody>
      </table>
      {hidden > 0 && (
        <button type="button" onClick={() => setShown((n) => n + STEP)}
          className="block w-full bg-transparent border-none cursor-pointer text-center
                     text-[10.5px] text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] py-1.5">
          ⋮ {hidden} more — show
        </button>
      )}
    </div>
  )
}

function RowPair({ r, i, open, onToggle }) {
  const hasEvidence = Boolean(r.heat) || r.indPct != null || r.perf1w != null
  return (
    <>
      <tr tabIndex={0}
          onClick={() => { window.location.hash = tickerHref(r.ticker) }}
          // Enter on the row only — the caret button's keydown bubbles here,
          // and expanding evidence must not also navigate away
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.target === e.currentTarget) {
              window.location.hash = tickerHref(r.ticker)
            }
          }}
          className={`group border-t border-[var(--color-border-light)] cursor-pointer
                      hover:bg-[var(--color-hover-bg)] outline-none focus-visible:ring-1
                      ${r.inUniverse ? '' : 'opacity-45'}`}>
        <td className="py-[4px] pr-2.5 text-right tabular-nums text-[var(--color-text-muted)]">{i + 1}</td>
        <td className="py-[4px] pr-2.5 font-mono font-semibold text-[var(--color-text-bold)]">{r.ticker}</td>
        <HeatCell heat={r.heat} />
        <AlignDots rs3={r.rs3} indState={r.indState} indName={r.ind} />
        <td className="py-[4px] pr-2.5 text-[10.5px]">
          <StateWord state={r.state} fallback={r.inUniverse ? '—' : 'not in universe'} />
        </td>
        <GroupTrendCell />
        <RsCell v={r.rs1} />
        <RsCell v={r.rs3} />
        <RsCell v={r.rs6} />
        <td className="py-[4px] pr-2.5 text-right tabular-nums"
            style={r.accel == null ? { color: 'var(--color-text-muted)' }
                 : { color: r.accel > 0 ? 'var(--color-took)' : 'var(--color-refused)' }}>
          {r.accel == null ? '—' : `${r.accel > 0 ? '+' : '−'}${Math.abs(r.accel).toFixed(2)}`}
        </td>
        <td className="py-[4px] pr-2.5 text-right tabular-nums opacity-55 group-hover:opacity-100 transition-opacity">
          {r.h52 == null ? '—' : `${(r.h52 * 100).toFixed(1)}%`}
        </td>
        <td className="py-[4px] pr-2.5 text-right tabular-nums opacity-55 group-hover:opacity-100 transition-opacity">
          {r.relVol == null ? '—' : r.relVol.toFixed(2)}
        </td>
        <td className="py-[4px] pr-2.5 text-right text-[var(--color-text-muted)] opacity-40 group-hover:opacity-100 transition-opacity"
            title="not measured yet">—</td>
        <td className="py-[4px] pr-2.5 whitespace-nowrap opacity-55 group-hover:opacity-100 transition-opacity">
          <Squares n={r.tq} of={r.tqOf}
            title={r.tqOf ? `top quartile of its cohort on ${r.tq} of ${r.tqOf} windows` : undefined} />
        </td>
        <td className="py-[4px] text-right">
          {hasEvidence && (
            <button type="button"
              onClick={(e) => { e.stopPropagation(); onToggle(r.ticker) }}
              aria-label={open ? 'hide evidence' : 'show evidence'}
              className="bg-transparent border-none cursor-pointer p-0 text-[var(--color-text-muted)]
                         hover:text-[var(--color-text)] outline-none focus-visible:ring-1">
              {open ? '▾' : '▸'}
            </button>
          )}
        </td>
      </tr>
      {open && <EvidenceFold row={r} />}
    </>
  )
}
