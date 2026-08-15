import { useState, useMemo } from 'react'
import Squares from '../Squares'
import { barStyle } from '../groups/ThemeBars'
import { tickerHref } from '../portfolio/lib/tickerUrl'
import { useLanguage } from '../../i18n/LanguageContext'

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
 *   Group trend the home group's state history, one cell per completed
 *               fortnight of the group archive (began 2026-08-07). The home
 *               is the pipeline's primary_group pointer; cells light from
 *               the right as the archive matures. Unmeasured ≠ zero, so the
 *               unlived past is drawn dashed, not omitted.
 *   Vol 5d/50d  five-day over fifty-day average volume, from daily bars;
 *               younger than fifty sessions prints a dash, not a ratio over
 *               a shorter window.
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
  const { t: tr } = useLanguage()
  if (!state) return <span className="text-[var(--color-text-muted)]">{fallback}</span>
  return (
    <span className="text-[var(--color-text-secondary)] whitespace-nowrap">
      <i className="inline-block w-[7px] h-[7px] rounded-[1px] mr-[5px] align-[-0.5px]"
         style={barStyle(state)} />
      {tr(`state.${state}`)}
    </span>
  )
}

const fmtPct = (v) =>
  v == null || !Number.isFinite(v) ? '—' : `${v > 0 ? '+' : ''}${(v * 100).toFixed(1)}%`

function RsCell({ v }) {
  if (v == null || !Number.isFinite(v)) return <td className="py-[4px] pr-2.5 text-right tabular-nums text-[var(--color-text-muted)]">—</td>
  // v3: a percentile is a position in a ranking, not a pole — grey ladder
  const style = v >= 67
    ? { background: 'var(--color-surface-raised)', fontWeight: 600 }
    : v <= 33
      ? { color: 'var(--color-text-muted)' }
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
             ? { background: 'var(--color-text-bold)' }
             : { border: '1px solid var(--color-untested)' }} />
      <i className="inline-block w-[7px] h-[7px] rounded-[1px] mx-[1.5px] align-middle"
         title={indState ? `${indName}: ${indState}` : 'industry state not measured'}
         style={indState ? barStyle(indState) : { border: '1px dashed var(--color-text-muted)' }} />
    </td>
  )
}

/** The home group's state history — five fortnight cells, oldest first.
 *  The home is the pipeline's one-per-stock pointer (smallest curated theme,
 *  industry as the total fallback); the cells come from the group archive,
 *  which began 2026-08-07, so a young archive lights from the right and the
 *  unlived past stays dashed. A lit ribbon earns full opacity — only the
 *  still-empty ones rest faded. */
