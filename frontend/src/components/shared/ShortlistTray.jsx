import { useState } from 'react'
import TickerLink from '../ticker/TickerLink'
import { useShortlist } from '../../hooks/useShortlist'
import { useLanguage } from '../../i18n/LanguageContext'
import { rich } from '../screener/richText'

/**
 * Today's shortlist — the thing you leave page 3 holding.
 *
 * The three morning pages answer "what is changing, what is strong" at three
 * grains, and PRODUCT.md says the read ends in an act: pick the names you will
 * watch today and take them with you. This is that act, and everything about
 * the tray is built so the list is reviewable later rather than merely
 * collected now.
 *
 *   · each row keeps the SCREEN it came off, so a week later the list still
 *     says why each name was on it
 *   · the readings are FROZEN at the moment of adding. Refreshing them would
 *     quietly rewrite the reason, and the one question worth asking about an
 *     old shortlist is whether the call was good on the day it was made
 *   · a list made against an older close announces that fact instead of
 *     passing as today's
 *
 * It is small on purpose: it is the page's OUTPUT, not its subject. The scan
 * grid stays the largest thing here, because the work is still discovery.
 */

const copy = (text) => navigator.clipboard?.writeText(text).catch(() => {})

export default function ShortlistTray() {
  const { names, madeOn, stale, remove, clear } = useShortlist()
  const [copied, setCopied] = useState(null)
  const { t } = useLanguage()

  const flash = (what, text) => { copy(text); setCopied(what); setTimeout(() => setCopied(null), 1400) }

  return (
    <section className="rounded-3xl bg-[var(--color-surface)] p-4">
      <div className="flex items-baseline gap-2.5 mb-3">
        <h2 className="m-0 text-[11px] font-mono uppercase tracking-[.24em]
                       text-[var(--color-text-muted)]">
          {t('sh.st.title')}
        </h2>
        <span className="text-[11px] font-mono tabular-nums text-[var(--color-text-muted)]">
          {names.length}
        </span>
        {names.length > 0 && (
          <button type="button" onClick={clear}
                  className="ml-auto text-[11px] font-mono uppercase tracking-[.14em]
                             bg-transparent border-none p-0 cursor-pointer
                             text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
            {t('sh.st.clear')}
          </button>
        )}
      </div>

      {stale && (
        /* right names, wrong clock — say which close this was made against
           rather than letting it pass as this morning's work */
        <p className="m-0 mb-3 pl-3 text-[11px] leading-relaxed text-[var(--color-text-secondary)]
                      border-l border-dashed border-[var(--color-text-muted)]">
          {rich(t('sh.st.stale', { madeOn }))}
        </p>
      )}

      {names.length === 0 ? (
        <p className="m-0 text-[11px] leading-relaxed text-[var(--color-text-muted)]">
          {rich(t('sh.st.empty'), {}, 'text-[var(--color-text-secondary)]')}
        </p>
      ) : (
        <>
          <ul className="list-none m-0 p-0">
            {names.map((n) => (
              <li key={n.ticker}
                  className="flex items-baseline gap-2 py-[5px]
                             border-b border-[var(--color-border-light)] last:border-b-0">
                <TickerLink symbol={n.ticker}
                            className="shrink-0 text-[11px] font-mono font-semibold
                                       text-[var(--color-text-bold)]" />
                <span className="min-w-0 flex-1 truncate text-[11px] text-[var(--color-text-muted)]"
                      title={[n.from, n.group, n.group_state].filter(Boolean).join(' · ')}>
                  {n.from ?? t('sh.st.byHand')}
                </span>
                {n.rs_1m != null && (
                  <span className="shrink-0 text-[11px] font-mono tabular-nums
                                   text-[var(--color-text-secondary)]"
                        title={t('sh.st.rsTitle')}>
                    {n.rs_1m}
                  </span>
                )}
                <button type="button" onClick={() => remove(n.ticker)}
                        aria-label={t('sh.st.remove', { t: n.ticker })}
                        className="shrink-0 w-4 text-[11px] font-mono bg-transparent border-none
                                   p-0 cursor-pointer text-[var(--color-text-muted)]
                                   hover:text-[var(--color-text)]">
                  &minus;
                </button>
              </li>
            ))}
          </ul>

          {/* WHAT A CLICK DOES HERE, said out loud (Andy, 2026-08-18).
              A name in the table above charts it; a name in this tray opens
              its tear-sheet. Two behaviours for one gesture on one screen is
              exactly the thing a reader should not have to discover by
              clicking — the tray is where a name goes once you have decided
              it is worth reading properly, so the destination differs on
              purpose, and the purpose has to be printed. */}
          <p className="m-0 mt-2 text-[11px] leading-relaxed text-[var(--color-text-muted)]">
            {rich(t('sh.st.click'), {}, 'text-[var(--color-text-secondary)]')}
          </p>

          {/* taking it away. Two shapes because they go to two places: the
              bare symbols paste into a broker or a TradingView list, the
              table pastes into a sheet with the reasons intact. */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3">
            <button type="button"
                    onClick={() => flash('symbols', names.map((n) => n.ticker).join(','))}
                    className="text-[11px] font-mono uppercase tracking-[.14em] bg-transparent
                               border-none p-0 cursor-pointer text-[var(--color-text-muted)]
                               hover:text-[var(--color-text)]">
              {copied === 'symbols' ? t('sh.st.copied') : t('sh.st.copySymbols')}
            </button>
            <button type="button"
                    onClick={() => flash('table', [
                      ['ticker', 'from', 'group', 'state', 'rs_1m'].join('\t'),
                      ...names.map((n) => [n.ticker, n.from ?? '', n.group ?? '',
                                           n.group_state ?? '', n.rs_1m ?? ''].join('\t')),
                    ].join('\n'))}
                    className="text-[11px] font-mono uppercase tracking-[.14em] bg-transparent
                               border-none p-0 cursor-pointer text-[var(--color-text-muted)]
                               hover:text-[var(--color-text)]">
              {copied === 'table' ? t('sh.st.copied') : t('sh.st.copyReasons')}
            </button>
          </div>
        </>
      )}

      <p className="m-0 mt-3 text-[11px] leading-relaxed text-[var(--color-text-muted)]">
        {t('sh.st.local')}
      </p>
    </section>
  )
}
