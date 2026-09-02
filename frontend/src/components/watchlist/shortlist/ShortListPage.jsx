import { useEffect, useMemo, useState, useSyncExternalStore } from 'react'
import NameCard from './NameCard'
import { MarkGlyph, MARK_KINDS } from './CardChart'
import { useShortlistFile } from '../../../hooks/useShortlistFile'
import { useShortlist } from '../../../hooks/useShortlist'
import { useUniverse } from '../../../hooks/useUniverse'
import { manualCards } from './manualCards'
import { buildLedger, tally } from './ledger'
import { credentials, pushOne, record, state as syncState } from './sync'

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
  /* A CONTENT change makes the record unsent again — an edited note is a new
     record, and `syncedAt` means "the sheet has THIS", not "the sheet has heard
     of this ticker". Stamping the mirror is not a content change, and clearing
     the stamp here too was an infinite loop: a successful push wrote syncedAt,
     this reset it to null, the effect saw an unsent record and pushed again.
     The unit test missed it because it stubbed a FAILING endpoint; the browser
     found it by freezing. */
  if (!('syncedAt' in patch)) next.syncedAt = null
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
 * Mirror what has not reached the sheet.
 *
 * Local first, always: nothing here can lose a judgement Andy made. Records are
 * flushed when the page opens and after each mark — never on a timer, because
 * the GAS action does not exist yet and an endpoint that is not there should
 * not be hammered. One record per call; this never touches `sync_all`.
 *
 * A push in flight is not retried under it (`inflight`), so a double-click or a
 * second flush cannot send the same record twice while the first is still out.
 */
let inflight = false
let lastError = null
/** the pending set that last failed — a failure is not retried until the set
 *  itself changes. Without this the effect that calls flush re-fires on every
 *  render and a missing endpoint gets hammered, which is the exact thing this
 *  file promises not to do. */
let failedFor = null
export const syncError = () => lastError

export async function flush(date, seatOf, readingsOf) {
  if (inflight) return
  const creds = credentials()
  if (!creds) return
  const day = marks[date] || {}
  const pending = Object.entries(day).filter(([, e]) => !e.syncedAt)
  if (!pending.length) { failedFor = null; return }
  const key = `${date}|${pending.map(([t, e]) => `${t}:${e.mark ?? ''}:${e.note ?? ''}`).join(',')}`
  if (lastError && failedFor === key) return
  inflight = true
  try {
    for (const [ticker, entry] of pending) {
      const res = await pushOne(
        record(date, ticker, entry, seatOf?.(ticker), readingsOf?.(ticker)), creds)
      if (!res.ok) { lastError = res.error; failedFor = key; break }
      lastError = null; failedFor = null
      write(date, ticker, { syncedAt: new Date().toISOString() })
    }
  } finally { inflight = false; subs.forEach((f) => f()) }
}

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
        <span className="text-[11px] font-mono uppercase tracking-[.24em]
                         text-[var(--color-text-muted)]">{label}</span>
        {seat.why && (
          <span className="text-[11px] text-[var(--color-text-secondary)]">{seat.why}</span>
        )}
      </div>
      <div className="mt-3 rounded-2xl p-5 flex gap-4 items-start"
           style={{ backgroundImage:
             'repeating-linear-gradient(45deg,var(--color-border-light) 0 1px,transparent 1px 7px)' }}>
        <svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"
             className="shrink-0 mt-[3px] text-[var(--color-text-muted)]">{state.glyph}</svg>
        <div className="min-w-0">
          <p className="m-0 text-[17px] leading-snug text-[var(--color-text-bold)]">
            这一席今天没有名字 —— {state.label}。
          </p>
          <p className="m-0 mt-1.5 text-[13px] leading-relaxed text-[var(--color-text-secondary)]">
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

/**
 * Add a name by hand, without leaving the page you compare on.
 *
 * Validated against universe.json — the same list the rest of the site treats
 * as "every name we measure". A ticker outside it is still ADDED, because Andy
 * asking to watch something is not a claim it passed our gate; it is added with
 * the page saying it has no readings, which is the true state rather than a
 * refusal that looks like a bug.
 */
