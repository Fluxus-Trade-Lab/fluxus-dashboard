import { useEffect, useMemo, useRef, useState } from 'react'
import PageHeader from '../PageHeader'
import DataFreshnessBadge from '../shared/DataFreshnessBadge'
import { useGroups } from '../../hooks/useGroups'
import { useGroupsHistory } from '../../hooks/useGroupsHistory'
import { useRotationChecks } from './useRotationChecks'
import {
  questionLists, defaultPicks, stateCounts, summaryParts, measurable, wkAccel, DEFAULT_THRESHOLDS,
} from './rotationLogic'
import FieldChart from './FieldChart'
import LeadershipChart from './LeadershipChart'
import SwarmChart from './SwarmChart'
import QuestionLists from './QuestionLists'
import CompareChart from './CompareChart'
import './rotation.css'

/**
 * Rotation — five instruments, one selection.
 *
 * Andy, 2026-09-02/03: the Themes page's job is a funnel that answers three
 * questions (what is building, what is igniting from the bottom, what is
 * fading), told with charts, interactive, on the newest data; keep the
 * existing Themes page as it is. So this is a NEW page beside it, not a
 * rewrite: the field with a time scrubber and eight-session tails, the
 * leadership counts over the archive, the three lists with live thresholds,
 * Compare with the state ribbons and the verify/watch checks (F3), and the
 * acceleration swarm. Click any dot, row or chip: up to three selected, shared
 * by every instrument; Escape clears.
 *
 * Compare draws the QUARTER excess over the archive, which is what
 * groups_history.json carries. The daily relative-to-SPY line the prototype
 * drew needs per-session returns in that file — a §七 ask to the data lane —
 * and the card says which of the two it is drawing.
 */
export const STATE_COLOUR = {
  Leading: 'var(--rot-lead)', Improving: 'var(--rot-impr)', Weakening: 'var(--rot-weak)', Lagging: 'var(--rot-lag)',
}
export const COHORTS = [
  { key: 'theme', label: 'Themes' }, { key: 'sector', label: 'Sectors' }, { key: 'factor', label: 'Factors' }, { key: 'all', label: 'All' },
]

