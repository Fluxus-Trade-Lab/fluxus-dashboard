import { useState } from 'react'

/*
 * Van Tharp position-sizing curriculum — living module.
 * To add a lesson: append one object to LESSONS. Nothing else to touch.
 * Sources: Van Tharp, "Definitive Guide to Position Sizing" (DGPS);
 * LordFed, "Size Matters" (lordfed.co.uk/p/size-matters).
 * Account numbers: H1 2026 audit (331 closed trades, 2025-12-31 → 2026-07-22).
 */
const LESSONS = [
  {
    key: 'r-multiples',
    title: 'R-Multiples & Expectancy',
    subtitle: 'Measure every trade in units of initial risk',
    principle: 'Express every result as a multiple of initial risk: 1R = |entry − stop| × shares. A trade risking $2,500 that makes $7,500 is +3R. Expectancy is the mean R across trades — what one unit of risk pays on average. Tharp: a system IS its R-multiple distribution; until results are in R, you cannot study sizing at all.',
    ourNumber: {
      stat: 'This book’s expectancy',
      value: '+0.88R',
      read: '331 closed trades, 39.9% win rate, 3.40× payoff — a right-tail distribution: loses often and small, gets paid on the tail (47 trades ≥3R).',
    },
    source: 'Tharp, DGPS · ch. on R-multiples',
  },
  {
    key: 'how-much-separate',
    title: '"How Much" Is a Separate Question',
    subtitle: 'Sizing is independent of entry and exit — it meets your objectives',
    principle: 'Position sizing is the part of the system that answers HOW MUCH, and it is fully separate from what to buy or when to exit. Tharp’s sharpest claim: sizing is the component through which you achieve your OBJECTIVES — the same signal stream can be sized to grind, to compound, or to blow up.',
    ourNumber: {
      stat: 'corr(position size, R) — H1',
      value: '≈ 0.00',
      read: 'His discretionary size was uncorrelated with which trades worked — the sizing layer added no edge on top of entries/exits. Exactly why it deserves separate study.',
    },
    source: 'Tharp, DGPS · audit: PositionSizeChart (Analytics → Summary)',
  },
  {
    key: 'percent-risk',
    title: 'The Percent-Risk Model',
    subtitle: 'Risk the same % of equity on every trade',
    principle: 'Tharp’s workhorse model: pick a risk fraction (e.g. 0.25% of equity), divide by stop distance, get shares. Every trade then loses the same fraction when the stop hits, and R becomes comparable across all trades. The discipline is keeping the fraction FIXED — the model fails the moment "conviction" starts inflating it.',
    ourNumber: {
      stat: 'Real 1R vs target',
      value: '0.52% vs 0.25%',
      read: 'Average initial risk ran 2× the stated target (median 0.39%). The account was running a bigger percent-risk model than the trader believed.',
    },
    source: 'Tharp, DGPS · audit: sizing section of H1 review',
  },
  {
    key: 'percent-volatility',
    title: 'The Percent-Volatility Model',
    subtitle: 'Size by ATR so every position breathes the same',
    principle: 'Instead of stop distance, divide the risk budget by the ATR: shares = (equity × vol%) ÷ ATR. Every position then contributes equal daily volatility to the book. Useful when stops vary in quality or when names differ wildly in volatility — a 2% ATR mega-cap and a 15% ATR small-cap stop being sized the same notional is a hidden bet on the wilder one.',
    ourNumber: {
      stat: 'This book’s pick profile',
      value: 'ATR 8–21%',
      read: 'ALAB, DOCN and peers ran 8–21% ATR at entry — high-volatility names. Percent-volatility sizing would have equalized what each position could do to the equity curve in a day.',
    },
    source: 'Tharp, DGPS · percent-volatility model',
  },
  {
    key: 'anti-martingale',
    title: 'Anti-Martingale: Press Winners, Cut Losers',
    subtitle: 'Never average down unless it was pre-planned',
    principle: 'Martingale sizes UP after losses (averaging down); anti-martingale sizes up only as equity grows and positions work. Tharp: all sound sizing is anti-martingale. LordFed’s Test → Core → Press ladder is the practical form — earn size with confirmation, never buy more of what’s going against you unless the add was in the plan at entry.',
    ourNumber: {
      stat: 'Re-attacks — all 148 trades',
      value: '+1.21R avg',
      read: 'Re-attacking was NOT the leak (it beat fresh entries’ +0.61R). The damage was OVERSIZING the failures — BABA’s 5-entry martingale cost −$54k. The behavior is fine; the sizing of it wasn’t.',
    },
    source: 'LordFed, Size Matters · audit: conviction_sizing.py',
  },
  {
    key: 'kelly-trap',
    title: 'The Kelly Trap',
    subtitle: 'Optimal f is only optimal if your edge estimate is real',
    principle: 'Kelly / optimal-f maximizes geometric growth — IF the R-distribution you feed it is the true, stationary one. Feed it a hot sample and it prescribes ruin. Tharp treats optimal-f as an upper bound you stay well below, not a target; half-Kelly is the common compromise, and even that assumes your sample generalizes.',
    ourNumber: {
      stat: 'Full Kelly on this sample',
      value: 'f* = 15.9%/1R',
      read: 'Computed on a +90%/6-month bull sample, Kelly says risk 15.9% of equity per trade (λ* = 5.8× leverage). That is the sample talking, not the edge — on the next regime it’s ruin. Distrust it until the edge is measured over a full cycle.',
    },
    source: 'Tharp, DGPS · audit: pipeline/portfolio/sizing.py',
  },
  {
    key: 'discipline-over-prediction',
    title: 'Discipline Beats Prediction',
    subtitle: 'You cannot forecast R at entry — so stop sizing like you can',
    principle: '"You trade your beliefs about the market." If conviction at entry could forecast outcome, conviction-weighted sizing would beat flat risk. Test it — Tharp’s whole method is turning beliefs into measurable claims. Where conviction fails the test, the percent-risk model IS the edge: equal risk, every trade, no exceptions.',
    ourNumber: {
      stat: 'Plain equal-risk vs his actual sizing',
      value: '+66.7%',
      read: 'Equal risk per trade would have beaten his discretionary sizing by 66.7% (robust: +27% even dropping the top-10 winners). Conviction score ANTI-predicted outcome (corr −0.16; Test tier +1.48R > Press +0.53R). His edge is discipline, not prediction.',
    },
    source: 'Audit: conviction_sizing.py · LordFed, Size Matters',
  },
]

