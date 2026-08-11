import { useState, useMemo, useEffect } from 'react'
import PageHeader from '../PageHeader'
import Reading, { readScreener } from '../Reading'
import { useHeatingUp } from '../../hooks/useHeatingUp'
import { useUniverse } from '../../hooks/useUniverse'
import { useGroups } from '../../hooks/useGroups'
import { useMarketData } from '../../hooks/useMarketData'
import { usePresets } from '../../hooks/usePresets'
import { SCAN_DEFS, scanTickers } from '../../lib/scanSets'
import ScanBar from './ScanBar'
import StockTable from './StockTable'
import WatchlistTab from './WatchlistTab'
import HowToRead from '../HowToRead'

/**
 * One table over the tradeable universe, read through four vocabularies the
 * pipeline already speaks — a scan, a state, a theme, a name. The row set is
 * their intersection; the columns never change.
 *
 * The min/max query builder that used to live here is retired (2026-08-11).
 * It let a reader construct questions the pipeline had never answered; every
 * selector on this page only chooses between answers that already exist.
 * Its files remain in the repo unmounted, alongside HeatingUp, whose ledger
 * became the Confluence scan — the default vocabulary word, not the page.
 */

const TABS = ['Screener', 'Watchlist']
const QUERY_KEY = 'screener-query'

const STATE_WORDS = ['Leading', 'Weakening', 'Improving', 'Lagging']

function loadQuery() {
  try {
    const q = JSON.parse(localStorage.getItem(QUERY_KEY)) ?? {}
    return {
      // a persisted scan key that has left the vocabulary must not survive the
      // restore — the bar would highlight nothing while the fallback filtered
      scan: SCAN_DEFS.some((d) => d.key === q.scan) ? q.scan : 'confluence',
      states: Array.isArray(q.states) ? q.states.filter((s) => STATE_WORDS.includes(s)) : [],
      theme: typeof q.theme === 'string' ? q.theme : null,
    }
  } catch {
    return { scan: 'confluence', states: [], theme: null }
  }
}