function AddName({ onAdd, known }) {
  const [v, setV] = useState('')
  const t = v.trim().toUpperCase()
  const inUniverse = t ? known.has(t) : null
  return (
    <form className="flex items-center gap-2 flex-wrap"
          onSubmit={(e) => { e.preventDefault(); if (t) { onAdd(t); setV('') } }}>
      <input value={v} onChange={(e) => setV(e.target.value)}
             placeholder="加个名字" aria-label="加个名字"
             className="w-[130px] rounded-full bg-[var(--color-bg)] px-3 py-1
                        border border-[var(--color-border)] text-[13px] font-mono uppercase
                        tracking-wide text-[var(--color-text-bold)]
                        placeholder:text-[var(--color-text-muted)] placeholder:normal-case
                        focus:outline-none focus:border-[var(--color-text-muted)]" />
      <button type="submit" disabled={!t}
              className="text-[11px] font-mono uppercase tracking-[.14em] px-2.5 py-[3px]
                         border border-[var(--color-border)] bg-transparent cursor-pointer
                         text-[var(--color-text-muted)] hover:text-[var(--color-text)]
                         disabled:opacity-40 disabled:cursor-default">加入</button>
      {t && inUniverse === false && (
        <span className="text-[11px] text-[var(--color-text-secondary)]">
          {t} 不在 universe.json 里 —— 还是能加，但它一个读数都不会有
        </span>
      )}
    </form>
  )
}

/**
 * The guard, and nothing else.
 *
 * The page used to be one component with `if (!data) return null` in the middle
 * and hooks on both sides of it. That crashed twice in one day — the file
 * resolves a tick after the first paint, so the second render ran more hooks
 * than the first and React tore the page down. Both times the whole suite
 * passed: nothing renders this page in jsdom, and a hook-order fault is a
 * runtime fault.
 *
 * A comment saying "every hook above the early returns" was already sitting
 * here when I broke it the second time, which is the evidence that a comment is
 * the wrong instrument. The split is the fix: this component may return early
 * because it has one hook and nothing after it, and `Body` may use as many
 * hooks as it likes because it has no early return to sit above.
 */
export default function ShortListPage() {
  const { data, failed } = useShortlistFile()

  if (failed) {
    return (
      <p className="text-[13px] text-[var(--color-text-muted)] mt-4">
        shortlist.json 还没有 —— 每晚 cron 产出，不是空名单，是文件还没到。
      </p>
    )
  }
  if (!data) return null
  return <Body data={data} />
}

