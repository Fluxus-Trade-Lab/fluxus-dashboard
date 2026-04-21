import { useState, useMemo, useCallback } from 'react'
import { usePortfolio } from '../../portfolio/context/PortfolioContext'
import { analyzeTrades, computeDemonStats, getActiveCircuitBreakers, DEMONS, DEFAULT_RULES } from '../../portfolio/lib/demonFinder'
import { fmtPct, fmt, clr } from '../../portfolio/lib/portfolioFormat'
import DemonRulesConfig from './DemonRulesConfig'

const RULES_KEY = 'fluxus-demon-rules'

function loadRules() {
  try {
    const raw = localStorage.getItem(RULES_KEY)
    return raw ? { ...DEFAULT_RULES, ...JSON.parse(raw) } : DEFAULT_RULES
  } catch { return DEFAULT_RULES }
}

function saveRules(rules) {
  localStorage.setItem(RULES_KEY, JSON.stringify(rules))
}

function CircuitBreakerBanner({ breakers }) {
  if (breakers.length === 0) return null

  return (
    <div className="bg-red-500/10 border border-[var(--color-loss)] rounded-lg px-5 py-4">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">&#x1F6D1;</span>
        <span className="text-sm font-bold text-[var(--color-loss)]">STOP TRADING</span>
      </div>
      {breakers.map(b => (
        <p key={b.id} className="text-xs text-[var(--color-text)] mt-1">
          <strong>{b.name}</strong> triggered {b.currentStreak} times in a row. Review these trades before taking new entries.
        </p>
      ))}
    </div>
  )
}

function DemonCard({ stat, isActive, onClick }) {
  const borderColor = stat.currentStreak >= 6
    ? 'border-[var(--color-loss)]'
    : stat.currentStreak >= 3
      ? 'border-[var(--color-signal-caution)]'
      : 'border-[var(--color-border)]'

  return (
    <button
      onClick={onClick}
      className={`bg-[var(--color-surface)] border ${borderColor} rounded-lg px-3 py-3 text-left cursor-pointer transition-colors hover:bg-[var(--color-hover-bg)] ${
        isActive ? 'ring-2 ring-[var(--color-accent)]' : ''
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm">{stat.icon}</span>
        {stat.currentStreak >= 3 && (
          <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${
            stat.currentStreak >= 6 ? 'bg-red-500/10 text-[var(--color-loss)]' : 'bg-amber-500/10 text-[var(--color-signal-caution)]'
          }`}>
            {stat.currentStreak} streak
          </span>
        )}
      </div>
      <div className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-1">
        {stat.name}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-lg font-mono font-bold text-[var(--color-text-bold)]">{stat.fireCount}</span>
        <span className="text-[10px] text-[var(--color-text-muted)]">/ 30 trades</span>
      </div>
      <div className="text-[10px] text-[var(--color-text-muted)] mt-1">
        {fmtPct(stat.fireRate)} fire rate
      </div>
      {stat.winRateWith != null && stat.winRateWithout != null && (
        <div className="text-[10px] mt-1.5 pt-1.5 border-t border-[var(--color-border-light)]">
          <span className="text-[var(--color-text-muted)]">Win rate: </span>
          <span className={clr(stat.winRateWith - stat.winRateWithout)}>
            {fmt(stat.winRateWith, 0)}%
          </span>
          <span className="text-[var(--color-text-muted)]"> vs </span>
          <span className="text-[var(--color-text-secondary)]">{fmt(stat.winRateWithout, 0)}%</span>
        </div>
      )}
    </button>
  )
}

