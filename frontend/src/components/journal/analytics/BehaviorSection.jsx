import { useMemo, useState } from 'react'
import Empty from '../Empty'
import TickerLink from '../../ticker/TickerLink'
import { useLanguage } from '../../../i18n/LanguageContext'
import { fmtCur, clr } from '../../portfolio/lib/portfolioFormat'
import {
  computeRMultipleStats,
  computeExitStyleStats,
  computeRevengeTradeClusters,
  computePanicTrimSummary,
} from '../../portfolio/lib/diagnosticsR'

/**
 * The ledger: where the money actually went.
 *
 * A ledger has one job the test above it does not — it has to ADD UP. So the
 * spine of this zone is a single bar in dollars whose segments are the four
 * exit styles: every closed trade falls in exactly one, and the parts sum to
 * the book. That is what makes it an account rather than four more findings.
 *
 * It used to be four full-width tables — R stat cards, an exit-style table, 32
 * revenge rows, 14 panic rows — about 1,200px of chrome in which nothing added
 * to anything. The numbers were fine; the form said "here are four unrelated
 * reports". Same numbers here, arranged as one account plus two annotations on
 * it: money that came back out (re-attacks) and money that never came in
 * (trims into weakness). Those two are deliberately NOT in the bar — one is
 * realised and one is foregone, and adding them would be a lie about the sum.
 */

const STYLE_ORDER = ['stop_only', 'weakness', 'strength', 'mixed']

/** A number's share of the bar, by absolute size — the bar shows flow, not net. */
const abs = (v) => Math.abs(v || 0)

function Rows({ items, render, cap = 6, moreLabel }) {
  const [all, setAll] = useState(false)
  const shown = all ? items : items.slice(0, cap)
  return (
    <>
      {shown.map(render)}
      {items.length > cap && (
        <button type="button" onClick={() => setAll(!all)}
                className="mt-1.5 text-[11px] font-mono bg-transparent border-none p-0
                           cursor-pointer text-[var(--color-text-muted)]
                           hover:text-[var(--color-text)]">
          {all ? '−' : `+${items.length - cap}`} {moreLabel}
        </button>
      )}
    </>
  )
}

