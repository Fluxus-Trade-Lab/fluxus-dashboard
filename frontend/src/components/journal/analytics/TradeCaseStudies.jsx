import { useEffect, useMemo, useState } from 'react'
import { rMultiple } from '../../portfolio/lib/diagnosticsR'
import { computeTradeTechnicals, classifyTrade } from './lib/tradeTechnicals'
import { useLanguage } from '../../../i18n/LanguageContext'
import { rich, word } from '../../screener/richText'

const BASE = '/data/output/tickers'
const money = v => (v < 0 ? '-$' : '$') + Math.abs(Math.round(v)).toLocaleString()
const safe = s => String(s).toUpperCase().replace(/[/^]/g, '_')

function MAcell({ label, ma, above }) {
  const { t } = useLanguage()
  if (ma == null) return <div className="text-[var(--color-text-muted)]">{label} <span className="opacity-60">{t('jn.cs.na')}</span></div>
  return (
    <div>
      {label} <span className={above ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}>{above ? '▲' : '▼'}</span>{' '}
      <span className="tabular-nums">{ma.toFixed(2)}</span>
    </div>
  )
}

// Stack labels: jn.cs.stack.<bull|bull*|bear|bear*|mixed>.

function TradeCard({ t, bars }) {
  const { t: tr } = useLanguage()
  const R = rMultiple(t)
  const pl = t.realizedPL ?? t.totalPL ?? 0
  const win = pl > 0
  const tech = useMemo(() => (bars ? computeTradeTechnicals(bars, t) : null), [bars, t])
  const cls = useMemo(() => classifyTrade({ ...t, rr: R }, tech, t._isReattack), [t, tech, R])
  const trims = t.trims || []
  const intoStrength = trims.length && (t.direction !== 'short' ? trims[0].price > t.entryPrice : trims[0].price < t.entryPrice)
  const extreme = tech?.extAtr != null && Math.abs(tech.extAtr) >= 2

  return (
    <div className={`rounded-lg border p-3.5 bg-[var(--color-bg)] ${win ? 'border-[color-mix(in_srgb,var(--color-profit)_40%,transparent)]' : 'border-[color-mix(in_srgb,var(--color-loss)_40%,transparent)]'}`}>
      <div className="flex items-baseline justify-between mb-0.5">
        <div className="flex items-baseline gap-2">
          <span className="font-mono font-bold text-[13px]">{t.ticker}</span>
          <span className="text-[11px] uppercase px-1.5 py-0.5 rounded bg-[var(--color-surface)] text-[var(--color-text-muted)]">{word(tr, `jn.dir.${t.direction}`, t.direction)}</span>
        </div>
        <span className={`font-semibold text-[13px] tabular-nums ${win ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
          {money(pl)} {R != null && <span className="text-[13px] font-normal">· {R >= 0 ? '+' : ''}{R.toFixed(1)}R</span>}
        </span>
      </div>

      <div className={`text-[13px] font-medium mb-2 ${win ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>{tr(`jn.cs.type.${cls.code}`, cls.vars)}</div>

      {tech ? (
        <>
          <div className="grid grid-cols-3 gap-x-2 text-[11px] mb-1.5">
            <MAcell label="20EMA" ma={tech.ema20} above={tech.aboveEma20} />
            <MAcell label="50SMA" ma={tech.sma50} above={tech.aboveSma50} />
            <MAcell label="200SMA" ma={tech.sma200} above={tech.aboveSma200} />
          </div>
          <div className="text-[11px] text-[var(--color-text-secondary)] mb-1.5">{tech.stack ? tr(`jn.cs.stack.${tech.stack}`) : '—'}</div>

          <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[11px] text-[var(--color-text-secondary)]">
            <div>{rich(tr('jn.cs.ext'), { v: (
              <b className={extreme ? (win ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]') : ''}>
                {tr('jn.cs.extAtr', { v: `${tech.extAtr >= 0 ? '+' : ''}${tech.extAtr?.toFixed(1)}` })}</b>) })}</div>
            <div>{tr('jn.cs.atr', { v: tech.atrPct?.toFixed(1) })}</div>
            <div>{tr('jn.cs.hi20', { v: `${tech.distHi20Pct >= 0 ? '+' : ''}${tech.distHi20Pct?.toFixed(1)}` })}</div>
            <div>{tr('jn.cs.gap', { v: `${tech.gapPct >= 0 ? '+' : ''}${tech.gapPct?.toFixed(1)}` })}</div>
            <div>{tr(trims.length === 1 ? 'jn.cs.hold.one' : 'jn.cs.hold.many', { d: t.holdingDays, n: trims.length })}</div>
            <div>{tr(intoStrength ? 'jn.cs.intoStrength' : trims.length ? 'jn.cs.intoWeakness' : 'jn.cs.noScale')}</div>
          </div>
          {cls.notes?.length > 0 && (
            <div className="mt-1.5 text-[11px] text-[var(--color-signal-caution)]">⚠ {cls.noteCodes.map((n) => tr(`jn.cs.note.${n.k}`, n.vars)).join(' · ')}</div>
          )}
        </>
      ) : (
        <div className="text-[11px] text-[var(--color-text-muted)] py-2">
          {bars ? tr('jn.cs.noHistory') : tr('jn.cs.loadingHistory')}
        </div>
      )}
    </div>
  )
}

/**
 * Per-trade case-study cards — the 4 largest winners and 4 largest losers by
 * dollar P&L, each with point-in-time MA alignment, ATR extension, and a
 * setup/mistake label computed from public ticker OHLC (data/output/tickers).
 */
export default function TradeCaseStudies({ enriched }) {
  const { t: tr } = useLanguage()
  const closed = useMemo(() => (enriched || []).filter(t => t.isClosed), [enriched])

  // re-attack flag: an entry placed after a prior *red* entry on the same name
  const withFlag = useMemo(() => {
    const byTk = {}
    for (const t of closed) (byTk[t.ticker] ||= []).push(t)
    for (const tk in byTk) byTk[tk].sort((a, b) => (a.entryDate < b.entryDate ? -1 : 1))
    return closed.map(t => {
      const priors = (byTk[t.ticker] || []).filter(x => x.entryDate < t.entryDate)
      return { ...t, _isReattack: priors.some(x => (x.realizedPL ?? 0) < 0) }
    })
  }, [closed])

  const { winners, losers } = useMemo(() => {
    const sorted = [...withFlag].sort((a, b) => (b.realizedPL ?? 0) - (a.realizedPL ?? 0))
    return { winners: sorted.slice(0, 4), losers: sorted.slice(-4).reverse() }
  }, [withFlag])

  const tickers = useMemo(
    () => [...new Set([...winners, ...losers].map(t => t.ticker))],
    [winners, losers]
  )

  const [ohlc, setOhlc] = useState({})   // ticker -> bars | null (fetched, none)
  useEffect(() => {
    let cancelled = false
    tickers.forEach(async tk => {
      try {
        const res = await fetch(`${BASE}/${safe(tk)}.json`)
        if (!res.ok) throw new Error(String(res.status))
        const j = await res.json()
        const bars = j.ohlc_2y || j.ohlc_1y || j.ohlc || null
        if (!cancelled) setOhlc(p => ({ ...p, [tk]: bars }))
      } catch {
        if (!cancelled) setOhlc(p => ({ ...p, [tk]: null }))
      }
    })
    return () => { cancelled = true }
  }, [tickers])

  if (!closed.length) return null

  const Grid = ({ title, list, tint }) => (
    <div className="mb-5">
      <h4 className={`text-[13px] font-semibold uppercase tracking-wide mb-2 ${tint}`}>{title}</h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {list.map((t, i) => <TradeCard key={`${t.ticker}-${t.entryDate}-${i}`} t={t} bars={ohlc[t.ticker]} />)}
      </div>
    </div>
  )

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-4 mb-4">
      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-[13px] font-bold text-[var(--color-accent)]">★</span>
        <span className="font-semibold text-[13px]">{tr('jn.cs.title')}</span>
      </div>
      <p className="text-[11px] text-[var(--color-text-muted)] mb-3">
        {tr('jn.cs.lede')}
      </p>
      <Grid title={tr('jn.cs.winners')} list={winners} tint="text-[var(--color-profit)]" />
      <Grid title={tr('jn.cs.losers')} list={losers} tint="text-[var(--color-loss)]" />
    </div>
  )
}
