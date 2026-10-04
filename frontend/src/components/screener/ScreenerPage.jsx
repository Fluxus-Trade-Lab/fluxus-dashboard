import { useState, useMemo, useEffect } from 'react'
import PageHeader from '../PageHeader'
import PickedChart from '../ticker/PickedChart'
import { useThemeHandoff } from '../../hooks/useThemeHandoff'
import { useChartPick } from '../../hooks/useChartPick'
import { useMyShortlist } from '../../hooks/useMyShortlist'
import { useWatchlist } from '../../hooks/useWatchlist'
import { useHeatingUp } from '../../hooks/useHeatingUp'
import { useUniverse } from '../../hooks/useUniverse'
import { useGroups } from '../../hooks/useGroups'
import { useMarketData } from '../../hooks/useMarketData'
import { SCAN_DEFS, scanTickers } from '../../lib/scanSets'
import ScanBar from './ScanBar'
import ResultsTable, { DEFAULT_TOP_N } from './ResultsTable'
import MarketStrip from './MarketStrip'
import { StepBar, ScanList } from './funnel/FunnelSteps'
import { useFocusDay } from './funnel/useFocusDay'
import { PENDING_SETUPS, noteFor, isFlagged } from './funnel/funnelMath'
import {
  FOCUS_SETUPS, DEFAULT_STEP, isWater, rowsPassingGate, setupCards, stepCounts, panelScans, byRs,
} from './funnel/stepMath'
import { panelName } from '../watchlist/panelName'
import { useLanguage } from '../../i18n/LanguageContext'

/**
 * The Screener after the merge with Today's List (Andy 2026-10-04: 「选A」, then
 * 「可以」 on the preview; 「先把已经有内容的做出来上线。管线没有到位的待会儿做」).
 *
 * Top to bottom: header with the shortlist count · one line of market
 * readings · a preset switch (funnel | custom) · the step bar and one scan
 * list, or the custom controls · ONE results table. The funnel cards, the
 * market card, the browser-only shortlist tray and the second "all data"
 * block are gone; the custom screen is the old free table's controls feeding
 * the same results table.
 *
 * The custom half keeps the old page's query logic as it was (scan / state /
 * theme / gate / ticker search, the Themes-page handoff, the persisted query).
 */
const QUERY_KEY = 'screener-query'
const PRESET_KEY = 'screener-preset'
const STATE_WORDS = ['Leading', 'Weakening', 'Improving', 'Lagging']

/** Reads the pipeline's own verdicts; see useUniverse for why nothing is re-derived. */
const GATES = {
  liquid: { test: (r) => r.tradeable === true },
  exHealth: { test: (r) => r.sector !== 'Healthcare' },
}

/** Pending scans the scan list draws dashed. `liquidLeader` is left out: the
 *  Liquid Leaders panel now supplies it, so it is live under the panel's name. */
const DASHED = PENDING_SETUPS.filter((k) => k !== 'liquidLeader')

function loadQuery() {
  try {
    const q = JSON.parse(localStorage.getItem(QUERY_KEY)) ?? {}
    return {
      scan: SCAN_DEFS.some((d) => d.key === q.scan) ? q.scan : 'confluence',
      states: Array.isArray(q.states) ? q.states.filter((s) => STATE_WORDS.includes(s)) : [],
      themes: Array.isArray(q.themes) ? q.themes.filter((x) => typeof x === 'string')
        : typeof q.theme === 'string' && q.theme ? [q.theme] : [],
      gates: Array.isArray(q.gates) ? q.gates.filter((g) => g in GATES) : [],
    }
  } catch {
    return { scan: 'confluence', states: [], themes: [], gates: [] }
  }
}

function loadPreset() {
  try { return localStorage.getItem(PRESET_KEY) === 'custom' ? 'custom' : 'funnel' } catch { return 'funnel' }
}

