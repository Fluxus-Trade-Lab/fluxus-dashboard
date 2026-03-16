import MarketMonitor from './MarketMonitor'
import ClassicBreadth from './ClassicBreadth'
import BreadthCharts from './BreadthCharts'

export default function BreadthPage({ data }) {
  const breadth = data?.breadth

  if (!breadth) {
    return (
      <div className="text-stone-400 text-sm font-medium uppercase tracking-wide py-8 text-center">
        No breadth data available
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <MarketMonitor data={breadth} />
      <ClassicBreadth data={breadth} />
      <BreadthCharts data={breadth} />
    </div>
  )
}
