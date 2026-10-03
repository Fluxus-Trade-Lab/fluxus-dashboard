import { useMemo } from 'react'
import Empty from '../Empty'
import { rMultiple, rRisk } from '../../portfolio/lib/diagnosticsR'
import { DivergingBars } from '../lib/MiniBars'
import TradeCaseStudies from './TradeCaseStudies'
import { toJstDate } from '../../../lib/tradingDate'
import { useLanguage } from '../../../i18n/LanguageContext'
import { rich } from '../../screener/richText'

const mean = a => (a.length ? a.reduce((s, x) => s + x, 0) / a.length : 0)
const money = v => (v < 0 ? '-$' : '$') + Math.abs(Math.round(v)).toLocaleString()

function Card({ n, title, verdict, children }) {
  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-4 mb-4">
      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-[13px] font-bold text-[var(--color-accent)]">{n}</span>
        <span className="font-semibold text-[13px]">{title}</span>
      </div>
      <div className="text-[13px] text-[var(--color-text-secondary)] leading-6">{children}</div>
      {verdict && (
        <div className="mt-2 text-[13px] font-medium text-[var(--color-text)] border-l-2 border-[var(--color-accent)] pl-2">
          {verdict}
        </div>
      )}
    </div>
  )
}

/**
 * Behavioral diagnosis — answers the four audit questions live from the trade
 * log: largest-loss / winner character, drawdown sizing, trim/stop discipline.
 */
