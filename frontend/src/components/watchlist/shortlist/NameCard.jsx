import { useRef, useState } from 'react'
import CardChart from './CardChart'
import { pctFromReading, fmtPct, fmtAtr, fmtPctl } from './scales'
import { useLanguage } from '../../../i18n/LanguageContext'
import { dataName } from '../../../i18n/names'
import { rich, word } from '../../screener/richText'
import { panelName, panelNameFromLabel } from '../panelName'

/* The tray stores where a name was taken from; a hand-typed name is stored
   with this literal (ShortListPage), so it is translated at display. */
const BY_HAND = '手工加入'

/**
 * One name, and everything the engine already decided about it.
 *
 * The page computes nothing: the verdict sentence, the readings and the marks
 * all arrive composed (DATA_CONTRACTS §四点十). What this file decides is only
 * what gets the reader's eye first — the seat's QUESTION, because a card that
 * leads with the ticker invites you to judge the name, and a card that leads
 * with the question invites you to judge whether the question was answered
 * well. The second is the thing Andy is here to do.
 */

/** A reading that was not taken says so. Never 0, never blank, never a dash
 *  that could be mistaken for a value of zero — this is the rule the whole
 *  dashboard is built on and the asset card exercises it six ways: GLD arrives
 *  with rs_1m, vcs, trend_base and seven others null, because the asset layer
 *  measures fewer things, not because they came out zero. */
function Reading({ label, value, title }) {
  const { t } = useLanguage()
  const missing = value == null
  return (
    <div className="flex flex-col gap-[1px] min-w-0" title={title}>
      <span className="text-[11px] font-mono uppercase tracking-[.12em]
                       text-[var(--color-text-muted)] truncate">{label}</span>
      <span className={`text-[13px] font-mono tabular-nums ${missing
        ? 'text-[var(--color-text-muted)] italic' : 'text-[var(--color-text-bold)]'}`}>
        {missing ? t('wl.unmeasured') : value}
      </span>
    </div>
  )
}