export default function BehaviorSection({ enriched }) {
  const { t } = useLanguage()
  const rStats = useMemo(() => computeRMultipleStats(enriched), [enriched])
  const styles = useMemo(() => computeExitStyleStats(enriched), [enriched])
  const revenge = useMemo(() => computeRevengeTradeClusters(enriched, 30, 2), [enriched])
  const panic = useMemo(() => computePanicTrimSummary(enriched), [enriched])
  const [open, setOpen] = useState(null)

  if (!rStats && STYLE_ORDER.every((s) => (styles[s]?.count ?? 0) === 0)) {
    return <Empty k="empty.noClosed" />
  }

  const segs = STYLE_ORDER.map((k) => ({ k, ...styles[k] })).filter((s) => s.count > 0)
  const flow = segs.reduce((s, x) => s + abs(x.totalPL), 0) || 1
  const net = segs.reduce((s, x) => s + x.totalPL, 0)
  const revengeTotal = revenge.reduce((s, c) => s + c.totalPL, 0)

  return (
    <div>
      {/* The account, in one bar. Width is money moved; blue in, red out. */}
      <div className="flex items-baseline gap-3 mb-2.5">
        <b className="text-[11px] font-mono uppercase tracking-[.16em]
                      text-[var(--color-text-muted)]">{t('led.bar')}</b>
        <span className={`ml-auto text-[17px] font-semibold tabular-nums ${clr(net)}`}>
          {fmtCur(net)}
        </span>
      </div>

      <div className="flex h-9 rounded-lg overflow-hidden mb-1.5">
        {segs.map((s) => {
          const neg = s.totalPL < 0
          const w = (abs(s.totalPL) / flow) * 100
          return (
            <button
              key={s.k}
              type="button"
              onClick={() => setOpen(open === s.k ? null : s.k)}
              title={`${t(`led.style.${s.k}`)} · ${fmtCur(s.totalPL)}`}
              style={{ width: `${w}%` }}
              className={`relative border-none cursor-pointer p-0 transition-opacity
                          hover:opacity-100 ${
                neg ? 'bg-[var(--color-loss)]' : 'bg-[var(--color-profit)]'} ${
                open && open !== s.k ? 'opacity-35' : 'opacity-85'}`}>
              {/* A label only when it fits on one line. A segment too thin to
                  carry text is named in the key below, not squeezed. */}
              {w > 13 && (
                <span className="absolute inset-0 flex items-center justify-center px-2
                                 text-[11px] font-semibold text-white whitespace-nowrap
                                 overflow-hidden">
                  {t(`led.style.${s.k}`)}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Every segment named, including the ones too thin to carry a label. */}
      <div className="flex flex-wrap gap-x-5 gap-y-1 mb-2">
        {segs.map((s) => (
          <button key={s.k} type="button"
                  onClick={() => setOpen(open === s.k ? null : s.k)}
                  className={`flex items-center gap-1.5 bg-transparent border-none p-0
                              cursor-pointer text-[11px] ${
                    open === s.k ? 'text-[var(--color-text)]'
                                 : 'text-[var(--color-text-muted)]'}`}>
            <i className={`w-2 h-2 rounded-sm ${s.totalPL < 0
              ? 'bg-[var(--color-loss)]' : 'bg-[var(--color-profit)]'}`} />
            {t(`led.style.${s.k}`)}
            {/* Every segment's amount lives here, including the ones too thin
                to carry a label — so the bar shows shape and this shows size. */}
            <span className={`font-mono tabular-nums ${clr(s.totalPL)}`}>
              {fmtCur(s.totalPL)}
            </span>
            <span className="font-mono tabular-nums opacity-60">{s.count}</span>
          </button>
        ))}
      </div>

      {open && styles[open] && (
        <div className="rounded-2xl bg-[var(--color-surface)] px-4 py-3 mb-2">
          <p className="text-[11px] text-[var(--color-text-secondary)] m-0 mb-2 max-w-[62ch]">
            {t(`led.hint.${open}`)}
            {' · '}
            <span className="font-mono">{t('led.avg', { v: fmtCur(styles[open].avgPL) })}</span>
          </p>
          <div className="flex flex-wrap gap-x-3 gap-y-1">
            {styles[open].trades.slice(0, 40).map((x, i) => (
              <span key={`${x.ticker}-${i}`} className="text-[11px] font-mono">
                <TickerLink symbol={x.ticker} />
                <span className={clr(x.realizedPL)}> {fmtCur(x.realizedPL)}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      <p className="text-[11px] text-[var(--color-text-muted)] max-w-[64ch]">
        {t('led.legend')}
      </p>

      {/* The same book in R, as one line. It was five stat cards; five cards is
          a dashboard, and a dashboard is what this page is not. */}
      {rStats && (
        <p className="text-[11px] mt-3 max-w-[68ch] border-l-2 pl-3
                      border-[var(--color-border)] text-[var(--color-text-secondary)]">
          {t('led.rline', {
            n: rStats.n,
            avg: `${rStats.avgR.toFixed(2)}R`,
            med: `${rStats.medianR.toFixed(2)}R`,
            win: `${rStats.avgWinR.toFixed(2)}R`,
            loss: `${rStats.avgLossR.toFixed(2)}R`,
          })}
          {rStats.medianR < 0 && rStats.avgR > 0 && ` ${t('led.rtail')}`}
        </p>
      )}

      {/* Two annotations on the account. Neither belongs in the bar: one is
          money that came back out, one is money that never came in. */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-5 mt-7">
        <div>
          <b className="text-[11px] font-mono uppercase tracking-[.16em]
                        text-[var(--color-text-muted)] block">{t('led.revenge')}</b>
          <span className="block text-[17px] font-semibold tabular-nums mt-1
                           text-[var(--color-loss)]">{fmtCur(revengeTotal)}</span>
          <span className="block text-[11px] text-[var(--color-text-muted)] mb-2.5
                           max-w-[40ch]">{t('led.revenge.lede')}</span>
          {revenge.length === 0 ? <Empty k="empty.noClusters" /> : (
            <Rows items={revenge} moreLabel={t('led.more')}
                  render={(c, i) => {
                    const w = (abs(c.totalPL) / abs(revenge[0].totalPL)) * 100
                    return (
                      <div key={`${c.ticker}-${i}`}
                           className="grid grid-cols-[52px_26px_1fr_86px] items-center gap-2
                                      py-1.5 border-b border-[var(--color-border-light)]">
                        <span className="text-[13px] font-semibold">
                          <TickerLink symbol={c.ticker} />
                        </span>
                        <span className="text-[11px] font-mono text-[var(--color-text-muted)]
                                         text-right">×{c.trades.length}</span>
                        <span className="h-1.5 rounded-sm bg-[var(--color-loss)] opacity-70"
                              style={{ width: `${Math.max(3, w)}%` }} />
                        <span className="text-[11px] font-mono tabular-nums text-right
                                         text-[var(--color-loss)]">{fmtCur(c.totalPL)}</span>
                      </div>
                    )
                  }} />
          )}
        </div>

        <div>
          <b className="text-[11px] font-mono uppercase tracking-[.16em]
                        text-[var(--color-text-muted)] block">{t('led.panic')}</b>
          <span className="block text-[17px] font-semibold tabular-nums mt-1
                           text-[var(--color-signal-caution)]">
            {fmtCur(panic.totalLeak)}
          </span>
          <span className="block text-[11px] text-[var(--color-text-muted)] mb-2.5
                           max-w-[40ch]">
            {t('led.panic.lede', { n: panic.count })}
          </span>
          {panic.perTrade.length === 0 ? <Empty k="empty.noClosed" /> : (
            <Rows items={panic.perTrade} moreLabel={t('led.more')}
                  render={(x, i) => {
                    const w = (abs(x.leak) / abs(panic.perTrade[0].leak)) * 100
                    return (
                      <div key={`${x.ticker}-${i}`}
                           className="grid grid-cols-[52px_58px_1fr_86px] items-center gap-2
                                      py-1.5 border-b border-[var(--color-border-light)]">
                        <span className="text-[13px] font-semibold">
                          <TickerLink symbol={x.ticker} />
                        </span>
                        <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
                          {x.entryDate?.slice(5, 10)}
                        </span>
                        <span className="h-1.5 rounded-sm bg-[var(--color-signal-caution)]
                                         opacity-70"
                              style={{ width: `${Math.max(3, w)}%` }} />
                        <span className="text-[11px] font-mono tabular-nums text-right
                                         text-[var(--color-signal-caution)]">
                          {fmtCur(x.leak)}
                        </span>
                      </div>
                    )
                  }} />
          )}
        </div>
      </div>
    </div>
  )
}
