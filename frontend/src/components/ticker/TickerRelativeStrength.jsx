import { useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useBenchmarks } from '../../hooks/useBenchmarks'

const PERIODS = [
  { label: '1 Month', days: 21 },
  { label: '3 Months', days: 63 },
  { label: '6 Months', days: 126 },
  { label: '1 Year', days: 252 },
]

/**
 * Relative Strength vs SPY & QQQ — rebased 1y line chart + period table.
 *
 * Reads ticker's 1y OHLC + benchmark closes from _benchmarks.json.
 */
export default function TickerRelativeStrength({ tickerData }) {
  const { data: benchData } = useBenchmarks()
  const ohlc = tickerData?.ohlc_1y || []

  const chartData = useMemo(() => {
    if (!ohlc.length) return []
    const spy = benchData?.benchmarks?.SPY || []
    const qqq = benchData?.benchmarks?.QQQ || []
    const spyByDate = Object.fromEntries(spy.map(r => [r.date, r.close]))
    const qqqByDate = Object.fromEntries(qqq.map(r => [r.date, r.close]))

    const firstSym = ohlc[0]?.close
    const firstSpy = spy[0]?.close
    const firstQqq = qqq[0]?.close

    return ohlc.map(row => {
      const sClose = spyByDate[row.date]
      const qClose = qqqByDate[row.date]
      return {
        date: row.date,
        sym: firstSym ? row.close / firstSym * 100 : null,
        spy: sClose && firstSpy ? sClose / firstSpy * 100 : null,
        qqq: qClose && firstQqq ? qClose / firstQqq * 100 : null,
      }
    })
  }, [ohlc, benchData])

  const periodPerf = useMemo(() => {
    if (!ohlc.length || !benchData) return []
    const spy = benchData.benchmarks?.SPY || []
    const qqq = benchData.benchmarks?.QQQ || []
    const lastSym = ohlc[ohlc.length - 1]?.close
    const lastSpy = spy[spy.length - 1]?.close
    const lastQqq = qqq[qqq.length - 1]?.close

    return PERIODS.map(p => {
      const symStart = ohlc[Math.max(0, ohlc.length - 1 - p.days)]?.close
      const spyStart = spy[Math.max(0, spy.length - 1 - p.days)]?.close
      const qqqStart = qqq[Math.max(0, qqq.length - 1 - p.days)]?.close
      const symPct = symStart ? (lastSym / symStart - 1) * 100 : null
      const spyPct = spyStart ? (lastSpy / spyStart - 1) * 100 : null
      const qqqPct = qqqStart ? (lastQqq / qqqStart - 1) * 100 : null
      return {
        label: p.label,
        sym: symPct, spy: spyPct, qqq: qqqPct,
        vsSpy: symPct != null && spyPct != null ? symPct - spyPct : null,
        vsQqq: symPct != null && qqqPct != null ? symPct - qqqPct : null,
      }
    })
  }, [ohlc, benchData])

  if (!ohlc.length) {
    return (
      <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
        <div className="font-semibold mb-3 text-[14px]">Relative Strength vs SPY & QQQ</div>
        <div className="text-[var(--color-text-muted)] text-[14px]">No price history available.</div>
      </div>
    )
  }

  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
      <div className="font-semibold mb-3 text-[14px]">Relative Strength vs SPY & QQQ</div>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10 }}
            tickFormatter={d => d?.slice(5)}
            interval={Math.max(1, Math.floor(chartData.length / 8))}
          />
          <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${Number(v).toFixed(0)}`} />
          <Tooltip formatter={v => v != null ? Number(v).toFixed(1) : '—'} />
          <Legend />
          <Line type="monotone" dataKey="sym" stroke="#5b8fa8" strokeWidth={2.5} dot={false} name={tickerData.ticker} />
          <Line type="monotone" dataKey="spy" stroke="#9da6b3" strokeWidth={1.5} dot={false} name="SPY" strokeDasharray="4 4" />
          <Line type="monotone" dataKey="qqq" stroke="#c89a4e" strokeWidth={1.5} dot={false} name="QQQ" strokeDasharray="4 4" />
        </LineChart>
      </ResponsiveContainer>

      <table className="w-full text-[12.5px] mt-4">
        <thead>
          <tr className="text-left text-[10px] text-[var(--color-text-muted)] uppercase tracking-wide border-b border-[var(--color-border-light)]">
            <th className="px-2 py-1.5">Period</th>
            <th className="px-2 py-1.5 text-right">{tickerData.ticker}</th>
            <th className="px-2 py-1.5 text-right">SPY</th>
            <th className="px-2 py-1.5 text-right">QQQ</th>
            <th className="px-2 py-1.5 text-right">vs SPY</th>
            <th className="px-2 py-1.5 text-right">vs QQQ</th>
          </tr>
        </thead>
        <tbody>
          {periodPerf.map(p => (
            <tr key={p.label} className="border-b border-[var(--color-border-light)]">
              <td className="px-2 py-1.5">{p.label}</td>
              <td className={`px-2 py-1.5 text-right tabular-nums font-semibold ${p.sym == null ? '' : p.sym >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                {fmt(p.sym)}
              </td>
              <td className="px-2 py-1.5 text-right tabular-nums">{fmt(p.spy)}</td>
              <td className="px-2 py-1.5 text-right tabular-nums">{fmt(p.qqq)}</td>
              <td className={`px-2 py-1.5 text-right tabular-nums font-semibold ${p.vsSpy == null ? '' : p.vsSpy >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                {fmt(p.vsSpy)}
              </td>
              <td className={`px-2 py-1.5 text-right tabular-nums font-semibold ${p.vsQqq == null ? '' : p.vsQqq >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                {fmt(p.vsQqq)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function fmt(v) {
  if (v == null) return '—'
  const s = v >= 0 ? '+' : ''
  return `${s}${v.toFixed(1)}%`
}
