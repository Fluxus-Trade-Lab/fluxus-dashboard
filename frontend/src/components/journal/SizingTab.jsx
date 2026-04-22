import { useState, useMemo } from 'react'
import { usePortfolio } from '../portfolio/context/PortfolioContext'
import { enrichTrades, lookupPrice } from '../portfolio/lib/calculations'
import { todayStr } from '../portfolio/lib/portfolioFormat'

/* ── Educational Content ─────────────────────────────────── */

const METHODS = [
  {
    key: 'fixed-dollar',
    title: 'Fixed Dollar Amount',
    subtitle: 'Same $ per trade, regardless of setup quality',
    description: 'Allocate a fixed dollar amount (e.g., $50,000) to every trade. Simple, but ignores volatility — a $200 stock and a $20 stock get the same notional exposure despite very different risk profiles.',
    formula: 'Shares = Fixed Amount ÷ Entry Price',
    example: { amount: 50000, entry: 150, result: '333 shares ($50,000 ÷ $150)' },
    pros: ['Dead simple', 'Easy to track allocation'],
    cons: ['Ignores stop distance (risk varies wildly)', 'Tight-stop trades get same size as wide-stop trades', 'No edge-based scaling'],
    verdict: 'beginner',
  },
  {
    key: 'fixed-pct',
    title: 'Fixed % of Portfolio',
    subtitle: 'Same portfolio weight per position',
    description: 'Allocate a fixed percentage of portfolio value (e.g., 5%) to each trade. As your account grows, position sizes grow proportionally. Better than fixed dollar, but still ignores the distance to your stop.',
    formula: 'Shares = (Portfolio × Weight%) ÷ Entry Price',
    example: { amount: 1000000, entry: 150, result: '333 shares ($1M × 5% ÷ $150)' },
    pros: ['Scales with account size', 'Prevents outsized positions'],
    cons: ['Still ignores stop distance', 'A 2% stop and a 10% stop get same weight', 'Risk per trade is inconsistent'],
    verdict: 'intermediate',
  },
  {
    key: 'fixed-risk',
    title: 'Fixed Fractional Risk',
    subtitle: 'Risk the same % of portfolio on every trade',
    description: 'The professional standard. Define your risk per trade (e.g., 0.25% of portfolio), then calculate shares based on the distance between entry and stop. Tight stops = bigger position. Wide stops = smaller position. Your risk is always the same dollar amount.',
    formula: 'Shares = (Portfolio × Risk%) ÷ (Entry − Stop)',
    example: { amount: 1000000, entry: 150, result: '500 shares ($2,500 risk ÷ $5 stop distance)' },
    pros: ['Consistent risk per trade', 'Tight stops = larger position (reward tight patterns)', 'Mathematically optimal for compounding'],
    cons: ['Requires a defined stop on every trade', 'Can lead to large notional on low-volatility setups'],
    verdict: 'professional',
  },
  {
    key: 'dynamic',
    title: 'Dynamic / Kelly-Based',
    subtitle: 'Scale size by edge strength and market regime',
    description: 'Advanced: adjust the risk fraction based on win rate, R-multiple, and market conditions. In strong trends with high win rates, size up (toward Kelly optimal). In choppy markets or cold streaks, size down. Requires a track record to calibrate.',
    formula: 'Risk% = Base% × Kelly Factor × Market Multiplier',
    example: { amount: 1000000, entry: 150, result: 'Variable — 0.15% in choppy, 0.50% in trending' },
    pros: ['Maximizes geometric growth', 'Adapts to regime changes', 'Compounds edge aggressively when conditions favor'],
    cons: ['Needs reliable win rate / R data', 'Over-sizing kills accounts if stats are wrong', 'Complex to implement correctly'],
    verdict: 'advanced',
  },
]

const VERDICT_LABELS = {
  beginner: { label: 'Beginner', color: 'text-amber-600 dark:text-amber-400' },
  intermediate: { label: 'Intermediate', color: 'text-blue-600 dark:text-blue-400' },
  professional: { label: 'Professional', color: 'text-green-600 dark:text-green-400' },
  advanced: { label: 'Advanced', color: 'text-purple-600 dark:text-purple-400' },
}

/* ── Position Size Calculator ────────────────────────────── */