export default function BehaviorDiagnosisSection({ enriched, performanceData, startingCapital }) {
  const { t: tr } = useLanguage()
  const d = useMemo(() => {
    const closed = (enriched || []).filter(t => t.isClosed)
    const withR = closed.map(t => ({ t, r: rMultiple(t) })).filter(x => x.r != null)
    const wins = withR.filter(x => x.r > 0)
    const losses = withR.filter(x => x.r < 0)
    if (wins.length < 2 || losses.length < 2) return null

    const holdDays = t => {
      const exit = t.trims?.length ? t.trims[t.trims.length - 1].date : t.entryDate
      return (new Date(exit) - new Date(t.entryDate)) / 86400000
    }
    // re-attack — names entered 3+ times that net a loss; split first entry vs re-adds
    const pnlOf = t => t.realizedPL ?? 0
    const rOf = t => rMultiple(t) ?? 0
    const byTk = {}
    for (const t of closed) (byTk[t.ticker] ||= []).push(t)
    for (const tk in byTk) byTk[tk].sort((a, b) => (a.entryDate < b.entryDate ? -1 : 1))
    const reattack = Object.entries(byTk)
      .filter(([, ts]) => ts.length >= 3 && ts.reduce((s, t) => s + pnlOf(t), 0) < 0)
      .map(([tk, ts]) => {
        const rest = ts.slice(1)
        return {
          tk, n: ts.length, nLoss: ts.filter(t => pnlOf(t) < 0).length,
          net: ts.reduce((s, t) => s + pnlOf(t), 0),
          firstPL: pnlOf(ts[0]), firstR: rOf(ts[0]),
          readdPL: rest.reduce((s, t) => s + pnlOf(t), 0),
          readdR: rest.reduce((s, t) => s + rOf(t), 0),
        }
      })
      .sort((a, b) => a.net - b.net).slice(0, 5)

    // counterfactual — fixing the top-5 leaks
    const totalPL = closed.reduce((s, t) => s + pnlOf(t), 0)
    const totalR = withR.reduce((s, x) => s + x.r, 0)
    const cfOnedonePL = -reattack.reduce((s, r) => s + r.readdPL, 0)
    const cfOnedoneR = -reattack.reduce((s, r) => s + r.readdR, 0)
    const cfAvoidPL = -reattack.reduce((s, r) => s + r.net, 0)

    // drawdown sizing
    const eq = performanceData || []
    let peak = startingCapital
    const ddFlag = {}
    for (const p of eq) { peak = Math.max(peak, p.value); ddFlag[p.date] = (p.value - peak) / peak < -0.03 }
    const inDD = ds => { const prior = eq.filter(p => p.date <= ds); return prior.length ? ddFlag[prior[prior.length - 1].date] : false }
    // HOUSE RULE (2026-09-01): risk-per-trade % is ÷ equity on the ENTRY DAY,
    // never ÷ starting capital — that denominator halves as the account doubles
    // and once mislabeled a mid-band 0.30% median as "2× over target".
    const equityAt = (ds) => {
      let v = startingCapital
      for (const p of eq) { if (p.date <= ds) v = p.value; else break }
      return v || startingCapital
    }
    const riskPctOf = t => {
      const r = rRisk(t)
      return r ? (r / equityAt(toJstDate(t.entryDate))) * 100 : null
    }
    const rDD = closed.map(t => inDD(toJstDate(t.entryDate)) ? riskPctOf(t) : null).filter(Boolean)
    const rOK = closed.map(t => !inDD(toJstDate(t.entryDate)) ? riskPctOf(t) : null).filter(Boolean)

    // trims / stops
    const scaled = closed.filter(t => (t.trims?.length || 0) >= 2)
    const scaledWin = scaled.filter(t => (t.realizedPL ?? 0) > 0)
    const into = scaledWin.filter(t => {
      const fp = t.trims[0].price
      return t.direction === 'long' ? fp > t.entryPrice : fp < t.entryPrice
    }).length
    const risks = closed.map(riskPctOf).filter(Boolean)
    const risksSorted = [...risks].sort((a, b) => a - b)

    return {
      avgWinHold: mean(wins.map(x => holdDays(x.t))),
      avgLossHold: mean(losses.map(x => holdDays(x.t))),
      reattack,
      totalPL, totalR, cfOnedonePL, cfOnedoneR, cfAvoidPL,
      capital: startingCapital,
      winLegs: mean(wins.map(x => x.t.trims?.length || 1)),
      lossLegs: mean(losses.map(x => x.t.trims?.length || 1)),
      intoPct: scaledWin.length ? (into / scaledWin.length) * 100 : 0,
      scalePct: (scaled.length / closed.length) * 100,
      respectPct: (losses.filter(x => x.r >= -1.2).length / losses.length) * 100,
      blewPct: (losses.filter(x => x.r < -1).length / losses.length) * 100,
      riskDDpct: rDD.length ? mean(rDD) : null,
      riskOKpct: rOK.length ? mean(rOK) : null,
      avgRiskPct: risks.length ? mean(risks) : null,
      medRiskPct: risks.length ? risksSorted[Math.floor(risks.length / 2)] : null,
      over1n: risks.filter(r => r > 1).length,
    }
  }, [enriched, performanceData, startingCapital])

  if (!d) return <Empty k="empty.needMore" />

  const R1 = (v) => `${v >= 0 ? '+' : ''}${v.toFixed(1)}R`
  const medPct = d.medRiskPct ? d.medRiskPct.toFixed(2) + '%' : '—'
  const medNum = d.medRiskPct ? d.medRiskPct.toFixed(2) : '—'

  return (
    <div>
      <TradeCaseStudies enriched={enriched} />

      <Card n="1" title={tr('jn.bd.c1.title')}
        verdict={tr('jn.bd.c1.verdict')}>
        {rich(tr('jn.bd.c1.body', { l: d.avgLossHold.toFixed(1), w: d.avgWinHold.toFixed(1) }))}
        <div className="mt-2 mb-1">
          <DivergingBars rows={d.reattack.map((r) => ({ key: r.tk, value: r.net }))}
                         formatValue={money} />
        </div>
        <table className="w-full text-[13px] mt-2 mb-2">
          <thead><tr className="text-[var(--color-text-muted)]"><td>{tr('jn.bd.h.name')}</td><td>{tr('jn.bd.h.entries')}</td><td className="text-right">{tr('jn.bd.h.first')}</td><td className="text-right">{tr('jn.bd.h.readds')}</td><td className="text-right">{tr('jn.bd.h.net')}</td></tr></thead>
          <tbody>{d.reattack.map(r => (
            <tr key={r.tk}>
              <td className="font-mono">{r.tk}</td><td>{r.n}</td>
              <td className="text-right">{money(r.firstPL)} <span className="text-[var(--color-text-muted)]">({R1(r.firstR)})</span></td>
              <td className={`text-right ${r.readdPL < 0 ? 'text-[var(--color-loss)]' : 'text-[var(--color-profit)]'}`}>{money(r.readdPL)} ({R1(r.readdR)})</td>
              <td className={`text-right font-medium ${r.net < 0 ? 'text-[var(--color-loss)]' : 'text-[var(--color-profit)]'}`}>{money(r.net)}</td>
            </tr>
          ))}</tbody>
        </table>
        <div className="mt-1 space-y-1">
          <div>{rich(tr('jn.bd.modeA'))}</div>
          <div>{rich(tr('jn.bd.modeB'))}</div>
        </div>
      </Card>

      <Card n="2" title={tr('jn.bd.c2.title')}
        verdict={tr('jn.bd.c2.verdict')}>
        {rich(tr('jn.bd.c2.body', {
          w: d.avgWinHold.toFixed(1), l: d.avgLossHold.toFixed(1),
          wl: d.winLegs.toFixed(1), ll: d.lossLegs.toFixed(1), into: d.intoPct.toFixed(0),
        }))}
      </Card>

      <Card n="3" title={tr('jn.bd.c3.title')}
        verdict={tr('jn.bd.c3.verdict')}>
        {d.riskDDpct != null && d.riskOKpct != null
          ? rich(tr('jn.bd.c3.body', { dd: d.riskDDpct.toFixed(2), ok: d.riskOKpct.toFixed(2) }))
          : tr('jn.bd.c3.none')}
      </Card>

      <Card n="4" title={tr('jn.bd.c4.title')}
        verdict={tr('jn.bd.c4.verdict', { med: medPct, n: d.over1n })}>
        {rich(tr('jn.bd.c4.body', {
          s: d.scalePct.toFixed(0), into: d.intoPct.toFixed(0),
          r: d.respectPct.toFixed(0), b: d.blewPct.toFixed(0),
        }))}
      </Card>

      <Card n="5" title={tr('jn.bd.c5.title')}
        verdict={tr('jn.bd.c5.verdict', {
          pl: money(d.cfOnedonePL), r: d.cfOnedoneR.toFixed(0),
          pts: (d.cfOnedonePL / d.capital * 100).toFixed(1),
        })}>
        {tr('jn.bd.c5.body')}
        <table className="w-full text-[13px] mt-2 mb-1">
          <thead><tr className="text-[var(--color-text-muted)]"><td>{tr('jn.bd.h.scenario')}</td><td className="text-right">{tr('jn.bd.h.pl')}</td><td className="text-right">{tr('jn.bd.h.totalR')}</td><td className="text-right">{tr('jn.bd.h.return')}</td></tr></thead>
          <tbody>
            <tr><td>{tr('jn.bd.actual')}</td><td className="text-right">{money(d.totalPL)}</td><td className="text-right">+{d.totalR.toFixed(0)}R</td><td className="text-right">+{(d.totalPL / d.capital * 100).toFixed(1)}%</td></tr>
            <tr className="font-medium"><td>{tr('jn.bd.onedone')}</td><td className="text-right">{money(d.totalPL + d.cfOnedonePL)}</td><td className="text-right">+{(d.totalR + d.cfOnedoneR).toFixed(0)}R</td><td className="text-right text-[var(--color-profit)]">+{((d.totalPL + d.cfOnedonePL) / d.capital * 100).toFixed(1)}%</td></tr>
            <tr className="text-[var(--color-text-muted)]"><td>{tr('jn.bd.avoid')}</td><td className="text-right">{money(d.totalPL + d.cfAvoidPL)}</td><td className="text-right">—</td><td className="text-right">+{((d.totalPL + d.cfAvoidPL) / d.capital * 100).toFixed(1)}%</td></tr>
          </tbody>
        </table>
      </Card>

      <Card n="→" title={tr('jn.bd.c6.title')}>
        <ol className="list-decimal ml-4 space-y-1.5">
          <li>{rich(tr('jn.bd.do1', { pl: money(d.cfOnedonePL) }), { new: <i>{tr('jn.bd.new')}</i> })}</li>
          <li>{rich(tr('jn.bd.do2'))}</li>
          <li>{rich(tr('jn.bd.do3', { med: medNum, n: d.over1n }))}</li>
        </ol>
      </Card>
    </div>
  )
}