export default function ScreenerPage() {
  const { universe, loading } = useUniverse()
  const groups = useGroups()
  const heat = useHeatingUp()
  const { data: market } = useMarketData()
  const { allPresets } = usePresets()

  const [activeTab, setActiveTab] = useState(0)
  const initial = useMemo(loadQuery, [])
  const [scan, setScan] = useState(initial.scan)
  const [states, setStates] = useState(() => new Set(initial.states))
  const [theme, setTheme] = useState(initial.theme)
  const [search, setSearch] = useState('')

  useEffect(() => {
    try {
      localStorage.setItem(QUERY_KEY, JSON.stringify({ scan, states: [...states], theme }))
    } catch { /* storage may be unavailable; the query is still live in memory */ }
  }, [scan, states, theme])

  // A persisted theme the taxonomy no longer publishes must be cleared, not
  // kept: with the name held but the lookup failing, no rows are filtered while
  // the receipt still claims the intersection — a filter that asserts itself
  // and does nothing.
  useEffect(() => {
    if (theme && !groups.loading && groups.themes.length &&
        !groups.themes.some((t) => t.group === theme)) {
      setTheme(null)
    }
  }, [theme, groups.loading, groups.themes])

  const heatByTicker = useMemo(() => {
    const m = new Map()
    for (const r of heat?.rows ?? []) m.set(r.ticker, r)
    return m
  }, [heat])

  const industryState = useMemo(() => {
    const m = new Map()
    for (const g of groups.industries) m.set(g.group, g.state)
    return m
  }, [groups.industries])

  // `count: null` means the file has not arrived — a different claim from a
  // measured zero, and the bar renders them differently. Collapsing the two
  // would print "found nothing this session" about a fetch that never landed.
  const scans = useMemo(() => SCAN_DEFS.map((d) => {
    if (d.key === 'all') {
      return { ...d, count: universe?.length ?? null, set: null, loaded: Boolean(universe) }
    }
    if (d.key === 'confluence') {
      const loaded = Boolean(heat?.rows)
      return {
        ...d, loaded,
        count: loaded ? heatByTicker.size : null,
        set: loaded ? new Set(heatByTicker.keys()) : null,
      }
    }
    const json = market?.[d.key]
    if (!json) return { ...d, count: null, set: null, loaded: false }
    const set = scanTickers(json, d.container)
    return { ...d, count: set.size, set, loaded: true }
  }), [universe, heat, heatByTicker, market])

  const activeScan = scans.find((s) => s.key === scan) ?? scans[0]
  const themeRow = theme ? groups.themes.find((t) => t.group === theme) : null

  // Rows before the state filter, so state counts can be honest facet counts
  // of what each state word would keep — not of the whole world.
  const preState = useMemo(() => {
    if (!universe) return []
    const byTicker = new Map(universe.map((r) => [r.ticker, r]))
    const themeSet = themeRow ? new Set(themeRow.tickers) : null
    const q = search.trim().toUpperCase()

    const tickers = activeScan.set
      ? [...activeScan.set]
      : universe.map((r) => r.ticker)

    const out = []
    for (const t of tickers) {
      if (themeSet && !themeSet.has(t)) continue
      if (q && !t.toUpperCase().includes(q)) continue
      const u = byTicker.get(t)
      const s = groups.stocks[t]
      // The industry is known for universe rows even when the stock carries no
      // RS payload — its group's state is a measurement about the group, and a
      // measured state must not render as "not measured" just because this
      // member went unranked.
      const indName = s?.group ?? u?.industry ?? null
      out.push({
        ticker: t,
        inUniverse: Boolean(u),
        heat: heatByTicker.get(t) ?? null,
        state: s?.state ?? null,
        ind: indName,
        indState: indName ? industryState.get(indName) ?? null : null,
        indPct: s?.group_pctile ?? null,
        accel: s?.rs_accel ?? null,
        tq: s?.persistence ?? null,
        tqOf: s?.persistence_of ?? null,
        rs1: u?.rs_1m ?? u?.rs_21d ?? null,
        rs3: u?.rs_3m ?? u?.rs_63d ?? null,
        rs6: u?.rs_6m ?? u?.rs_126d ?? null,
        // high_52w_dist is a fraction (-0.065 = 6.5% below the high), not a percent
        h52: u?.high_52w_dist ?? u?.high_52w ?? null,
        relVol: u?.rel_volume ?? null,
        perf1w: u?.perf_1w ?? null,
        sector: u?.sector ?? null,
      })
    }
    return out
  }, [universe, activeScan, themeRow, search, groups.stocks, heatByTicker, industryState])

  // null while groups.json is absent — "Leading 0" is a reading, not a shrug
  const statesLoaded = !groups.loading && !groups.error
  const stateCounts = useMemo(() => {
    if (!statesLoaded) return null
    const c = {}
    for (const r of preState) if (r.state) c[r.state] = (c[r.state] ?? 0) + 1
    return c
  }, [preState, statesLoaded])

  const rows = useMemo(() => {
    const kept = states.size ? preState.filter((r) => r.state && states.has(r.state)) : preState
    const sorted = [...kept]
    if (scan === 'confluence') {
      sorted.sort((a, b) => (b.heat?.score ?? -1) - (a.heat?.score ?? -1))
    } else {
      sorted.sort((a, b) => (b.rs3 ?? -1) - (a.rs3 ?? -1))
    }
    return sorted
  }, [preState, states, scan])

  const noState = states.size ? preState.filter((r) => !r.state).length : 0

  const receipt = useMemo(() => {
    if (!activeScan.loaded) return `${activeScan.label} — still loading`
    const parts = [activeScan.label]
    if (states.size) parts.push([...states].join('+'))
    if (theme) parts.push(theme)
    if (search.trim()) parts.push(`"${search.trim().toUpperCase()}"`)
    let s = `${rows.length} rows · ${parts.join(' ∩ ')}`
    if (noState) s += ` · ${noState} without a state hidden`
    return s
  }, [rows.length, activeScan, states, theme, search, noState])

  const conditions = market?.breadth?.conditions
  const toggleState = (st) => setStates((prev) => {
    const next = new Set(prev)
    if (next.has(st)) next.delete(st); else next.add(st)
    return next
  })

  if (loading) {
    return (
      <div className="text-[var(--color-text-muted)] text-sm font-medium uppercase tracking-wide text-center py-20">
        Loading universe...
      </div>
    )
  }

  return (
    <div>
      <PageHeader group="market" title="Screener"
        blurb="One table over the tradeable universe, read through four vocabularies the pipeline already speaks — a scan, a state, a theme, a name. Nothing here is typed in; everything is selected."
        meta={[
          conditions ? (
            <a key="mc" href="#/breadth" className="no-underline text-inherit"
               title="the fifteen conditions behind this number — the page-level third light">
              Market conditions{' '}
              <b className="text-[15px] text-[var(--color-text-bold)]">{conditions.today}</b>
              {' '}· {conditions.positive_today} of {conditions.n_votes} positive
            </a>
          ) : 'Market conditions — not loaded',
          heat?.as_of ?? '',
        ]} />

      {/* the whole confluence ledger, not the old 25-row display slice — the
          sentence says "here", and here now holds all fifty */}
      <Reading text={readScreener(heat)} />

      <div className="flex gap-0 border-b border-[var(--color-border)] mb-4" role="tablist">
        {TABS.map((tab, i) => (
          <button key={tab} role="tab" aria-selected={activeTab === i}
            onClick={() => setActiveTab(i)}
            className={`px-5 py-2.5 font-semibold text-sm cursor-pointer bg-transparent border-none border-b-2 transition-colors ${
              activeTab === i
                ? 'border-green-600 text-green-600'
                : 'border-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'
            }`}>
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 0 && (
        <>
          <ScanBar
            scans={scans} scan={scan} onScan={setScan}
            stateCounts={stateCounts} states={states} onToggleState={toggleState}
            themes={groups.themes} theme={theme} onTheme={setTheme}
            search={search} onSearch={setSearch}
            receipt={receipt} />
          {activeScan.loaded ? (
            // key: normalized search only — a trailing space changes nothing
            // about the row set and must not remount the table
            <StockTable key={`${scan}|${[...states].join()}|${theme}|${search.trim().toUpperCase()}`}
                        rows={rows} />
          ) : (
            <p className="m-0 py-8 text-center text-[12px] text-[var(--color-text-muted)]">
              {activeScan.label} has not loaded yet.
            </p>
          )}
        </>
      )}

      {activeTab === 1 && (
        <WatchlistTab universe={universe} presets={allPresets} />
      )}

      <HowToRead>
        <p>
          Every control on this page is a <b>vocabulary, not a query</b>. A scan is a
          list a screener wrote this session; a state is the four-state read the
          group engine assigned; a theme is a membership the taxonomy defines; a
          name is a ticker. The table is their intersection, and changing a
          selection changes only which rows you see — never what any column means.
        </p>
        <p>
          <b>Heat</b> exists only for names on the confluence ledger — the fifty
          that stacked more than one screen. Everything else prints a dash,
          because absence from a top-50 list is not a score of zero. The marks
          beside the number are the appearances that produced it; the caret opens
          them so the arithmetic stays checkable.
        </p>
        <p>
          <b>Align</b> is two lights that are never added together: the stock&rsquo;s
          own 3-month RS in the top third, and its industry&rsquo;s state. The
          market-conditions number in the header is the third light, printed once
          because it is the same for every row. Three lights agreeing is something
          you see; a weighted total would be something we invented.
        </p>
        <p>
          Two columns are drawn <b>unmeasured on purpose</b>: Group trend (five
          dashed cells awaiting the per-stock home pointer) and Vol 5d/50d
          (awaiting the pipeline field). A dashed outline means not measured yet —
          it never means zero. The theme ribbon, when you choose a theme, appears
          on the control bar rather than in every row: it is a property of the
          theme, not of each stock.
        </p>
      </HowToRead>
    </div>
  )
}
