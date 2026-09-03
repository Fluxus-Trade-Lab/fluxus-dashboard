import { useEffect, useMemo, useRef, useState } from 'react'
import PageHeader from '../PageHeader'
import DataFreshnessBadge from '../shared/DataFreshnessBadge'
import HowToRead from '../HowToRead'
import { useGroups } from '../../hooks/useGroups'
import { useGroupsHistory } from '../../hooks/useGroupsHistory'
import { changeOf } from '../groups/stateChange'
import { useRotationChecks } from './useRotationChecks'
import {
  questionLists, defaultPicks, stateCounts, summaryParts, measurable, sideChanges, fastest, DEFAULT_THRESHOLDS, CHANGE_WINDOW,
} from './rotationLogic'
import FieldChart from './FieldChart'
import LeadershipChart from './LeadershipChart'
import SwarmChart from './SwarmChart'
import ShapesCard from './ShapesCard'
import CompareChart from './CompareChart'
import { fmtPct } from './TipBody'
import './rotation.css'

/**
 * Rotation — five instruments, one selection, no sentences on the cards.
 *
 * Andy, 2026-09-03, on the first version: the pair and greys only; the field
 * should read like a 吴冠中 — thin lines, space, a few points of colour; play
 * must glide; every card had been drowned in explanation and counts ("4 of
 * 30" — he wants the four names, not the four). So: titles are names, the
 * how-it-is-computed lives in How to read at the bottom with the two
 * threshold sliders, the verified mark is a small tick on the chip, and play
 * is a requestAnimationFrame glide between sessions.
 *
 * This page sits beside Themes; that page is untouched. Compare draws the
 * quarter excess over the archive (what groups_history.json carries); the
 * daily relative-to-SPY line waits on per-session returns in that file (§七).
 */
export const COHORTS = [
  { key: 'theme', label: 'Themes' }, { key: 'sector', label: 'Sectors' }, { key: 'factor', label: 'Factors' }, { key: 'all', label: 'All' },
]
const SESSION_MS = 900   // one archive session per 0.9s when playing

const Names = ({ list, empty = '—' }) => (list.length ? list.join(', ') : empty)

