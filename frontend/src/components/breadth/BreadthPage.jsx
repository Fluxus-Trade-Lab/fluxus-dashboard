import VerdictBanner from './VerdictBanner'
import MarketStateSummary from './MarketStateSummary'
import HealthChart from './HealthChart'
import RatioChart from './RatioChart'
import SpreadChart from './SpreadChart'
import DangerPanel from './DangerPanel'
import MarketMonitor from './MarketMonitor'
import ClassicBreadth from './ClassicBreadth'
import BreadthCharts from './BreadthCharts'
import BreadthTable from './BreadthTable'

export default function BreadthPage({ data }) {
  const breadth = data?.breadth
  const mh = data?.market_health

  if (!breadth) {
    return (
      <div className="text-[var(--color-text-muted)] text-sm font-medium uppercase tracking-wide py-8 text-center">
        No breadth data available
      </div>
    )
  }

  const verdict = breadth.verdict
  const t2108Overlay = breadth.history
    ? { dates: breadth.history.dates, values: breadth.history.rows.map((r) => r.t2108) }
    : null
  const rows = breadth.history?.rows ?? []

  return (
    <div className="space-y-3">
      <VerdictBanner verdict={verdict} dataQuality={breadth.data_quality} />
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
      {mh && (
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