function Body({ data }) {
  const { names: trayNames, add, remove, madeOn, fileDate, stale } = useShortlist()
  const { all: universeRows } = useUniverse()
  const all = useMarks()

  const uniByTicker = useMemo(() => Object.fromEntries(
    (universeRows ?? []).map((r) => [r.ticker, r])), [universeRows])
  const known = useMemo(() => new Set(Object.keys(uniByTicker)), [uniByTicker])

  /* The two halves of this page, joined: the six the engine pushed, and the
     names Andy took off the morning pages himself. They were separate stores
     until he said it out loud — this page is the pushed cards plus his own. */
  const mine = useMemo(() => manualCards(trayNames, data, uniByTicker),
    [trayNames, data, uniByTicker])
  const docWithMine = useMemo(() => ({ ...data, cards: [...(data.cards ?? []), ...mine] }),
    [data, mine])

  /* `|| {}` minted a fresh object every render on a day with no marks, which
     leaked straight through `rows` into the flush dependency. Memoised on the
     stored value, so an untouched day is the SAME empty object each time. */
  const day = useMemo(() => all[data.date] || {}, [all, data.date])
  const entryOf = (tk) => day[tk] || {}
  const byTicker = Object.fromEntries((data.cards || []).map((c) => [c.ticker, c]))
  const seats = data.seats || []

  /* Memoised because `byRow` below is a flush dependency: an array rebuilt
     every render makes the effect fire every render, which turned a failing
     endpoint into a retry storm the first time this shipped. */
  const rows = useMemo(() => buildLedger(docWithMine, Object.fromEntries(
    Object.entries(day).map(([tk, e]) => [tk, e.mark]).filter(([, m]) => m))),
    [docWithMine, day])
  const t = tally(rows)

  /* Mirror on arrival and after each change. The ledger row is what goes — the
     seat it came from and the readings on the day, because the question worth
     asking about an old veto is what the name looked like when it was cast. */
  const byRow = useMemo(() => Object.fromEntries(rows.map((r) => [r.ticker, r])), [rows])
  const sync = syncState({ hasCreds: !!credentials(),
                           unsent: Object.values(day).filter((e) => !e.syncedAt).length,
                           lastError: syncError() })
  useEffect(() => {
    if (!data?.date) return
    flush(data.date, (tk) => byRow[tk]?.seat ?? null, (tk) => byRow[tk]?.readings ?? null)
  }, [data?.date, byRow, sync.unsent])

  return (
    <div className="mt-1">
      <div className="flex items-baseline gap-4 flex-wrap">
        <p className="text-[13px] font-mono text-[var(--color-text-muted)] m-0">
          {data.date} 收盘 · 六席 {seats.filter((s) => s.ticker).length}/{t.seats} 有名字
          {mine.length > 0 && ` · 我的 ${mine.length}`}
        </p>
        {/* The denominator, on the page rather than in a later analysis. 未表态
            is a reading, not a gap: a seat he saw and walked past is the row a
            veto-only log throws away, and 空席 sits outside the ratio entirely
            because nobody judged anything. */}
        <p className="text-[13px] font-mono text-[var(--color-text-muted)] m-0">
          今天 ✗{t.vetoed} ★{t.starred} · 未表态 {t.ignored} · 空席 {t.empty}
        </p>
      </div>
      <Legend legend={data.legend} />

      {/* The loop's other half is missing, and the page has to say so — a mark
          that looks saved but feeds nothing is worse than no button at all. */}
      {/* Three states, three sentences. A mark that looks saved and feeds
          nothing is worse than no button, so this says which of the three is
          true rather than one hedge covering all of them. */}
      <p className="m-0 mt-3 text-[11px] font-mono leading-relaxed
                    text-[var(--color-text-muted)]">
        {sync.kind === 'synced' ? (
          <>✗/★/备注 已经写进 Sheet 的 Shortlist 页 —— 每条一行，只发这一条，不碰组合。</>
        ) : sync.kind === 'off' ? (
          <>✗/★/备注 只落在这台机器上 —— <b className="font-semibold">没有配 Google Sheet</b>
            （在 Portfolio 页设 GAS 地址和 token）。它们不会丢，但也不会进学习语料。</>
        ) : (
          <>
            <b className="font-semibold">{sync.unsent} 条还没送到 Sheet。</b>{' '}
            {sync.lastError === 'action-not-implemented'
              ? <>GAS 那边还没有 <code>shortlist_upsert</code> 这个动作 ——
                  回路的另一半还没接，标记留在本地等着，接通那天会自动补送。</>
              : <>上次失败：<code>{sync.lastError ?? '未知'}</code>。标记不会丢，下次打开或
                  下次表态时会重试。</>}
          </>
        )}
      </p>

      <div className="flex items-baseline gap-4 flex-wrap mt-7 mb-2">
        <h2 className="m-0 text-[13px] font-mono uppercase tracking-[.2em]
                       text-[var(--color-text-muted)]">我的名单 {mine.length || ''}</h2>
        <AddName known={known} onAdd={(tk) => add(tk, uniByTicker[tk] ?? {}, '手工加入')} />
        {mine.length > 0 && (
          <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
            在晨报页图卡上按 add to shortlist 也进这里
          </span>
        )}
      </div>
      {stale && (
        /* right names, wrong clock — the tray already knew to say this, and it
           has to keep saying it now that the names render as full cards */
        <p className="m-0 mb-3 pl-3 text-[11px] leading-relaxed text-[var(--color-text-secondary)]
                      border-l border-dashed border-[var(--color-text-muted)]">
          这份名单是照 <b className="font-semibold">{madeOn}</b> 的收盘挑的，屏幕上的文件是{' '}
          {fileDate} 的。名字照原样留着 —— 开始今天的时候清掉它。
        </p>
      )}
      {mine.length > 0 ? (
        <div className="grid grid-cols-1 2xl:grid-cols-2 gap-4">
          {mine.map((c) => (
            <NameCard key={c.ticker} card={c} verdictOf={c.verdict}
                      entry={entryOf(c.ticker)}
                      onRemove={() => remove(c.ticker)}
                      onMark={(v) => setMark(data.date, c.ticker, v)}
                      onNote={(v) => setNote(data.date, c.ticker, v)} />
          ))}
        </div>
      ) : (
        <p className="m-0 text-[13px] leading-relaxed text-[var(--color-text-muted)]">
          空的。在晨报页把一个名字点出图、按 add to shortlist，或者在上面直接打代码 ——
          两个入口进的是同一份名单。
        </p>
      )}

      <h2 className="text-[13px] font-mono uppercase tracking-[.2em]
                     text-[var(--color-text-muted)] mt-7 mb-1">今日六席</h2>
      <p className="m-0 mb-3 text-[11px] text-[var(--color-text-secondary)]">
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