export default function RotationPage() {
  const { themes, date, benchmark, loading, error } = useGroups()
  const history = useGroupsHistory()
  const [cohort, setCohort] = useState('theme')
  const [selected, setSelected] = useState([])
  const [thresholds, setThresholds] = useState(DEFAULT_THRESHOLDS)
  const [t, setT] = useState(null)             // fractional session; null = the latest
  const [playing, setPlaying] = useState(false)
  const [tip, setTip] = useState(null)
  const checks = useRotationChecks(date)

  const all = useMemo(() => themes.filter(measurable), [themes])
  const rows = useMemo(() => all.filter((r) => cohort === 'all' || r.kind === cohort), [all, cohort])
  const dates = history.data?.dates ?? []
  const historyOf = useMemo(() => { const g = history.data?.groups ?? {}; return (name) => g[name] ?? null }, [history.data])
  const last = Math.max(0, dates.length - 1)
  const tt = t == null ? last : t
  const at = Math.round(tt)
  const lists = useMemo(() => questionLists(rows, thresholds), [rows, thresholds])
  const parts = useMemo(() => summaryParts(lists), [lists])
  const counts = useMemo(() => stateCounts(rows, historyOf, dates.length ? at : null), [rows, historyOf, dates.length, at])
  const changes = useMemo(() => sideChanges(rows, historyOf, at, changeOf, CHANGE_WINDOW), [rows, historyOf, at])
  const movers = useMemo(() => fastest(rows, 4, 2), [rows])

  const picked = selected.map((n) => all.find((r) => r.group === n)).filter(Boolean)
  const shown = picked.length ? picked : defaultPicks(lists)

  const toggle = (name) => setSelected((s) => (s.includes(name) ? s.filter((n) => n !== name) : [...s.slice(-2), name]))
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') setSelected([]) }
    window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey)
  }, [])
  // drop selections that left the cohort — returning the same object when
  // nothing changed, or React re-renders forever (`rows` is fresh each render)
  useEffect(() => {
    setSelected((s) => (s.some((n) => !rows.some((r) => r.group === n)) ? s.filter((n) => rows.some((r) => r.group === n)) : s))
  }, [rows])
  // play: a glide, not steps — requestAnimationFrame from the first session to the last
  const raf = useRef(null)
  useEffect(() => {
    if (!playing) { cancelAnimationFrame(raf.current); return undefined }
    let cur = 0, prev = performance.now()
    setT(0)
    const step = (now) => {
      cur = Math.min(last, cur + (now - prev) / SESSION_MS); prev = now
      setT(cur)
      if (cur >= last) { setPlaying(false); return }
      raf.current = requestAnimationFrame(step)
    }
    raf.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf.current)
  }, [playing, last])

  const showTip = (e, content) => setTip({ x: e.clientX + 14, y: e.clientY + 14, content })
  const hideTip = () => setTip(null)

  if (loading) return <div className="text-[13px] text-[var(--color-text-muted)]">Loading themes…</div>
  if (error) return <div className="text-[13px] text-[var(--color-text-muted)]">Could not load groups.json.</div>

  return (
    <div className="rot space-y-5">
      <PageHeader group="market" title="Rotation"
        meta={[`vs ${benchmark} · ${date} · ${rows.length} of ${all.length} groups`, <DataFreshnessBadge key="fresh" sessionDate={date} />]} />

      {/* the headline: names, and the cohort switch */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <p className="m-0 text-[17px] leading-[1.35] max-w-[64ch]" style={{ textWrap: 'balance' }}>
          {parts.map((p, i) => <span key={i}>{p.text}{p.strong && <b className="font-semibold">{p.strong}</b>}{' '}</span>)}
        </p>
        <div className="rot-seg inline-flex gap-[2px] rounded-[12px] p-[3px] bg-[var(--color-bg)]" role="group" aria-label="cohort">
          {COHORTS.map((c) => <button key={c.key} type="button" aria-pressed={cohort === c.key} onClick={() => setCohort(c.key)}>{c.label}</button>)}
        </div>
      </div>

      {/* FIELD */}
      <div className="rot-card">
        <h2 className="rot-title">
          <span style={{ color: 'var(--color-took)' }}><Names list={changes.up} /></span>
          <span className="text-[var(--color-text-muted)]"> · </span>
          <span style={{ color: 'var(--color-refused)' }}><Names list={changes.down} /></span>
        </h2>
        <FieldChart rows={rows} historyOf={historyOf} dates={dates} t={tt} selected={selected} onSelect={toggle} onTip={showTip} offTip={hideTip} />
        <div className="flex flex-wrap items-center gap-3 mt-2 text-[11px] text-[var(--color-text-muted)]">
          <button type="button" className="rot-btn" onClick={() => setPlaying((p) => !p)} disabled={!dates.length}>{playing ? 'pause' : 'play'}</button>
          <input type="range" className="rot-range" min={0} max={last} step={0.01} value={tt} aria-label="session"
                 onChange={(e) => { setPlaying(false); setT(+e.target.value) }} disabled={!dates.length} />
          <span className="font-mono text-[var(--color-text)]">{dates[at] ?? date}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[2fr_3fr] gap-5">
        {/* LEADERSHIP */}
        <div className="rot-card">
          <h2 className="rot-title"><b>{counts.Leading}</b> leading <span className="text-[var(--color-text-muted)]">·</span> <b>{counts.Lagging}</b> lagging</h2>
          <LeadershipChart rows={rows} historyOf={historyOf} dates={dates} at={at} onScrub={(i) => { setPlaying(false); setT(i) }} onTip={showTip} offTip={hideTip} />
        </div>
        {/* SWARM */}
        <div className="rot-card">
          <h2 className="rot-title"><Names list={movers.up.map((r) => r.group)} empty="Nobody" /> <span className="text-[var(--color-text-muted)] font-normal">speeding up</span></h2>
          <SwarmChart rows={rows} lists={lists} historyOf={historyOf} dates={dates} selected={selected} onSelect={toggle} onTip={showTip} offTip={hideTip}
                      named={[...movers.up, ...movers.down].map((r) => r.group)} />
        </div>
      </div>

      {/* SHAPES */}
      <div className="rot-card">
        <ShapesCard lists={lists} selected={selected} onSelect={toggle} />
      </div>

      {/* COMPARE */}
      <div className="rot-card">
        <CompareChart shown={shown} picked={!!picked.length} dates={dates} historyOf={historyOf} onSelect={toggle} checks={checks} onTip={showTip} offTip={hideTip} />
      </div>

      <HowToRead>
        <p><b>Colour.</b> Blue: the group moved to a stronger state over the last {CHANGE_WINDOW} sessions. Red: to a weaker one. Ink: unchanged. The ribbons under Compare read the four states as greys, darkest = Leading, then Weakening, Improving, Lagging.</p>
        <p><b>The field.</b> Right of centre = ahead of {benchmark} on the quarter; above = accelerating (last month's excess above the two months before it). Each thin line is a group's whole path through the archive; the dot is where it is on the scrubbed session. Play glides one session per {SESSION_MS / 1000}s.</p>
        <p><b>Leaders and laggards.</b> How many groups sit in each state, every session of the archive. Click a day to scrub the field there.</p>
        <p><b>Speeding up.</b> This week's pace minus the prior three weeks' pace, per week. The fastest on each end are named. A ring means the group sits on one of the three lists.</p>
        <p><b>The three lists.</b> Building: prior three weeks up, this week up and at least as fast, and not already strong one to three months ago. Igniting: weak for months (three to six months ago, or the quarter, negative), quiet for the prior three weeks, this week up and faster. Fading: ahead for months, the acceleration slope negative, this week still slower than the prior three. The shape beside each name is the four stretches — three to six months, one to three months, the prior three weeks, this week — as per-week pace, this week in ink.</p>
        <div className="flex flex-wrap gap-6 mt-3 text-[11px] text-[var(--color-text-muted)]">
          <label className="grid grid-cols-[auto_1fr_auto] gap-2 items-center min-w-[280px]">
            <span>Building: "not strong before" cap</span>
            <input type="range" className="rot-range" min={0} max={0.15} step={0.005} value={thresholds.q1PriorCap} onChange={(e) => setThresholds({ ...thresholds, q1PriorCap: +e.target.value })} />
            <span className="font-mono text-[var(--color-text)]">{fmtPct(thresholds.q1PriorCap)}</span>
          </label>
          <label className="grid grid-cols-[auto_1fr_auto] gap-2 items-center min-w-[280px]">
            <span>Igniting: "prior 3w quiet" cap</span>
            <input type="range" className="rot-range" min={0} max={0.06} step={0.005} value={thresholds.q2PriorCap} onChange={(e) => setThresholds({ ...thresholds, q2PriorCap: +e.target.value })} />
            <span className="font-mono text-[var(--color-text)]">{fmtPct(thresholds.q2PriorCap)}</span>
          </label>
        </div>
        <p><b>Compare.</b> The quarter excess of up to three groups over the archive — the top of each list until you pick. The tick on a chip marks the group as verified for this session date; the marks stay in this browser and can be copied as JSON here:{' '}
          <button type="button" className="rot-btn" onClick={() => { try { navigator.clipboard?.writeText(checks.exportJson()) } catch { /* clipboard may be unavailable */ } }}>copy checks</button>
          {' '}({checks.verified} verified today).</p>
        <p><b>Data.</b> groups.json {date}; groups_history.json {dates.length ? `${dates[0]} → ${dates[dates.length - 1]}` : '(empty)'}. A group missing from the archive on a day is not counted that day.</p>
      </HowToRead>

      {tip && <div className="rot-tip" style={{ left: tip.x, top: tip.y }} role="status">{tip.content}</div>}
    </div>
  )
}
