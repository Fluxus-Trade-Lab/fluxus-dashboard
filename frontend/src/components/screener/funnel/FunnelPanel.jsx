import { useState } from 'react'
import { useLanguage } from '../../../i18n/LanguageContext'
import { useFocusDay } from './useFocusDay'
import {
  LIVE_SETUPS, PENDING_SETUPS, FOCUS_CAP,
  groupOf, accelDir, blockedAt, splitSetup, noteFor, isFlagged, freshness, netHighs,
} from './funnelMath'

/* The funnel Andy approved (artifact TTVDd4Jd8n2e6bRgrMxb1N, 2026-09-30 「合」):
   course ch.5 §5.2 made into the top of this page. Six layers, each one line of
   rule and one count; the last layer is the Focus list with one sentence per
   name (2026-10-01 「那 27 句候选，写法ok」). Every number comes from the daily
   focus-notes file — see funnelMath.js for why the page recomputes nothing. */

const fmt = (n) => (n == null ? '—' : n.toLocaleString('en-US'))
const signed = (x) => (x == null ? '—' : `${x > 0 ? '+' : x < 0 ? '−' : ''}${Math.abs(x)}`)
const ARROW = { up: '▲', down: '▼', flat: '·' }

function Layer({ n, title, rule, count, countLabel, children }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-[150px_minmax(0,1fr)_84px] gap-x-4 gap-y-1
                    py-3 border-t border-[var(--color-border-light)] first:border-t-0">
      <div>
        <div className="text-[11px] uppercase tracking-[0.06em] text-[var(--color-text-muted)]">{n}</div>
        <div className="text-[13px] font-semibold text-[var(--color-text-bold)]">{title}</div>
      </div>
      <div className="min-w-0">
        {rule && <p className="m-0 text-[13px] text-[var(--color-text-secondary)]">{rule}</p>}
        {children}
      </div>
      <div className="sm:text-right">
        {count != null && (
          <>
            <span className="font-mono text-[17px] text-[var(--color-text-bold)] tabular-nums">{count}</span>
            <span className="sm:block ml-2 sm:ml-0 text-[11px] text-[var(--color-text-muted)]">{countLabel}</span>
          </>
        )}
      </div>
    </div>
  )
}

function Chip({ on, off, onClick, children }) {
  const base = 'inline-flex items-baseline gap-2 rounded-md px-2.5 py-1 text-[13px] border'
  if (off) {
    return <span className={`${base} border-dashed border-[var(--color-border)] text-[var(--color-text-muted)]`}>{children}</span>
  }
  return (
    <button type="button" onClick={onClick} aria-pressed={on}
            className={`${base} cursor-pointer bg-[var(--color-surface)]
                        focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)]
                        ${on ? 'border-[var(--color-accent)] text-[var(--color-text-bold)] font-medium'
                             : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-hover-bg)]'}`}>
      {children}
    </button>
  )
}

function FactCard({ r, t }) {
  const g = groupOf(r)
  const items = [
    [t('funnel.fc.ema21'), r.ema21_atr == null ? '—' : `${r.ema21_atr.toFixed(2)} ATR`],
    [t('funnel.fc.sma50'), r.sma50_atr == null ? '—' : `${r.sma50_atr} ATR`],
    [t('funnel.fc.hi52'), `${r.hi52}%`],
    [t('funnel.fc.m1'), r.perf_1m == null ? '—' : `${r.perf_1m}%`],
    [t('funnel.fc.pctile'), r.grp_pctile ?? '—'],
    [t('funnel.fc.eps'), r.eps == null ? '—' : `${r.eps}%`],
    [t('funnel.fc.rev'), r.rev == null ? '—' : `${r.rev}%`],
    ...(g ? [
      [t('funnel.fc.group'), `${g.name}${g.kind === 'industry' ? ` (${t('funnel.industryNoTheme')})` : ''} · ${g.state}`],
      [t('funnel.fc.accel'), signed(g.accel)],
      [t('funnel.fc.ex1m'), `${g.ex1m}%`],
      [t('funnel.fc.prev'), (g.prev || []).join(' → ')],
    ] : []),
    [t('funnel.fc.big'), r.healthy ? '●' : '—'],
  ]
  return (
    <dl className="m-0 mt-1.5 flex flex-wrap gap-x-4 gap-y-0.5 text-[11px] text-[var(--color-text-muted)]">
      {items.map(([k, v]) => (
        <div key={k} className="flex gap-1.5"><dt>{k}</dt><dd className="m-0 font-mono tabular-nums text-[var(--color-text-secondary)]">{v}</dd></div>
      ))}
    </dl>
  )
}

/* 2026-10-01 「组方向和一行句子的内容重复性极高，有改」: the sentence already
   restates the group's name/state/accel in prose (e.g. "Cloud Software slid
   from Leading to Weakening, decelerating −33.6"), so a separate group row
   said the same thing twice and cost a whole line per candidate. The fix that
   stays in frontend/ — the sentence text itself is the daily skill's output,
   out of bounds until T-1001-16 rules — is to fold the group cue down to an
   arrow-and-state tag on the ticker line, and move the full name/accel number
   into the fact card where it was already half-duplicated (ex1m/prev). One
   row saved per candidate, nothing shown twice at first glance. */
