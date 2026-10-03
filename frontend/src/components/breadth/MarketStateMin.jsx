import BreadthPanes from './BreadthPanes'
import { verdictParts, indexCards, breadthTiles, crossAsset } from './marketStateMinMath'
import { leaderRows, themeTransitions, themeRows } from './morningReadMath'

/* Market State, minimal (Andy 2026-10-03, preview artifact Mf9ZEf6kYwVNSp3sR9GMNb:
   「对」). Data, not annotation: a label, one big number, one line under it.
   No book citations, no questions, no "what changed" prose — the order still
   follows the book (index → breadth → leaders → themes → cross-asset). */

const sgn = (v, d = 1) => (v == null ? '—' : `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(d)}`)
const pc = (v, d = 1) => (v == null ? '—' : `${sgn(v * 100, d)}%`)
const tone = (v) => (v == null || v === 0 ? '' : v > 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]')
const edge = (v) => (v == null || v === 0 ? 'border-l-[var(--color-border-light)]' : v > 0 ? 'border-l-[var(--color-profit)]' : 'border-l-[var(--color-loss)]')
const cell = (v) => (v == null || v === 0 ? '' : v > 0 ? 'bg-[color-mix(in_srgb,var(--color-profit)_12%,transparent)] text-[var(--color-profit)]' : 'bg-[color-mix(in_srgb,var(--color-loss)_12%,transparent)] text-[var(--color-loss)]')

function Sec({ children }) {
  return <h2 className="m-0 mt-6 mb-2 text-[11px] font-medium uppercase tracking-[.08em] text-[var(--color-text-muted)]">{children}</h2>
}

function Card({ sign, children }) {
  return <div className={`rounded-lg border border-[var(--color-border-light)] border-l-[3px] ${edge(sign)} bg-[var(--color-surface)] px-3.5 py-3`}>{children}</div>
}

function Pill({ good, children }) {
  const c = good === true ? 'text-[var(--color-profit)] bg-[color-mix(in_srgb,var(--color-profit)_12%,transparent)]'
    : good === false ? 'text-[var(--color-loss)] bg-[color-mix(in_srgb,var(--color-loss)_12%,transparent)]'
    : 'text-[var(--color-text-secondary)] bg-[var(--color-surface-alt)]'
  return <span className={`inline-block rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[.06em] ${c}`}>{children}</span>
}

const Mono = ({ className = '', children }) => <span className={`font-mono tabular-nums ${className}`}>{children}</span>

export function VerdictStrip({ ml }) {
  const v = verdictParts(ml)
  if (!v) return null
  const word = { full: true, dim: null, avoid: false }[v.verdict]
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 rounded-lg border border-[var(--color-border-light)] bg-[var(--color-surface)] px-4 py-3">
      <Pill good={word}>{v.verdict}</Pill>
      {v.parts.map((p) => (
        <span key={p.key} className="inline-flex items-baseline gap-1.5 text-[13px]">
          <span className="text-[11px] uppercase tracking-[.06em] text-[var(--color-text-muted)]">{p.label}</span>
          <Mono className={p.good === true ? 'text-[var(--color-profit)]' : p.good === false ? 'text-[var(--color-loss)]' : 'text-[var(--color-text)]'}>{p.value ?? '—'}</Mono>
          {p.detail && <span className="text-[11px] text-[var(--color-text-muted)]">{p.detail}</span>}
        </span>
      ))}
    </div>
  )
}

