import { useLanguage } from '../../i18n/LanguageContext'
import { dataName } from '../../i18n/names'
import { useShortlist } from '../../hooks/useShortlist'
import { useMyShortlist } from '../../hooks/useMyShortlist'
import { word } from './richText'

/**
 * The Screener's one results table (Andy 2026-10-04, plan A): the funnel and
 * the custom screen both land here. Row count is a switch — 5 / 10 / 15 / all,
 * default 10 — and the footer says how many are folded. 「+ 短名单」 writes the
 * same store Today's List reads.
 *
 * A row: { t, rs, group, gstate, e21, s50, m1, hi, note, flagged, entry }
 *   e21 / s50 in ATR, m1 / hi in percent, entry = what the shortlist keeps.
 */

export const TOP_N = [5, 10, 15, Infinity]
export const DEFAULT_TOP_N = 10

const PRESS = 'transition-transform duration-100 ease-out active:scale-[0.97]'
const atr = (v, d) => (v == null ? '—' : `${v.toFixed(d)} ATR`)
const pct = (v) => (v == null ? '—' : `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(1)}%`)
const STATE_INK = {
  Leading: 'text-[var(--color-profit)]',
  Improving: 'text-[var(--color-profit)]',
  Weakening: 'text-[var(--color-loss)]',
  Lagging: 'text-[var(--color-loss)]',
}

function TopN({ n, setN }) {
  const { t } = useLanguage()
  return (
    <div role="group" aria-label={t('scx.show.aria')} data-testid="top-n"
         className="inline-flex rounded-[9px] p-[3px] bg-[var(--color-surface-alt)]">
      {TOP_N.map((k) => (
        <button key={k} type="button" aria-pressed={n === k} onClick={() => setN(k)}
                className={`border-0 rounded-[7px] px-2.5 py-1 text-[13px] cursor-pointer ${PRESS}
                            ${n === k ? 'bg-[var(--color-surface)] text-[var(--color-text-bold)] font-semibold'
                                      : 'bg-transparent text-[var(--color-text-secondary)]'}`}>
          {k === Infinity ? t('scx.show.all') : k}
        </button>
      ))}
    </div>
  )
}

function AddButton({ row }) {
  const { t } = useLanguage()
  const { add, remove } = useShortlist()
  // on = on 我的短名单 as Today's List shows it, including the file's own names
  const on = useMyShortlist().includes(row.t)
  return (
    <button type="button" aria-pressed={on} data-add={row.t}
            title={t(on ? 'scx.removeT' : 'scx.addT')}
            onClick={() => (on ? remove(row.t) : add(row.t, row.entry ?? {}, row.from ?? null))}
            className={`whitespace-nowrap rounded-[7px] border px-2 py-0.5 text-[13px] cursor-pointer ${PRESS}
                        ${on ? 'bg-[var(--color-accent-solid)] border-[var(--color-accent-solid)] text-white'
                             : 'bg-transparent border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-hover-bg)]'}`}>
      {t(on ? 'scx.added' : 'scx.add')}
    </button>
  )
}

export default function ResultsTable({ title, rows, n, setN, onChart }) {
  const { t, lang } = useLanguage()
  const shown = rows.slice(0, n)
  const rest = rows.length - shown.length
  const th = 'px-2 py-1.5 text-[11px] font-medium tracking-[0.04em] text-[var(--color-text-muted)] whitespace-nowrap border-b border-[var(--color-border-light)]'
  const td = 'px-2 py-2 border-b border-[var(--color-border-light)] align-top'
  const num = 'text-right font-mono tabular-nums whitespace-nowrap'
  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
        <div className="text-[13px]">
          <b className="text-[var(--color-text-bold)]">{title}</b>{' '}
          <span className="font-mono text-[var(--color-text-muted)]" data-testid="row-count">{shown.length} / {rows.length}</span>
        </div>
        <TopN n={n} setN={setN} />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-[13px]" data-testid="results">
          <thead>
            <tr>
              <th className={`${th} text-right`}>#</th>
              <th className={`${th} text-left`}>{t('scx.col.ticker')}</th>
              <th className={`${th} text-right`}>RS</th>
              <th className={`${th} text-left`}>{t('scx.col.theme')}</th>
              <th className={`${th} text-right`}>{t('scx.col.e21')}</th>
              <th className={`${th} text-right`}>{t('scx.col.s50')}</th>
              <th className={`${th} text-right`}>{t('scx.col.m1')}</th>
              <th className={`${th} text-right`}>{t('scx.col.hi')}</th>
              <th className={`${th} text-left`}>{t('scx.col.note')}</th>
              <th className={th} />
            </tr>
          </thead>
          <tbody>
            {shown.map((r, i) => (
              <tr key={r.t} data-row={r.t}>
                <td className={`${td} ${num} text-[11px] text-[var(--color-text-muted)]`}>{i + 1}</td>
                <td className={td}>
                  <button type="button" onClick={() => onChart?.(r.t)} title={t('scx.chartT', { t: r.t })}
                          className="font-mono font-semibold text-[13px] text-[var(--color-text-bold)] bg-transparent border-0 p-0 cursor-pointer hover:underline">
                    {r.t}
                  </button>
                </td>
                <td className={`${td} ${num}`}>{r.rs ?? '—'}</td>
                <td className={`${td} min-w-[150px]`}>
                  <span className="text-[var(--color-text)]">{r.group ? dataName(r.group, lang) : '—'}</span>
                  {r.gstate && (
                    <span className={`ml-1.5 whitespace-nowrap rounded-full px-1.5 py-px text-[11px] bg-[var(--color-surface-alt)] ${STATE_INK[r.gstate] ?? 'text-[var(--color-text-secondary)]'}`}>
                      {word(t, `state.${r.gstate}`, r.gstate)}
                    </span>
                  )}
                </td>
                <td className={`${td} ${num}`}>{atr(r.e21, 2)}</td>
                <td className={`${td} ${num}`}>{atr(r.s50, 1)}</td>
                <td className={`${td} ${num} ${r.m1 > 0 ? 'text-[var(--color-profit)]' : r.m1 < 0 ? 'text-[var(--color-loss)]' : ''}`}>{pct(r.m1)}</td>
                <td className={`${td} ${num}`}>{pct(r.hi)}</td>
                <td className={`${td} min-w-[260px] ${r.flagged ? 'text-[var(--color-loss)]' : 'text-[var(--color-text-secondary)]'}`}>{r.note ?? '—'}</td>
                <td className={`${td} text-right`}><AddButton row={r} /></td>
              </tr>
            ))}
            {!rows.length && (
              <tr><td colSpan={10} className="py-6 text-center text-[13px] text-[var(--color-text-muted)]">{t('scx.empty')}</td></tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="flex justify-between items-center mt-2.5 text-[13px] text-[var(--color-text-muted)]">
        <span data-testid="more">{rest > 0 ? t('scx.more', { n: rest }) : ''}</span>
        <span>{t('scx.sortedRs')}</span>
      </div>
    </div>
  )
}
