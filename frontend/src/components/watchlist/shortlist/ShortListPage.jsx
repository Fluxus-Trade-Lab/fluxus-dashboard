import { useSyncExternalStore } from 'react'
import NameCard from './NameCard'
import { MarkGlyph, MARK_KINDS } from './CardChart'
import { useShortlist } from '../../../hooks/useShortlist'
import { buildLedger, tally } from './ledger'

/**
 * Short List — six seats, six questions, and one page for comparing them.
 *
 * The seats are an outcome-ordered list, so every one of them prints the
 * QUESTION it answers and the rule that filled it. Which is also the honest
 * frame for what this page is for: Andy is not judging six names, he is judging
 * six selection rules, and the plan says outright that the ranking inside each
 * rule is a convenience choice waiting to be tested against his vetoes.
 *
 * The feedback half of that loop is not wired yet. The GAS `shortlist_upsert`
 * action does not exist (the existing push is a whole-payload `sync_all` that
 * two open tabs would clobber — the ask is filed in DATA_CONTRACTS §七), so a
 * mark lands in localStorage and the page says so rather than implying the
 * learning set is being fed.
 */

/* ── marks: one store, not one useState per card ─────────────────────────
   A hook holding this state would give every card its own copy — the tray on
   the other page shipped that bug twice in one round, showing 0 while a button
   said "on shortlist". Module store, one subscription, one truth. */
const KEY = 'fluxus.shortlist.marks'
const read = () => {
  try { return JSON.parse(localStorage.getItem(KEY) || '{}') } catch { return {} }
}
/* The store shipped for an hour holding a bare string per ticker; a note was
   added the same afternoon. An old localStorage payload is read forward rather
   than dropped — a veto Andy already cast is data. */
function migrate(raw) {
  const out = {}
  for (const [date, day] of Object.entries(raw || {})) {
    out[date] = Object.fromEntries(Object.entries(day || {})
      .map(([tk, v]) => [tk, typeof v === 'string' ? { mark: v } : v]))
  }
  return out
}
let marks = migrate(read())
const subs = new Set()
const subscribe = (fn) => { subs.add(fn); return () => subs.delete(fn) }
const snapshot = () => marks
/**
 * An entry is `{ mark, note }`, and either half can stand without the other.
 *
 * `✗` means one thing — not this, today (Andy, 2026-08-20) — so everything it
 * does NOT mean has to have somewhere to go, or it comes back as noise inside
 * the one signal that was supposed to be clean. The note is that somewhere. It
 * is also allowed on its own: a name he wants to say something about but not
 * judge is a real state, and requiring a verdict to leave a comment would
 * manufacture verdicts.
 */
function write(date, ticker, patch) {
  const day = { ...(marks[date] || {}) }
  const next = { ...(day[ticker] || {}), ...patch }
  if (next.mark == null && !next.note) delete day[ticker]
  else day[ticker] = next
  marks = { ...marks, [date]: day }
  try { localStorage.setItem(KEY, JSON.stringify(marks)) } catch { /* private mode */ }
  subs.forEach((f) => f())
}
export const setMark = (date, ticker, mark) => write(date, ticker, { mark })
export const setNote = (date, ticker, note) => write(date, ticker, { note })
export function useMarks() { return useSyncExternalStore(subscribe, snapshot, snapshot) }

/**
 * A seat with no name is not one state, and the file cannot yet say which.
 *
 * Three different things print the same empty seat: the panel feeding it did
 * not run tonight, it ran and found nobody, or it found somebody a gate then
 * excluded. Those must not look alike — it is the rule the rest of this
 * dashboard is built on. `seats[]` carries only `ticker: null` today, so the
 * page says what it does not know instead of picking one and sounding sure.
 * The ask for `empty_reason` + `excluded_n` is filed in DATA_CONTRACTS §七.
 */
/**
 * Three ways to be empty, three shapes — and a fourth for not knowing which.
 *
 * Shape, not colour: this is the same greyscale-first rule the mark glyphs
 * follow, and an empty seat is not a side. A dashed outline is already this
 * dashboard's word for "could not be counted" (the vote glyphs use it), so the
 * unmeasured case inherits it; a plain frame is "ran, nobody came"; a barred
 * frame is "someone came and a gate stopped them".
 *
 * The fourth shape exists because `seats[]` does not carry `empty_reason` yet.
 * Picking one of the three and sounding sure would be the exact failure this
 * page is built to avoid, so the unknown case gets a mark of its own and says
 * what it cannot tell apart. When the field ships, three of these light up and
 * the fourth stops appearing — no other change.
 */
