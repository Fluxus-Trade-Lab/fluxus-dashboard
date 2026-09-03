import { useEffect, useMemo, useState } from 'react'
import PageHeader from '../PageHeader'
import DataFreshnessBadge from '../shared/DataFreshnessBadge'
import HowToRead from '../HowToRead'
import { useGroups } from '../../hooks/useGroups'
import { useThemeLadder } from '../../hooks/useThemeLadder'
import { boardsOf, defaultPicks, Y_MAX, R2W_LAG, PRIOR_WEEKS } from './rotationLogic'
import TerrainCard from './TerrainCard'
import PointsCard from './PointsCard'
import FluxCard from './FluxCard'
import './rotation.css'

/**
 * Rotation — Point · Line · Plane. Three cards, one selection, no sentences
 * on the cards (Andy 2026-09-03; brief §18.22).
 *
 *   TERRAIN   the two-week board's four-state counts by session — a plane
 *   MOMENTUM & ACCELERATION   every theme as a dot on three axes — points
 *   FLUX      up to three themes against the benchmark over ten weeks — lines
 *
 * The temperature of the market is read off the two-week board
 * (`theme_ladder.json`), not the month-scale state that sizes positions:
 * that is the reading TSF's Current Leadership makes, and on 2026-09-02 the
 * two boards agreed name-for-name 60% and on the strong/weak axis 89%,
 * against 23% for the month-scale state (brief §18.20). The dots and the
 * lines are the 30 themes; the plane counts every group the ladder measures.
 */
export default function RotationPage() {
  const { themes, date, benchmark, loading, error } = useGroups()
  const ladder = useThemeLadder()
  const [selected, setSelected] = useState([])

  const rows = useMemo(() => themes.filter((t) => t.kind === 'theme'), [themes])
  const seriesOf = useMemo(() => { const s = ladder.data?.series ?? {}; return (n) => s[n] ?? null }, [ladder.data])
  const boards = useMemo(() => boardsOf(rows, seriesOf), [rows, seriesOf])
  const picks = useMemo(() => defaultPicks(boards), [boards])
  const names = selected.length ? selected : picks
  const seriesDates = ladder.data?.series_dates ?? []
  const stateDates = ladder.data?.history?.['2w']?.dates ?? null
  const shown = names.map((n) => ({ name: n, rel: seriesOf(n)?.rel ?? null, states: seriesOf(n)?.states_2w ?? null }))

  // the first click builds on the three default lines rather than replacing them: a reader adding a fourth name drops the oldest
  const toggle = (name) => setSelected((s) => { const base = s.length ? s : picks; return base.includes(name) ? base.filter((n) => n !== name) : [...base.slice(-2), name] })
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') setSelected([]) }
    window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey)
  }, [])

  if (loading) return <div className="text-[13px] text-[var(--color-text-muted)]">Loading themes…</div>
  if (error) return <div className="text-[13px] text-[var(--color-text-muted)]">Could not load groups.json.</div>

  const ladderDate = ladder.data?.as_of ?? null
  const missing = shown.filter((o) => !o.rel?.length).map((o) => o.name)

  return (
    <div className="rot space-y-5">
      <PageHeader group="market" title="Rotation"
        meta={[`vs ${benchmark} · ${date} · ${rows.length} themes${ladderDate ? ` · ladder ${ladderDate}` : ''}`, <DataFreshnessBadge key="fresh" sessionDate={date} />]} />

      <TerrainCard ladder={ladder.data} selected={names} onSelect={toggle} />
      <PointsCard boards={boards} selected={names} onSelect={toggle} />
      <FluxCard shown={shown} dates={seriesDates} stateDates={stateDates} benchmark={benchmark} picked={!!selected.length} onSelect={toggle} />

      <HowToRead>
        <p><b>Terrain.</b> Every group the ladder measures, placed on the two-week board each session: level = the last ten sessions' excess over {benchmark}, momentum = the last five; Leading when both are positive, Weakening when only the level is, Improving when only the momentum is, Lagging when neither. Stacked, darkest = Leading. The window select moves the board to an earlier fortnight; expand lists who sat where on that fortnight's last session.</p>
        <p><b>Momentum &amp; Acceleration.</b> 爆发 RS 0–2w: the two-week strength, the same arithmetic as the Terrain's level axis. 转折 Acceleration: this week's excess minus the prior three weeks' excess per week (÷{PRIOR_WEEKS}). 持续 Quarter: the quarter's excess. Dots grow with the value; the top five and bottom two are named. Click any dot or name to put it on the Flux line; Escape clears.</p>
        <p><b>Flux.</b> The two-week strength every session for up to three themes — the top of each board until you pick. The y-axis is fixed at ±{Math.round(Y_MAX * 100)}%; what overflows is clipped and the hover still reads the true value. Under each line, that theme's two-week state per session. The benchmark is the zero line.{seriesDates.length ? ` Window ${seriesDates[R2W_LAG] ?? seriesDates[0]} → ${seriesDates[seriesDates.length - 1]}.` : ''}{missing.length ? ` No series yet for ${missing.join(', ')}.` : ''}{boards.approx ? ' Until the ladder ships its series, RS 0–2w is approximated as this week plus one week of the prior three.' : ''}</p>
        <p><b>Data.</b> groups.json {date} for the dots; theme_ladder.json {ladderDate ?? '(missing)'} for the plane and the lines, equal-weighted baskets of each theme's constituents over {benchmark}. Counts are not comparable across dashboards that weight themes differently — the change is.</p>
      </HowToRead>
    </div>
  )
}
