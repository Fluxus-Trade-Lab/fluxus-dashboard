import { useUniverse } from '../../hooks/useUniverse'

export default function ScreenerPage() {
  const { universe, loading } = useUniverse()

  if (loading) {
    return (
      <div className="text-stone-400 text-sm font-medium uppercase tracking-wide text-center py-20">
        Loading universe...
      </div>
    )
  }

  return (
    <div className="text-stone-500 text-sm text-center py-10">
      {universe ? `${universe.length} stocks loaded` : 'No data'}
    </div>
  )
}
