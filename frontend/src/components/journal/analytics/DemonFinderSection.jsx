import { useState, useMemo, useCallback } from 'react'
import Empty from '../Empty'
import { usePortfolio } from '../../portfolio/context/PortfolioContext'
import { analyzeTrades, computeDemonStats, getActiveCircuitBreakers, computeTacticalStats, DEMONS, DEFAULT_RULES } from '../../portfolio/lib/demonFinder'
import { fmtPct, fmt, clr } from '../../portfolio/lib/portfolioFormat'
import { toJstDate } from '../../../lib/tradingDate'
import { Bar } from '../lib/MiniBars'
import DemonRulesConfig from './DemonRulesConfig'
import { useLanguage } from '../../../i18n/LanguageContext'
import { rich, word } from '../../screener/richText'

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
  const { t } = useLanguage()
  if (breakers.length === 0) return null

  return (
    <div className="bg-[color-mix(in_srgb,var(--color-loss)_10%,transparent)] border border-[var(--color-loss)] rounded-2xl px-5 py-4">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[17px]">&#x1F6D1;</span>
        <span className="text-[13px] font-bold text-[var(--color-loss)]">{t('jn.df.stop')}</span>
      </div>
      {breakers.map(b => (
        <p key={b.id} className="text-[13px] text-[var(--color-text)] mt-1">
          {rich(t('jn.df.breaker', { n: b.currentStreak }), { name: <strong>{word(t, `jn.demon.${b.id}`, b.name)}</strong> })}
        </p>
      ))}
    </div>
  )
}

function DemonCard({ stat, isActive, onClick }) {
  const { t } = useLanguage()
  const borderColor = stat.currentStreak >= 6
    ? 'border-[var(--color-loss)]'
    : stat.currentStreak >= 3
      ? 'border-[var(--color-signal-caution)]'
      : 'border-[var(--color-border)]'

  return (
    <button
      onClick={onClick}
      className={`bg-[var(--color-surface)] border ${borderColor} rounded-2xl px-3 py-3 text-left cursor-pointer transition-colors hover:bg-[var(--color-hover-bg)] ${
        isActive ? 'ring-2 ring-[var(--color-accent)]' : ''
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-[13px]">{stat.icon}</span>
        {stat.currentStreak >= 3 && (
          <span className={`text-[11px] font-bold uppercase px-1.5 py-0.5 rounded ${
            stat.currentStreak >= 6 ? 'bg-[color-mix(in_srgb,var(--color-loss)_10%,transparent)] text-[var(--color-loss)]' : 'bg-[color-mix(in_srgb,var(--color-signal-caution)_10%,transparent)] text-[var(--color-signal-caution)]'
          }`}>
            {t('jn.df.streak', { n: stat.currentStreak })}
          </span>
        )}
      </div>
      <div className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-1">
        {word(t, `jn.demon.${stat.id}`, stat.name)}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-[17px] font-mono font-bold text-[var(--color-text-bold)]">{stat.fireCount}</span>
        <span className="text-[11px] text-[var(--color-text-muted)]">{t('jn.df.of30')}</span>
      </div>
      <div className="text-[11px] text-[var(--color-text-muted)] mt-1">
        {t('jn.df.fireRate', { p: fmtPct(stat.fireRate) })}
      </div>
      {stat.winRateWith != null && stat.winRateWithout != null && (
        <div className="text-[11px] mt-1.5 pt-1.5 border-t border-[var(--color-border-light)]">
          <span className="text-[var(--color-text-muted)]">{t('jn.df.winRate')}</span>
          <span className={clr(stat.winRateWith - stat.winRateWithout)}>
            {fmt(stat.winRateWith, 0)}%
          </span>
          <span className="text-[var(--color-text-muted)]">{t('jn.df.vs')}</span>
          <span className="text-[var(--color-text-secondary)]">{fmt(stat.winRateWithout, 0)}%</span>
        </div>
      )}
    </button>
  )
}

function TradeRow({ trade }) {
  const { t } = useLanguage()
  const demons = trade.demons || []

  return (
    <div className="flex items-center gap-3 px-3 py-2 border-b border-[var(--color-border-light)] hover:bg-[var(--color-hover-bg)]">
      {/* Clean/flagged indicator */}
      <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] flex-shrink-0 ${
        trade.isClean
          ? 'bg-[color-mix(in_srgb,var(--color-profit)_10%,transparent)] text-[var(--color-profit)]'
          : 'bg-[color-mix(in_srgb,var(--color-loss)_10%,transparent)] text-[var(--color-loss)]'
      }`}>
        {trade.isClean ? '\u2713' : demons.length}
      </span>

      {/* Trade info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[13px] font-medium text-[var(--color-text-bold)]">{trade.ticker}</span>
          <span className="text-[11px] text-[var(--color-text-muted)] uppercase">{word(t, `jn.dir.${trade.direction}`, trade.direction)}</span>
          <span className="text-[11px] text-[var(--color-text-muted)]">{toJstDate(trade.entryDate)}</span>
        </div>
        {/* Demon badges */}
        {demons.length > 0 && (
          <div className="flex gap-1 mt-1 flex-wrap">
            {demons.map(dId => {
              const d = DEMONS.find(x => x.id === dId)
              return (
                <span
                  key={dId}
                  title={d && word(t, `jn.demon.${dId}.desc`, d.desc)}
                  className="px-1.5 py-0.5 text-[11px] font-medium rounded bg-[color-mix(in_srgb,var(--color-loss)_10%,transparent)] text-[var(--color-loss)]"
                >
                  {d?.icon} {d && word(t, `jn.demon.${dId}`, d.name)}
                </span>
              )
            })}
          </div>
        )}
      </div>

      {/* R/R and result */}
      <div className="text-right flex-shrink-0">
        {trade.rr != null && (
          <div className={`font-mono text-[13px] ${clr(trade.rr)}`}>{fmt(trade.rr, 1)}R</div>
        )}
        {trade.totalReturnPct != null && (
          <div className={`font-mono text-[11px] ${clr(trade.totalReturnPct)}`}>
            {trade.totalReturnPct > 0 ? '+' : ''}{fmt(trade.totalReturnPct, 1)}%
          </div>
        )}
      </div>
    </div>
  )
}

