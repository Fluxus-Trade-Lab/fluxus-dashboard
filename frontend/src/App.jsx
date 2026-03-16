import { useMarketData } from './hooks/useMarketData'
import Layout from './components/Layout'

function App() {
  const { data, loading, lastUpdated, isOffline } = useMarketData()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg)]">
        <div className="text-[var(--color-text-muted)] text-sm font-medium uppercase tracking-wide">
          Loading market data...
        </div>
      </div>
    )
  }

  return <Layout data={data} lastUpdated={lastUpdated} isOffline={isOffline} />
}

export default App