const EMPTY_STATE = {
  not_measured: {
    label: '那格今晚没跑',
    body: '喂这一席的筛选器今晚没有产出——不是没找到人，是没测。',
    glyph: <rect x="1.5" y="1.5" width="17" height="17" fill="none" stroke="currentColor"
                 strokeWidth="1.4" strokeDasharray="3 3" />,
  },
  none_found: {
    label: '跑了，一个都没有',
    body: '筛选器跑了，今天没有名字过它的条件。这是一个读数。',
    glyph: <rect x="1.5" y="1.5" width="17" height="17" fill="none" stroke="currentColor"
                 strokeWidth="1.4" />,
  },
  all_excluded: {
    label: '有人，但被闸挡了',
    body: '有名字命中，全部被门槛挡下——空的原因在闸上，不在市场上。',
    glyph: <><rect x="1.5" y="1.5" width="17" height="17" fill="none" stroke="currentColor"
                   strokeWidth="1.4" /><line x1="1.5" y1="10" x2="18.5" y2="10"
                   stroke="currentColor" strokeWidth="1.4" /></>,
  },
}
const UNKNOWN_EMPTY = {
  label: '不知道是哪一种',
  body: '文件里只有一种「空」。分不出是那格没跑、跑了没人，还是有人被闸挡了——' +
        '这三种在别处必须长得不一样，所以这里不猜。',
  glyph: <circle cx="10" cy="10" r="8.5" fill="none" stroke="currentColor"
                 strokeWidth="1.4" strokeDasharray="2.5 2.5" />,
}

export function EmptySeat({ seat, label }) {
  const state = EMPTY_STATE[seat.empty_reason] ?? UNKNOWN_EMPTY
  const known = state !== UNKNOWN_EMPTY
  return (
    <section className="rounded-3xl bg-[var(--color-surface)] px-5 py-5">
      <div className="flex items-baseline gap-2 flex-wrap">
        <span className="text-[10px] font-mono uppercase tracking-[.24em]
                         text-[var(--color-text-muted)]">{label}</span>
        {seat.why && (
          <span className="text-[11.5px] text-[var(--color-text-secondary)]">{seat.why}</span>
        )}
      </div>
      <div className="mt-3 rounded-2xl p-5 flex gap-4 items-start"
           style={{ backgroundImage:
             'repeating-linear-gradient(45deg,var(--color-border-light) 0 1px,transparent 1px 7px)' }}>
        <svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"
             className="shrink-0 mt-[3px] text-[var(--color-text-muted)]">{state.glyph}</svg>
        <div className="min-w-0">
          <p className="m-0 text-[15px] leading-snug text-[var(--color-text-bold)]">
            这一席今天没有名字 —— {state.label}。
          </p>
          <p className="m-0 mt-1.5 text-[12px] leading-relaxed text-[var(--color-text-secondary)]">
            {state.body}
            {seat.excluded_n != null && ` 被挡下 ${seat.excluded_n} 个。`}
            {!known && (
              <span className="font-mono text-[11px] text-[var(--color-text-muted)]">
                {' '}（已向数据端要 <code>empty_reason</code> + <code>excluded_n</code>，
                DATA_CONTRACTS §七；到了这里就自动分成三种）
              </span>
            )}
          </p>
        </div>
      </div>
    </section>
  )
}

const SEAT_LABEL = {
  burning: '在烧', new_leader: '领跑', entry: '入场',
  v_reversal: 'V 反', coiling: '蓄势', asset: '资产层',
}
const SEAT_QUESTION = {
  burning: '今天谁在堆叠信号', new_leader: '谁刚成为 TML',
  entry: '今天最好的入场刀', v_reversal: '谁在深回撤后翻身',
  coiling: '谁压得最紧', asset: '资产里谁在领跑',
}

function Legend({ legend }) {
  if (!legend) return null
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 mt-1">
      {MARK_KINDS.map((k) => (
        <span key={k} className="inline-flex items-center gap-1.5 text-[11px]
                                 text-[var(--color-text-secondary)]">
          <span className={['x21', 'x50'].includes(k)
            ? 'text-[var(--color-text-muted)]' : 'text-[var(--color-text-bold)]'}>
            <MarkGlyph kind={k} />
          </span>
          <b className="font-semibold font-mono">{k}</b>
          <span className="font-mono text-[var(--color-text-muted)]">{legend[k] ?? '—'}</span>
        </span>
      ))}
      <span className="text-[11px] text-[var(--color-text-muted)]">
        发生的事画在收盘价上方（实心），穿过的线画在下方（空心）
      </span>
    </div>
  )
}