export default function RotationPage() {
  const { themes, date, benchmark, loading, error } = useGroups()
  const history = useGroupsHistory()
  const [cohort, setCohort] = useState('theme')
  const [selected, setSelected] = useState([])
  const [thresholds, setThresholds] = useState(DEFAULT_THRESHOLDS)
  const [scrub, setScrub] = useState(null)          // null = the latest session
  const [playing, setPlaying] = useState(false)
  const [tip, setTip] = useState(null)
  const checks = useRotationChecks(date)

  const all = useMemo(() => themes.filter(measurable), [themes])
  const rows = useMemo(() => all.filter((r) => cohort === 'all' || r.kind === cohort), [all, cohort])
  const dates = history.data?.dates ?? []
  const historyOf = useMemo(() => { const g = history.data?.groups ?? {}; return (name) => g[name] ?? null }, [history.data])
  const at = scrub == null ? Math.max(0, dates.length - 1) : scrub
  const lists = useMemo(() => questionLists(rows, thresholds), [rows, thresholds])
  const counts = useMemo(() => stateCounts(rows, historyOf), [rows, historyOf])
  const parts = useMemo(() => summaryParts(rows, lists, counts), [rows, lists, counts])

  const picked = selected.map((n) => all.find((r) => r.group === n)).filter(Boolean)
  const shown = picked.length ? picked : defaultPicks(lists)

  const toggle = (name) => setSelected((s) => {
    if (s.includes(name)) return s.filter((n) => n !== name)
    return [...s.slice(-2), name]
  })
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') setSelected([]) }
    window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey)
  }, [])
  // drop selections that left the cohort. `rows` is a fresh array every render
  // (useGroups filters on the way out), so this effect runs every render: it
  // must return the SAME state object when nothing changed, or React re-renders
  // forever ("Maximum update depth exceeded" — caught on the first open).
  useEffect(() => {
    setSelected((s) => (s.some((n) => !rows.some((r) => r.group === n)) ? s.filter((n) => rows.some((r) => r.group === n)) : s))
  }, [rows])
  // play: one session every 550ms, stops at the end
  const timer = useRef(null)
  useEffect(() => {
    if (!playing) { clearInterval(timer.current); return undefined }
    setScrub(0)
    timer.current = setInterval(() => setScrub((i) => {
      const next = Math.min(dates.length - 1, (i ?? 0) + 1)
      if (next >= dates.length - 1) setPlaying(false)
      return next
    }), 550)
    return () => clearInterval(timer.current)
  }, [playing, dates.length])

  const showTip = (e, content) => setTip({ x: e.clientX + 14, y: e.clientY + 14, content })
  const hideTip = () => setTip(null)
  const counters = counts
  const accelerating = rows.filter((r) => wkAccel(r) > 0).length

  if (loading) return <div className="text-[13px] text-[var(--color-text-muted)]">Loading themes…</div>
  if (error) return <div className="text-[13px] text-[var(--color-text-muted)]">Could not load groups.json.</div>

  return (
    <div className="rot space-y-5">
      <PageHeader group="market" title="Rotation"
        meta={[`vs ${benchmark} · ${date} · ${rows.length} of ${all.length} groups · ${dates.length} sessions of archive`,
               <DataFreshnessBadge key="fresh" sessionDate={date} />]} />

      {/* headline card: the summary sentence, the cohort switch, the legend */}
      <div className="rot-card">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <p className="m-0 text-[17px] leading-[1.35] font-semibold max-w-[60ch]" style={{ textWrap: 'balance' }}>
            {parts.map((p, i) => <span key={i}>{p.text}{p.strong && <b className="font-bold text-white">{p.strong}</b>}{' '}</span>)}
          </p>
          <div className="rot-seg inline-flex gap-[2px] rounded-[12px] p-[3px]" style={{ background: 'var(--rot-well)' }} role="group" aria-label="cohort">
            {COHORTS.map((c) => (
              <button key={c.key} type="button" aria-pressed={cohort === c.key} onClick={() => setCohort(c.key)}>
                {c.label} <span className="font-mono">{c.key === 'all' ? all.length : all.filter((r) => r.kind === c.key).length}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="flex flex-wrap gap-4 mt-3 text-[11px]" style={{ color: 'var(--rot-muted)' }}>
          {['Leading', 'Weakening', 'Improving', 'Lagging'].map((s) => (
            <span key={s}><i className="inline-block w-[9px] h-[9px] rounded-full mr-[6px] align-[-1px]" style={{ background: STATE_COLOUR[s] }} />{s} {counters[s]}</span>
          ))}
          <span style={{ color: 'var(--rot-faint)' }}>blue = ahead of {benchmark} on the quarter · orange = behind · lighter = accelerating</span>
          <span className="ml-auto">click any dot, row or chip to select up to three · esc clears</span>
        </div>
      </div>

      {/* FIELD */}
      <div className="rot-card">
        <h2 className="m-0 text-[17px] font-bold" style={{ letterSpacing: '-.02em' }}>
          {dates[at] ?? date}: {stateCounts(rows, historyOf, dates.length ? at : null).Leading} leading, {stateCounts(rows, historyOf, dates.length ? at : null).Lagging} lagging
        </h2>
        <div className="text-[11px] mb-3" style={{ color: 'var(--rot-muted)' }}>quarter excess vs {benchmark} → · acceleration ↑ · dot size = names in the theme · tails = the last eight sessions · scrub or play the date</div>
        <FieldChart rows={rows} historyOf={historyOf} dates={dates} at={at} selected={selected} onSelect={toggle} onTip={showTip} offTip={hideTip} colourOf={STATE_COLOUR} />
        <div className="flex flex-wrap items-center gap-3 mt-3 text-[11px]" style={{ color: 'var(--rot-muted)' }}>
          <button type="button" className="rot-btn" onClick={() => setPlaying((p) => !p)} disabled={!dates.length}>{playing ? '⏸ pause' : '▶ play'}</button>
          <input type="range" className="rot-range" min={0} max={Math.max(0, dates.length - 1)} step={1} value={at} aria-label="session"
                 onChange={(e) => { setPlaying(false); setScrub(+e.target.value) }} disabled={!dates.length} />
          <span className="font-mono font-semibold" style={{ color: 'var(--rot-paper)' }}>{dates[at] ?? '—'}</span>
        </div>
        <div className="rot-src">Rotation field · excess_3m × rs_accel · groups_history.json {dates[0] ?? '—'} → {dates[dates.length - 1] ?? '—'}</div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* LEADERSHIP */}
        <div className="rot-card">
          <h2 className="m-0 text-[17px] font-bold" style={{ letterSpacing: '-.02em' }}>
            {dates.length
              ? `Leaders ${counters.Leading - stateCounts(rows, historyOf, 0).Leading >= 0 ? 'up' : 'down'} ${Math.abs(counters.Leading - stateCounts(rows, historyOf, 0).Leading)}, laggards ${counters.Lagging - stateCounts(rows, historyOf, 0).Lagging >= 0 ? 'up' : 'down'} ${Math.abs(counters.Lagging - stateCounts(rows, historyOf, 0).Lagging)} since ${dates[0].slice(5)}`
              : 'No archive yet'}
          </h2>
          <div className="text-[11px] mb-3" style={{ color: 'var(--rot-muted)' }}>themes in each state, every session · hover for the count · click a day to scrub the field there</div>
          <LeadershipChart rows={rows} historyOf={historyOf} dates={dates} at={at} onScrub={(i) => { setPlaying(false); setScrub(i) }} onTip={showTip} offTip={hideTip} colourOf={STATE_COLOUR} />
          <div className="rot-src">Leadership over time · four-state counts · {dates.length} sessions</div>
        </div>

        {/* SWARM */}
        <div className="rot-card">
          <h2 className="m-0 text-[17px] font-bold" style={{ letterSpacing: '-.02em' }}>{accelerating} of {rows.length} are moving faster this week than the three before</h2>
          <div className="text-[11px] mb-3" style={{ color: 'var(--rot-muted)' }}>this week's pace minus the prior three weeks' pace, per week · right = speeding up · ringed = on one of the three lists</div>
          <SwarmChart rows={rows} lists={lists} selected={selected} onSelect={toggle} onTip={showTip} offTip={hideTip} colourOf={STATE_COLOUR} />
          <div className="rot-src">Acceleration swarm · rs_0_1w − rs_1w_1m ÷ 3.2 · groups.json {date}</div>
        </div>
      </div>

      {/* QUESTIONS */}
      <div className="rot-card">
        <h2 className="m-0 text-[17px] font-bold" style={{ letterSpacing: '-.02em' }}>
          Building {lists.q1.length} · igniting {lists.q2.length} · fading {lists.q3.length} — {rows.length - lists.q1.length - lists.q2.length - lists.q3.length} are just travelling
        </h2>
        <div className="text-[11px] mb-3" style={{ color: 'var(--rot-muted)' }}>shapes across the four stretches · 3–6m · 1–3m · prior 3w · this week · the two thresholds are live</div>
        <QuestionLists lists={lists} selected={selected} onSelect={toggle} thresholds={thresholds} onThresholds={setThresholds} colourOf={STATE_COLOUR} />
        <div className="rot-src">Three questions · building · igniting · fading · thresholds are placeholders</div>
      </div>

      {/* COMPARE */}
      <div className="rot-card">
        <CompareChart shown={shown} picked={!!picked.length} dates={dates} historyOf={historyOf} benchmark={benchmark}
                      onSelect={toggle} checks={checks} onTip={showTip} offTip={hideTip} colourOf={STATE_COLOUR} lists={lists} />
        <div className="rot-src">Compare · quarter excess over the archive · checks kept in this browser per session date</div>
      </div>

      {tip && (
        <div className="rot-tip" style={{ left: tip.x, top: tip.y }} role="status">
          {tip.content}
        </div>
      )}
    </div>
  )
}