function SizingCalculator({ startingCapital }) {
  const [entry, setEntry] = useState('')
  const [stop, setStop] = useState('')
  const [riskPct, setRiskPct] = useState(0.25)

  const calc = useMemo(() => {
    const e = parseFloat(entry)
    const s = parseFloat(stop)
    if (!e || !s || e === s) return null

    const capital = startingCapital || 1000000
    const riskDollar = capital * (riskPct / 100)
    const stopDist = Math.abs(e - s)
    const stopPct = (stopDist / e) * 100
    const shares = Math.floor(riskDollar / stopDist)
    const positionValue = shares * e
    const positionPct = (positionValue / capital) * 100
    const rTarget1 = e + stopDist * (e > s ? 3 : -3)
    const rTarget2 = e + stopDist * (e > s ? 5 : -5)

    return { riskDollar, stopDist, stopPct, shares, positionValue, positionPct, rTarget1, rTarget2 }
  }, [entry, stop, riskPct, startingCapital])

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 space-y-4">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
        Position Size Calculator
      </h3>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1">Entry Price</label>
          <input
            type="number"
            value={entry}
            onChange={e => setEntry(e.target.value)}
            placeholder="150.00"
            className="w-full text-xs bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1.5 text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
          />
        </div>
        <div>
          <label className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1">Stop Price</label>
          <input
            type="number"
            value={stop}
            onChange={e => setStop(e.target.value)}
            placeholder="145.00"
            className="w-full text-xs bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1.5 text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
          />
        </div>
        <div>
          <label className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1">Risk %</label>
          <input
            type="number"
            value={riskPct}
            onChange={e => setRiskPct(parseFloat(e.target.value) || 0)}
            step="0.05"
            className="w-full text-xs bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1.5 text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
          />
        </div>
      </div>

      {calc && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 border-t border-[var(--color-border-light)]">
          <div>
            <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Shares</span>
            <span className="text-sm font-semibold text-[var(--color-text)]">{calc.shares.toLocaleString()}</span>
          </div>
          <div>
            <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Position Value</span>
            <span className="text-sm font-medium text-[var(--color-text)]">${calc.positionValue.toLocaleString()}</span>
            <span className="text-[9px] text-[var(--color-text-muted)] ml-1">({calc.positionPct.toFixed(1)}%)</span>
          </div>
          <div>
            <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">$ at Risk</span>
            <span className="text-sm font-medium text-red-600 dark:text-red-400">${calc.riskDollar.toLocaleString()}</span>
            <span className="text-[9px] text-[var(--color-text-muted)] ml-1">({calc.stopPct.toFixed(1)}% stop)</span>
          </div>
          <div>
            <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">R Targets</span>
            <span className="text-xs font-mono text-[var(--color-text)]">
              3R: ${calc.rTarget1.toFixed(2)} · 5R: ${calc.rTarget2.toFixed(2)}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Portfolio Sizing Audit ──────────────────────────────── */

function PortfolioAudit({ trades, dailyPrices, startingCapital }) {
  const audit = useMemo(() => {
    if (!trades?.length) return null

    const capital = startingCapital || 1000000
    const targetRisk = capital * 0.0025 // 0.25%
    const today = todayStr()

    const openTrades = trades.filter(t => !t.isClosed && t.currentQty > 0)
    if (!openTrades.length) return null

    let totalHeat = 0
    const positions = openTrades.map(t => {
      const dir = t.direction === 'long' ? 1 : -1
      const stopDist = Math.abs(t.entryPrice - t.stopPrice)
      const riskDollar = t.currentQty * stopDist
      const riskPct = (riskDollar / capital) * 100
      totalHeat += riskPct

      const targetShares = stopDist > 0 ? Math.floor(targetRisk / stopDist) : 0
      const sizeRatio = targetShares > 0 ? t.originalQty / targetShares : 0

      let status = 'ok'
      if (sizeRatio < 0.6) status = 'undersized'
      else if (sizeRatio > 1.4) status = 'oversized'

      const lastP = lookupPrice(t.ticker, today, dailyPrices, t.entryPrice)
      const riskUnit = stopDist > 0 ? stopDist : 1
      const rr = ((lastP - t.entryPrice) * dir) / riskUnit

      return {
        ticker: t.ticker,
        originalQty: t.originalQty,
        currentQty: t.currentQty,
        entryPrice: t.entryPrice,
        stopPrice: t.stopPrice,
        stopDist,
        riskDollar,
        riskPct,
        targetShares,
        sizeRatio,
        status,
        rr,
      }
    }).sort((a, b) => b.riskPct - a.riskPct)

    return { positions, totalHeat, capital, targetRisk }
  }, [trades, dailyPrices, startingCapital])

  if (!audit) {
    return (
      <div className="text-xs text-[var(--color-text-muted)] py-4 text-center">
        No open positions to audit.
      </div>
    )
  }

  const STATUS_COLORS = {
    ok: 'text-green-700 dark:text-green-400',
    undersized: 'text-amber-600 dark:text-amber-400',
    oversized: 'text-red-600 dark:text-red-400',
  }

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Current Positions — Sizing Audit
        </h3>
        <span className={`text-xs font-mono font-semibold ${audit.totalHeat > 3 ? 'text-red-600 dark:text-red-400' : 'text-[var(--color-text)]'}`}>
          Total Heat: {audit.totalHeat.toFixed(2)}%
          {audit.totalHeat > 3 && ' ⚠'}
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[var(--color-border)] text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
              <th className="text-left px-2 py-1.5">Ticker</th>
              <th className="text-right px-2 py-1.5">Qty</th>
              <th className="text-right px-2 py-1.5">Entry</th>
              <th className="text-right px-2 py-1.5">Stop</th>
              <th className="text-right px-2 py-1.5">$ Risk</th>
              <th className="text-right px-2 py-1.5">% Risk</th>
              <th className="text-right px-2 py-1.5">Target Qty</th>
              <th className="text-right px-2 py-1.5">R</th>
              <th className="text-center px-2 py-1.5">Status</th>
            </tr>
          </thead>
          <tbody>
            {audit.positions.map(p => (
              <tr key={p.ticker} className="border-b border-[var(--color-border-light)]">
                <td className="px-2 py-1.5 font-semibold text-blue-700 dark:text-blue-400">{p.ticker}</td>
                <td className="px-2 py-1.5 text-right font-mono">{p.currentQty}</td>
                <td className="px-2 py-1.5 text-right font-mono">${p.entryPrice.toFixed(2)}</td>
                <td className="px-2 py-1.5 text-right font-mono">${p.stopPrice.toFixed(2)}</td>
                <td className="px-2 py-1.5 text-right font-mono text-red-600 dark:text-red-400">${p.riskDollar.toLocaleString()}</td>
                <td className="px-2 py-1.5 text-right font-mono">{p.riskPct.toFixed(2)}%</td>
                <td className="px-2 py-1.5 text-right font-mono text-[var(--color-text-muted)]">{p.targetShares}</td>
                <td className={`px-2 py-1.5 text-right font-mono ${p.rr >= 0 ? 'text-green-700 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {p.rr.toFixed(1)}R
                </td>
                <td className={`px-2 py-1.5 text-center font-medium ${STATUS_COLORS[p.status]}`}>
                  {p.status === 'ok' ? '✓' : p.status === 'undersized' ? '↓ Small' : '↑ Large'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/* ── Main Tab ────────────────────────────────────────────── */

export default function SizingTab() {
  const { state } = usePortfolio()
  const [expandedMethod, setExpandedMethod] = useState('fixed-risk')

  const enriched = useMemo(() => {
    if (!state.trades?.length) return []
    return enrichTrades(state.trades, state.startingCapital || 1000000, state.dailyPrices)
  }, [state.trades, state.startingCapital, state.dailyPrices])

  return (
    <div className="space-y-6">
      {/* Section 1: Framework Education */}
      <div>
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
          Position Sizing Methods
        </h3>
        <div className="space-y-2">
          {METHODS.map(method => {
            const isExpanded = expandedMethod === method.key
            const verdict = VERDICT_LABELS[method.verdict]
            return (
              <div
                key={method.key}
                className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden"
              >
                {/* Header — always visible */}
                <button
                  onClick={() => setExpandedMethod(isExpanded ? null : method.key)}
                  className="w-full flex items-center justify-between px-4 py-3 text-left cursor-pointer hover:bg-[var(--color-hover-bg)] transition-colors"
                >
                  <div>
                    <span className="text-xs font-semibold text-[var(--color-text)]">{method.title}</span>
                    <span className="text-[10px] text-[var(--color-text-muted)] ml-2">{method.subtitle}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-[9px] font-medium uppercase tracking-wide ${verdict.color}`}>
                      {verdict.label}
                    </span>
                    <span className="text-[var(--color-text-muted)] text-xs">{isExpanded ? '−' : '+'}</span>
                  </div>
                </button>

                {/* Expanded content */}
                {isExpanded && (
                  <div className="px-4 pb-4 space-y-3 border-t border-[var(--color-border-light)]">
                    <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed pt-3">
                      {method.description}
                    </p>

                    {/* Formula */}
                    <div className="bg-[var(--color-bg)] rounded px-3 py-2">
                      <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1">Formula</span>
                      <code className="text-xs font-mono text-[var(--color-text)]">{method.formula}</code>
                    </div>

                    {/* Example */}
                    <div className="bg-[var(--color-bg)] rounded px-3 py-2">
                      <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1">Example</span>
                      <span className="text-xs text-[var(--color-text-secondary)]">{method.example.result}</span>
                    </div>

                    {/* Pros / Cons */}
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <span className="text-[9px] font-medium uppercase tracking-wide text-green-600 dark:text-green-400 block mb-1">Pros</span>
                        <ul className="space-y-0.5">
                          {method.pros.map((p, i) => (
                            <li key={i} className="text-[10px] text-[var(--color-text-secondary)] flex gap-1.5">
                              <span className="text-green-500 shrink-0">+</span>{p}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <span className="text-[9px] font-medium uppercase tracking-wide text-red-600 dark:text-red-400 block mb-1">Cons</span>
                        <ul className="space-y-0.5">
                          {method.cons.map((c, i) => (
                            <li key={i} className="text-[10px] text-[var(--color-text-secondary)] flex gap-1.5">
                              <span className="text-red-500 shrink-0">−</span>{c}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Section 2: Calculator */}
      <SizingCalculator startingCapital={state.startingCapital || 1000000} />

      {/* Section 3: Portfolio Audit */}
      <PortfolioAudit
        trades={enriched}
        dailyPrices={state.dailyPrices}
        startingCapital={state.startingCapital || 1000000}
      />
    </div>
  )
}
