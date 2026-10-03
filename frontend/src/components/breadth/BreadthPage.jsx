import { useMemo } from 'react'
import PageHeader from '../PageHeader'
import DataFreshnessBadge from '../shared/DataFreshnessBadge'
import MarketStateSummary from './MarketStateSummary'
import RotationPanel from './RotationPanel'
import BenchmarkPanel from './BenchmarkPanel'
import CorrectionRiskPanel from './CorrectionRiskPanel'
import RatioChart from './RatioChart'
import SpreadChart from './SpreadChart'
import BreadthCharts from './BreadthCharts'
import BreadthTable from './BreadthTable'
import { useMarketLight } from '../../hooks/useMarketLight'
import MarketStateMin from './MarketStateMin'
import { useGroups } from '../../hooks/useGroups'
import { useGroupsHistory } from '../../hooks/useGroupsHistory'
import { useBreadthReplay } from '../../hooks/useBreadthReplay'
import { useUniverse } from '../../hooks/useUniverse'
import Reference from '../Reference'

/**
 * Market State — minimal (2026-10-03).
 *
 * Andy: 「重点是数据呈现，少注解和状态判断」「我让你按照书本的书序，但并不意味着，
 * 你每一个都要表明书本出处」「做到极简」 — and, on the preview
 * (artifact Mf9ZEf6kYwVNSp3sR9GMNb), 「对。market time machine 这个功能先下线。」
 *
 *   main screen = MarketStateMin: the verdict and the readings it is made of,
 *                 then index → breadth → leaders → themes → cross-asset, in the
 *                 book's order, with no citations or explanatory prose
 *   one fold    = the advanced breadth panels, data only
 *
 * Off the page (files kept): MorningRead (the six annotated steps), the
 * HowToRead block, the time machine, and the three internal panels — the
 * engine's votes, the conditions catalog, the board & chain.
 */
export default function BreadthPage({ data }) {
  const { data: ml } = useMarketLight()
  const groups = useGroups()
  const gh = useGroupsHistory()
  const replay = useBreadthReplay()
  const { universe } = useUniverse()
  const breadth = data?.breadth
  const mh = data?.market_health

  const universeByTicker = useMemo(
    () => Object.fromEntries((universe ?? []).map((r) => [r.ticker, r])),
    [universe],
  )
  const history = breadth?.history
  const t2108Overlay = useMemo(
    () => (history ? { dates: history.dates, values: history.rows.map((r) => r.t2108) } : null),
    [history],
  )

  if (!breadth) {
    return (
      <div className="text-[var(--color-text-muted)] text-[13px] font-medium uppercase tracking-wide py-8 text-center">
        No breadth data available
      </div>
    )
  }

  const verdict = breadth.verdict
  const rows = breadth.history?.rows ?? []
  const session = rows[rows.length - 1]?.date

  return (
    <div className="space-y-3">
      <PageHeader group="market" title="Market State"
        meta={[<DataFreshnessBadge key="fresh" sessionDate={session} />]} />

      <MarketStateMin ml={ml} etfs={data?.etf_data} signals={data?.signals} rows={rows}
                      paneRows={replay.rows ?? rows} loadingFull={replay.loading}
                      themes={groups.themes} groupsHistory={gh.data} universe={universeByTicker} />

      <div className="bg-[var(--color-surface)] rounded-3xl px-5 py-2">
        <Reference label="Advanced breadth" count={6}>
          <div className="space-y-4">
            <BreadthCharts data={breadth} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              <RatioChart rows={rows} />
              <SpreadChart rows={rows} />
            </div>
            <MarketStateSummary mm={breadth.mm} breadth={breadth.breadth} verdict={verdict} lastRow={rows[rows.length - 1]} />
            <CorrectionRiskPanel session={session} />
            <RotationPanel />
            {mh && !mh.stale && <BenchmarkPanel mh={mh} verdict={verdict} t2108={t2108Overlay} signals={data?.signals} />}
            <BreadthTable data={breadth} />
          </div>
        </Reference>
      </div>
    </div>
  )
}
