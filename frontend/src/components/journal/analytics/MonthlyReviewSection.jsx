import { useState, useMemo, useCallback } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import StatCard from '../../portfolio/ui/StatCard'
import { fmtPct, fmt, clr } from '../../portfolio/lib/portfolioFormat'
import { usePortfolio } from '../../portfolio/context/PortfolioContext'

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
  if (!stats || stats.totalTrades === 0) {
    return <div className="text-xs text-[var(--color-text-muted)] py-4 text-center">No closed trades this month.</div>
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <StatCard label="Return" value={fmtPct(stats.monthlyRetPct)} colorClass={clr(stats.monthlyRetPct)} />
      <StatCard label="Trades" value={stats.totalTrades} />
      <StatCard label="Win Rate" value={fmtPct(stats.winPct)} colorClass={stats.winPct >= 50 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'} />
      <StatCard label="Avg Gain" value={fmtPct(stats.avgGain)} colorClass="text-[var(--color-profit)]" />
      <StatCard label="Avg Loss" value={fmtPct(stats.avgLoss)} colorClass="text-[var(--color-loss)]" />
      <StatCard label="Best Trade" value={fmtPct(stats.largestGain)} colorClass="text-[var(--color-profit)]" />
      <StatCard label="Worst Trade" value={fmtPct(stats.largestLoss)} colorClass="text-[var(--color-loss)]" />
      <StatCard label="Avg Hold" value={`${fmt(stats.avgHoldWin, 0)}d W / ${fmt(stats.avgHoldLoss, 0)}d L`} />
    </div>
  )
}

function MiniEquityCurve({ data }) {
  if (!data || data.length < 2) return null

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
      <h4 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
        Equity Curve (Month)
      </h4>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
          <XAxis dataKey="date" tick={{ fontSize: 9 }} tickFormatter={d => d.slice(8)} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 9 }} tickFormatter={v => `${v.toFixed(1)}%`} domain={['auto', 'auto']} />
          <Tooltip
            contentStyle={{ fontSize: 11, background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }}
            formatter={v => [`${v.toFixed(2)}%`, 'Return']}
            labelFormatter={l => l}
          />
          <Line type="monotone" dataKey="returnPct" stroke="var(--color-accent)" dot={false} strokeWidth={1.5} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function VsPrevMonth({ current, prev }) {
  if (!current || !prev || prev.totalTrades === 0) return null

  const metrics = [
    { label: 'Return', curr: current.monthlyRetPct, prev: prev.monthlyRetPct, fmt: fmtPct },
    { label: 'Win Rate', curr: current.winPct, prev: prev.winPct, fmt: fmtPct },
    { label: 'Trades', curr: current.totalTrades, prev: prev.totalTrades, fmt: v => v },
  ]

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
      <h4 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
        vs {prev.month}
      </h4>
      <div className="flex gap-6">
        {metrics.map(({ label, curr, prev: p, fmt: f }) => {
          const delta = curr - p
          const arrow = delta > 0 ? '\u2191' : delta < 0 ? '\u2193' : '\u2192'
          const color = delta > 0 ? 'text-green-600' : delta < 0 ? 'text-red-500' : 'text-[var(--color-text-muted)]'
          return (
            <div key={label} className="flex items-center gap-1.5">
              <span className="text-[10px] text-[var(--color-text-secondary)]">{label}</span>
              <span className={`text-xs font-mono font-medium ${color}`}>{arrow} {f(curr)}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function MonthlyReviewSection({ enriched, monthlyStats, performanceData }) {
  const { state: portfolioState, dispatch } = usePortfolio()
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
    return <div className="text-center py-16 text-[var(--color-text-muted)]">No monthly data yet.</div>
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
            {reviews[m] && <span className="ml-1 text-[9px] opacity-60">*</span>}
          </button>
        ))}
      </div>

      {/* Stats */}
      <MonthStats stats={currentStats} />

      {/* Equity curve + vs prev month */}
      <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-3">
        <MiniEquityCurve data={monthEquity} />
        <VsPrevMonth current={currentStats} prev={prevStats} />
      </div>

      {/* Review section */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-5 py-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
            Monthly Review
          </h4>
          <div className="flex gap-2">
            <button
              onClick={handleCopyPrompt}
              disabled={!currentStats}
              className="px-3 py-1 text-[11px] font-medium rounded cursor-pointer bg-[var(--color-accent)] text-white hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {copied ? 'Copied!' : 'Review with Claude'}
            </button>
          </div>
        </div>

        {editing ? (
          <div className="space-y-2">
            <textarea
              value={draftReview}
              onChange={e => setDraftReview(e.target.value)}
              placeholder="Paste Claude's review here..."
              rows={12}
              className="w-full px-3 py-2 text-xs bg-[var(--color-bg)] border border-[var(--color-border)] rounded resize-y outline-none focus:border-[var(--color-text-muted)] font-sans text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] leading-relaxed"
            />
            <div className="flex gap-2">
              <button
                onClick={handleSaveReview}
                disabled={!draftReview.trim()}
                className="px-3 py-1 text-[11px] font-medium rounded cursor-pointer bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Save Review
              </button>
              <button
                onClick={() => setEditing(false)}
                className="px-3 py-1 text-[11px] font-medium rounded cursor-pointer text-[var(--color-text-secondary)] hover:text-[var(--color-text)]"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : savedReview ? (
          <div>
            <div className="text-xs text-[var(--color-text)] whitespace-pre-wrap leading-relaxed">
              {savedReview.text}
            </div>
            <div className="flex items-center justify-between mt-3 pt-2 border-t border-[var(--color-border-light)]">
              <span className="text-[10px] text-[var(--color-text-muted)]">
                Saved {new Date(savedReview.savedAt).toLocaleDateString()}
              </span>
              <button
                onClick={handleStartEdit}
                className="text-[11px] text-[var(--color-accent)] hover:underline cursor-pointer"
              >
                Edit
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center py-6">
            <p className="text-xs text-[var(--color-text-muted)] mb-3">
              Click "Review with Claude" to copy a prompt with your {selectedMonth} data.
              <br />
              Paste it in claude.ai, then save the response here.
            </p>
            <button
              onClick={handleStartEdit}
              className="text-[11px] text-[var(--color-accent)] hover:underline cursor-pointer"
            >
              Or write your own review
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