function Candidate({ r, i, doc, lang, t, onTicker }) {
  const [open, setOpen] = useState(false)
  const g = groupOf(r)
  const dir = accelDir(g?.accel)
  const say = noteFor(doc, r.t, lang)
  const flag = isFlagged(say)
  return (
    <li className="grid grid-cols-[26px_72px_minmax(0,1fr)] gap-x-3 py-2 border-b border-[var(--color-border-light)]">
      <span className={`font-mono text-[11px] text-right pt-0.5 ${i < FOCUS_CAP ? 'text-[var(--color-accent)]' : 'text-[var(--color-text-muted)]'}`}>{i + 1}</span>
      <div>
        <button type="button" onClick={() => onTicker?.(r.t)}
                className="font-mono font-semibold text-[13px] text-[var(--color-text-bold)] bg-transparent border-0 p-0 cursor-pointer hover:underline"
                title={t('funnel.chartIt')}>
          {r.t}
        </button>
        <div className="text-[11px] text-[var(--color-text-muted)] font-mono">RS {r.rs ?? '—'}</div>
        {g && (
          <div className="text-[11px] text-[var(--color-text-muted)] font-mono" title={g.name}>
            {ARROW[dir]} {t(`funnel.accel.${dir}`)}
          </div>
        )}
      </div>
      <div className="min-w-0">
        <p className={`m-0 text-[13px] leading-relaxed max-w-[68ch]
                       ${flag ? 'text-[var(--color-loss)]' : say ? 'text-[var(--color-text)]' : 'text-[var(--color-text-muted)]'}`}>
          {say ?? t('funnel.noNote')}
        </p>
        <button type="button" onClick={() => setOpen((o) => !o)} aria-expanded={open}
                className="mt-1 text-[11px] text-[var(--color-text-muted)] bg-transparent border-0 p-0 cursor-pointer hover:text-[var(--color-text)]">
          {open ? '−' : '+'} {t('funnel.factCard')}
        </button>
        {open && <FactCard r={r} t={t} />}
      </div>
    </li>
  )
}

