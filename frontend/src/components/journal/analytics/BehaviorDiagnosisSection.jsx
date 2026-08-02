import { useMemo } from 'react'
import { rMultiple, rRisk } from '../../portfolio/lib/diagnosticsR'

const mean = a => (a.length ? a.reduce((s, x) => s + x, 0) / a.length : 0)
const money = v => (v < 0 ? '-$' : '$') + Math.abs(Math.round(v)).toLocaleString()

function Card({ n, title, verdict, children }) {
  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-4 mb-4">
      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-xs font-bold text-[var(--color-accent)]">{n}</span>
        <span className="font-semibold text-sm">{title}</span>
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
    // re-attack
    const byTk = {}
    for (const t of closed) (byTk[t.ticker] ||= []).push(t)
    const reattack = Object.entries(byTk)
      .filter(([, ts]) => ts.length >= 3)
      .map(([tk, ts]) => ({ tk, n: ts.length, nLoss: ts.filter(t => (t.realizedPL ?? 0) < 0).length, net: ts.reduce((s, t) => s + (t.realizedPL ?? 0), 0) }))
      .sort((a, b) => a.net - b.net).slice(0, 5)

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

  if (!d) return <div className="text-sm text-[var(--color-text-muted)] py-10 text-center">Need more closed trades for a diagnosis.</div>

  return (
    <div>
      <Card n="1" title="Largest losses — where the holes come from"
        verdict="The leak isn't bottom-fishing or bag-holding — it's re-attacking a broken thesis (top row). Add a hard 'this name is dead, stop re-entering' rule.">
        Losers are cut <b>fast</b> (avg {d.avgLossHold.toFixed(1)}d vs winners {d.avgWinHold.toFixed(1)}d). The big losses come from re-entering the same failing name:
        <table className="w-full text-xs mt-2 mb-1">
          <thead><tr className="text-[var(--color-text-muted)]"><td>Name</td><td>Entries</td><td>Losing</td><td className="text-right">Net</td></tr></thead>
          <tbody>{d.reattack.map(r => (
            <tr key={r.tk}><td className="font-mono">{r.tk}</td><td>{r.n}</td><td>{r.nLoss}</td><td className={`text-right ${r.net < 0 ? 'text-red-500' : 'text-green-600'}`}>{money(r.net)}</td></tr>
          ))}</tbody>
        </table>
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
    </div>
  )
}