export default function MarketStateMin({ ml, etfs, signals, rows, paneRows, loadingFull, themes, groupsHistory, universe }) {
  const idx = indexCards(etfs, ml)
  const tiles = breadthTiles(rows)
  const leaders = leaderRows(ml, universe)
  const trans = themeRows(themeTransitions(groupsHistory), themes)
  const cross = crossAsset(etfs, signals)
  return (
    <div>
      <VerdictStrip ml={ml} />

      <Sec>Index</Sec>
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-2.5">
        {idx.map((c) => {
          const st = c.light ? [c.light === 'green' ? 'Uptrend' : c.light === 'red' ? 'Downtrend' : 'Mixed', c.light === 'green' ? true : c.light === 'red' ? false : null]
            : c.aboveSma50 == null ? null : [c.aboveSma50 ? '> 50-day' : '< 50-day', c.aboveSma50]
          return (
            <Card key={c.ticker} sign={c.chg}>
              <div className="flex items-baseline justify-between gap-2">
                <Mono className="text-[13px] font-semibold text-[var(--color-text-bold)]">{c.ticker}</Mono>
                <Mono className={`text-[17px] ${tone(c.chg)}`}>{pc(c.chg, 2)}</Mono>
              </div>
              <Mono className="block mt-0.5 text-[11px] text-[var(--color-text-muted)]">${c.close?.toFixed(2)} · {c.fromHigh == null ? '' : Math.abs(c.fromHigh) < 0.0005 ? 'at high' : `${pc(c.fromHigh)} from high`}</Mono>
              <div className="mt-2 flex items-center justify-between gap-2 text-[11px] text-[var(--color-text-muted)]">
                {st ? <Pill good={st[1]}>{st[0]}</Pill> : <span />}
                <Mono className="whitespace-nowrap">1W {pc(c.w1)}</Mono>
              </div>
            </Card>
          )
        })}
      </div>

      <Sec>Breadth</Sec>
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-2.5">
        {tiles.map((t) => (
          <Card key={t.key} sign={t.sign}>
            <div className="text-[11px] uppercase tracking-[.04em] text-[var(--color-text-muted)]">{t.label}</div>
            <Mono className="block mt-0.5 text-[26px] leading-tight text-[var(--color-text-bold)]">
              {t.value == null ? '—' : typeof t.value === 'string' ? t.value
                : t.key === 'adv' ? `${t.value > 0 ? '+' : ''}${t.value.toLocaleString()}`
                : t.key === 'mco' ? sgn(t.value) : `${Math.round(t.value)}${t.unit ?? ''}`}
            </Mono>
            <Mono className="block mt-1 text-[11px] text-[var(--color-text-muted)]">
              {t.sub ?? (t.delta == null ? '' : `${sgn(t.delta)} vs prior`)}
            </Mono>
          </Card>
        ))}
      </div>
      <div className="mt-2.5 rounded-lg border border-[var(--color-border-light)] bg-[var(--color-surface)] px-3 py-2.5">
        <BreadthPanes rows={paneRows} loadingFull={loadingFull} bare initialIndicator="kma" />
      </div>

      <Sec>Leaders</Sec>
      <div className="overflow-x-auto rounded-lg border border-[var(--color-border-light)] bg-[var(--color-surface)]">
        <table className="w-full border-collapse text-[13px]">
          <thead><tr className="text-[11px] uppercase tracking-[.04em] text-[var(--color-text-muted)]">
            {['Ticker', 'Theme', 'RS', 'RS line', '1D', '1W', 'From high', '50-day'].map((h, i) =>
              <th key={h} className={`px-2.5 py-2 font-medium border-b border-[var(--color-border-light)] whitespace-nowrap ${i < 2 ? 'text-left' : 'text-right'}`}>{h}</th>)}
          </tr></thead>
          <tbody>{leaders.map((l) => (
            <tr key={l.ticker} className="border-b border-[var(--color-border-light)] last:border-0">
              <td className="px-2.5 py-1.5"><Mono className="font-semibold text-[var(--color-text-bold)]">{l.ticker}</Mono></td>
              <td className="px-2.5 py-1.5 text-[var(--color-text-secondary)] whitespace-nowrap">{l.theme ?? '—'}</td>
              <td className="px-2.5 py-1.5 text-right"><Mono>{l.rs_rating ?? '—'}</Mono></td>
              <td className="px-2.5 py-1.5 text-right"><Mono>{l.rs_line == null ? '—' : Math.round(l.rs_line)}</Mono></td>
              <td className={`px-2.5 py-1.5 text-right ${cell(l.chg)}`}><Mono>{pc(l.chg)}</Mono></td>
              <td className={`px-2.5 py-1.5 text-right ${cell(l.w1)}`}><Mono>{pc(l.w1)}</Mono></td>
              <td className="px-2.5 py-1.5 text-right"><Mono>{pc(l.from_high)}</Mono></td>
              <td className={`px-2.5 py-1.5 text-right ${l.status === 'holding' ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>{l.status === 'holding' ? '●' : '○'}</td>
            </tr>))}
          </tbody>
        </table>
      </div>

      <Sec>Themes</Sec>
      <div className="overflow-x-auto rounded-lg border border-[var(--color-border-light)] bg-[var(--color-surface)]">
        <table className="w-full border-collapse text-[13px]">
          <thead><tr className="text-[11px] uppercase tracking-[.04em] text-[var(--color-text-muted)]">
            {['Theme', 'State', '1D', '1W', '1M', '3M', 'Names'].map((h, i) =>
              <th key={h} className={`px-2.5 py-2 font-medium border-b border-[var(--color-border-light)] whitespace-nowrap ${i < 2 ? 'text-left' : 'text-right'}`}>{h}</th>)}
          </tr></thead>
          <tbody>{trans.map((t) => (
            <tr key={t.name} className="border-b border-[var(--color-border-light)] last:border-0">
              <td className="px-2.5 py-1.5 whitespace-nowrap">{t.name}</td>
              <td className="px-2.5 py-1.5 whitespace-nowrap text-[var(--color-text-secondary)]">{t.from} → <b className={`font-medium ${t.dir === 'up' ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>{t.to}</b></td>
              {[t.d1, t.w1, t.m1, t.m3].map((v, i) => <td key={i} className={`px-2.5 py-1.5 text-right ${cell(v)}`}><Mono>{pc(v)}</Mono></td>)}
              <td className="px-2.5 py-1.5 text-right"><Mono>{t.members ?? '—'}</Mono></td>
            </tr>))}
          </tbody>
        </table>
      </div>

      <Sec>Cross-asset</Sec>
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-2.5">
        {cross.map((c) => (
          <Card key={c.ticker} sign={c.chg}>
            <div className="flex items-baseline justify-between gap-2">
              <Mono className="text-[13px] font-semibold text-[var(--color-text-bold)]">{c.ticker}</Mono>
              <Mono className={`text-[13px] ${c.ticker === 'VIX' ? 'text-[var(--color-text)]' : tone(c.chg)}`}>{c.ticker === 'VIX' ? (c.last?.toFixed(2) ?? '—') : pc(c.chg, 2)}</Mono>
            </div>
            <Mono className="block mt-1 text-[11px] text-[var(--color-text-muted)]">
              {c.ticker === 'VIX' ? 'volatility index' : `1W ${pc(c.w1)} · vs SPY ${sgn(c.vsSpy == null ? null : c.vsSpy * 100)}`}
            </Mono>
          </Card>
        ))}
      </div>
    </div>
  )
}
