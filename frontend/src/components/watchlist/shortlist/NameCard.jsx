import { useRef, useState } from 'react'
import CardChart from './CardChart'
import { pctFromReading, fmtPct, fmtAtr, fmtPctl } from './scales'

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
  const missing = value == null
  return (
    <div className="flex flex-col gap-[1px] min-w-0" title={title}>
      <span className="text-[10px] font-mono uppercase tracking-[.12em]
                       text-[var(--color-text-muted)] truncate">{label}</span>
      <span className={`text-[13px] font-mono tabular-nums ${missing
        ? 'text-[var(--color-text-muted)] italic' : 'text-[var(--color-text-bold)]'}`}>
        {missing ? 'not measured' : value}
      </span>
    </div>
  )
}

export default function NameCard({ card, seat, seatLabel, verdictOf,
                                   entry = {}, onMark, onNote }) {
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
              <span className="text-[10px] font-mono uppercase tracking-[.24em]
                               text-[var(--color-text-muted)]">{seatLabel}</span>
              <span className="text-[11.5px] text-[var(--color-text-secondary)]">{seat.why}</span>
            </div>
          )}
          <div className="flex items-baseline gap-2.5 mt-1 flex-wrap">
            <h3 className="m-0 text-[24px] font-semibold leading-none tracking-tight"
                style={{ fontFamily: 'var(--font-cond)' }}>{card.ticker}</h3>
            {chg != null && (
              <span className="text-[14px] font-mono tabular-nums text-[var(--color-text-bold)]">
                {fmtPct(chg)}
              </span>
            )}
            {r.close != null && (
              <span className="text-[12.5px] font-mono tabular-nums
                               text-[var(--color-text-muted)]">{r.close}</span>
            )}
            {card.flags?.tml && (
              <span className="text-[10px] font-mono uppercase tracking-[.16em]
                               px-1.5 py-[1px] bg-[var(--color-text-bold)]
                               text-[var(--color-bg)]">TML</span>
            )}
            {card.flags?.chase && (
              <span className="text-[10px] font-mono uppercase tracking-[.16em]
                               px-1.5 py-[1px] bg-[var(--color-refused)]
                               text-[var(--color-bg)]"
                    title="当日 ≥15% —— 追高警告，不是买点">chase</span>
            )}
          </div>
          <p className="m-0 mt-1 text-[11.5px] text-[var(--color-text-muted)]">
            {[card.group || (card.is_asset ? 'asset' : '无主题'), card.state, r.sector]
              .filter(Boolean).join(' · ')}
          </p>
        </div>

        <Marks mark={mark} onMark={onMark} ticker={card.ticker}
               note={entry.note} noteOpen={noteOpen} setNoteOpen={setNoteOpen} />
      </div>

      <div className="mt-4">
        <CardChart series={card.series} marks={card.marks} />
      </div>

      {/* The verdict, composed by the engine from a fixed template — same input,
          same sentence, which is why it can be snapshot-tested rather than read
          and hoped over. */}
      {verdictOf && (
        <p className="m-0 mt-3 text-[13px] leading-snug text-[var(--color-text-bold)]">
          {verdictOf}
        </p>
      )}

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
          placeholder="为什么 —— 这只票本身的问题？这一席选错了人？还是别的。按钮只说「今天不要」，剩下的写这里。"
          rows={2}
          className="mt-3 w-full resize-y rounded-2xl bg-[var(--color-bg)]
                     border border-[var(--color-border)] px-3 py-2
                     text-[12.5px] leading-relaxed text-[var(--color-text-bold)]
                     placeholder:text-[var(--color-text-muted)]
                     focus:outline-none focus:border-[var(--color-text-muted)]" />
      )}

      <div className="mt-3.5 grid grid-cols-3 sm:grid-cols-5 gap-x-4 gap-y-2.5">
        <Reading label="RS 1M" value={fmtPctl(r.rs_1m)}
                 title="rs_1m — 相对强弱在全池里的排名" />
        <Reading label="RS线 21d" value={fmtPctl(r.rs_line_pctl_21)}
                 title="rs_line_pctl_21 — RS 线自己过去 21 日的百分位。和 RS 1M 不是同一个量" />
        <Reading label="ATR 位" value={fmtAtr(r.atr_from_sma50)}
                 title="atr_from_sma50 — 离 50 日线几个 ATR，负数是在线下" />
        <Reading label="52w 高" value={r.high_52w_dist == null ? null
                   : fmtPct(r.high_52w_dist * 100, 1)}
                 title="high_52w_dist — 离 52 周高点多远" />
        <Reading label="VCS" value={fmtPctl(r.vcs)} title="vcs — 波动收缩分" />
        <Reading label="量比" value={r.rel_volume == null ? null : `${r.rel_volume.toFixed(2)}x`}
                 title="rel_volume — 相对成交量" />
        <Reading label="heat" value={card.heat?.score == null ? null
                   : `${card.heat.score}${card.heat.rank ? ` (#${card.heat.rank})` : ''}`}
                 title="合流分与名次" />
        <Reading label="合流日" value={card.heat?.confluence_days ?? null}
                 title="confluence_days — 同日 ≥4 个筛选器齐亮的天数" />
        <Reading label="RS 3M" value={fmtPctl(r.rs_3m)} title="rs_3m" />
        <Reading label="信号" value={r.sp_signal} title="sp_signal — Structure Pivot" />
      </div>

      {(card.panels?.length || card.events?.length) ? (
        <>
          <button type="button" onClick={() => setOpen(!open)}
                  className="mt-3 text-[11px] font-mono uppercase tracking-[.16em]
                             text-[var(--color-text-muted)] hover:text-[var(--color-text)]
                             bg-transparent border-0 p-0 cursor-pointer">
            {open ? '收起历史' : `近三月痕迹 (${card.panels?.length ?? 0} 格 · ${card.events?.length ?? 0} 天)`}
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
function Marks({ mark, onMark, ticker, note, noteOpen, setNoteOpen }) {
  const btn = (on) => `text-[11px] font-mono uppercase tracking-[.14em] px-2 py-[3px]
    border cursor-pointer transition-colors ${on
      ? 'bg-[var(--color-text-bold)] text-[var(--color-bg)] border-[var(--color-text-bold)]'
      : 'bg-transparent text-[var(--color-text-muted)] border-[var(--color-border)] hover:text-[var(--color-text)]'}`
  return (
    <div className="flex gap-1.5 shrink-0">
      <button type="button" className={btn(mark === 'vetoed')}
              aria-pressed={mark === 'vetoed'}
              title={`不是这个，今天 —— 只有这一个意思。不是「${ticker} 这只票不行」，也不是「这一席选错了人」；那些写进备注。再按一下取消。`}
              onClick={() => onMark(mark === 'vetoed' ? null : 'vetoed')}>✗ 今天不要</button>
      <button type="button" className={btn(mark === 'starred')}
              aria-pressed={mark === 'starred'}
              title="进我的名单。再按一下取消。"
              onClick={() => onMark(mark === 'starred' ? null : 'starred')}>★ 关注</button>
      <button type="button" className={btn(!!note)}
              aria-pressed={!!note}
              title={note ? `备注：${note}` : '写备注 —— 按钮之外的话都写这里'}
              onClick={() => setNoteOpen(!noteOpen)}>备注</button>
    </div>
  )
}

function History({ card }) {
  return (
    <div className="mt-2.5 rounded-2xl bg-[var(--color-bg)] px-3.5 py-3
                    text-[11.5px] text-[var(--color-text-secondary)] max-h-[220px] overflow-y-auto">
      {card.panels?.length > 0 && (
        <div className="mb-2">
          <div className="text-[10px] font-mono uppercase tracking-[.18em]
                          text-[var(--color-text-muted)] mb-1">上过哪些格</div>
          {card.panels.map((p, i) => (
            <div key={i} className="font-mono tabular-nums">
              {p.date} · {p.panel}
              {p.chg_pct != null && ` · ${p.chg_pct > 0 ? '+' : ''}${p.chg_pct}%`}
              {p.atr != null && ` · ${p.atr} ATR`}
            </div>
          ))}
        </div>
      )}
      {card.events?.length > 0 && (
        <div>
          {/* P: 前缀是预设命中，不是原始筛选器 —— 数据端的口径，原样透出 */}
          <div className="text-[10px] font-mono uppercase tracking-[.18em]
                          text-[var(--color-text-muted)] mb-1">
            近三月筛选器命中（P: = 预设）
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