function GroupTrendCell({ home, homeKind, ribbon }) {
  // a cell can be null INSIDE the array too — a fortnight the group sat out
  // (skipped scoring, thin membership); the calendar keeps the slot, drawn
  // dashed, so cell k means the same dates on every row
  const cells = ribbon ?? []
  const measured = cells.filter(Boolean)
  const pad = Math.max(0, 5 - cells.length)
  const kindWord = homeKind === 'industry_unscored' ? 'industry, unscored' : homeKind
  const title = home
    ? measured.length
      ? `${home} (home ${kindWord}) — ${measured.length} of 5 fortnights, oldest first: ${measured.map((c) => c.state).join(' · ')}`
      : `${home} (home ${kindWord}) — 0 of 5 fortnights measured; the archive is accumulating`
    : 'no home group — not in the group layer'
  return (
    <td className={`py-[4px] pr-2.5 transition-opacity group-hover:opacity-100
                    ${measured.length ? '' : 'opacity-40'}`}>
      <span className="inline-flex gap-[2px]" title={title}>
        {Array.from({ length: pad }, (_, i) => (
          <i key={`p${i}`} className="block w-[10px] h-[8px] rounded-[1px] opacity-50"
             style={{ border: '1px dashed var(--color-text-muted)' }} />
        ))}
        {cells.map((c, i) => (
          <i key={i} className="block w-[10px] h-[8px] rounded-[1px]"
             style={c ? barStyle(c.state)
                      : { border: '1px dashed var(--color-text-muted)', opacity: 0.5 }} />
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
      <span className="text-[10px] tracking-[1px] text-[var(--color-text-muted)] opacity-0 group-hover:opacity-60 transition-opacity ml-1.5">{marks}</span>
    </td>
  )
}

function EvidenceFold({ row }) {
  return (
    <tr>
      <td colSpan={15} className="pb-2 pt-0 pl-9 border-none">
        <div className="border border-[var(--color-border-light)] rounded-md bg-[var(--color-surface)]
                        px-3.5 py-2 text-[12.5px] text-[var(--color-text-secondary)] flex flex-wrap gap-x-5 gap-y-1">
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

/** Sortable columns and how each one reads its row. Sorting re-orders and
 *  nothing else — no column re-encodes, and nulls sink to the bottom in both
 *  directions, because "no reading" belongs at neither extreme. */
const SORTS = {
  ticker: { get: (r) => r.ticker, str: true },
  heat: { get: (r) => r.heat?.score ?? null },
  rs1: { get: (r) => r.rs1 },
  rs3: { get: (r) => r.rs3 },
  rs6: { get: (r) => r.rs6 },
  accel: { get: (r) => r.accel },
  h52: { get: (r) => r.h52 },
  relVol: { get: (r) => r.relVol },
  vol5050: { get: (r) => r.vol5050 },
  tq: { get: (r) => (r.tqOf ? r.tq / r.tqOf : null) },
}

/** A header that sorts. The arrow only appears on the active column — ten
 *  permanent arrows would be ten more marks on a page fighting overload. */
function SortTh({ k, sort, onSort, align = 'right', title, children }) {
  const on = sort.key === k
  // literal classes only — `text-${align}` would never reach the stylesheet
  const alignCls = align === 'left' ? 'text-left' : 'text-right'
  return (
    <th className={`py-1 pr-2.5 font-medium ${alignCls}`} title={title}>
      <button type="button" onClick={() => onSort(k)}
        className={`bg-transparent border-none p-0 cursor-pointer font-inherit uppercase
                    tracking-wider text-[10px] outline-none focus-visible:ring-1
                    ${on ? 'text-[var(--color-text-secondary)]' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'}`}>
        {children}{on && <span className="ml-0.5">{sort.dir === 'desc' ? '▼' : '▲'}</span>}
      </button>
    </th>
  )
}

export default function StockTable({ rows, defaultSort = 'rs3' }) {
  const { t: tr } = useLanguage()
  const [shown, setShown] = useState(HEAD)
  const [open, setOpen] = useState(() => new Set())
  const [sort, setSort] = useState(() => ({ key: defaultSort, dir: 'desc' }))

  const sorted = useMemo(() => {
    const spec = SORTS[sort.key]
    if (!spec) return rows
    const sign = sort.dir === 'asc' ? 1 : -1
    return [...rows].sort((a, b) => {
      const va = spec.get(a); const vb = spec.get(b)
      if (va == null && vb == null) return 0
      if (va == null) return 1
      if (vb == null) return -1
      if (spec.str) return sign * String(va).localeCompare(String(vb))
      return sign * (va - vb)
    })
  }, [rows, sort])

  const clickSort = (key) => setSort((prev) =>
    prev.key === key
      ? { key, dir: prev.dir === 'desc' ? 'asc' : 'desc' }
      : { key, dir: SORTS[key]?.str ? 'asc' : 'desc' })

  const visible = sorted.slice(0, shown)
  const hidden = sorted.length - visible.length

  const toggle = (t) => setOpen((prev) => {
    const next = new Set(prev)
    if (next.has(t)) next.delete(t); else next.add(t)
    return next
  })

  if (!rows.length) {
    return (
      <p className="m-0 py-8 text-center text-[12.5px] text-[var(--color-text-muted)]">
        {tr('scr.noRows')}
      </p>
    )
  }

  return (
    <div>
      <table className="w-full text-[12.5px] border-collapse">
        <thead>
          <tr className="text-[10px] font-mono font-medium uppercase tracking-wider text-[var(--color-text-muted)]">
            <th className="text-right py-1 pr-2.5 font-medium w-7">#</th>
            <SortTh k="ticker" sort={sort} onSort={clickSort} align="left">{tr('scr.col.ticker')}</SortTh>
            <SortTh k="heat" sort={sort} onSort={clickSort} align="left"
                title="confluence score — how many screens stacked, quality tier ×3">{tr('scr.col.heat')}</SortTh>
            <th className="text-center py-1 pr-2.5 font-medium"
                title="left dot: own RS 3M ≥ 67 · right dot: industry state">{tr('scr.col.align')}</th>
            <th className="text-left py-1 pr-2.5 font-medium">{tr('scr.col.state')}</th>
            <th className="text-left py-1 pr-2.5 font-medium"
                title="state history of the stock's home group; cells light as the archive completes fortnights">{tr('scr.col.groupTrend')}</th>
            <SortTh k="rs1" sort={sort} onSort={clickSort}>RS 1M</SortTh>
            <SortTh k="rs3" sort={sort} onSort={clickSort}>RS 3M</SortTh>
            <SortTh k="rs6" sort={sort} onSort={clickSort}>RS 6M</SortTh>
            <SortTh k="accel" sort={sort} onSort={clickSort}
                title="rs_accel — the same number the state machine reads">{tr('scr.col.accel')}</SortTh>
            <SortTh k="h52" sort={sort} onSort={clickSort}>{tr('scr.col.from52wh')}</SortTh>
            <SortTh k="relVol" sort={sort} onSort={clickSort}
                title="today's volume ÷ 3-month average (Finviz construction)">{tr('scr.col.relVol')}</SortTh>
            <SortTh k="vol5050" sort={sort} onSort={clickSort}
                title="5-day average volume over 50-day average volume, from daily bars">{tr('scr.col.vol5d50d')}</SortTh>
            <SortTh k="tq" sort={sort} onSort={clickSort} align="left"
                title="windows spent in the top quartile of its own cohort">{tr('scr.col.topQuartile')}</SortTh>
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
                     text-[10px] text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] py-1.5">
          ⋮ {hidden} {tr('scr.more')}
        </button>
      )}
    </div>
  )
}

function RowPair({ r, i, open, onToggle }) {
  const { t: tr } = useLanguage()
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
        <td className="py-[4px] pr-2.5 text-[10px]">
          <StateWord state={r.state} fallback={r.inUniverse ? '—' : tr('scr.notInUniverse')} />
        </td>
        <GroupTrendCell home={r.home} homeKind={r.homeKind} ribbon={r.homeRibbon} />
        <RsCell v={r.rs1} />
        <RsCell v={r.rs3} />
        <RsCell v={r.rs6} />
        {/* neutral: the sign already carries the direction, and this row's
            encoding lives in the Align dots and the State glyph. A naked
            coloured number with no mark of its own was the leak Andy named. */}
        <td className={`py-[4px] pr-2.5 text-right tabular-nums ${
          r.accel == null ? 'text-[var(--color-text-muted)]' : 'text-[var(--color-text-secondary)]'}`}>
          {r.accel == null ? '—' : `${r.accel > 0 ? '+' : '−'}${Math.abs(r.accel).toFixed(2)}`}
        </td>
        <td className="py-[4px] pr-2.5 text-right tabular-nums opacity-78 group-hover:opacity-100 transition-opacity">
          {r.h52 == null ? '—' : `${(r.h52 * 100).toFixed(1)}%`}
        </td>
        <td className="py-[4px] pr-2.5 text-right tabular-nums opacity-78 group-hover:opacity-100 transition-opacity">
          {r.relVol == null ? '—' : r.relVol.toFixed(2)}
        </td>
        <td className="py-[4px] pr-2.5 text-right tabular-nums opacity-78 group-hover:opacity-100 transition-opacity"
            title={r.vol5050 == null
              ? 'not measured — fewer than fifty sessions of bars, or the vendor had none'
              : `5-day avg volume is ${r.vol5050}x the 50-day avg`}>
          {r.vol5050 == null ? '—' : r.vol5050.toFixed(2)}
        </td>
        <td className="py-[4px] pr-2.5 whitespace-nowrap opacity-78 group-hover:opacity-100 transition-opacity">
          <Squares n={r.tq} of={r.tqOf}
            title={r.tqOf ? `top quartile of its cohort on ${r.tq} of ${r.tqOf} windows` : undefined} />
        </td>
        <td className="py-[4px] text-right">
          {hasEvidence && (
            <button type="button"
              onClick={(e) => { e.stopPropagation(); onToggle(r.ticker) }}
              aria-label={open ? tr('scr.hideEvidence') : tr('scr.showEvidence')}
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
