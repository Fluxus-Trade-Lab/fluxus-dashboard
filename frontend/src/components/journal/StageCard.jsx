import { useMemo } from 'react'
import { useLanguage } from '../../i18n/LanguageContext'
import { usePortfolio } from '../portfolio/context/PortfolioContext'
import { enrichTrades } from '../portfolio/lib/calculations'
import { buildEquityCurve } from '../portfolio/lib/equityCurve'
import { positionSizeStats } from '../portfolio/lib/positionSize'
import { sequence } from './lib/afterLoss'
import { holdCapture } from './lib/holdCapture'
import { setupEdge } from './lib/setupEdge'
import { stageLeaks } from './lib/headCoach'

/**
 * One stage, as a card: its question, its shape, its reading.
 *
 * The four cards ARE the ranking — which is why the verdict sentence that used
 * to sit above them is gone. A sentence saying "the leak is in holding" next to
 * four cards that already show it is the same fact printed twice, and the rule
 * this page keeps is that a picture which can be read is not also written out.
 *
 * The shapes here are the SAME shapes as the detail pages, at a smaller size —
 * not different charts. A thumbnail that does not look like what it opens is a
 * promise the page cannot keep.
 */

const R1 = (v) => `${v.toFixed(1)}R`

/** 选 — one band per label, one dot per trade. Overlap is the reading. */
function SelectViz({ trades }) {
  const res = useMemo(() => setupEdge(trades), [trades])
  if (!res) return null
  const x = (r) => ((Math.max(-3, Math.min(8, r)) + 3) / 11) * 100
  return (
    <div className="space-y-1">
      {res.rows.slice(0, 5).map((row) => (
        <div key={row.setup}
             className="relative h-3 rounded-sm bg-[var(--color-hover-bg)]">
          {/* Means only — the card cannot hold 300 dots legibly, and a
              thumbnail that lies about its density is worse than a sparse one. */}
          <i className="absolute top-[3px] w-[3px] h-[6px] rounded-sm bg-[var(--color-text)]"
             style={{ left: `${x(row.mean)}%` }} />
          <i className="absolute top-[5px] h-[2px] rounded-sm bg-[var(--color-untested)]"
             style={{ left: `${x(row.lo)}%`, width: `${Math.max(1, x(row.hi) - x(row.lo))}%` }} />
        </div>
      ))}
    </div>
  )
}

/** 持有 — entry → peak, one line per trade, exit marked. */
function HoldViz({ trades }) {
  const rows = useMemo(() => {
    const ok = trades.filter((t) => typeof t.optimal_R === 'number' && t.optimal_R > 0.2
      && typeof t.realized_R === 'number' && Math.abs(t.optimal_R) < 100)
    return ok.sort((a, b) => b.optimal_R - a.optimal_R).slice(0, 34)
  }, [trades])
  const X = (j) => ((Math.max(-0.35, Math.min(1.15, j)) + 0.35) / 1.5) * 100
  const E = X(0), TOP = X(1)
  return (
    <div className="space-y-[2px]">
      {rows.map((t, i) => {
        const xe = X(t.realized_R / t.optimal_R)
        const [l, r] = xe >= E ? [E, xe] : [xe, E]
        return (
          <div key={i} className="relative h-[2px]">
            <i className="absolute top-0 h-px bg-[var(--color-border)]"
               style={{ left: `${E}%`, width: `${TOP - E}%` }} />
            <i className={`absolute top-0 h-[2px] ${xe >= E
              ? 'bg-[var(--color-took)]' : 'bg-[var(--color-refused)]'}`}
               style={{ left: `${l}%`, width: `${Math.max(0.5, r - l)}%`, opacity: 0.7 }} />
          </div>
        )
      })}
    </div>
  )
}

/** 收手 — trades in time, the ones after two losses outlined. */
function StopViz({ trades }) {
  const R = useMemo(() => sequence(trades).slice(-90), [trades])
  return (
    <div className="flex flex-wrap gap-[2px]">
      {R.map((r, i) => (
        <i key={i}
           className={`w-[6px] h-3 rounded-sm ${r > 0
             ? 'bg-[var(--color-took)]' : 'bg-[var(--color-refused)]'} ${
             i >= 2 && R[i - 1] < 0 && R[i - 2] < 0
               ? 'opacity-100 outline outline-1 outline-offset-1 outline-[var(--color-text)]'
               : 'opacity-40'}`} />
      ))}
    </div>
  )
}

/**
 * 定量 — position size per trade, the same bars the detail page draws.
 *
 * This card used to render "— —" and say the data was not connected, which was
 * true of the post-mortem index the other three cards read and false of the
 * page behind the card: sizing lives on the portfolio's own trades, and the
 * detail page has been charting them all along. A card that disclaims what its
 * own page shows is worse than no card.
 *
 * The numbers come from the one shared helper, so the card cannot drift from
 * the chart it opens.
 */
