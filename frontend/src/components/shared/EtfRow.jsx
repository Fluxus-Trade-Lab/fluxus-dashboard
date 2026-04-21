import { fmtPct, pctColor, abcColor } from '../../lib/format'
import Sparkline from './Sparkline'

export default function EtfRow({ etf }) {
  const {
    ticker,
    change_pct,
    perf_1w,
    perf_1m,
    atr_pct,
    dist_sma50_atr,
    rs,
    abc,
    sparkline,
  } = etf

  return (
    <div className="grid grid-cols-[1.5rem_3.5rem_3.5rem_3.5rem_3.5rem_3rem_3rem_4rem] items-center px-2 py-1 border-b border-[var(--color-border-light)] hover:bg-[var(--color-hover-bg)]">
      {/* ABC dot */}
      <span
        className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold text-white ${abcColor(abc)}`}
      >
        {abc}
      </span>

      {/* Ticker */}
      <span className="font-mono text-xs font-medium text-[var(--color-text-bold)]">
        {ticker}
      </span>

      {/* 1D */}
      <span className={`font-mono text-xs ${pctColor(change_pct)}`}>
        {fmtPct(change_pct)}
      </span>

      {/* 5D */}
      <span className={`font-mono text-xs ${pctColor(perf_1w)}`}>
        {fmtPct(perf_1w)}
      </span>

      {/* 20D */}
      <span className={`font-mono text-xs ${pctColor(perf_1m)}`}>
        {fmtPct(perf_1m)}
      </span>

      {/* ATR dist */}
      <span className="font-mono text-xs text-[var(--color-text-secondary)]">
        {dist_sma50_atr != null ? dist_sma50_atr.toFixed(1) : '—'}
      </span>

      {/* RRS */}
      <span className="font-mono text-xs text-[var(--color-text-secondary)]">
        {rs != null ? `${Math.round(rs)}%` : '—'}
      </span>

      {/* Sparkline */}
      <span className="flex items-center justify-end text-[var(--color-text-muted)]">
        <Sparkline data={sparkline} />
      </span>
    </div>
  )
}
