import { usePortfolio } from './context/PortfolioContext'
import { usePrices } from './hooks/usePrices'
import StatCard from './ui/StatCard'
import Button from './ui/Button'
import { fmtCur, fmtPct, clr, MASK } from './lib/portfolioFormat'
import { useLanguage } from '../../i18n/LanguageContext'

export default function Header({ portfolioValue, totalPL, totalReturnPct, cashAvailable, cashPct, openCount, onShowForm, showForm, onExport, onImport, onShowSettings, onReset }) {
  const { state, dispatch } = usePortfolio()
  const { refreshOpenPositions } = usePrices()
  const { t } = useLanguage()
  const pm = state.privacyMode

  return (
    <div className="px-6 py-4 border-b border-[var(--color-border)] flex items-center justify-between flex-wrap gap-3">
      <div>
        <div className="text-lg font-bold flex items-center gap-1.5">
          {t('pf.title')}
          {state.gasUrl && state.syncToken && (
            <span className="text-xs" title={
              state.syncStatus === 'success' ? `Synced ${state.lastSyncTime ? new Date(state.lastSyncTime).toLocaleTimeString() : ''}` :
              state.syncStatus === 'syncing' ? 'Syncing...' :
              state.syncStatus === 'error' ? 'Sync failed' : 'Not synced'
            }>
              {state.syncStatus === 'success' && <span className="text-[var(--color-profit)]">●</span>}
              {state.syncStatus === 'syncing' && <span className="text-[var(--color-signal-caution)] animate-pulse">●</span>}
              {state.syncStatus === 'error' && <span className="text-[var(--color-loss)]">●</span>}
              {state.syncStatus === 'idle' && <span className="text-[var(--color-text-muted)]">○</span>}
            </span>
          )}
        </div>
        <div className="text-xs text-[var(--color-text-muted)]">{t('pf.starting')}: {pm ? MASK : fmtCur(state.startingCapital)}</div>
      </div>

      <div className="flex gap-3 items-center flex-wrap">
        <StatCard label={t('pf.stat.portfolio')} value={pm ? MASK : fmtCur(portfolioValue)} />
        <StatCard label={t('pf.stat.pl')} value={pm ? MASK : fmtCur(totalPL)} colorClass={pm ? '' : clr(totalPL)} />
        <StatCard label={t('pf.stat.return')} value={fmtPct(totalReturnPct)} colorClass={clr(totalReturnPct)} />
        <StatCard label={t('pf.stat.cash')} value={pm ? fmtPct(cashPct) : fmtCur(cashAvailable)} />
        <StatCard
          label="Names"
          value={openCount}
          colorClass={openCount >= 14 ? 'text-[var(--color-loss)]' : openCount >= 12 ? 'text-[var(--color-signal-caution)]' : ''}
          sub={openCount >= 14 ? '⚠ greed zone — stop adding' : openCount >= 12 ? 'heat building' : undefined}
        />
      </div>

      <div className="flex gap-1 flex-wrap">
        <Button onClick={onShowForm}>{showForm ? t('pf.btn.cancel') : t('pf.btn.trade')}</Button>
        <Button variant="ghost" onClick={refreshOpenPositions} disabled={state.loading}>
          {state.loading ? t('pf.btn.fetching') : t('pf.btn.refresh')}
        </Button>
        <Button variant="ghost" onClick={onExport}>{t('pf.btn.export')}</Button>
        <Button variant="ghost" onClick={onImport}>{t('pf.btn.import')}</Button>
        <Button variant="ghost" onClick={onShowSettings}>{t('pf.btn.settings')}</Button>
        <button
          onClick={() => dispatch({ type: 'TOGGLE_PRIVACY' })}
          className="px-2.5 py-1.5 rounded text-xs font-medium cursor-pointer border transition-colors bg-transparent border-[var(--color-input-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-hover-bg)]"
          title={pm ? t('pf.sync.showValues') : t('pf.sync.hideValues')}
        >
          {pm ? `◉ ${t('pf.btn.private')}` : `○ ${t('pf.btn.private')}`}
        </button>
        <Button variant="ghost" onClick={onReset} className="!text-[var(--color-loss)]">{t('pf.btn.reset')}</Button>
      </div>
    </div>
  )
}
