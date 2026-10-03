import { useEffect, useMemo, useState } from 'react'
import PageHeader from '../PageHeader'
import DataFreshnessBadge from '../shared/DataFreshnessBadge'
import HowToRead from '../HowToRead'
import { useLanguage } from '../../i18n/LanguageContext'
import { dataName } from '../../i18n/names'
import { useGroups } from '../../hooks/useGroups'
import { useThemeLadder } from '../../hooks/useThemeLadder'
import { boardsOf, defaultPicks, Y_MAX, R2W_LAG, PRIOR_WEEKS } from './rotationLogic'
import TerrainCard from './TerrainCard'
import PointsCard from './PointsCard'
import ThemeBoardCard from './ThemeBoardCard'
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
  const { lang, t } = useLanguage()
  const { themes, date, benchmark, loading, error } = useGroups()
  const ladder = useThemeLadder()
  const [selected, setSelected] = useState([])
  const [wk, setWk] = useState(0)          // the Terrain window, shared with the names band
  const [open, setOpen] = useState(true)   // the names open by default; the '−' folds them away

  const rows = useMemo(() => themes.filter((t) => t.kind === 'theme'), [themes])
  const seriesOf = useMemo(() => { const s = ladder.data?.series ?? {}; return (n) => s[n] ?? null }, [ladder.data])
  const boards = useMemo(() => boardsOf(rows, seriesOf), [rows, seriesOf])
  const picks = useMemo(() => defaultPicks(boards), [boards])
  const names = selected.length ? selected : picks
  const seriesDates = ladder.data?.series_dates ?? []
  const stateDates = ladder.data?.history?.['2w']?.dates ?? null
  const shown = names.map((n) => ({ name: n, rel: seriesOf(n)?.rel ?? null, states: seriesOf(n)?.states_2w ?? null }))

  // The name just clicked becomes the focus — the orange one — and the others
  // fall back a place; a fourth drops the one that has been quiet longest.
  const toggle = (name) => setSelected((s) => {
    const base = s.length ? s : picks
    return base.includes(name) ? base.filter((n) => n !== name) : [name, ...base].slice(0, 3)
  })
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') setSelected([]) }
    window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey)
  }, [])

  if (loading) return <div className="text-[13px] text-[var(--color-text-muted)]">{t('rp.loading')}</div>
  if (error) return <div className="text-[13px] text-[var(--color-text-muted)]">{t('rp.error')}</div>

  const ladderDate = ladder.data?.as_of ?? null
  const missing = shown.filter((o) => !o.rel?.length).map((o) => o.name)

  return (
    <div className="rot space-y-5">
      <PageHeader group="market" title={t('nav.rotation')}
        meta={[ladderDate ? t('rp.metaLadder', { bench: benchmark, date, n: rows.length, ladder: ladderDate }) : t('rp.meta', { bench: benchmark, date, n: rows.length }), <DataFreshnessBadge key="fresh" sessionDate={date} />]} />

      <div className="rot-grid2">
        <TerrainCard ladder={ladder.data} loading={ladder.loading} wk={wk} setWk={setWk} open={open} onToggle={() => setOpen((v) => !v)} selected={names} onSelect={toggle} />
        <FluxCard shown={shown} dates={seriesDates} stateDates={stateDates} benchmark={benchmark} picked={!!selected.length} loading={ladder.loading} onSelect={toggle} />
      </div>
      <PointsCard boards={boards} selected={names} onSelect={toggle} />

      {/* 明细层：代理 ETF 的两周桶读数 + 每个主题成分股的四态分布。
          三卡维持原样，这块接在它们下面（Andy 2026-09-24）。 */}
      <ThemeBoardCard />

      <HowToRead>
        <p><b>{t('rp.how.terrainH')}</b>{t('rp.how.terrain', { bench: benchmark })}</p>
        <p><b>{t('rp.how.pointsH')}</b>{t('rp.how.points', { prior: PRIOR_WEEKS })}</p>
        <p><b>{t('rp.how.fluxH')}</b>{t('rp.how.flux', { ymax: Math.round(Y_MAX * 100) })}{seriesDates.length ? t('rp.how.fluxWindow', { from: seriesDates[R2W_LAG] ?? seriesDates[0], to: seriesDates[seriesDates.length - 1] }) : ''}{missing.length ? t('rp.how.fluxMissing', { names: missing.map((n) => dataName(n, lang)).join(lang === 'zh' ? '、' : ', ') }) : ''}{boards.approx ? t('rp.how.fluxApprox') : ''}</p>
        <p><b>{t('rp.how.dataH')}</b>{t('rp.how.data', { date, ladder: ladderDate ?? t('rp.how.missingFile'), bench: benchmark })}</p>
      </HowToRead>
    </div>
  )
}
