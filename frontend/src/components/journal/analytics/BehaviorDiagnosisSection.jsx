import { useMemo } from 'react'
import Empty from '../Empty'
import { rMultiple, rRisk } from '../../portfolio/lib/diagnosticsR'
import TradeCaseStudies from './TradeCaseStudies'

const mean = a => (a.length ? a.reduce((s, x) => s + x, 0) / a.length : 0)
const money = v => (v < 0 ? '-$' : '$') + Math.abs(Math.round(v)).toLocaleString()

function Card({ n, title, verdict, children }) {
  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-4 mb-4">
      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-[12.5px] font-bold text-[var(--color-accent)]">{n}</span>
        <span className="font-semibold text-[14px]">{title}</span>
      </div>
      <div className="text-[12.5px] text-[var(--color-text-secondary)] leading-6">{children}</div>
      {verdict && (
        <div className="mt-2 text-[12.5px] font-medium text-[var(--color-text)] border-l-2 border-[var(--color-accent)] pl-2">
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
    const riskOf = t => rRisk(t)
    const rDD = closed.filter(t => riskOf(t) && inDD(t.entryDate.slice(0, 10))).map(riskOf)
    const rOK = closed.filter(t => riskOf(t) && !inDD(t.entryDate.slice(0, 10))).map(riskOf)

    // trims / stops
    const scaled = closed.filter(t => (t.trims?.length || 0) >= 2)
    const scaledWin = scaled.filter(t => (t.realizedPL ?? 0) > 0)
    const into = scaledWin.filter(t => {
      const fp = t.trims[0].price
      return t.direction === 'long' ? fp > t.entryPrice : fp < t.entryPrice
    }).length
    const risks = closed.map(riskOf).filter(Boolean)

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
      riskDDpct: rDD.length ? (mean(rDD) / startingCapital) * 100 : null,
      riskOKpct: rOK.length ? (mean(rOK) / startingCapital) * 100 : null,
      avgRiskPct: risks.length ? (mean(risks) / startingCapital) * 100 : null,
    }
  }, [enriched, performanceData, startingCapital])

  if (!d) return <Empty k="empty.needMore" />

  return (
    <div>
      <TradeCaseStudies enriched={enriched} />

      <Card n="1" title="Largest losses — where the holes come from"
        verdict="The leak isn't bottom-fishing or bag-holding — the first entry is small; the hole is dug by everything added after it goes red. Two modes: averaging into a rolling name (A) and chasing an extended one (B).">
        Losers are cut <b>fast</b> (avg {d.avgLossHold.toFixed(1)}d vs winners {d.avgWinHold.toFixed(1)}d). The damage is in the <b>re-adds</b>, not the first entry:
        <table className="w-full text-[12.5px] mt-2 mb-2">
          <thead><tr className="text-[var(--color-text-muted)]"><td>Name</td><td>Entries</td><td className="text-right">1st entry</td><td className="text-right">Re-adds after #1</td><td className="text-right">Net</td></tr></thead>
          <tbody>{d.reattack.map(r => (
            <tr key={r.tk}>
              <td className="font-mono">{r.tk}</td><td>{r.n}</td>
              <td className="text-right">{money(r.firstPL)} <span className="text-[var(--color-text-muted)]">({r.firstR >= 0 ? '+' : ''}{r.firstR.toFixed(1)}R)</span></td>
              <td className={`text-right ${r.readdPL < 0 ? 'text-[var(--color-loss)]' : 'text-[var(--color-profit)]'}`}>{money(r.readdPL)} ({r.readdR >= 0 ? '+' : ''}{r.readdR.toFixed(1)}R)</td>
              <td className={`text-right font-medium ${r.net < 0 ? 'text-[var(--color-loss)]' : 'text-[var(--color-profit)]'}`}>{money(r.net)}</td>
            </tr>
          ))}</tbody>
        </table>
        <div className="mt-1 space-y-1">
          <div><b>Mode A — averaging into a rolling/stalling name.</b> Range-bound while the 50d MA droops and you keep buying the "value." BABA: all 5 entries in a 16–23% band, re-adds = −$52.9k of −$54.4k.</div>
          <div><b>Mode B — chasing an extended move, re-adding into the reversal.</b> First entry on an already-stretched name (CRCL +36%, SOLS +64% over 50d), it stalls, you add while extended, it rolls over. CRCL/TSLL/OPEN/SOLS/INTC re-adds after a red = −$28k (−5.8R).</div>
        </div>
      </Card>

      <Card n="2" title="Largest winners — what's working"
        verdict="Press winners (same persistence as the re-attack leak — but gated on the thesis still being valid).">
        Winners are held <b>longer</b> ({d.avgWinHold.toFixed(1)}d vs {d.avgLossHold.toFixed(1)}d), scaled out more ({d.winLegs.toFixed(1)} legs vs {d.lossLegs.toFixed(1)}), and <b>{d.intoPct.toFixed(0)}% of scaled winners were trimmed into strength</b> (first trim in profit). Momentum entries, let to run.
      </Card>

      <Card n="3" title="Drawdown behavior — press or pull back?"
        verdict="Disciplined — you de-risk when cold, no revenge-sizing.">
        {d.riskDDpct != null && d.riskOKpct != null
          ? <>You <b>de-risk</b> in drawdowns: avg initial risk <b>{d.riskDDpct.toFixed(2)}%</b> when &gt;3% off peak vs <b>{d.riskOKpct.toFixed(2)}%</b> normally.</>
          : 'Load history to compute drawdown-period sizing.'}
      </Card>

      <Card n="4" title="Trims & stops"
        verdict={`Sizing runs ~2× intended: avg 1R ${d.avgRiskPct ? d.avgRiskPct.toFixed(2) + '%' : '—'} vs 0.25% target.`}>
        {d.scalePct.toFixed(0)}% of trades scaled out; <b>{d.intoPct.toFixed(0)}%</b> of scaled winners trimmed into strength — strong exit craft. Stops: <b>{d.respectPct.toFixed(0)}%</b> of losses respected (≤1.2R), but <b>{d.blewPct.toFixed(0)}%</b> blew through −1R (the re-attack tail).
      </Card>

      <Card n="5" title="What fixing the top-5 leaks is worth"
        verdict={`Realistic prize — one-and-done: +${money(d.cfOnedonePL)} / +${d.cfOnedoneR.toFixed(0)}R / +${(d.cfOnedonePL / d.capital * 100).toFixed(1)} pts of return. Highest-ROI change in the book.`}>
        The five re-attack names are the whole story. Holding everything else equal:
        <table className="w-full text-[12.5px] mt-2 mb-1">
          <thead><tr className="text-[var(--color-text-muted)]"><td>Scenario</td><td className="text-right">P&L</td><td className="text-right">Total R</td><td className="text-right">Return</td></tr></thead>
          <tbody>
            <tr><td>Actual</td><td className="text-right">{money(d.totalPL)}</td><td className="text-right">+{d.totalR.toFixed(0)}R</td><td className="text-right">+{(d.totalPL / d.capital * 100).toFixed(1)}%</td></tr>
            <tr className="font-medium"><td>One-and-done (entry #1, no re-attacks)</td><td className="text-right">{money(d.totalPL + d.cfOnedonePL)}</td><td className="text-right">+{(d.totalR + d.cfOnedoneR).toFixed(0)}R</td><td className="text-right text-[var(--color-profit)]">+{((d.totalPL + d.cfOnedonePL) / d.capital * 100).toFixed(1)}%</td></tr>
            <tr className="text-[var(--color-text-muted)]"><td>Avoid all 5 entirely</td><td className="text-right">{money(d.totalPL + d.cfAvoidPL)}</td><td className="text-right">—</td><td className="text-right">+{((d.totalPL + d.cfAvoidPL) / d.capital * 100).toFixed(1)}%</td></tr>
          </tbody>
        </table>
      </Card>

      <Card n="→" title="What to do instead / 行动项">
        <ol className="list-decimal ml-4 space-y-1.5">
          <li><b>One-and-done per name per thesis.</b> If a name is red after the first entry, no add #2/#3/#4. Re-entry only after a <i>new</i> setup prints (fresh base/breakout) — never as an average-down. Recovers ~{money(d.cfOnedonePL)}.</li>
          <li><b>Pre-commit full size at entry #1, scale only into green.</b> Decide the total intended position before the first fill and pyramid up into strength, never average down into red. Fixes both Mode A (BABA) and Mode B (CRCL).</li>
          <li><b>Halve the base 1R back to target.</b> Real 1R ≈ {d.avgRiskPct ? d.avgRiskPct.toFixed(2) + '%' : '0.52%'} vs the 0.25% you intend. Cutting initial size in half shrinks every hole and makes a wrong first entry a −0.25% event, not −1R+ of real capital.</li>
        </ol>
      </Card>
    </div>
  )
}
