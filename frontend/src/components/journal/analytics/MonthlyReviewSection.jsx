import { useState, useMemo, useCallback } from 'react'
import Empty from '../Empty'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import StatCard from '../../portfolio/ui/StatCard'
import { fmtPct, fmt, clr } from '../../portfolio/lib/portfolioFormat'
import { usePortfolio } from '../../portfolio/context/PortfolioContext'
import MonthlyCalendar from './MonthlyCalendar'
import { useLanguage } from '../../../i18n/LanguageContext'

const REVIEWS_KEY = 'fluxus-monthly-reviews'

function loadReviews() {
  try {
    return JSON.parse(localStorage.getItem(REVIEWS_KEY)) || {}
  } catch { return {} }
}

function saveReviews(reviews) {
  localStorage.setItem(REVIEWS_KEY, JSON.stringify(reviews))
}

function buildPrompt(month, stats, trades) {
  const tradeLines = trades.map(t => {
    const dir = t.direction === 'long' ? 'L' : 'S'
    const result = t.totalPL >= 0 ? `+${fmtPct(t.totalReturnPct)}` : fmtPct(t.totalReturnPct)
    return `  ${t.ticker} (${dir}) | Entry ${t.entryPrice} | ${result} | ${fmt(t.rr, 1)}R | ${t.holdingDays}d`
  }).join('\n')

  const prevComparison = stats.prevMonth
    ? `\nPrevious month (${stats.prevMonth.month}): ${fmtPct(stats.prevMonth.monthlyRetPct)} return, ${stats.prevMonth.totalTrades} trades, ${fmtPct(stats.prevMonth.winPct)} win rate`
    : ''

  return `You are a trading coach reviewing my monthly performance. Be direct, specific, and actionable. No fluff.

## ${month} Performance Summary

Portfolio Return: ${fmtPct(stats.monthlyRetPct)}
Trades Closed: ${stats.totalTrades}
Win Rate: ${fmtPct(stats.winPct)}
Avg Gain (winners): ${fmtPct(stats.avgGain)}
Avg Loss (losers): ${fmtPct(stats.avgLoss)}
Largest Gain: ${fmtPct(stats.largestGain)}
Largest Loss: ${fmtPct(stats.largestLoss)}
Avg Hold (winners): ${fmt(stats.avgHoldWin, 0)} days
Avg Hold (losers): ${fmt(stats.avgHoldLoss, 0)} days
${prevComparison}

## Individual Trades
${tradeLines || '  No closed trades this month.'}

## Instructions
1. Start with a 1-sentence overall assessment
2. List 2-3 key findings (what went well, what didn't)
3. Identify any patterns (holding losers too long, cutting winners short, sizing issues)
4. Give 2-3 specific, actionable suggestions for next month
5. Rate this month 1-10 and explain why
6. Keep the total response under 400 words`
}

