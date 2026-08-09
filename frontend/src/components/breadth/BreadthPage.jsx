import { useMemo } from 'react'
import VerdictBanner from './VerdictBanner'
import StateBoard from './StateBoard'
import MarketStateSummary from './MarketStateSummary'
import HealthChart from './HealthChart'
import RatioChart from './RatioChart'
import SpreadChart from './SpreadChart'
import DangerPanel from './DangerPanel'
import MarketMonitor from './MarketMonitor'
import ClassicBreadth from './ClassicBreadth'
import BreadthCharts from './BreadthCharts'
import BreadthTable from './BreadthTable'
import TimeMachineBar from './TimeMachineBar'
import { useTimeMachine } from './useTimeMachine'

export default function BreadthPage({ data }) {
  const tm = useTimeMachine()
  const liveBreadth = data?.breadth
  const breadth = (tm.active && tm.sliced) ? tm.sliced.breadth : liveBreadth
  const mh = (tm.active && tm.sliced) ? tm.sliced.marketHealth : data?.market_health

  // Memoised so the HealthChart setup closure (and therefore the chart redraw
  // effect) only sees a new overlay when the underlying history actually
  // changes — not on every render. Declared before the early return so hook
  // order stays stable.
  const history = breadth?.history
  const t2108Overlay = useMemo(
    () => (history
      ? { dates: history.dates, values: history.rows.map((r) => r.t2108) }
      : null),
    [history],
  )

  if (!liveBreadth) {
    return (
      <div className="space-y-3">
        <TimeMachineBar tm={tm} />
        <div className="text-[var(--color-text-muted)] text-sm font-medium uppercase tracking-wide py-8 text-center">
          No breadth data available
        </div>
      </div>
    )
  }

  const verdict = breadth.verdict
  const rows = breadth.history?.rows ?? []

  return (
    <div className="space-y-3">
      <TimeMachineBar tm={tm} />
      <VerdictBanner verdict={verdict} dataQuality={breadth.data_quality} />
      <StateBoard board={breadth.state_board} session={rows[rows.length - 1]?.date} />
      <MarketStateSummary mm={breadth.mm} breadth={breadth.breadth} verdict={verdict} />
      {mh && !mh.stale && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <HealthChart title="SPY Market Health" block={mh.spy} state={verdict?.spy_state} t2108={t2108Overlay} />
          <HealthChart title="QQQ Market Health" block={mh.qqq} state={verdict?.qqq_state} t2108={t2108Overlay} />
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <RatioChart rows={rows} />
        <SpreadChart rows={rows} />
      </div>
      {mh && !mh.stale && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <DangerPanel title="SPY danger signals" danger={mh.spy?.danger} />
          <DangerPanel title="QQQ danger signals" danger={mh.qqq?.danger} />
        </div>
      )}
      <MarketMonitor data={breadth} />
      <ClassicBreadth data={breadth} />
      <BreadthCharts data={breadth} />
      <BreadthTable data={breadth} />
    </div>
  )
}
