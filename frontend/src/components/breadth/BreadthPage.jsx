import MarketMonitor from './MarketMonitor'
import ClassicBreadth from './ClassicBreadth'
import BreadthCharts from './BreadthCharts'
import BreadthTable from './BreadthTable'

export default function BreadthPage({ data }) {
  const breadth = data?.breadth

  if (!breadth) {
    return (
      <div className="text-[var(--color-text-muted)] text-sm font-medium uppercase tracking-wide py-8 text-center">
        No breadth data available
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <MarketMonitor data={breadth} />
      <ClassicBreadth data={breadth} />
      <BreadthCharts data={breadth} />
      <BreadthTable data={breadth} />
    </div>
  )
}