export default function NameCard({ card, seat, seatLabel, verdictOf,
                                   entry = {}, onMark, onNote, onRemove }) {
  const { t, lang } = useLanguage()
  const [open, setOpen] = useState(false)
  const [noteOpen, setNoteOpen] = useState(false)
  const noteTimer = useRef(0)
  const r = card.readings || {}
  const chg = pctFromReading(r.change_pct)
  const mark = entry.mark ?? null
  const vetoed = mark === 'vetoed'

  return (
    <section className={`rounded-3xl bg-[var(--color-surface)] px-5 py-5 transition-opacity
                         ${vetoed ? 'opacity-45' : ''}`}>
      {/* The seat's question, and how this name came to answer it. An
          outcome-ordered list has to state its selection mechanism, and `why`
          is that mechanism in the engine's own words. */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          {seat && (
            <div className="flex items-baseline gap-2 flex-wrap">
              <span className="text-[11px] font-mono uppercase tracking-[.24em]
                               text-[var(--color-text-muted)]">{seatLabel}</span>
              <span className="text-[11px] text-[var(--color-text-secondary)]">{seat.why}</span>
            </div>
          )}
          <div className="flex items-baseline gap-2.5 mt-1 flex-wrap">
            <h3 className="m-0 text-[26px] font-semibold leading-none tracking-tight"
                style={{ fontFamily: 'var(--font-cond)' }}>{card.ticker}</h3>
            {chg != null && (
              <span className="text-[13px] font-mono tabular-nums text-[var(--color-text-bold)]">
                {fmtPct(chg)}
              </span>
            )}
            {r.close != null && (
              <span className="text-[13px] font-mono tabular-nums
                               text-[var(--color-text-muted)]">{r.close}</span>
            )}
            {card.flags?.tml && (
              <span className="text-[11px] font-mono uppercase tracking-[.16em]
                               px-1.5 py-[1px] bg-[var(--color-text-bold)]
                               text-[var(--color-bg)]">TML</span>
            )}
            {card.flags?.chase && (
              <span className="text-[11px] font-mono uppercase tracking-[.16em]
                               px-1.5 py-[1px] bg-[var(--color-refused)]
                               text-[var(--color-bg)]"
                    title={t('wl2.nc.chaseTitle')}>{t('wl2.nc.chase')}</span>
            )}
          </div>
          <p className="m-0 mt-1 text-[11px] text-[var(--color-text-muted)]">
            {/* 「无主题」is a claim, and only the engine is in a position to make
                it — it looked. A name typed into the box here was never checked
                against the theme map, so its group is simply not printed. */}
            {[dataName(card.group, lang)
                || (card.is_asset ? t('wl2.nc.asset') : card.source === 'manual' ? null : t('wl2.nc.noTheme')),
              word(t, `state.${card.state}`, card.state), dataName(r.sector, lang)].filter(Boolean).join(' · ')}
            {/* where it was picked off — the one thing you cannot reconstruct
                a week later, and the tray froze it at the moment of adding */}
            {card.takenFrom && (
              <span className="ml-2 text-[var(--color-text-secondary)]">
                {t('wl2.nc.from', { from: card.takenFrom === BY_HAND ? t('sh.st.byHand')
                  : panelNameFromLabel(t, lang, card.takenFrom) })}
              </span>
            )}
          </p>
        </div>

        <Marks mark={mark} onMark={onMark} ticker={card.ticker} onRemove={onRemove}
               note={entry.note} noteOpen={noteOpen} setNoteOpen={setNoteOpen} />
      </div>

      <div className="mt-4">
        {card.series ? (
          <CardChart series={card.series} marks={card.marks} />
        ) : (
          /* Not a chart that failed — a chart nobody has built. The 130 bars and
             the signal marks are made by the nightly engine off names it knows
             about, and a ticker added in this browser has not reached the
             pipeline at all: the GAS half of that loop is unbuilt. Saying so is
             the difference between "no data" and "not yet asked for". */
          <div className="rounded-2xl px-5 py-6"
               style={{ backgroundImage:
                 'repeating-linear-gradient(45deg,var(--color-border-light) 0 1px,transparent 1px 7px)' }}>
            <p className="m-0 text-[13px] leading-snug text-[var(--color-text-bold)]">
              {t('wl2.nc.noChart.head')}
            </p>
            <p className="m-0 mt-1.5 text-[13px] leading-relaxed text-[var(--color-text-secondary)]">
              {rich(t('wl2.nc.noChart.body'), {
                upsert: <code className="font-mono">shortlist_upsert</code>,
                universe: <code className="font-mono">universe.json</code> })}
              {card.inUniverse === false && (
                <b className="font-semibold">{' '}{t('wl2.nc.noChart.notInUniverse')}</b>
              )}
            </p>
          </div>
        )}
      </div>

      {/* The verdict, composed by the engine from a fixed template — same input,
          same sentence, which is why it can be snapshot-tested rather than read
          and hoped over. */}
      {verdictOf ? (
        <p className="m-0 mt-3 text-[13px] leading-snug text-[var(--color-text-bold)]">
          {verdictOf}
        </p>
      ) : card.source === 'manual' ? (
        <p className="m-0 mt-3 text-[13px] leading-snug text-[var(--color-text-muted)] italic">
          {t('wl2.nc.noVerdict')}
        </p>
      ) : null}

      {/* Where everything ✗ does NOT mean goes.
          The button says one thing — not this, today — and it can only keep
          saying one thing if the other three sentences have somewhere else to
          live. Open on demand, but always open when it already holds text: a
          note that has to be hunted for is a note that will be written once. */}
      {(noteOpen || entry.note) && (
        <textarea
          defaultValue={entry.note ?? ''}
          /* Saved while typing, not only on blur. A note lost because the tab
             closed before focus moved is a note written once and never again —
             and blur is exactly the event that does not fire on the way out.
             Debounced so six cards of chart marks do not re-render per key. */
          onChange={(e) => {
            const v = e.target.value
            clearTimeout(noteTimer.current)
            noteTimer.current = setTimeout(() => onNote?.(v.trim()), 400)
          }}
          onBlur={(e) => { clearTimeout(noteTimer.current); onNote?.(e.target.value.trim()) }}
          placeholder={t('wl2.nc.notePlaceholder')}
          rows={2}
          className="mt-3 w-full resize-y rounded-2xl bg-[var(--color-bg)]
                     border border-[var(--color-border)] px-3 py-2
                     text-[13px] leading-relaxed text-[var(--color-text-bold)]
                     placeholder:text-[var(--color-text-muted)]
                     focus:outline-none focus:border-[var(--color-text-muted)]" />
      )}

      <div className="mt-3.5 grid grid-cols-3 sm:grid-cols-5 gap-x-4 gap-y-2.5">
        <Reading label="RS 1M" value={fmtPctl(r.rs_1m)}
                 title={t('wl2.nc.t.rs1m')} />
        <Reading label={t('wl2.nc.r.rsLine')} value={fmtPctl(r.rs_line_pctl_21)}
                 title={t('wl2.nc.t.rsLine')} />
        <Reading label={t('wl2.nc.r.atr')} value={fmtAtr(r.atr_from_sma50)}
                 title={t('wl2.nc.t.atr')} />
        <Reading label={t('wl2.nc.r.high52')} value={r.high_52w_dist == null ? null
                   : fmtPct(r.high_52w_dist * 100, 1)}
                 title={t('wl2.nc.t.high52')} />
        <Reading label="VCS" value={fmtPctl(r.vcs)} title={t('wl2.nc.t.vcs')} />
        <Reading label={t('wl2.nc.r.relVol')} value={r.rel_volume == null ? null : `${r.rel_volume.toFixed(2)}x`}
                 title={t('wl2.nc.t.relVol')} />
        <Reading label={t('wl2.nc.r.heat')} value={card.heat?.score == null ? null
                   : `${card.heat.score}${card.heat.rank ? ` (#${card.heat.rank})` : ''}`}
                 title={t('wl2.nc.t.heat')} />
        <Reading label={t('wl2.nc.r.confluence')} value={card.heat?.confluence_days ?? null}
                 title={t('wl2.nc.t.confluence')} />
        <Reading label="RS 3M" value={fmtPctl(r.rs_3m)} title="rs_3m" />
        <Reading label={t('wl2.nc.r.signal')} value={r.sp_signal} title={t('wl2.nc.t.signal')} />
      </div>

      {(card.panels?.length || card.events?.length) ? (
        <>
          <button type="button" onClick={() => setOpen(!open)}
                  className="mt-3 text-[11px] font-mono uppercase tracking-[.16em]
                             text-[var(--color-text-muted)] hover:text-[var(--color-text)]
                             bg-transparent border-0 p-0 cursor-pointer">
            {open ? t('wl2.nc.histHide')
              : t('wl2.nc.histShow', { p: card.panels?.length ?? 0, e: card.events?.length ?? 0 })}
          </button>
          {open && <History card={card} />}
        </>
      ) : null}
    </section>
  )
}

/**
 * Two buttons, and one of them means exactly one thing.
 *
 * `✗` collapses three different judgements if it is left undefined — not today
 * / not this name ever / this seat picked the wrong kind of name — and a
 * learning set built on the three mixed together is noise. It is pinned to
 * "not this, today" here and in the ask filed with the data side; anything else
 * belongs in a note.
 *
 * Both are togglable. A control that goes one way only is not a control, and
 * §三.3 of the plan says a veto greys the card rather than removing it, so the
 * day's own mind can still be changed.
 */
function Marks({ mark, onMark, ticker, note, noteOpen, setNoteOpen, onRemove }) {
  const { t } = useLanguage()
  const btn = (on) => `text-[11px] font-mono uppercase tracking-[.14em] px-2 py-[3px]
    border cursor-pointer transition-colors ${on
      ? 'bg-[var(--color-text-bold)] text-[var(--color-bg)] border-[var(--color-text-bold)]'
      : 'bg-transparent text-[var(--color-text-muted)] border-[var(--color-border)] hover:text-[var(--color-text)]'}`
  return (
    <div className="flex gap-1.5 shrink-0">
      <button type="button" className={btn(mark === 'vetoed')}
              aria-pressed={mark === 'vetoed'}
              title={t('wl2.nc.vetoTitle', { ticker })}
              onClick={() => onMark(mark === 'vetoed' ? null : 'vetoed')}>{t('wl2.nc.veto')}</button>
      <button type="button" className={btn(mark === 'starred')}
              aria-pressed={mark === 'starred'}
              title={t('wl2.nc.starTitle')}
              onClick={() => onMark(mark === 'starred' ? null : 'starred')}>{t('wl2.nc.star')}</button>
      <button type="button" className={btn(!!note)}
              aria-pressed={!!note}
              title={note ? t('wl2.nc.noteTitle', { note }) : t('wl2.nc.noteTitleEmpty')}
              onClick={() => setNoteOpen(!noteOpen)}>{t('wl2.nc.note')}</button>
      {/* A name you put on the list by hand has to come off it by hand. ✗ is a
          judgement about today and does not remove anything; this does. */}
      {onRemove && (
        <button type="button" className={btn(false)} title={t('wl2.nc.removeTitle')}
                onClick={onRemove}>{t('wl2.nc.remove')}</button>
      )}
    </div>
  )
}

function History({ card }) {
  const { t, lang } = useLanguage()
  return (
    <div className="mt-2.5 rounded-2xl bg-[var(--color-bg)] px-3.5 py-3
                    text-[11px] text-[var(--color-text-secondary)] max-h-[220px] overflow-y-auto">
      {card.panels?.length > 0 && (
        <div className="mb-2">
          <div className="text-[11px] font-mono uppercase tracking-[.18em]
                          text-[var(--color-text-muted)] mb-1">{t('wl2.nc.histPanels')}</div>
          {card.panels.map((p, i) => (
            <div key={i} className="font-mono tabular-nums">
              {p.date} · {lang === 'zh' ? panelName(t, lang, p.panel, p.panel) : p.panel}
              {p.chg_pct != null && ` · ${p.chg_pct > 0 ? '+' : ''}${p.chg_pct}%`}
              {p.atr != null && ` · ${p.atr} ATR`}
            </div>
          ))}
        </div>
      )}
      {card.events?.length > 0 && (
        <div>
          {/* P: 前缀是预设命中，不是原始筛选器 —— 数据端的口径，原样透出 */}
          <div className="text-[11px] font-mono uppercase tracking-[.18em]
                          text-[var(--color-text-muted)] mb-1">
            {t('wl2.nc.histEvents')}
          </div>
          {card.events.map((e, i) => (
            <div key={i} className="font-mono tabular-nums">
              {e.date} · {e.screeners.join(' ')}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
