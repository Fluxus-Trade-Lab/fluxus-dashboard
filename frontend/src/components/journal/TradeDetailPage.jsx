import { useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ReferenceDot, ResponsiveContainer } from 'recharts'
import { useTradePostmortem } from '../../hooks/useTradeJournal'
import TickerLink from '../ticker/TickerLink'
import { fmtCur } from '../portfolio/lib/portfolioFormat'
import { useLanguage } from '../../i18n/LanguageContext'
import { rich, word } from '../screener/richText'
import { narrativeFor } from './lib/narrative'

export default function TradeDetailPage({ tradeId }) {
  const { data, loading, error } = useTradePostmortem(tradeId)
  const { t: tr, lang } = useLanguage()
  const w = (key, raw) => word(tr, key, raw)

  // All hooks must run on every render — compute chart data before any early returns
  const chartData = useMemo(() => {
    const ohlc = data?.ohlc_window || []
    return ohlc.map(b => ({
      date: b.date, close: b.close, high: b.high, low: b.low, volume: b.volume,
    }))
  }, [data])

  if (loading) return <div className="text-[var(--color-text-muted)] py-10 text-center text-[13px]">{tr('jn.td.loading')}</div>
  if (error || !data) {
    return (
      <div className="py-10 text-center text-[13px] text-[var(--color-text-muted)]">
        <button onClick={() => window.history.back()} className="text-[var(--color-text-muted)] hover:text-[var(--color-text)] mb-3 block mx-auto">{tr('jn.td.back')}</button>
        {rich(tr('jn.td.notFound'), { id: <code>{tradeId}</code> })}
      </div>
    )
  }

  const t = data.trade
  const snap = data.entry_snapshot
  const analytics = data.path_analytics

  return (
    <div className="max-w-[1800px] mx-auto px-3 py-4">
      {/* Header */}
      <div className="border-b border-[var(--color-border)] pb-4 mb-4">
        <button
          onClick={() => window.history.back()}
          className="text-[11px] text-[var(--color-text-muted)] hover:text-[var(--color-text)] cursor-pointer mb-1 block"
        >{tr('jn.td.backJournal')}</button>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-[26px] font-bold tracking-tight flex items-center gap-3">
              <TickerLink symbol={t.ticker} className="text-[var(--color-accent)]" />
              <span className={`text-[13px] font-normal text-[var(--color-text-secondary)]`}>
                {w(`jn.dir.${t.direction}`, t.direction).toUpperCase()}
              </span>
              <span className={`px-2 py-0.5 rounded text-[11px] uppercase tracking-wide ${t.closed ? 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]' : 'bg-[color-mix(in_srgb,var(--color-accent)_15%,transparent)] text-[var(--color-accent)]'}`}>
                {t.closed ? tr('jn.td.closedBadge') : tr('jn.td.openBadge')}
              </span>
            </h1>
            <div className="text-[11px] text-[var(--color-text-muted)] mt-1">
              {String(t.entry_date).slice(0, 10)}{t.exit_date && ` → ${String(t.exit_date).slice(0, 10)}`} · {w(`jn.setup.${data.setup_type}`, data.setup_type)}
            </div>
          </div>
          <div className="text-right">
            <div className={`text-[26px] font-bold tabular-nums ${analytics.realized_R == null ? 'text-[var(--color-text-muted)]' : analytics.realized_R >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
              {fmtR(analytics.realized_R)}
            </div>
            <div className="text-[11px] text-[var(--color-text-muted)]">
              {analytics.capture_pct != null
                ? tr('jn.td.optimalCapture', { r: fmtR(analytics.optimal_R), pct: analytics.capture_pct.toFixed(0) })
                : tr('jn.td.optimal', { r: fmtR(analytics.optimal_R) })}
            </div>
          </div>
        </div>
      </div>

      {/* Narrative */}
      <div className="bg-[var(--color-bg)] rounded-3xl p-5 mb-4">
        <div className="text-[13px] leading-relaxed" dangerouslySetInnerHTML={{ __html: markdownish(narrativeFor(data, lang, tr, w)) }} />
        <div className="mt-3 pt-3 border-t border-[var(--color-border-light)]">
          <span className="text-[11px] uppercase tracking-wide text-[var(--color-text-muted)]">{tr('jn.td.lesson')}</span>
          <div className={`text-[17px] font-bold ${lessonColor(data.lesson)}`}>{w(`rev.lesson.${data.lesson}`, data.lesson)}</div>
        </div>
      </div>

      {/* Annotated chart */}
      <div className="bg-[var(--color-bg)] rounded-3xl p-5 mb-4">
        <div className="font-semibold mb-3 text-[13px]">{tr('jn.td.path')}</div>
        {chartData.length === 0 ? (
          <div className="text-[var(--color-text-muted)] text-[13px]">{tr('jn.td.noOhlc')}</div>
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
                tickFormatter={d => d?.slice(5)}
                interval={Math.max(1, Math.floor(chartData.length / 10))}
              />
              <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} tickFormatter={v => `$${Number(v).toFixed(0)}`} domain={['auto', 'auto']} />
              <Tooltip
                formatter={(v, name) => [name === 'close' ? `$${Number(v).toFixed(2)}` : v, name]}
                labelFormatter={l => tr('jn.td.tipDate', { d: l })}
              />
              <Line type="monotone" dataKey="close" stroke="var(--color-text-muted)" strokeWidth={2} dot={false} name={tr('jn.td.close')} />

              {/* Entry */}
              <ReferenceLine y={t.entry_price} stroke="var(--color-text-muted)" strokeDasharray="3 3" label={{ value: tr('jn.td.refEntry', { p: t.entry_price.toFixed(2) }), fill: 'var(--color-text-muted)', fontSize: 11, position: 'left' }} />
              <ReferenceLine x={String(t.entry_date).slice(0, 10)} stroke="var(--color-text-muted)" strokeDasharray="2 2" />
              <ReferenceDot x={String(t.entry_date).slice(0, 10)} y={t.entry_price} r={5} fill="var(--color-text)" stroke="var(--color-surface)" strokeWidth={1.5} />

              {/* Stop */}
              <ReferenceLine y={t.stop_price} stroke="var(--color-loss)" strokeDasharray="3 3" label={{ value: tr('jn.td.refStop', { p: t.stop_price.toFixed(2) }), fill: 'var(--color-loss)', fontSize: 11, position: 'left' }} />

              {/* Trims */}
              {t.trims.map((tr, i) => (
                <ReferenceDot
                  key={i}
                  x={tr.date}
                  y={tr.price}
                  r={4}
                  fill={tr.type === 'sell_rest' ? 'var(--color-loss)' : 'var(--color-text-secondary)'}
                  stroke="var(--color-surface)"
                  strokeWidth={1.5}
                />
              ))}

              {/* Optimal exit */}
              {analytics.optimal_exit_date && analytics.optimal_exit_price && (
                <ReferenceDot
                  x={String(analytics.optimal_exit_date).slice(0, 10)}
                  y={analytics.optimal_exit_price}
                  r={6}
                  fill="var(--color-profit)"
                  stroke="var(--color-surface)"
                  strokeWidth={2}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        )}
        <div className="text-[11px] text-[var(--color-text-muted)] mt-2 flex flex-wrap gap-3">
          <span><span className="inline-block w-2 h-2 rounded-full bg-[var(--color-text)] mr-1"/>{tr('jn.td.legEntry')}</span>
          <span><span className="inline-block w-2 h-2 rounded-full bg-[var(--color-text-secondary)] mr-1"/>{tr('jn.td.legTrim')}</span>
          <span><span className="inline-block w-2 h-2 rounded-full bg-[var(--color-loss)] mr-1"/>{tr('jn.td.legExit')}</span>
          <span><span className="inline-block w-2 h-2 rounded-full bg-[var(--color-profit)] mr-1"/>{tr('jn.td.legOptimal')}</span>
        </div>
      </div>

      {/* Three-column detail */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        {/* Entry snapshot */}
        <div className="bg-[var(--color-bg)] rounded-3xl p-5">
          <div className="font-semibold mb-3 text-[13px]">{tr('jn.td.snapshot')}</div>
          <div className="text-[13px] flex flex-col gap-1.5">
            <Row label={tr('jn.td.entryPrice')} value={fmtCur(t.entry_price)} />
            <Row label={tr('jn.td.stop')} value={fmtCur(t.stop_price)} />
            {/* R and % only — no share counts or dollar risk (Andy 2026-09-13). */}
            <Row label={tr('jn.td.oneR')} value={t.r_pct_of_entry == null ? '—' : tr('jn.td.ofEntry', { v: t.r_pct_of_entry.toFixed(1) })} />
            <hr className="border-[var(--color-border-light)] my-1" />
            <Row label="MA20" value={snap.ma20 != null ? fmtCur(snap.ma20) : '—'} />
            <Row label="MA50" value={snap.ma50 != null ? fmtCur(snap.ma50) : '—'} />
            <Row label="MA200" value={snap.ma200 != null ? fmtCur(snap.ma200) : '—'} />
            <Row label="RSI(14)" value={snap.rsi14 != null ? snap.rsi14.toFixed(1) : '—'} />
            <Row label="ATR(14)%" value={snap.atr14_pct != null ? `${snap.atr14_pct.toFixed(1)}%` : '—'} />
            <Row label={tr('jn.td.pos52')} value={snap.position_in_52w_range_pct != null ? `${snap.position_in_52w_range_pct.toFixed(0)}%` : '—'} />
          </div>
        </div>

        {/* Execution */}
        <div className="bg-[var(--color-bg)] rounded-3xl p-5">
          <div className="font-semibold mb-3 text-[13px]">{tr('jn.td.execution')}</div>
          <div className="text-[13px] flex flex-col gap-1.5">
            <Row label={tr('jn.td.status')} value={t.closed ? tr('jn.td.closed') : tr('jn.td.open')} />
            {!t.closed && <Row label={tr('jn.td.remaining')} value={fmtPct(t.remaining_pct, 0)} />}
            <Row label={tr('jn.td.exitDate')} value={t.exit_date ? String(t.exit_date).slice(0, 10) : '—'} />
            <Row label={tr('jn.td.holdCal')} value={analytics.hold_calendar_days ?? '—'} />
            <Row label={tr('jn.td.realizedR')} value={fmtR(t.realized_R)} valueColor={rColor(t.realized_R)} />
            <hr className="border-[var(--color-border-light)] my-1" />
            <div className="text-[11px] uppercase text-[var(--color-text-muted)] mt-1">{tr('jn.td.trims')}</div>
            {t.trims.length === 0 ? (
              <div className="text-[var(--color-text-muted)] text-[11px]">{tr('jn.td.noTrims')}</div>
            ) : (
              t.trims.map((tr, i) => (
                <div key={i} className="text-[11px] flex justify-between">
                  <span className="text-[var(--color-text-muted)]">{String(tr.date).slice(0, 10)} · {w(`jn.trim.${tr.type}`, tr.type)}</span>
                  <span className="tabular-nums">{fmtPct(tr.pct_of_position, 0)} @ {fmtCur(tr.price)}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Path analytics */}
        <div className="bg-[var(--color-bg)] rounded-3xl p-5">
          <div className="font-semibold mb-3 text-[13px]">{tr('jn.td.pathAnalytics')}</div>
          <div className="text-[13px] flex flex-col gap-1.5">
            <Row label={tr('jn.td.optExit')} value={analytics.optimal_exit_price != null ? fmtCur(analytics.optimal_exit_price) : '—'} />
            <Row label={tr('jn.td.optDate')} value={analytics.optimal_exit_date ? String(analytics.optimal_exit_date).slice(0, 10) : '—'} />
            <Row label={tr('jn.td.daysToOpt')} value={analytics.days_to_optimal ?? '—'} />
            <Row label={tr('jn.td.mfe')} value={fmtR(analytics.mfe_R)} valueColor={rColor(analytics.mfe_R)} />
            <Row label={tr('jn.td.mae')} value={fmtR(analytics.mae_R)} valueColor="text-[var(--color-loss)]" />
            <hr className="border-[var(--color-border-light)] my-1" />
            <Row label={tr('jn.td.realizedR')} value={fmtR(analytics.realized_R)} valueColor={rColor(analytics.realized_R)} />
            <Row label={tr('jn.td.availableR')} value={fmtR(analytics.optimal_R)} valueColor={rColor(analytics.optimal_R)} />
            <Row label={tr('jn.td.capturePct')} value={analytics.capture_pct != null ? `${analytics.capture_pct.toFixed(0)}%` : '—'} valueColor={captureColor(analytics.capture_pct)} />
          </div>
        </div>
      </div>
    </div>
  )
}

function Row({ label, value, valueColor }) {
  return (
    <div className="flex justify-between">
      <span className="text-[var(--color-text-muted)]">{label}</span>
      <span className={`tabular-nums font-semibold ${valueColor || ''}`}>{value}</span>
    </div>
  )
}

function fmtR(r) { return r == null ? '—' : `${r >= 0 ? '+' : ''}${r.toFixed(2)}R` }
function fmtPct(v, digits = 0, suffix = '') { return v == null ? '—' : `${v.toFixed(digits)}%${suffix}` }
function rColor(r) {
  if (r == null) return 'text-[var(--color-text-muted)]'
  if (r > 0) return 'text-[var(--color-profit)]'
  if (r < 0) return 'text-[var(--color-loss)]'
  return 'text-[var(--color-text-muted)]'
}
function lessonColor(lesson) {
  const map = {
    'Good execution':    'text-[var(--color-profit)]',
    'Premature trim':    'text-[var(--color-signal-caution)]',
    'Stopped too tight': 'text-[var(--color-signal-warning)]',
    'Failed setup':      'text-[var(--color-loss)]',
    'Choppy / no edge':  'text-[var(--color-text-muted)]',
    'In progress':       'text-[var(--color-accent)]',
  }
  return map[lesson] || 'text-[var(--color-text)]'
}
function captureColor(pct) {
  if (pct == null) return 'text-[var(--color-text-muted)]'
  if (pct >= 70) return 'text-[var(--color-profit)]'
  if (pct >= 40) return 'text-[var(--color-signal-caution)]'
  return 'text-[var(--color-loss)]'
}

/** Minimal markdownish renderer for the narrative: **bold** only. */
function markdownish(s) {
  if (!s) return ''
  return s
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
}
