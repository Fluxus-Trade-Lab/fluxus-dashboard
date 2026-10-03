import { useMemo, useState } from 'react'
import { buildPanes, INDICATORS, POOLS, indicatorText } from './breadthPanesMath'
import { useLanguage } from '../../i18n/LanguageContext'
import { withVars } from './marketStateMinMath'

/**
 * Index over breadth, on one time axis — step ②'s chart.
 *
 * Andy 09-23, from his TradingView "NASDAQ / net new highs vs lows" screenshot:
 * 「上方是指数，下方是指标。可以和历史超卖进行对比」, then 「把σ尺子和切池子加进
 * 预览，接进②广度那段，设计方向朝traderslab走」. What is TradersLab's here: the
 * card header with pool tabs, the value tags on the right edge, the fixed σ
 * lines. What is ours: the oversold bands and the "what the index did next"
 * table — the part that turns "looks like last time" into a number.
 *
 * Axes are fixed for the window shown; switching the indicator never rescales
 * the index pane. Hover reads true values. Nothing is marked on the line
 * itself (chart-for-andy: 突变不标记).
 */

const W = 1120, H = 470, L = 8, R = 84, T = 12, GAP = 26, H1 = 230, BOTTOM = 26
const H2 = H - T - H1 - GAP - BOTTOM

function Seg({ items, value, onChange, label }) {
  return (
    <span className="inline-flex items-center gap-1.5 max-w-full">
      {label && <span className="text-[11px] font-mono uppercase tracking-[.08em] text-[var(--color-text-muted)]">{label}</span>}
      <span className="inline-flex max-w-full border border-[var(--color-border)] rounded-md overflow-x-auto">
        {items.map((it) => (
          <button key={it.key} type="button" disabled={!!it.disabled} title={it.title}
                  aria-pressed={value === it.key}
                  onClick={() => !it.disabled && onChange(it.key)}
                  className={`shrink-0 whitespace-nowrap text-[11px] font-mono px-2.5 py-1 border-0 cursor-pointer disabled:cursor-not-allowed disabled:opacity-45
                              ${value === it.key ? 'bg-[var(--color-text)] text-[var(--color-surface)]' : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'}`}>
            {it.label}
          </button>
        ))}
      </span>
    </span>
  )
}

/** TradersLab-style value tag on the right edge of a pane. */
// 20-day ink, 50-day accent, 200-day muted + dashed: told apart by colour AND
// stroke, since this theme's accent is itself a blue (chart-for-andy: never
// two greys, never two blues).
const EXTRA_INK = ['var(--color-accent)', 'var(--color-text-muted)']
const EXTRA_DASH = ['', '6 3']

function Tag({ y, text, tone = 'ink' }) {
  const fill = tone === 'pos' ? 'var(--color-took)' : tone === 'neg' ? 'var(--color-refused)' : tone === 'accent' ? 'var(--color-accent)' : tone === 'muted' ? 'var(--color-text-muted)' : 'var(--color-text)'
  const w = Math.max(30, text.length * 6.6 + 8)
  return (
    <g>
      <rect x={W - R + 4} y={y - 8} width={w} height={16} rx="2" fill={fill} />
      <text x={W - R + 8} y={y + 4} fontSize="11" style={{ fill: 'var(--color-surface)', fontFamily: 'var(--font-mono, ui-monospace, monospace)' }}>{text}</text>
    </g>
  )
}