export default function FunnelPanel({ siteDate, onTicker }) {
  const { t, lang } = useLanguage()
  const { doc, status } = useFocusDay()
  const [setup, setSetup] = useState('pullback')
  const [showOther, setShowOther] = useState(false)
  const [showAll, setShowAll] = useState(false)

  if (status === 'loading') return null
  if (!doc) {
    return (
      <section className="mb-5 rounded-xl border border-[var(--color-border)] px-4 py-3 text-[13px] text-[var(--color-text-muted)]">
        {t('funnel.missing')}
      </section>
    )
  }

  const C = doc.counts || {}
  const G = doc.rule?.gate || {}
  const M = doc.market || {}
  const fresh = freshness(doc.asof, siteDate)
  const { focus, other, total } = splitSetup(doc, setup)
  const nh = netHighs(M)
  const market = doc.notes?._market?.[lang === 'zh' ? 'zh' : 'en']

  return (
    <section className="mb-6" aria-label={t('funnel.title')}>
      <div className="flex flex-wrap items-baseline justify-between gap-2 mb-1">
        <h2 className="m-0 text-[17px] font-semibold text-[var(--color-text-bold)]">{t('funnel.title')}</h2>
        <span className="text-[11px] text-[var(--color-text-muted)] font-mono">{t('funnel.asof', { date: doc.asof })}</span>
      </div>
      <p className="m-0 mb-2 text-[13px] text-[var(--color-text-secondary)]">{t('funnel.sub', { universe: fmt(C.universe) })}</p>
      {fresh === 'stale' && (
        <p className="m-0 mb-2 text-[13px] text-[var(--color-signal-caution)]">{t('funnel.stale', { date: doc.asof })}</p>
      )}

      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4">
        <Layer n="①" title={t('funnel.l1')} count={fmt(C.gate)} countLabel={t('funnel.pass')}
               rule={t('funnel.l1.rule', { cap: (G.cap ?? 0) / 1e9, vol: (G.dollar_vol ?? 0) / 1e6, adr: G.adr })} />
        <Layer n="②" title={t('funnel.l2')} count={fmt(C.healthy)} countLabel={t('funnel.onRadar')}
               rule={t('funnel.l2.rule', { healthy: fmt(C.healthy), both: fmt(C.healthy_gate) })} />
        <Layer n="③" title={t('funnel.l3')} rule={t('funnel.l3.rule')} />
        <Layer n="④" title={t('funnel.l4')} count={fmt(total)} countLabel={t('funnel.hits')}>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {LIVE_SETUPS.map((k) => (
              <Chip key={k} on={k === setup} onClick={() => { setSetup(k); setShowOther(false); setShowAll(false) }}>
                {t(`funnel.setup.${k}`)} <b className="font-mono font-medium">{doc.setups?.[k]?.rows?.length ?? 0}</b>
              </Chip>
            ))}
            {PENDING_SETUPS.map((k) => <Chip key={k} off>{t(`funnel.setup.${k}`)}</Chip>)}
          </div>
          <p className="m-0 mt-1.5 text-[11px] text-[var(--color-text-muted)]">{t('funnel.l4.pending')}</p>
        </Layer>
        <Layer n="⑤" title={t('funnel.l5')}>
          <dl className="m-0 grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-1 text-[13px]">
            {[
              [t('funnel.m.spy'), `${M.spy_light ?? '—'} ${M.spy_checks ?? '—'}/3`],
              [t('funnel.m.qqq'), `${M.qqq_light ?? '—'} ${M.qqq_checks ?? '—'}/3`],
              [t('funnel.m.verdict'), M.light_verdict ?? '—'],
              [t('funnel.m.breadth'), `${M.env ?? '—'} ${signed(M.score)}`],
              [t('funnel.m.regime'), `${M.regime ?? '—'} ${M.regime_score ?? ''}`],
              [t('funnel.m.highs'), `${M.nh ?? '—'} / ${M.nl ?? '—'}${nh == null ? '' : ` (${signed(nh)})`}`],
              [t('funnel.m.leaders'), `${M.leaders_hold ?? '—'} / ${M.leaders_n ?? '—'}`],
              [t('funnel.m.exposure'), M.exposure ?? '—'],
            ].map(([k, v]) => (
              <div key={k}><dt className="text-[11px] text-[var(--color-text-muted)]">{k}</dt>
                <dd className="m-0 font-mono tabular-nums text-[var(--color-text)]">{v}</dd></div>
            ))}
          </dl>
          <p className="m-0 mt-1.5 text-[11px] text-[var(--color-text-muted)]">
            {t('funnel.m.themes', {
              lead: (M.themes_leading || []).length, imp: (M.themes_improving || []).length,
              weak: (M.themes_weakening || []).length, lag: (M.themes_lagging || []).length,
            })}
          </p>
        </Layer>
        <Layer n="⑥" title={t('funnel.l6')} rule={t('funnel.l6.rule')} count={fmt(focus.length)} countLabel={t('funnel.candidates')}>
          {market && (
            <p className="m-0 mt-2 rounded-md bg-[var(--color-surface-alt)] px-3 py-2 text-[13px] text-[var(--color-text-secondary)]">
              <b className="text-[var(--color-text-bold)]">{t('funnel.marketLine')}</b> {market}
            </p>
          )}
          <p className="m-0 mt-2 text-[11px] text-[var(--color-text-muted)]">{t('funnel.ai')}</p>
          {focus.length ? (
            <>
              {/* §5.6 caps Focus at fifteen. The file may carry more; the page
                  shows the fifteen and folds the rest behind one line, so the
                  table below is not pushed three screens down. */}
              <ol className="list-none m-0 mt-1 p-0">
                {(showAll ? focus : focus.slice(0, FOCUS_CAP)).map((r, i) =>
                  <Candidate key={r.t} r={r} i={i} doc={doc} lang={lang} t={t} onTicker={onTicker} />)}
              </ol>
              {focus.length > FOCUS_CAP && (
                <button type="button" onClick={() => setShowAll((s) => !s)} aria-expanded={showAll}
                        className="mt-2 text-[11px] text-[var(--color-text-secondary)] bg-transparent border-0 p-0 cursor-pointer hover:text-[var(--color-text)]">
                  {showAll ? '−' : '+'} {t('funnel.overCap', { n: focus.length - FOCUS_CAP, cap: FOCUS_CAP })}
                </button>
              )}
            </>
          ) : (
            <p className="m-0 mt-2 text-[13px] text-[var(--color-text-muted)]">{t('funnel.none')}</p>
          )}
          {other.length > 0 && (
            <div className="mt-2">
              <button type="button" onClick={() => setShowOther((s) => !s)} aria-expanded={showOther}
                      className="text-[11px] text-[var(--color-text-secondary)] bg-transparent border-0 p-0 cursor-pointer hover:text-[var(--color-text)]">
                {showOther ? '−' : '+'} {t('funnel.more', { n: other.length })}
              </button>
              {showOther && (
                <ul className="list-none m-0 mt-1 p-0 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-[var(--color-text-muted)]">
                  {other.map((r) => {
                    const b = blockedAt(r)
                    return (
                      <li key={r.t}>
                        <button type="button" onClick={() => onTicker?.(r.t)}
                                className="font-mono text-[var(--color-text-secondary)] bg-transparent border-0 p-0 cursor-pointer hover:underline">{r.t}</button>
                        {' '}{b.layer === 'gate' ? t('funnel.blocked.gate') : t('funnel.blocked.s111', { n: b.passed })}
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>
          )}
          <p className="m-0 mt-3 mb-1 rounded-md border border-dashed border-[var(--color-border)] px-3 py-2 text-[11px] text-[var(--color-text-secondary)]">
            {t('funnel.stop')}
          </p>
        </Layer>
      </div>
    </section>
  )
}
