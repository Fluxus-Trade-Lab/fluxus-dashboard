import { useLanguage } from '../../i18n/LanguageContext'
import { word } from './richText'

/* One line of market readings off focus.json `market` (Andy 2026-10-04: the
   funnel's market card copied Market State; now it is one line and a link). */

const LIGHT_INK = { green: 'text-[var(--color-profit)]', red: 'text-[var(--color-loss)]' }

function Item({ k, children }) {
  return (
    <span className="inline-flex items-baseline gap-1.5 whitespace-nowrap">
      <span className="text-[11px] uppercase tracking-[0.06em] text-[var(--color-text-muted)]">{k}</span>
      {children}
    </span>
  )
}

function Light({ color, checks, t }) {
  return (
    <span>
      <span className={LIGHT_INK[color] ?? 'text-[var(--color-text)]'}>{word(t, `ms.light.${color}`, color) ?? '—'}</span>
      {' '}<span className="font-mono tabular-nums">{checks ?? '—'}/3</span>
    </span>
  )
}

export default function MarketStrip({ market: m }) {
  const { t } = useLanguage()
  if (!m) return null
  const env = m.env == null ? null : (t(`ms.env.${m.env}`) !== `ms.env.${m.env}` ? t(`ms.env.${m.env}`) : word(t, `sc.env.${m.env}`, m.env))
  return (
    <div data-testid="market-strip"
         className="flex flex-wrap items-center gap-x-5 gap-y-1.5 mb-4 px-4 py-2.5 rounded-xl
                    border border-[var(--color-border-light)] bg-[var(--color-surface)] text-[13px]">
      <span className="rounded-full px-2.5 py-0.5 text-[13px] font-semibold
                       bg-[var(--color-surface-alt)] text-[var(--color-text-bold)]">
        {word(t, `ms.verdict.${m.light_verdict}`, m.light_verdict) ?? '—'}
      </span>
      <Item k="SPY"><Light color={m.spy_light} checks={m.spy_checks} t={t} /></Item>
      <Item k="QQQ"><Light color={m.qqq_light} checks={m.qqq_checks} t={t} /></Item>
      <Item k={t('scx.m.breadth')}><span>{env ?? '—'}</span></Item>
      <Item k={t('scx.m.regime')}>
        <span>{word(t, `sc.regime.${m.regime}`, m.regime) ?? '—'}
          {m.regime_score != null && <span className="font-mono tabular-nums"> {m.regime_score}</span>}</span>
      </Item>
      <Item k={t('scx.m.highs')}>
        <span className="font-mono tabular-nums">{m.nh ?? '—'} / {m.nl ?? '—'}</span>
      </Item>
      <a href="#/breadth" className="ml-auto no-underline text-[var(--color-accent)] hover:underline">
        {t('scx.marketLink')}
      </a>
    </div>
  )
}