// `bare` (Market State minimal, Andy 2026-10-03 「少注解」「做到极简」): no subtitle,
// no explanatory footer, no pending pool tab, no episodes fold — data and controls only.
export default function BreadthPanes({ rows, loadingFull, bare = false, initialIndicator = 'nhnl' }) {
  const [indicator, setIndicator] = useState(initialIndicator)
  const [pool, setPool] = useState('all')
  const [scale, setScale] = useState('abs')
  const [window, setWindow] = useState(250)
  const [pct, setPct] = useState(0.1)
  const [hover, setHover] = useState(null)
  const lt = useLanguage().t
  const t = useMemo(() => withVars(lt), [lt])

  const p = useMemo(() => buildPanes(rows, { indicator, pool, scale, window, pct, t }), [rows, indicator, pool, scale, window, pct, t])
  const tx = p.text
  const n = p.dates.length
  if (n < 2) return <p className="m-0 text-[13px] italic text-[var(--color-text-muted)]">{t('ms.pane.notLoaded')}</p>

  const x = (j) => L + (j * (W - L - R)) / (n - 1)
  const bw = (W - L - R) / (n - 1)
  const idx = p.index.filter(Number.isFinite)
  const lo1 = Math.min(...idx), hi1 = Math.max(...idx)
  const y1 = (v) => T + (1 - (v - lo1) / (hi1 - lo1 || 1)) * H1
  // overlays count toward the scale, so a second line is never drawn off the pane
  const fin = [p.value, ...(p.extras ?? []).map((e) => e.values)].flat().filter(Number.isFinite)
  let lo2 = fin.length ? Math.min(...fin) : -1, hi2 = fin.length ? Math.max(...fin) : 1
  if (p.indicator.zero) { lo2 = Math.min(lo2, 0); hi2 = Math.max(hi2, 0) }
  if (p.indicator.range && scale === 'abs') { [lo2, hi2] = p.indicator.range }
  if (scale === 'z') { lo2 = -3.4; hi2 = 3.4 }
  const top2 = T + H1 + GAP
  const y2 = (v) => top2 + (1 - (v - lo2) / (hi2 - lo2 || 1)) * H2
  const path = (arr, yf) => { let d = '', pen = false; arr.forEach((v, j) => { if (!Number.isFinite(v)) { pen = false; return } d += `${pen ? 'L' : 'M'}${x(j).toFixed(1)} ${yf(v).toFixed(1)}`; pen = true }); return d }
  const fmt = (v, d = 0) => (v == null ? '—' : Number(v).toFixed(scale === 'z' ? 2 : d))
  // ratios live near 1, so they keep two decimals; counts and percents round
  const tagNum = (v) => (Math.abs(v) < 10 && v % 1 ? v.toFixed(2) : `${Math.round(v)}`)
  const last = p.value.at(-1), lastIdx = p.index.at(-1)
  const months = []
  let lastM = ''
  p.dates.forEach((d, j) => { const m = d.slice(0, 7); if (m !== lastM) { lastM = m; months.push([j, m]) } })

  const onMove = (ev) => {
    const svg = ev.currentTarget
    const pt = svg.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY
    const q = pt.matrixTransform(svg.getScreenCTM().inverse())
    setHover(Math.max(0, Math.min(n - 1, Math.round(((q.x - L) / (W - L - R)) * (n - 1)))))
  }

  return (
    <div>
      {/* header — the TradersLab register: title left, pool tabs right */}
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 mb-2">
        <div className="text-[13px] font-semibold text-[var(--color-text)]">
          {t('ms.pane.title')}
          {!bare && <span className="ml-2 text-[11px] font-normal text-[var(--color-text-muted)]">{t('ms.pane.subtitle', { label: tx.label })}</span>}
        </div>
        <Seg label={t('ms.pane.pool')} value={pool} onChange={setPool}
             items={POOLS.filter((q) => !(bare && q.pending)).map((q) => {
               const ql = t(`ms.pool.${q.key}`)
               return { key: q.key, label: q.pending ? t('ms.pane.pending', { label: ql }) : q.note && !bare ? t('ms.pane.sessions9', { label: ql }) : ql,
                 disabled: !!q.pending, title: q.pending ? t('ms.pane.pendingTitle', { id: q.pending }) : q.note ? t(`ms.pool.${q.key}Note`) : q.note }
             })} />
      </div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mb-2">
        <Seg value={indicator} onChange={setIndicator} items={Object.keys(INDICATORS).map((k) => ({ key: k, label: indicatorText(k, t).label }))} />
        <Seg label={t('ms.pane.ruler')} value={scale} onChange={setScale} items={[{ key: 'abs', label: t('ms.pane.abs') }, { key: 'z', label: t('ms.pane.z') }]} />
        <Seg label={t('ms.pane.window')} value={window} onChange={setWindow} items={[{ key: 120, label: t('ms.pane.w6m') }, { key: 250, label: t('ms.pane.w12m') }, { key: 9999, label: t('ms.pane.wAll') }]} />
        <Seg label={t('ms.pane.oversold')} value={pct} onChange={setPct} items={[{ key: 0.1, label: scale === 'z' ? '−2σ' : t('ms.pane.lowest10') }, { key: 0.2, label: scale === 'z' ? '−1σ' : t('ms.pane.lowest20') }]} />
      </div>

      <div className="relative rounded-2xl border border-[var(--color-border-light)] bg-[var(--color-bg)]">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto block" role="img"
             aria-label={t('ms.pane.aria', { label: tx.label, n })}
             onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
          {/* oversold bands across both panes; the last 15 sessions in accent */}
          {p.bands.map(([a, b]) => (
            <rect key={`${a}-${b}`} x={x(a) - bw / 2} y={T} width={x(b) - x(a) + bw} height={H - T - BOTTOM} fill="var(--color-text)" opacity=".07" />
          ))}
          <rect x={x(p.recentFrom) - bw / 2} y={T} width={x(n - 1) - x(p.recentFrom) + bw} height={H - T - BOTTOM} fill="var(--color-accent)" opacity=".10" />
          {/* index pane */}
          {[0, 0.25, 0.5, 0.75, 1].map((k) => {
            const v = lo1 + (hi1 - lo1) * k, y = y1(v)
            return <g key={k}><line x1={L} x2={W - R} y1={y} y2={y} stroke="var(--color-border-light)" strokeDasharray="2 4" /><text x={W - R + 6} y={y + 4} fontSize="10" style={{ fill: 'var(--color-text-muted)' }}>{v.toFixed(0)}</text></g>
          })}
          <path d={path(p.index, y1)} fill="none" stroke="var(--color-text)" strokeWidth="1.5" />
          <text x={L + 4} y={T + 11} fontSize="11" style={{ fill: 'var(--color-text-secondary)' }}>{t('ms.pane.spx')}</text>
          {lastIdx != null && <Tag y={y1(lastIdx)} text={lastIdx.toFixed(0)} />}
          {/* indicator pane */}
          {[0, 0.25, 0.5, 0.75, 1].map((k) => {
            const v = lo2 + (hi2 - lo2) * k, y = y2(v)
            return <g key={k}><line x1={L} x2={W - R} y1={y} y2={y} stroke="var(--color-border-light)" strokeDasharray="2 4" /><text x={W - R + 6} y={y + 4} fontSize="10" style={{ fill: 'var(--color-text-muted)' }}>{scale === 'z' ? v.toFixed(1) : v.toFixed(v % 1 ? 1 : 0)}</text></g>
          })}
          {p.indicator.zero && <line x1={L} x2={W - R} y1={y2(0)} y2={y2(0)} stroke="var(--color-text-muted)" />}
          {scale === 'abs' && (p.indicator.lines ?? []).map((v) => (
            <line key={v} x1={L} x2={W - R} y1={y2(v)} y2={y2(v)} stroke="var(--color-text-muted)" strokeDasharray="3 3" />
          ))}
          {scale === 'z' && [-2, -1, 1, 2].map((sv) => (
            <g key={sv}>
              <line x1={L} x2={W - R} y1={y2(sv)} y2={y2(sv)} stroke={sv < 0 ? 'var(--color-took)' : 'var(--color-refused)'} strokeDasharray={Math.abs(sv) === 2 ? '' : '3 3'} opacity=".7" />
              <Tag y={y2(sv)} text={`${sv > 0 ? '+' : ''}${sv}σ`} tone={sv < 0 ? 'pos' : 'neg'} />
            </g>
          ))}
          {p.threshold != null && scale === 'abs' && (
            <line x1={L} x2={W - R} y1={y2(p.threshold)} y2={y2(p.threshold)} stroke="var(--color-accent)" strokeDasharray="4 3" />
          )}
          {p.indicator.zero
            ? p.value.map((v, j) => Number.isFinite(v) && (
              <rect key={j} x={x(j) - bw * 0.45} y={Math.min(y2(v), y2(0))} width={Math.max(0.8, bw * 0.9)} height={Math.max(0.5, Math.abs(y2(v) - y2(0)))}
                    fill={v >= 0 ? 'var(--color-took)' : 'var(--color-refused)'} />
            ))
            : <path d={path(p.value, y2)} fill="none" stroke="var(--color-text)" strokeWidth="1.4" />}
          {/* overlays (kma): one colour per average, each tagged with its last value */}
          {(p.extras ?? []).map((e, i) => {
            const c = EXTRA_INK[i % EXTRA_INK.length], lv = e.values.at(-1)
            return (
              <g key={e.key}>
                <path d={path(e.values, y2)} fill="none" stroke={c} strokeWidth="1.4" strokeDasharray={e.dash == null ? EXTRA_DASH[i % EXTRA_DASH.length] : e.dash ? '6 3' : ''} />
                {Number.isFinite(lv) && <Tag y={Math.min(Math.max(y2(lv), top2 + 8), H - BOTTOM - 8)} text={tagNum(lv)} tone={i ? 'muted' : 'accent'} />}
              </g>
            )
          })}
          {(p.extras ?? []).length
            ? <text x={L + 4} y={top2 + 11} fontSize="11">
                <tspan style={{ fill: 'var(--color-text)' }}>{tx.primary}</tspan>
                {p.extras.map((e, i) => <tspan key={e.key} dx="10" style={{ fill: EXTRA_INK[i % EXTRA_INK.length] }}>{tx.extra[e.key] ?? e.label}</tspan>)}
              </text>
            : <text x={L + 4} y={top2 + 11} fontSize="11" style={{ fill: 'var(--color-text-secondary)' }}>{tx.label}{scale === 'z' ? ' · σ' : ''}</text>}
          {Number.isFinite(last) && <Tag y={Math.min(Math.max(y2(last), top2 + 8), H - BOTTOM - 8)} text={scale === 'z' ? `${last.toFixed(2)}σ` : (p.extras ?? []).length ? tagNum(last) : `${fmt(last, last % 1 ? 1 : 0)}`} tone={(p.extras ?? []).length ? 'ink' : 'accent'} />}
          {/* months */}
          {months.map(([j, m], i) => (i > 0 || window <= 250) && (
            <text key={m} x={x(j)} y={H - 8} fontSize="10" style={{ fill: 'var(--color-text-muted)' }}>{m.slice(5) === '01' ? m.slice(0, 4) : m.slice(5)}</text>
          ))}
          {hover != null && <line x1={x(hover)} x2={x(hover)} y1={T} y2={H - BOTTOM} stroke="var(--color-accent)" />}
        </svg>
        {hover != null && (
          <div className="absolute top-2 left-3 text-[11px] font-mono px-2 py-1 rounded bg-[var(--color-text)] text-[var(--color-surface)] pointer-events-none">
            {p.dates[hover]} · {t('ms.pane.spxShort')} {p.index[hover]?.toFixed(0) ?? '—'} · {tx.label} {Number.isFinite(p.value[hover])
              ? (scale === 'z' ? `${p.value[hover].toFixed(2)}σ (${t('ms.pane.raw', { v: fmt(p.raw[hover], 1) })})` : fmt(p.value[hover], p.value[hover] % 1 ? 1 : 0))
              : '—'}{tx.unit && scale !== 'z' ? ` ${tx.unit}` : ''}
          </div>
        )}
      </div>
      {/* the long form of all this lives on the tooltip — the page keeps one line
          (Andy 09-23: 「你的文字太多了」), but nothing self-made goes unstated */}
      {!bare && <p className="m-0 mt-1.5 text-[11px] text-[var(--color-text-muted)]"
         title={`${p.poolNote ? p.poolNote + ' ' : ''}${tx.note}. ${p.rule}`}>
        {t('ms.pane.legend')}
        {p.poolNote ? t('ms.pane.poolNoteMark') : ''}{loadingFull ? t('ms.pane.loadingFull') : ''}
        <span className="ml-1 underline decoration-dotted cursor-help">{t('ms.pane.howCut')}</span>
      </p>}

      {!bare && p.episodes.length > 0 && (
        <details className="mt-2 text-[13px]">
          <summary className="cursor-pointer text-[var(--color-text-secondary)]">
            {t('ms.pane.epHead')} <span className="font-mono text-[var(--color-text-muted)]">{p.episodes.length}</span> {t('ms.pane.epTail', { n: 20 })}
          </summary>
          <div className="overflow-x-auto mt-2">
            <table className="w-full border-collapse text-[13px]">
              <thead><tr className="text-[11px] font-mono uppercase tracking-[.08em] text-[var(--color-text-muted)]">
                <th className="text-left font-medium py-1 pr-3">{t('ms.pane.epCol')}</th><th className="text-right font-medium py-1 pr-3">{t('ms.pane.sessCol')}</th>
                <th className="text-right font-medium py-1 pr-3">{t('ms.pane.lowCol')}{scale === 'z' ? ' (σ)' : ''}</th><th className="text-right font-medium py-1">{t('ms.pane.afterCol')}</th>
              </tr></thead>
              <tbody>
                {p.episodes.map((e) => (
                  <tr key={e.from} className="border-t border-[var(--color-border-light)]">
                    <td className="py-1 pr-3 font-mono">{e.from} → {e.to}</td>
                    <td className="py-1 pr-3 text-right tabular-nums">{e.days}</td>
                    <td className="py-1 pr-3 text-right tabular-nums">{scale === 'z' ? e.min.toFixed(2) : e.min.toFixed(0)}</td>
                    <td className={`py-1 text-right tabular-nums ${e.after == null ? 'text-[var(--color-text-muted)]' : e.after >= 0 ? 'text-[var(--color-took)]' : 'text-[var(--color-refused)]'}`}>
                      {e.after == null ? t('ms.pane.inProgress') : `${(e.after * 100).toFixed(1)}%${e.partial ? t('ms.pane.under20') : ''}`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </div>
  )
}
