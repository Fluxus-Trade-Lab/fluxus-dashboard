import { useState, useMemo, useEffect } from 'react'
import PageHeader from '../PageHeader'
import PickedChart from '../ticker/PickedChart'
import { useThemeHandoff } from '../../hooks/useThemeHandoff'
import ShortlistTray from '../shared/ShortlistTray'
import Reading, { readScreener } from '../Reading'
import { useHeatingUp } from '../../hooks/useHeatingUp'
import { useUniverse } from '../../hooks/useUniverse'
import { useGroups } from '../../hooks/useGroups'
import { useMarketData } from '../../hooks/useMarketData'
import { SCAN_DEFS, scanTickers } from '../../lib/scanSets'
import ScanBar from './ScanBar'
import StockTable from './StockTable'
import HowToRead from '../HowToRead'
import { useLanguage } from '../../i18n/LanguageContext'

/**
 * One table over the tradeable universe, read through four vocabularies the
 * pipeline already speaks — a scan, a state, a theme, a name. The row set is
 * their intersection; the columns never change.
 *
 * The min/max query builder that used to live here is retired (2026-08-11).
 * It let a reader construct questions the pipeline had never answered; every
 * selector on this page only chooses between answers that already exist.
 * Its files were deleted 2026-08-12 (Andy: 确认不回头) along with HeatingUp,
 * whose ledger became the Confluence scan — the default vocabulary word, not
 * the page.
 *
 * The Watchlist tab went the same way on 2026-08-17. It computed preset lists
 * in the browser from the universe while the pipeline was writing a nightly
 * watchlist.json nobody rendered; two things called Watchlist, two sources,
 * one of them the real one. The page at #/watchlist reads the file. This page
 * is a table you tune, and now it is only that.
 */
const QUERY_KEY = 'screener-query'

const STATE_WORDS = ['Leading', 'Weakening', 'Improving', 'Lagging']

/**
 * The two gates the retired preset lists all shared.
 *
 * Every one of the ten browser presets carried a cap floor and excludeHealthcare
 * on top of whatever made it that preset; those two were the gate, not the
 * screen. The screens themselves already live in the scan bar as pipeline files
 * (EMA21, VCP, EP, 4% gainers, Vol-up), so what was actually missing here was
 * the gate — and a gate is two toggles, not a query builder.
 *
 * A row that cannot prove it passes does not pass: no market cap on file means
 * dropped, not waved through. That is what makes it a gate.
 */
const GATES = {
  liquid: { test: (r) => r.cap != null && r.cap >= 1e9 && r.vol != null && r.vol >= 1e6 },
  exHealth: { test: (r) => r.sector !== 'Healthcare' },
}

function loadQuery() {
  try {
    const q = JSON.parse(localStorage.getItem(QUERY_KEY)) ?? {}
    return {
      // a persisted scan key that has left the vocabulary must not survive the
      // restore — the bar would highlight nothing while the fallback filtered
      scan: SCAN_DEFS.some((d) => d.key === q.scan) ? q.scan : 'confluence',
      states: Array.isArray(q.states) ? q.states.filter((s) => STATE_WORDS.includes(s)) : [],
      // themes became a SET when the handoff from the Themes page landed: that
      // page lets you compare three, and carrying only the first would be a
      // silent narrowing of the reader's own choice. A stored single string is
      // a query written before that and is read as a set of one.
      themes: Array.isArray(q.themes) ? q.themes.filter((x) => typeof x === 'string')
        : typeof q.theme === 'string' && q.theme ? [q.theme] : [],
      gates: Array.isArray(q.gates) ? q.gates.filter((g) => g in GATES) : [],
    }
  } catch {
    return { scan: 'confluence', states: [], themes: [], gates: [] }
  }
}