export default function DemonFinderSection({ enriched, dailyPrices }) {
  const { dispatch } = usePortfolio()
  const { t } = useLanguage()
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

  const tacticalStats = useMemo(
    () => computeTacticalStats(enriched),
    [enriched]
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
    return <Empty k="empty.noTrades" />
  }

  return (
    <div className="space-y-4">
      {/* Rules config */}
      <DemonRulesConfig rules={rules} onUpdate={handleUpdateRules} />

      {/* Circuit breaker banner */}
      <CircuitBreakerBanner breakers={breakers} />

      {/* Summary line */}
      <div className="flex items-center gap-4 text-[13px] text-[var(--color-text-secondary)]">
        <span>{t('jn.df.analyzed', { n: analyzed.length })}</span>
        <span className="text-[var(--color-profit)]">{t('jn.df.clean', { n: cleanCount })}</span>
        <span className="text-[var(--color-loss)]">{t('jn.df.flagged', { n: flaggedCount })}</span>
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
          className={`bg-[var(--color-surface)] rounded-3xl px-3 py-3 text-left cursor-pointer transition-colors hover:bg-[var(--color-hover-bg)] ${
            activeFilter === 'clean' ? 'ring-2 ring-[var(--color-accent)]' : ''
          }`}
        >
          <div className="text-[13px] mb-2">{'\u2713'}</div>
          <div className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-1">
            {t('jn.df.cleanTrades')}
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-[17px] font-mono font-bold text-[var(--color-profit)]">{cleanCount}</span>
            <span className="text-[11px] text-[var(--color-text-muted)]">/ {analyzed.length}</span>
          </div>
        </button>
      </div>

      {/* Tactical discipline */}
      {tacticalStats && (
        <div className="bg-[var(--color-surface)] rounded-3xl px-4 py-3">
          <h4 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
            {t('jn.df.tactical')}
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1">
            <Bar label={t('jn.df.avgTrimSize')} value={tacticalStats.avgTrimRatio * 100} max={60} target={33}
                 color={tacticalStats.avgTrimRatio >= 0.25 && tacticalStats.avgTrimRatio <= 0.40
                   ? 'var(--color-profit)' : 'var(--color-signal-caution)'}
                 sub={t('jn.df.avgTrimSize.sub')} />
            <Bar label={t('jn.df.avgTrimR')} value={tacticalStats.avgTrimRR} max={5} target={3} unit="R"
                 color={tacticalStats.avgTrimRR >= 2.0 ? 'var(--color-profit)' : 'var(--color-signal-caution)'}
                 sub={t('jn.df.avgTrimR.sub')} />
            <Bar label={t('jn.df.goodSize')} value={tacticalStats.goodSizeRate} max={100} target={70}
                 color={tacticalStats.goodSizeRate >= 70 ? 'var(--color-profit)' : 'var(--color-signal-caution)'}
                 sub={t('jn.df.goodSize.sub')} />
            <Bar label={t('jn.df.goodRR')} value={tacticalStats.goodRRRate} max={100} target={50}
                 color={tacticalStats.goodRRRate >= 50 ? 'var(--color-profit)' : 'var(--color-signal-caution)'}
                 sub={t('jn.df.goodRR.sub')} />
            <Bar label={t('jn.df.daysToTrim')} value={tacticalStats.avgDaysToTrim}
                 max={Math.max(10, tacticalStats.avgDaysToTrim * 1.5)} unit="d"
                 sub={t('jn.df.daysToTrim.sub')} />
          </div>
        </div>
      )}

      {/* Trade list */}
      <div className="bg-[var(--color-surface)] rounded-3xl overflow-hidden">
        <div className="px-3 py-2 border-b border-[var(--color-border)] flex items-center justify-between">
          <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
            {activeFilter
              ? activeFilter === 'clean' ? t('jn.df.cleanTrades') : word(t, `jn.demon.${activeFilter}`, DEMONS.find(d => d.id === activeFilter)?.name)
              : t('jn.df.allTrades')
            }
          </span>
          {activeFilter && (
            <button
              onClick={() => setActiveFilter(null)}
              className="text-[11px] text-[var(--color-accent)] hover:underline cursor-pointer bg-transparent border-none"
            >
              {t('jn.k.showAll')}
            </button>
          )}
        </div>
        <div className="max-h-[400px] overflow-y-auto">
          {filteredTrades.slice(0, 50).map(trade => (
            <TradeRow key={trade.id} trade={trade} />
          ))}
          {filteredTrades.length === 0 && (
            <div className="text-center py-8 text-[13px] text-[var(--color-text-muted)]">
              {t('jn.df.noMatch')}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
