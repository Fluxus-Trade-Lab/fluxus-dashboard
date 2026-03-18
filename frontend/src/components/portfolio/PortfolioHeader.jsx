import { usePortfolio } from './context/PortfolioContext'
import { usePrices } from './hooks/usePrices'
import StatCard from './ui/StatCard'
import Button from './ui/Button'
import { fmtCur, fmtPct, clr, MASK } from './lib/portfolioFormat'

export default function Header({ portfolioValue, totalPL, totalReturnPct, cashAvailable, cashPct, openCount, onShowForm, showForm, onExport, onImport, onShowSettings, onReset }) {
  const { state, dispatch } = usePortfolio()
  const { refreshOpenPositions } = usePrices()
  const pm = state.privacyMode

  return (
    <div className="px-6 py-4 border-b border-[var(--color-border)] flex items-center justify-between flex-wrap gap-3">
      <div>
        <div className="text-lg font-bold">Portfolio Tracker</div>
        <div className="text-xs text-[var(--color-text-muted)]">Starting: {pm ? MASK : fmtCur(state.startingCapital)}</div>
      </div>

      <div className="flex gap-3 items-center flex-wrap">
        <StatCard label="Portfolio" value={pm ? MASK : fmtCur(portfolioValue)} />
        <StatCard label="P/L" value={pm ? MASK : fmtCur(totalPL)} colorClass={pm ? '' : clr(totalPL)} />
        <StatCard label="Return" value={fmtPct(totalReturnPct)} colorClass={clr(totalReturnPct)} />
        <StatCard label="Cash" value={pm ? fmtPct(cashPct) : fmtCur(cashAvailable)} />
        <StatCard label="Open" value={openCount} />
      </div>

      <div className="flex gap-1 flex-wrap">
        <Button onClick={onShowForm}>{showForm ? 'Cancel' : '+ Trade'}</Button>
        <Button variant="ghost" onClick={refreshOpenPositions} disabled={state.loading}>
          {state.loading ? 'Fetching...' : 'Refresh'}
        </Button>
        <Button variant="ghost" onClick={onExport}>Export</Button>
        <Button variant="ghost" onClick={onImport}>Import</Button>
        <Button variant="ghost" onClick={onShowSettings}>Settings</Button>
        <button
          onClick={() => dispatch({ type: 'TOGGLE_PRIVACY' })}
          className="px-2.5 py-1.5 rounded text-xs font-medium cursor-pointer border transition-colors bg-transparent border-[var(--color-input-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-hover-bg)]"
          title={pm ? 'Show values' : 'Hide values'}
        >
          {pm ? '◉ Private' : '○ Private'}
        </button>
        <Button variant="ghost" onClick={onReset} className="!text-red-500">Reset</Button>
      </div>
    </div>
  )
}