export default function TharpLessons() {
  const [expanded, setExpanded] = useState(null)

  return (
    <div>
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-1">
        Van Tharp — The Study of Position Sizing
      </h3>
      <p className="text-[10px] text-[var(--color-text-muted)] mb-3">
        His framework, lesson by lesson — each checked against this account's audited H1 2026 numbers. A living module: new lessons get appended over time.
      </p>
      <div className="space-y-2">
        {LESSONS.map(lesson => {
          const isExpanded = expanded === lesson.key
          return (
            <div key={lesson.key} className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
              <button
                onClick={() => setExpanded(isExpanded ? null : lesson.key)}
                className="w-full flex items-center justify-between px-4 py-3 text-left cursor-pointer hover:bg-[var(--color-hover-bg)] transition-colors"
              >
                <div>
                  <span className="text-xs font-semibold text-[var(--color-text)]">{lesson.title}</span>
                  <span className="text-[10px] text-[var(--color-text-muted)] ml-2 hidden sm:inline">{lesson.subtitle}</span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-[10px] font-mono font-semibold text-[var(--color-text-secondary)]">{lesson.ourNumber.value}</span>
                  <span className="text-[var(--color-text-muted)] text-xs">{isExpanded ? '−' : '+'}</span>
                </div>
              </button>

              {isExpanded && (
                <div className="px-4 pb-4 space-y-3 border-t border-[var(--color-border-light)]">
                  <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed pt-3">
                    {lesson.principle}
                  </p>
                  <div className="bg-[var(--color-bg)] rounded px-3 py-2">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
                        {lesson.ourNumber.stat}
                      </span>
                      <span className="text-[8px] font-mono uppercase tracking-wide px-1.5 py-0.5 rounded border border-[var(--color-border-light)] text-[var(--color-text-muted)] shrink-0">
                        H1 audit ref · 331 tr
                      </span>
                    </div>
                    <span className="text-sm font-semibold font-mono text-[var(--color-text)]">{lesson.ourNumber.value}</span>
                    <p className="text-[10px] text-[var(--color-text-secondary)] leading-relaxed mt-1">
                      {lesson.ourNumber.read}
                    </p>
                  </div>
                  <p className="text-[9px] text-[var(--color-text-muted)]">{lesson.source}</p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