function MonthStats({ stats }) {
  const { t } = useLanguage()
  if (!stats || stats.totalTrades === 0) {
    return <Empty k="empty.noMonth" />
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <StatCard label={t('jn.k.return')} value={fmtPct(stats.monthlyRetPct)} colorClass={clr(stats.monthlyRetPct)} />
      <StatCard label={t('jn.k.trades')} value={stats.totalTrades} />
      <StatCard label={t('jn.k.winRate')} value={fmtPct(stats.winPct)} colorClass={stats.winPct >= 50 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'} />
      <StatCard label={t('jn.k.avgGain')} value={fmtPct(stats.avgGain)} colorClass="text-[var(--color-profit)]" />
      <StatCard label={t('jn.k.avgLoss')} value={fmtPct(stats.avgLoss)} colorClass="text-[var(--color-loss)]" />
      <StatCard label={t('jn.mr.best')} value={fmtPct(stats.largestGain)} colorClass="text-[var(--color-profit)]" />
      <StatCard label={t('jn.mr.worst')} value={fmtPct(stats.largestLoss)} colorClass="text-[var(--color-loss)]" />
      <StatCard label={t('jn.k.avgHold')} value={t('jn.mr.holdVal', { w: fmt(stats.avgHoldWin, 0), l: fmt(stats.avgHoldLoss, 0) })} />
    </div>
  )
}

function MiniEquityCurve({ data }) {
  const { t } = useLanguage()
  if (!data || data.length < 2) return null

  return (
    <div className="bg-[var(--color-surface)] rounded-3xl p-4">
      <h4 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
        {t('jn.mr.curve')}
      </h4>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} tickFormatter={d => d.slice(8)} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} tickFormatter={v => `${v.toFixed(1)}%`} domain={['auto', 'auto']} />
          <Tooltip
            contentStyle={{ fontSize: 11, background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }}
            formatter={v => [`${v.toFixed(2)}%`, t('jn.k.return')]}
            labelFormatter={l => l}
          />
          <Line type="monotone" dataKey="returnPct" stroke="var(--color-text-bold)" dot={false} strokeWidth={2.4} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function VsPrevMonth({ current, prev }) {
  const { t } = useLanguage()
  if (!current || !prev || prev.totalTrades === 0) return null

  const metrics = [
    { label: t('jn.k.return'), curr: current.monthlyRetPct, prev: prev.monthlyRetPct, fmt: fmtPct },
    { label: t('jn.k.winRate'), curr: current.winPct, prev: prev.winPct, fmt: fmtPct },
    { label: t('jn.k.trades'), curr: current.totalTrades, prev: prev.totalTrades, fmt: v => v },
  ]

  return (
    <div className="bg-[var(--color-surface)] rounded-3xl px-4 py-3">
      <h4 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
        {t('jn.mr.vs', { m: prev.month })}
      </h4>
      <div className="flex gap-6">
        {metrics.map(({ label, curr, prev: p, fmt: f }) => {
          const delta = curr - p
          const arrow = delta > 0 ? '\u2191' : delta < 0 ? '\u2193' : '\u2192'
          const color = delta > 0 ? 'text-[var(--color-profit)]' : delta < 0 ? 'text-[var(--color-loss)]' : 'text-[var(--color-text-muted)]'
          return (
            <div key={label} className="flex items-center gap-1.5">
              <span className="text-[11px] text-[var(--color-text-secondary)]">{label}</span>
              <span className={`text-[13px] font-mono font-medium ${color}`}>{arrow} {f(curr)}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function MonthlyReviewSection({ enriched, monthlyStats, performanceData }) {
  const { state: portfolioState, dispatch } = usePortfolio()
  const { t } = useLanguage()
  const months = useMemo(() => monthlyStats.filter(m => m.month !== 'Unknown').map(m => m.month), [monthlyStats])
  const [selectedMonth, setSelectedMonth] = useState(() => months[months.length - 1] || '')
  // Use portfolio context reviews (synced to Sheets), fall back to localStorage
  const [reviews, setReviews] = useState(() => {
    const ctxReviews = portfolioState.monthlyReviews
    if (ctxReviews && Object.keys(ctxReviews).length > 0) return ctxReviews
    return loadReviews()
  })
  const [editing, setEditing] = useState(false)
  const [draftReview, setDraftReview] = useState('')
  const [copied, setCopied] = useState(false)

  const currentStats = useMemo(
    () => monthlyStats.find(m => m.month === selectedMonth) || null,
    [monthlyStats, selectedMonth]
  )

  const prevStats = useMemo(() => {
    const idx = monthlyStats.findIndex(m => m.month === selectedMonth)
    if (idx > 0) return monthlyStats[idx - 1]
    return null
  }, [monthlyStats, selectedMonth])

  const monthTrades = useMemo(() => {
    if (!selectedMonth) return []
    return enriched.filter(t => {
      if (!t.isClosed) return false
      const trims = t.trims || []
      const lastTrim = trims[trims.length - 1]
      return lastTrim?.date?.startsWith(selectedMonth)
    })
  }, [enriched, selectedMonth])

  const monthEquity = useMemo(() => {
    if (!selectedMonth || !performanceData.length) return []
    return performanceData.filter(pt => pt.date.startsWith(selectedMonth))
  }, [performanceData, selectedMonth])

  const savedReview = reviews[selectedMonth]

  const handleCopyPrompt = useCallback(() => {
    if (!currentStats) return
    const statsWithPrev = { ...currentStats, prevMonth: prevStats }
    const prompt = buildPrompt(selectedMonth, statsWithPrev, monthTrades)
    navigator.clipboard.writeText(prompt)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [currentStats, prevStats, selectedMonth, monthTrades])

  const handleSaveReview = useCallback(() => {
    const next = { ...reviews, [selectedMonth]: { text: draftReview, savedAt: new Date().toISOString() } }
    setReviews(next)
    saveReviews(next)
    dispatch({ type: 'SET_MONTHLY_REVIEWS', reviews: next })
    setEditing(false)
  }, [reviews, selectedMonth, draftReview, dispatch])

  const handleStartEdit = useCallback(() => {
    setDraftReview(savedReview?.text || '')
    setEditing(true)
  }, [savedReview])

  if (months.length === 0) {
    return <Empty k="empty.noMonthly" />
  }

  return (
    <div className="space-y-4">
      {/* Month selector */}
      <div className="flex gap-1 flex-wrap">
        {months.map(m => (
          <button
            key={m}
            onClick={() => { setSelectedMonth(m); setEditing(false) }}
            className={`px-3 py-1.5 text-[11px] font-medium rounded cursor-pointer transition-colors ${
              selectedMonth === m
                ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                : 'text-[var(--color-text-secondary)] bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]'
            }`}
          >
            {m}
            {reviews[m] && <span className="ml-1 text-[11px] opacity-60">*</span>}
          </button>
        ))}
      </div>

      {/* Stats */}
      <MonthStats stats={currentStats} />

      {/* Equity curve + calendar + vs prev month */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <MiniEquityCurve data={monthEquity} />
        <MonthlyCalendar
          monthEquity={monthEquity}
          startingCapital={portfolioState.startingCapital || 1000000}
        />
      </div>
      <VsPrevMonth current={currentStats} prev={prevStats} />

      {/* Review section */}
      <div className="bg-[var(--color-surface)] rounded-3xl px-5 py-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
            {t('jn.tab.monthly')}
          </h4>
          <div className="flex gap-2">
            <button
              onClick={handleCopyPrompt}
              disabled={!currentStats}
              className="px-3 py-1 text-[11px] font-medium rounded cursor-pointer bg-[var(--color-accent-solid)] text-white hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {copied ? t('jn.k.copied') : t('jn.mr.reviewClaude')}
            </button>
          </div>
        </div>

        {editing ? (
          <div className="space-y-2">
            <textarea
              value={draftReview}
              onChange={e => setDraftReview(e.target.value)}
              placeholder={t('jn.mr.ph')}
              rows={12}
              className="w-full px-3 py-2 text-[13px] bg-[var(--color-bg)] rounded-3xl resize-y outline-none focus:border-[var(--color-text-muted)] font-sans text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] leading-relaxed"
            />
            <div className="flex gap-2">
              <button
                onClick={handleSaveReview}
                disabled={!draftReview.trim()}
                className="px-3 py-1 text-[11px] font-medium rounded cursor-pointer bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {t('jn.mr.save')}
              </button>
              <button
                onClick={() => setEditing(false)}
                className="px-3 py-1 text-[11px] font-medium rounded cursor-pointer text-[var(--color-text-secondary)] hover:text-[var(--color-text)]"
              >
                {t('jn.k.cancel')}
              </button>
            </div>
          </div>
        ) : savedReview ? (
          <div>
            <div className="text-[13px] text-[var(--color-text)] whitespace-pre-wrap leading-relaxed">
              {savedReview.text}
            </div>
            <div className="flex items-center justify-between mt-3 pt-2 border-t border-[var(--color-border-light)]">
              <span className="text-[11px] text-[var(--color-text-muted)]">
                {t('jn.mr.saved', { d: new Date(savedReview.savedAt).toLocaleDateString() })}
              </span>
              <button
                onClick={handleStartEdit}
                className="text-[11px] text-[var(--color-accent)] hover:underline cursor-pointer"
              >
                {t('jn.mr.edit')}
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center py-6">
            <p className="text-[13px] text-[var(--color-text-muted)] mb-3">
              {t('jn.mr.hint1', { m: selectedMonth })}
              <br />
              {t('jn.mr.hint2')}
            </p>
            <button
              onClick={handleStartEdit}
              className="text-[11px] text-[var(--color-accent)] hover:underline cursor-pointer"
            >
              {t('jn.mr.own')}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