function TradeRow({ trade }) {
  const demons = trade.demons || []

  return (
    <div className="flex items-center gap-3 px-3 py-2 border-b border-[var(--color-border-light)] hover:bg-[var(--color-hover-bg)]">
      {/* Clean/flagged indicator */}
      <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] flex-shrink-0 ${
        trade.isClean
          ? 'bg-green-500/10 text-[var(--color-profit)]'
          : 'bg-red-500/10 text-[var(--color-loss)]'
      }`}>
        {trade.isClean ? '\u2713' : demons.length}
      </span>

      {/* Trade info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs font-medium text-[var(--color-text-bold)]">{trade.ticker}</span>
          <span className="text-[10px] text-[var(--color-text-muted)] uppercase">{trade.direction}</span>
          <span className="text-[10px] text-[var(--color-text-muted)]">{trade.entryDate}</span>
        </div>
        {/* Demon badges */}
        {demons.length > 0 && (
          <div className="flex gap-1 mt-1 flex-wrap">
            {demons.map(dId => {
              const d = DEMONS.find(x => x.id === dId)
              return (
                <span
                  key={dId}
                  title={d?.desc}
                  className="px-1.5 py-0.5 text-[9px] font-medium rounded bg-red-500/10 text-[var(--color-loss)]"
                >
                  {d?.icon} {d?.name}
                </span>
              )
            })}
          </div>
        )}
      </div>

      {/* R/R and result */}
      <div className="text-right flex-shrink-0">
        {trade.rr != null && (
          <div className={`font-mono text-xs ${clr(trade.rr)}`}>{fmt(trade.rr, 1)}R</div>
        )}
        {trade.totalReturnPct != null && (
          <div className={`font-mono text-[10px] ${clr(trade.totalReturnPct)}`}>
            {trade.totalReturnPct > 0 ? '+' : ''}{fmt(trade.totalReturnPct, 1)}%
          </div>
        )}
      </div>
    </div>
  )
}

export default function DemonFinderSection({ enriched, dailyPrices }) {
  const { dispatch } = usePortfolio()
  const [rules, setRules] = useState(loadRules)
  const [activeFilter, setActiveFilter] = useState(null) // demon id or 'clean'

  const handleUpdateRules = useCallback((newRules) => {
    setRules(newRules)
    saveRules(newRules)
  }, [])

  const analyzed = useMemo(
    () => analyzeTrades(enriched, dailyPrices, rules),
    [enriched, dailyPrices, rules]
  )

  const stats = useMemo(
    () => computeDemonStats(analyzed, rules),
    [analyzed, rules]
  )

  const breakers = useMemo(
    () => getActiveCircuitBreakers(stats),
    [stats]
  )

  // Filter trade list
  const filteredTrades = useMemo(() => {
    const reversed = [...analyzed].reverse() // most recent first
    if (!activeFilter) return reversed
    if (activeFilter === 'clean') return reversed.filter(t => t.isClean)
    return reversed.filter(t => t.demons.includes(activeFilter))
  }, [analyzed, activeFilter])

  const cleanCount = analyzed.filter(t => t.isClean).length
  const flaggedCount = analyzed.length - cleanCount

  if (enriched.length === 0) {
    return <div className="text-center py-16 text-[var(--color-text-muted)]">No trades to analyze.</div>
  }

  return (
    <div className="space-y-4">
      {/* Rules config */}
      <DemonRulesConfig rules={rules} onUpdate={handleUpdateRules} />

      {/* Circuit breaker banner */}
      <CircuitBreakerBanner breakers={breakers} />

      {/* Summary line */}
      <div className="flex items-center gap-4 text-xs text-[var(--color-text-secondary)]">
        <span>{analyzed.length} trades analyzed</span>
        <span className="text-[var(--color-profit)]">{cleanCount} clean</span>
        <span className="text-[var(--color-loss)]">{flaggedCount} flagged</span>
      </div>

      {/* Demon scorecard */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
        {stats.map(stat => (
          <DemonCard
            key={stat.id}
            stat={stat}
            isActive={activeFilter === stat.id}
            onClick={() => setActiveFilter(activeFilter === stat.id ? null : stat.id)}
          />
        ))}
        {/* Clean trades card */}
        <button
          onClick={() => setActiveFilter(activeFilter === 'clean' ? null : 'clean')}
          className={`bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-3 text-left cursor-pointer transition-colors hover:bg-[var(--color-hover-bg)] ${
            activeFilter === 'clean' ? 'ring-2 ring-[var(--color-accent)]' : ''
          }`}
        >
          <div className="text-sm mb-2">{'\u2713'}</div>
          <div className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-1">
            Clean Trades
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-lg font-mono font-bold text-[var(--color-profit)]">{cleanCount}</span>
            <span className="text-[10px] text-[var(--color-text-muted)]">/ {analyzed.length}</span>
          </div>
        </button>
      </div>

      {/* Trade list */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
        <div className="px-3 py-2 border-b border-[var(--color-border)] flex items-center justify-between">
          <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
            {activeFilter
              ? activeFilter === 'clean' ? 'Clean Trades' : DEMONS.find(d => d.id === activeFilter)?.name
              : 'All Trades'
            }
          </span>
          {activeFilter && (
            <button
              onClick={() => setActiveFilter(null)}
              className="text-[10px] text-[var(--color-accent)] hover:underline cursor-pointer bg-transparent border-none"
            >
              Show all
            </button>
          )}
        </div>
        <div className="max-h-[400px] overflow-y-auto">
          {filteredTrades.slice(0, 50).map(trade => (
            <TradeRow key={trade.id} trade={trade} />
          ))}
          {filteredTrades.length === 0 && (
            <div className="text-center py-8 text-xs text-[var(--color-text-muted)]">
              No trades match this filter.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