export default function ScreenerPage() {
  const { universe, all, loading } = useUniverse()
  const groups = useGroups()
  const heat = useHeatingUp()
  const { data: market } = useMarketData()
  const { data: watchlist } = useWatchlist()
  const { doc } = useFocusDay()
  const myShortlist = useMyShortlist()
  const { t: tr, lang } = useLanguage()
  const { pick: chartPick, symbol: charted } = useChartPick()

  const [preset, setPreset] = useState(loadPreset)
  const [setup, setSetup] = useState('pullback')
  const [step, setStep] = useState(DEFAULT_STEP)
  const [water, setWater] = useState(false)
  const [topN, setTopN] = useState(DEFAULT_TOP_N)
  const [chartOpen, setChartOpen] = useState(false)

  useEffect(() => {
    try { localStorage.setItem(PRESET_KEY, preset) } catch { /* storage unavailable */ }
  }, [preset])

  // ── custom screen: the old free table's query ─────────────────────────
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
    } catch { /* storage may be unavailable */ }
  }, [scan, states, themes, gates])

  const handoff = useThemeHandoff(themes, setThemes)
  // a theme the arrival handed over switches the page to the custom screen,
  // where the theme filter it landed in is on screen
  useEffect(() => { if (handoff?.length) setPreset('custom') }, [handoff])

  useEffect(() => {
    if (!themes.size || groups.loading || !groups.themes.length) return
    const live = new Set(groups.themes.map((t) => t.group))
    if ([...themes].every((n) => live.has(n))) return
    setThemes(new Set([...themes].filter((n) => live.has(n))))
  }, [themes, groups.loading, groups.themes])

  // ── lookups shared by both halves ─────────────────────────────────────
  const byTicker = useMemo(() => new Map((all ?? []).map((r) => [r.ticker, r])), [all])
  const groupState = useMemo(() => {
    const m = new Map()
    for (const g of groups.industries) m.set(`industry|${g.group}`, g.state)
    for (const g of groups.themes) m.set(`theme|${g.group}`, g.state)
    return m
  }, [groups.industries, groups.themes])

  /** a table row from a universe row: home group (theme, else industry) and its state */
  const fromUniverse = (ticker, from) => {
    const u = byTicker.get(ticker)
    const s = groups.stocks?.[ticker]
    const home = s?.primary_group ?? u?.industry ?? null
    const kind = s?.primary_kind === 'theme' ? 'theme' : 'industry'
    const gstate = home ? groupState.get(`${kind}|${home}`) ?? null : null
    const note = noteFor(doc, ticker, lang)
    return {
      t: ticker, rs: u?.rs_rating ?? null, group: home, gstate,
      waterState: kind === 'theme' ? gstate : null,
      e21: u?.ema21_atr_dist ?? null, s50: u?.sma50_atr_dist ?? null,
      m1: u?.perf_1m == null ? null : u.perf_1m * 100,
      hi: u?.high_52w_dist == null ? null : u.high_52w_dist * 100,
      note, flagged: isFlagged(note), from,
      entry: { group: home, group_state: gstate, rs_1m: u?.rs_1m ?? null },
    }
  }

  /** a table row from a focus.json card */
  const fromCard = (c, from) => {
    const g = c.theme ?? c.ind ?? null
    const note = noteFor(doc, c.t, lang)
    return {
      t: c.t, rs: c.rs ?? null, group: g?.name ?? null, gstate: g?.state ?? null,
      waterState: c.theme?.state ?? null,
      e21: c.ema21_atr ?? null, s50: c.sma50_atr ?? null, m1: c.perf_1m ?? null, hi: c.hi52 ?? null,
      note, flagged: isFlagged(note), from,
      entry: { group: g?.name ?? null, group_state: g?.state ?? null, rs_1m: byTicker.get(c.t)?.rs_1m ?? null },
    }
  }

  // ── funnel ────────────────────────────────────────────────────────────
  const panels = useMemo(() => panelScans(watchlist), [watchlist])
  const scanList = useMemo(() => [
    ...FOCUS_SETUPS.filter((k) => doc?.setups?.[k]).map((k) => ({
      key: k, kind: 'setup', live: true, count: doc.setups[k].rows?.length ?? 0,
      label: tr(`funnel.setup.${k}`), from: tr(`funnel.setup.${k}`),
    })),
    ...panels.map((p) => ({
      key: p.key, kind: 'panel', live: p.measured, count: p.tickers.length,
      label: panelName(tr, lang, p.key, p.label), from: p.label, tickers: p.tickers,
    })),
    ...DASHED.map((k) => ({ key: k, kind: 'pending', live: false, label: tr(`funnel.setup.${k}`) })),
  ], [doc, panels, tr, lang])
  const activeScan = scanList.find((s) => s.key === setup && s.live) ?? scanList[0]

  const pickScan = (k) => {
    setSetup(k)
    const s = scanList.find((x) => x.key === k)
    if (s?.kind === 'panel' && step !== 'gate') setStep('setup')
  }

  const funnelBase = useMemo(() => {
    if (!doc || !activeScan) return []
    if (step === 'gate') {
      return rowsPassingGate(all, doc.rule?.gate).map((u) => fromUniverse(u.ticker, null))
    }
    if (activeScan.kind === 'setup') {
      return setupCards(doc, activeScan.key, step).map((c) => fromCard(c, activeScan.from))
    }
    return (activeScan.tickers ?? []).map((tk) => fromUniverse(tk, activeScan.from))
  // fromCard/fromUniverse close over the lookups listed here
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc, activeScan, step, all, byTicker, groups.stocks, groupState, lang])

  const counts = useMemo(() => {
    if (!doc || !activeScan) return {}
    const inWater = funnelBase.filter((r) => isWater(r.waterState)).length
    if (activeScan.kind === 'setup') {
      const c = stepCounts(doc, activeScan.key)
      return { ...c, water: step === 'focus' ? c.water : inWater }
    }
    return { gate: doc.counts?.gate ?? null, setup: activeScan.tickers.length, qual: null, focus: null,
             water: inWater }
  }, [doc, activeScan, step, funnelBase])

  const funnelRows = useMemo(() => {
    const kept = water ? funnelBase.filter((r) => isWater(r.waterState)) : funnelBase
    return [...kept].sort(byRs)
  }, [funnelBase, water])

  // ── custom screen ─────────────────────────────────────────────────────
  const heatByTicker = useMemo(() => {
    const m = new Map()
    for (const r of heat?.rows ?? []) m.set(r.ticker, r)
    return m
  }, [heat])

  const scans = useMemo(() => SCAN_DEFS.map((d) => {
    if (d.key === 'all') return { ...d, count: universe?.length ?? null, set: null, loaded: Boolean(universe) }
    if (d.key === 'confluence') {
      const loaded = Boolean(heat?.rows)
      return { ...d, loaded, count: loaded ? heatByTicker.size : null,
               set: loaded ? new Set(heatByTicker.keys()) : null }
    }
    const json = market?.[d.key]
    if (!json) return { ...d, count: null, set: null, loaded: false }
    const set = scanTickers(json, d.container)
    return { ...d, count: set.size, set, loaded: true }
  }), [universe, heat, heatByTicker, market])
  const customScan = scans.find((s) => s.key === scan) ?? scans[0]

  const themeRows = useMemo(
    () => (themes.size ? groups.themes.filter((t) => themes.has(t.group)) : []),
    [themes, groups.themes])

  // rows before the state filter, so the state words can carry facet counts
  const preState = useMemo(() => {
    if (!universe) return []
    const themeSet = themeRows.length ? new Set(themeRows.flatMap((t) => t.tickers ?? [])) : null
    const q = search.trim().toUpperCase()
    const tickers = customScan.set ? [...customScan.set] : universe.map((r) => r.ticker)
    const out = []
    for (const tk of tickers) {
      if (themeSet && !themeSet.has(tk)) continue
      if (q && !tk.toUpperCase().includes(q)) continue
      const u = byTicker.get(tk)
      out.push({ ticker: tk, state: groups.stocks?.[tk]?.state ?? null,
                 sector: u?.sector ?? null, tradeable: u?.tradeable ?? null })
    }
    return out
  }, [universe, customScan, themeRows, search, groups.stocks, byTicker])

  const statesLoaded = !groups.loading && !groups.error
  const stateCounts = useMemo(() => {
    if (!statesLoaded) return null
    const c = {}
    for (const r of preState) if (r.state) c[r.state] = (c[r.state] ?? 0) + 1
    return c
  }, [preState, statesLoaded])
  const gateCounts = useMemo(() => ({
    liquid: preState.filter(GATES.liquid.test).length,
    exHealth: preState.filter(GATES.exHealth.test).length,
  }), [preState])

  const customRows = useMemo(() => {
    let kept = states.size ? preState.filter((r) => r.state && states.has(r.state)) : preState
    for (const g of gates) kept = kept.filter(GATES[g].test)
    return kept.map((r) => fromUniverse(r.ticker, null)).sort(byRs)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preState, states, gates, byTicker, groups.stocks, groupState, doc, lang])

  const themeWide = useMemo(() => {
    if (!themes.size || customRows.length || !themeRows.length || !universe?.length) return null
    const inThemes = new Set(themeRows.flatMap((t) => t.tickers ?? []))
    return universe.filter((r) => inThemes.has(r.ticker)).length
  }, [themes, customRows.length, themeRows, universe])

  const toggle = (set) => (v) => set((prev) => {
    const next = new Set(prev)
    if (next.has(v)) next.delete(v); else next.add(v)
    return next
  })

  const onChart = (tk) => {
    if (tk !== charted) chartPick(tk)
    setChartOpen(true)
    requestAnimationFrame(() => document.getElementById('screener-chart')
      ?.scrollIntoView?.({ behavior: 'smooth', block: 'start' }))
  }

  if (loading) {
    return (
      <div className="text-[var(--color-text-muted)] text-[13px] font-medium uppercase tracking-wide text-center py-20">
        {tr('sc.loadingUniverse')}
      </div>
    )
  }

  const funnel = preset === 'funnel'
  const rows = funnel ? funnelRows : customRows
  const title = funnel
    ? `${activeScan?.label ?? ''} · ${tr(`scx.step.${step}`)}`
    : tr('scx.results')
  const segBtn = (on) => `border-0 rounded-[7px] px-3 py-1 text-[13px] cursor-pointer
    transition-transform duration-100 ease-out active:scale-[0.97]
    ${on ? 'bg-[var(--color-surface)] text-[var(--color-text-bold)] font-semibold'
         : 'bg-transparent text-[var(--color-text-secondary)]'}`

  return (
    <div>
      <PageHeader group="market" title={tr('nav.screener')}
        meta={[
          <a key="sl" href="#/watchlist/shortlist" data-testid="shortlist-chip"
             className="inline-flex items-baseline gap-1 rounded-full border border-[var(--color-border)]
                        bg-[var(--color-surface)] px-3 py-1 text-[13px] no-underline text-[var(--color-text)]
                        hover:bg-[var(--color-hover-bg)]">
            {tr('scx.shortlistChip', { n: myShortlist.length })}
          </a>,
        ]} />

      <MarketStrip market={doc?.market} />

      <section className="rounded-2xl border border-[var(--color-border-light)] bg-[var(--color-surface)] p-4 mb-4">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div role="group" aria-label={tr('scx.preset.aria')}
               className="inline-flex rounded-[9px] p-[3px] bg-[var(--color-surface-alt)]">
            <button type="button" aria-pressed={funnel} data-preset="funnel"
                    onClick={() => setPreset('funnel')} className={segBtn(funnel)}>{tr('scx.preset.funnel')}</button>
            <button type="button" aria-pressed={!funnel} data-preset="custom"
                    onClick={() => setPreset('custom')} className={segBtn(!funnel)}>{tr('scx.preset.custom')}</button>
          </div>
          {doc?.asof && (
            <span className="font-mono text-[13px] text-[var(--color-text-muted)]">{tr('scx.asof', { date: doc.asof })}</span>
          )}
        </div>

        {funnel ? (
          doc ? (
            <>
              <StepBar counts={counts} step={step} onStep={setStep} water={water} onWater={() => setWater((w) => !w)} />
              <ScanList scans={scanList} active={activeScan?.key} onPick={pickScan} />
            </>
          ) : (
            <p className="m-0 mb-3 text-[13px] text-[var(--color-text-muted)]">{tr('scx.noFocus')}</p>
          )
        ) : (
          <div className="mb-3">
            <ScanBar
              scans={scans.map((s) => ({ ...s, label: tr(`sc.scan.${s.key}`) }))} scan={scan} onScan={setScan}
              stateCounts={stateCounts} states={states} onToggleState={toggle(setStates)}
              gates={gates} gateCounts={gateCounts} onToggleGate={toggle(setGates)}
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
              receipt=""
              wideNote={themeWide != null && scan !== 'all' && themeWide > 0
                ? { n: themeWide, onWiden: () => setScan('all') } : null} />
          </div>
        )}

        <ResultsTable title={title} rows={rows} n={topN} setN={setTopN} onChart={onChart} />
      </section>

      {chartOpen && (
        <div id="screener-chart" className="mb-4">
          <PickedChart height={320} />
        </div>
      )}
    </div>
  )
}