export default function ScreenerPage() {
  const { universe, loading, gated, dropped } = useUniverse()
  const groups = useGroups()
  const heat = useHeatingUp()
  const { data: market } = useMarketData()
  const { t: tr } = useLanguage()

  const initial = useMemo(loadQuery, [])
  const [scan, setScan] = useState(initial.scan)
  const [states, setStates] = useState(() => new Set(initial.states))
  const [themes, setThemes] = useState(() => new Set(initial.themes))
  const [gates, setGates] = useState(() => new Set(initial.gates))
  const [search, setSearch] = useState('')

  useEffect(() => {
    try {
      localStorage.setItem(QUERY_KEY,
        JSON.stringify({ scan, states: [...states], themes: [...themes], gates: [...gates] }))
    } catch { /* storage may be unavailable; the query is still live in memory */ }
  }, [scan, states, themes, gates])

  /**
   * The handoff from the Themes page — the one piece of state that crosses
   * between the morning's three pages, and it crosses in ONE direction only.
   *
   * Andy's call, 2026-08-18, made against the count: narrowing this table to
   * the themes picked next door takes it from 2,548 rows to 42, which is a
   * shortlist. Doing the same to Today's List takes 277 names to 5 and empties
   * twelve of its seventeen scans — a page whose whole premise is that the six
   * questions were already asked would come up reading zero, and that zero
   * would be the filter's, not the market's. So the handoff stops here.
   *
   * THE RULE IT FOLLOWS: state may only ever land in a control that is already
   * on screen and can be switched off by hand. It lands in the theme filter,
   * which draws a chip per theme with its own ×. It never becomes a hidden
   * predicate.
   */
  const handoff = useThemeHandoff(themes, setThemes)

  // A persisted theme the taxonomy no longer publishes must be cleared, not
  // kept: with the name held but the lookup failing, no rows are filtered while
  // the receipt still claims the intersection — a filter that asserts itself
  // and does nothing.
  useEffect(() => {
    if (!themes.size || groups.loading || !groups.themes.length) return
    const live = new Set(groups.themes.map((t) => t.group))
    if ([...themes].every((n) => live.has(n))) return
    setThemes(new Set([...themes].filter((n) => live.has(n))))
  }, [themes, groups.loading, groups.themes])

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

  // ribbons by home group — proxy themes carry bars-backed ribbons today;
  // composite themes and industries fill in from the archive as it matures
  const ribbonByHome = useMemo(() => {
    const m = new Map()
    for (const g of groups.industries) if (g.ribbon?.length) m.set(`industry|${g.group}`, g.ribbon)
    for (const t of groups.themes) if (t.ribbon?.length) m.set(`theme|${t.group}`, t.ribbon)
    return m
  }, [groups.industries, groups.themes])

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
  const themeRows = useMemo(
    () => (themes.size ? groups.themes.filter((t) => themes.has(t.group)) : []),
    [themes, groups.themes])

  // Rows before the state filter, so state counts can be honest facet counts
  // of what each state word would keep — not of the whole world.
  const preState = useMemo(() => {
    if (!universe) return []
    const byTicker = new Map(universe.map((r) => [r.ticker, r]))
    // the UNION of the chosen themes. Intersecting them would ask "which name
    // is in all three", which is not a question anyone picking three different
    // themes is asking.
    const themeSet = themeRows.length
      ? new Set(themeRows.flatMap((t) => t.tickers ?? [])) : null
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
      // one home per stock: the pipeline's primary_group (smallest curated
      // theme, industry as the total fallback) — never chosen by the frontend
      const home = s?.primary_group ?? indName
      const homeKind = s?.primary_kind ?? (indName ? 'industry' : null)
      out.push({
        ticker: t,
        inUniverse: Boolean(u),
        heat: heatByTicker.get(t) ?? null,
        state: s?.state ?? null,
        ind: indName,
        indState: indName ? industryState.get(indName) ?? null : null,
        home,
        homeKind,
        // primary_kind carries a third value, industry_unscored — its home is
        // still an industry, so the ribbon lookup normalises; the raw kind
        // stays on the row for the tooltip to state honestly
        homeRibbon: home && homeKind
          ? ribbonByHome.get(`${homeKind === 'industry_unscored' ? 'industry' : homeKind}|${home}`) ?? null
          : null,
        vol5050: u?.vol_5d_50d ?? null,
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
        cap: u?.market_cap ?? null,
        vol: u?.avg_volume ?? null,
      })
    }
    return out
  }, [universe, activeScan, themeRows, search, groups.stocks, heatByTicker, industryState, ribbonByHome])

  // null while groups.json is absent — "Leading 0" is a reading, not a shrug
  const statesLoaded = !groups.loading && !groups.error

  const untouched = scan === 'confluence' && !states.size && !themes.size && !search.trim()
  // A state or theme filter needs the group layer; while groups.json is in
  // flight (or failed) the filter has nothing measured to act on, and a page
  // that filtered anyway would ship an empty set claiming to be a reading.
  const needsGroups = states.size > 0 || themes.size > 0
  const viewReady = activeScan.loaded && (!needsGroups || statesLoaded)
  const stateCounts = useMemo(() => {
    if (!statesLoaded) return null
    const c = {}
    for (const r of preState) if (r.state) c[r.state] = (c[r.state] ?? 0) + 1
    return c
  }, [preState, statesLoaded])

  // Facet counts: what each gate would keep from the current cut, so the number
  // beside a toggle answers "what does turning this on cost me" before it is on.
  const gateCounts = useMemo(() => ({
    liquid: preState.filter(GATES.liquid.test).length,
    exHealth: preState.filter(GATES.exHealth.test).length,
  }), [preState])

  const rows = useMemo(() => {
    let kept = states.size ? preState.filter((r) => r.state && states.has(r.state)) : preState
    for (const g of gates) kept = kept.filter(GATES[g].test)
    const sorted = [...kept]
    if (scan === 'confluence') {
      sorted.sort((a, b) => (b.heat?.score ?? -1) - (a.heat?.score ?? -1))
    } else {
      sorted.sort((a, b) => (b.rs3 ?? -1) - (a.rs3 ?? -1))
    }
    return sorted
  }, [preState, states, scan, gates])

  const noState = states.size ? preState.filter((r) => !r.state).length : 0
  /**
   * Rows the gate did not stop.
   *
   * The confluence scan's ticker set comes from the heat ledger, which is not
   * filtered by `tradeable` — so names outside the gated universe arrive in
   * the table anyway, join against nothing, and render every measured column
   * as a dash. The rows themselves are already honest about it (their state
   * cell reads "not in the universe"), but the line above the table was not:
   * it said flatly that untradeable names are not in this table while seven of
   * twenty-five of them were. A gate that reports an exclusion it did not
   * perform is worse than no note, because the note is what the reader trusts
   * instead of counting.
   */
  const ungated = rows.filter((r) => !r.inUniverse).length

  /**
   * What the same themes would give without the scan on top.
   *
   * The handoff lands on whatever scan was last open, and the default is
   * Confluence — fifty names. Three themes intersected with fifty names is
   * routinely nothing, which is a true reading and a useless arrival. Rather
   * than switching the scan on the reader's behalf (this page never chooses a
   * vocabulary word for them), it counts what the wider view holds and offers
   * the number. Only computed when the current view came up empty, and only
   * while a theme filter is on.
   */
  const themeWide = useMemo(() => {
    if (!themes.size || rows.length || !themeRows.length || !universe?.length) return null
    const inThemes = new Set(themeRows.flatMap((t) => t.tickers ?? []))
    return universe.filter((r) => inThemes.has(r.ticker)).length
  }, [themes, rows.length, themeRows, universe])

  // Numbers only — the selections themselves are already visible as underlines,
  // and restating them here was the duplication Andy flagged.
  const receipt = useMemo(() => {
    if (!activeScan.loaded) return `${activeScan.label} — ${tr('scr.loading')}`
    if (needsGroups && !statesLoaded) return tr('scr.groupLayerLoading') 
    // the hidden count is honesty, not a headline — it rides the tooltip so a
    // four-digit number does not sit beside the one the reader came for
    return `${rows.length} rows`
  }, [rows.length, activeScan, noState, needsGroups, statesLoaded, tr])

  // The narrator follows the selection: the default view keeps the ledger's
  // own sentence, and any other vocabulary choice gets one computed from the
  // rows it actually produced — never typed, and it names its selection.
  const selectionReading = useMemo(() => {
    if (untouched || !viewReady) return null
    // built from the selection itself — the receipt is just a row count now,
    // and deriving words from it would couple the sentence to a display string
    const parts = [activeScan.label]
    if (states.size) parts.push([...states].join('+'))
    if (themes.size) parts.push([...themes].join(' + '))
    if (search.trim()) parts.push(`"${search.trim().toUpperCase()}"`)
    const desc = parts.join(' ∩ ')
    if (!rows.length) {
      return `Nothing clears ${desc} today — an empty intersection is a reading, not an error.`
    }
    const census = {}
    for (const r of rows) if (r.state) census[r.state] = (census[r.state] ?? 0) + 1
    const censusStr = ['Leading', 'Weakening', 'Improving', 'Lagging']
      .filter((st) => census[st]).map((st) => `${census[st]} ${st}`).join(' · ')
    const front = rows.slice(0, 3).map((r) => r.ticker).join(', ')
    return `${rows.length} names under ${desc}. States: ${censusStr || 'none measured'}. Front of the board: ${front}.`
  }, [scan, states, themes, search, activeScan, rows])

  const conditions = market?.breadth?.conditions
  const toggleState = (st) => setStates((prev) => {
    const next = new Set(prev)
    if (next.has(st)) next.delete(st); else next.add(st)
    return next
  })
  const toggleGate = (g) => setGates((prev) => {
    const next = new Set(prev)
    if (next.has(g)) next.delete(g); else next.add(g)
    return next
  })

  if (loading) {
    return (
      <div className="text-[var(--color-text-muted)] text-[14px] font-medium uppercase tracking-wide text-center py-20">
        Loading universe...
      </div>
    )
  }

  return (
    <div>
      <PageHeader group="market" title={tr('nav.screener')}
        meta={[
          conditions ? (
            <a key="mc" href="#/breadth" className="no-underline text-inherit"
               title="the fifteen conditions behind this number — the page-level third light">
              Market conditions{' '}
              <b className="text-[17px] text-[var(--color-text-bold)]">{conditions.today}</b>
              {' '}· {conditions.positive_today} of {conditions.n_votes} positive
            </a>
          ) : 'Market conditions — not loaded',
          heat?.as_of ?? '',
        ]} />

      {/* the whole confluence ledger, not the old 25-row display slice — the
          sentence says "here", and here now holds all fifty */}
      <Reading text={untouched ? readScreener(heat) : selectionReading} />

      {/* THE BAND (Andy, 2026-08-18): the chart runs across the page, under
          the one-line read and ABOVE the scan and state controls, with the
          shortlist beside it on the right.

          It was a tall card in a right-hand column and he rejected that. He is
          right, and the reason is the page's own argument: the controls and the
          table below them are one instrument, and a column parked alongside
          them for the full height of the page reads as a second instrument
          competing with the first. Across the top it reads as what it is — the
          thing you look at before you start filtering, and the tray you drop
          names into while you do.

          Wide also suits the chart itself. A month of candles in a 380px
          column is a smear; across the page it is a chart. */}
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_300px]
                      xl:grid-cols-[minmax(0,1fr)_340px] gap-3 items-start mb-4">
        <PickedChart height={400} />
        <ShortlistTray />
      </div>

      <ScanBar
        scans={scans} scan={scan} onScan={setScan}
        stateCounts={stateCounts} states={states} onToggleState={toggleState}
        gates={gates} gateCounts={gateCounts} onToggleGate={toggleGate}
        themes={groups.themes} chosen={themes}
        onTheme={(name) => setThemes((cur) => {
          const next = new Set(cur)
          if (name == null) next.clear()
          else if (next.has(name)) next.delete(name)
          else next.add(name)
          return next
        })}
        handoff={handoff}
        search={search} onSearch={setSearch}
        receipt={receipt}
        gateNote={gated
          ? `${dropped.toLocaleString()} untradeable names are not in this table`
            + (ungated
              ? ` — except ${ungated} this scan carried in from the heat ledger, which is not gated. They are marked, and carry no readings.`
              : '')
          : 'the tradeable column has not shipped yet — this table still includes names you cannot trade'}
        gateOn={gated}
        wideNote={themeWide != null && scan !== 'all' && themeWide > 0
          ? { n: themeWide, onWiden: () => setScan('all') }
          : null}
        hiddenNote={noState ? `${noState} rows carry no state and are not shown` : null} />
      {viewReady ? (
        // key: normalized search only — a trailing space changes nothing
        // about the row set and must not remount the table
        <StockTable key={`${scan}|${[...states].join()}|${[...themes].join()}|${search.trim().toUpperCase()}`}
                    rows={rows} defaultSort={scan === 'confluence' ? 'heat' : 'rs3'} />
      ) : (
        <p className="m-0 py-8 text-center text-[12.5px] text-[var(--color-text-muted)]">
          {!activeScan.loaded
            ? `${activeScan.label} ${tr('scr.notLoadedYet')}`
            : tr('scr.groupLayerLoading')}
        </p>
      )}

      <HowToRead>
        <p>
          <b>Heat</b> — how many screens a name stacked (quality screens ×3).
          Only the confluence 50 carry one. The caret opens the appearances
          behind the number.
        </p>
        <p>
          <b>Align</b> — left dot: own RS 3M in the top third. Right dot: its
          industry&rsquo;s state. The market-conditions number in the header is the
          third light. Three lit together is the aligned setup; they are never
          summed into a score.
        </p>
        <p>
          <b>Group trend</b> is the state history of the stock&rsquo;s home group —
          the pipeline&rsquo;s one-home-per-stock pointer (smallest curated theme,
          industry as the total fallback). Each cell is a completed fortnight
          from the group archive, which began 2026-08-07: cells light as
          fortnights complete, and a dashed cell is a fortnight the archive has
          not lived through yet — never a zero. <b>Vol 5d/50d</b> is the
          five-day average volume over the fifty-day; names younger than fifty
          sessions print a dash because their fifty-day average does not exist.
          Click a row for the full tear-sheet.
        </p>
      </HowToRead>
    </div>
  )
}