export default function ShortListPage() {
  const { data, failed } = useShortlist()
  const all = useMarks()

  if (failed) {
    return (
      <p className="text-[13px] text-[var(--color-text-muted)] mt-4">
        shortlist.json 还没有 —— 每晚 cron 产出，不是空名单，是文件还没到。
      </p>
    )
  }
  if (!data) return null

  const day = all[data.date] || {}
  const entryOf = (tk) => day[tk] || {}
  const byTicker = Object.fromEntries((data.cards || []).map((c) => [c.ticker, c]))
  const manualCards = (data.cards || []).filter((c) => c.source === 'manual')
  const seats = data.seats || []
  const rows = buildLedger(data, Object.fromEntries(
    Object.entries(day).map(([tk, e]) => [tk, e.mark]).filter(([, m]) => m)))
  const t = tally(rows)

  return (
    <div className="mt-1">
      <div className="flex items-baseline gap-4 flex-wrap">
        <p className="text-[12px] font-mono text-[var(--color-text-muted)] m-0">
          {data.date} 收盘 · 六席 {t.shown - (t.seats < rows.length ? manualCards.length : 0)}/{t.seats} 有名字
          {manualCards.length > 0 && ` · 手动 ${manualCards.length}`}
        </p>
        {/* The denominator, on the page rather than in a later analysis. 未表态
            is a reading, not a gap: a seat he saw and walked past is the row a
            veto-only log throws away, and 空席 sits outside the ratio entirely
            because nobody judged anything. */}
        <p className="text-[12px] font-mono text-[var(--color-text-muted)] m-0">
          今天 ✗{t.vetoed} ★{t.starred} · 未表态 {t.ignored} · 空席 {t.empty}
        </p>
      </div>
      <Legend legend={data.legend} />

      {/* The loop's other half is missing, and the page has to say so — a mark
          that looks saved but feeds nothing is worse than no button at all. */}
      <p className="m-0 mt-3 text-[11px] font-mono leading-relaxed
                    text-[var(--color-text-muted)]">
        ✗/★ 现在只落在这台机器上。回路的另一半 —— GAS 的 <code>shortlist_upsert</code> 与
        每晚拉回落 <code>shortlist_feedback</code> —— 还没接，所以这些标记<b className="font-semibold">还没有
        进学习语料</b>。接通之前它们不会消失，也不会被算进任何分析。
      </p>

      {manualCards.length > 0 && (
        <>
          <h2 className="text-[13px] font-mono uppercase tracking-[.2em]
                         text-[var(--color-text-muted)] mt-7 mb-3">我的名单</h2>
          <div className="grid grid-cols-1 2xl:grid-cols-2 gap-4">
            {manualCards.map((c) => (
              <NameCard key={c.ticker} card={c} verdictOf={c.verdict}
                        entry={entryOf(c.ticker)}
                        onMark={(v) => setMark(data.date, c.ticker, v)}
                        onNote={(v) => setNote(data.date, c.ticker, v)} />
            ))}
          </div>
        </>
      )}

      <h2 className="text-[13px] font-mono uppercase tracking-[.2em]
                     text-[var(--color-text-muted)] mt-7 mb-1">今日六席</h2>
      <p className="m-0 mb-3 text-[11.5px] text-[var(--color-text-secondary)]">
        六个座位是六个问题，不是一张排行榜 —— 席与席之间不比较大小。
        每席下面那行是它今天为什么选中这个名字，
        <b className="font-semibold">选法本身还没有验过</b>（方案 §四），你的 ✗ 就是用来验它的。
      </p>
      <div className="grid grid-cols-1 2xl:grid-cols-2 gap-4">
        {seats.map((s) => {
          const label = `${SEAT_LABEL[s.seat] ?? s.seat} · ${SEAT_QUESTION[s.seat] ?? ''}`
          const card = s.ticker ? byTicker[s.ticker] : null
          if (!card) return <EmptySeat key={s.seat} seat={s} label={label} />
          return (
            <NameCard key={s.seat} card={card} seat={s} seatLabel={label}
                      verdictOf={card.verdict} entry={entryOf(card.ticker)}
                      onMark={(v) => setMark(data.date, card.ticker, v)}
                      onNote={(v) => setNote(data.date, card.ticker, v)} />
          )
        })}
      </div>
    </div>
  )
}