function useSizeStats() {
  const { state } = usePortfolio()
  const { trades, dailyPrices, benchmarkHistories, startingCapital } = state

  // Same derivation chain the detail page uses. The equity curve is not
  // optional here: size is notional ÷ equity AT ENTRY, and without the curve
  // every trade would be divided by the starting capital instead — which would
  // make early trades look small and late ones large, purely from compounding.
  return useMemo(() => {
    const curve = buildEquityCurve(trades, startingCapital, dailyPrices, benchmarkHistories)
    const value = curve.length ? curve[curve.length - 1].value : startingCapital
    return positionSizeStats(enrichTrades(trades, value, dailyPrices), curve, startingCapital)
  }, [trades, dailyPrices, benchmarkHistories, startingCapital])
}

function SizeViz({ size }) {
  const { data, avg } = size
  if (data.length < 3) return null
  const max = Math.max(...data.map((d) => d.size)) || 1
  // Thinned to fit, evenly across the book rather than the last N — a card
  // showing only recent trades would flatter or damn whatever month it ends in.
  const step = Math.max(1, Math.ceil(data.length / 88))
  const shown = data.filter((_, i) => i % step === 0)

  return (
    <div className="relative h-full flex items-end gap-px">
      <i className="absolute left-0 right-0 border-t border-dashed border-[var(--color-border)]"
         style={{ bottom: `${(avg / max) * 100}%` }} />
      {shown.map((d, i) => (
        <i key={i}
           className={`flex-1 rounded-sm ${d.pl > 0
             ? 'bg-[var(--color-took)]' : 'bg-[var(--color-refused)]'} opacity-70`}
           style={{ height: `${Math.max(2, (d.size / max) * 100)}%` }} />
      ))}
    </div>
  )
}

export default function StageCard({ stageKey, trades, lead, onOpen }) {
  const { t } = useLanguage()
  const size = useSizeStats()

  const reading = useMemo(() => {
    if (stageKey === 'size') {
      if (size.data.length < 3) return { n: null, read: t('card.size.pending') }
      return {
        n: t('card.trades', { n: size.data.length }),
        read: t('card.size.read', {
          avg: `${size.avg.toFixed(1)}%`,
          corr: size.corr != null ? (size.corr >= 0 ? '+' : '') + size.corr.toFixed(2) : '—',
        }),
      }
    }
    if (stageKey === 'hold' || stageKey === 'select') {
      const row = stageLeaks(trades).find((r) => r.stage === stageKey)
      if (!row) return { n: null, read: '' }
      return { n: t('card.trades', { n: row.n }),
               read: t('card.leak', { r: R1(row.perTrade) }) }
    }
    const rows = sequence(trades)
    if (rows.length < 40) return { n: null, read: '' }
    const win = rows.filter((x) => x > 0).length / rows.length
    const after = rows.filter((_, i) => i >= 2 && rows[i - 1] < 0 && rows[i - 2] < 0)
    const winAfter = after.length ? after.filter((x) => x > 0).length / after.length : null
    return {
      n: t('card.trades', { n: rows.length }),
      read: winAfter == null ? '' : t('card.stop.read', {
        all: `${(win * 100).toFixed(0)}%`, after: `${(winAfter * 100).toFixed(0)}%` }),
    }
  }, [stageKey, trades, size, t])

  const Viz = { select: SelectViz, hold: HoldViz, stop: StopViz, size: SizeViz }[stageKey]

  return (
    <button
      type="button"
      onClick={() => onOpen(stageKey)}
      className={`text-left flex flex-col rounded-3xl px-4 py-3.5 border cursor-pointer
                  transition-colors bg-[var(--color-surface)]
                  hover:bg-[var(--color-hover-bg)] ${
        lead ? 'border-[var(--color-accent)]' : 'border-transparent'}`}>
      <span className="flex items-baseline gap-2">
        <b className="text-[17px] font-semibold">{t(`rev.stage.${stageKey}`)}</b>
        {lead && (
          <span className="ml-auto text-[11px] font-mono tracking-[.14em] px-1.5 py-0.5 rounded
                           bg-[var(--color-accent-solid)] text-white">{t('card.lead')}</span>
        )}
      </span>
      <span className="text-[11px] text-[var(--color-text-muted)] mt-0.5 mb-3">
        {t(`rev.asks.${stageKey}`)}
      </span>

      <div className="h-[92px] mb-3">{Viz && <Viz trades={trades} size={size} />}</div>

      <span className="mt-auto pt-2.5 border-t border-[var(--color-border-light)]">
        {reading.n && <b className="block text-[17px] font-semibold">{reading.n}</b>}
        <span className="block text-[11px] text-[var(--color-text-secondary)] mt-0.5">
          {reading.read}
        </span>
      </span>
    </button>
  )
}
