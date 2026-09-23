import Spark from './Spark'
import BreadthPanes from './BreadthPanes'
import { LightChart } from './CourseRead'
import { fourQuestions, greenStreak, negativeStreak, breadthReads, themeTransitions, sentinels, pct, voteFor, vsPrior, vsPriorSpread } from './morningReadMath'

/**
 * Market State's main screen since 2026-09-23 — the course's morning walk.
 *
 * Andy 09-23: the page 「形式太乱，内容没有逻辑和思考脉络」; the fix he picked
 * from two previews: 「A 的骨架，把B它的「四问对照表」搬进 A 的第①段当指数那格的正文」.
 *
 *   Verdict     one word — FULL / DIM / AVOID (aggression, never direction)
 *   ① Index     ch.1 §1.7's four questions, with the light's own history
 *   ② Breadth   ch.7 §7.6 — A/D, McClellan, MCSI, NH−NL; width; 20%-in-5-days
 *   ③ Leaders   ch.7 §7.2 (3) — the strongest 5–10, holding or broken
 *   ④ Themes    ch.7 §7.2 (4) — who just took the lead, who just lost it
 *   ⑤ News      ch.7 §7.4 / §7.5 — oil, dollar, Korea, defensives, VIX
 *   ⑥ Your book ch.7 §7.2 (6) — private; the public page carries a stand-in
 *
 * Each step ends in a "what changed" column, because a reader comes here for
 * the direction of the environment, not its level. A missing quantity prints
 * as missing, never as zero.
 */

const VERDICT = {
  full: { word: 'FULL', line: 'Bright green — the market is offering. Take the good ones at full size.' },
  dim: { word: 'DIM', line: 'Green, but thin — be picky, size smaller, or pass.' },
  avoid: { word: 'AVOID', line: 'Sit still today.' },
}

function Missing({ what, why }) {
  return (
    <span className="inline-flex items-baseline gap-1.5 text-[13px] italic text-[var(--color-text-muted)]">
      {what} — {why ?? 'not measured'}
    </span>
  )
}

function Chip({ tone = 'muted', children }) {
  const cls = tone === 'wait' ? 'text-[var(--color-signal-caution)] border-[var(--color-signal-caution)]'
    : tone === 'no' ? 'text-[var(--color-refused)] border-[var(--color-refused)]'
    : 'text-[var(--color-text-muted)] border-[var(--color-border)]'
  return <span className={`inline-block text-[11px] font-mono px-1.5 py-px rounded border ${cls} align-middle`}>{children}</span>
}

/** One step: the course's question on the left, readings in the middle,
 *  what changed on the right. Stacks on narrow screens. */
function Step({ n, source, title, ask, changed, faded, children }) {
  return (
    <section className={`grid grid-cols-1 lg:grid-cols-[150px_1fr_240px] gap-x-5 gap-y-3 py-5
                         border-t border-[var(--color-border-light)] ${faded ? 'opacity-45' : ''}`}
             aria-label={`Step ${n} · ${title}`}>
      <div>
        <div className="text-[11px] font-mono uppercase tracking-[.14em] text-[var(--color-text-muted)]">{source}</div>
        <h2 className="m-0 mt-0.5 text-[17px] font-semibold text-[var(--color-text)]">{n} · {title}</h2>
        <div className="text-[13px] text-[var(--color-text-secondary)]">{ask}</div>
      </div>
      <div className="min-w-0">{children}</div>
      <aside className="border-l-2 border-[var(--color-accent)] pl-3 text-[13px] text-[var(--color-text-secondary)]">
        <div className="text-[11px] font-mono uppercase tracking-[.12em] text-[var(--color-accent)] mb-1">What changed</div>
        {changed}
      </aside>
    </section>
  )
}

function Reading({ label, value, unit, note, chip, children }) {
  return (
    <div className="min-w-[150px]">
      <div className="text-[11px] font-mono uppercase tracking-[.08em] text-[var(--color-text-muted)]">{label} {chip}</div>
      {children}
      {value != null && (
        <div className="text-[17px] font-semibold tabular-nums text-[var(--color-text)]">
          {value}{unit && <span className="text-[13px] font-normal text-[var(--color-text-secondary)] ml-1">{unit}</span>}
        </div>
      )}
      {note && <div className="text-[13px] text-[var(--color-text-secondary)]">{note}</div>}
    </div>
  )
}

/* ── the two layouts (Andy 2026-09-23: 「①② 用 B，③–⑥ 用 A」) ───────────
 * A · Tile — one reading, one tile: value, change against the prior session,
 *     the ENGINE's word where the engine votes on it, and one line of source.
 * B · ChartThree — a chart carries the step, three tiles beside it, the rest
 *     folded. Used where a step has a chart worth leading with (① and ②).
 * Both are built from the same Tile, so the page reads as one thing.
 */

const VOTE_WORD = { bull: 'bull', bear: 'bear', neutral: 'neutral' }
const VOTE_CLS = {
  bull: 'bg-[var(--color-took)] text-[var(--color-surface)]',
  bear: 'bg-[var(--color-refused)] text-[var(--color-surface)]',
  neutral: 'bg-[var(--color-v2-off)] text-[var(--color-text-secondary)]',
}

/** The engine's vote as a pill. Never rendered for a reading the engine does
 *  not vote on — a word I wrote would look exactly like a measurement. */
function VotePill({ vote }) {
  if (!vote) return null
  return (
    <span className={`text-[11px] font-mono px-1.5 py-px rounded ${VOTE_CLS[vote]}`}
          title="the breadth engine's vote on this reading">{VOTE_WORD[vote]}</span>
  )
}

/** Change against the prior session, or nothing at all when there is no prior. */
function Delta({ d, digits = 0, unit = '' }) {
  if (d == null) return null
  const v = d.delta
  return (
    <span className="text-[13px] font-normal text-[var(--color-text-secondary)] ml-2 tabular-nums"
          title={`prior session ${d.was.toFixed(digits)}${unit}`}>
      {v > 0 ? '+' : ''}{v.toFixed(digits)}{unit} vs prior
    </span>
  )
}

function Tile({ label, vote, value, unit, delta, deltaDigits = 0, source, muted, children }) {
  return (
    <div className="bg-[var(--color-surface)] rounded-xl px-3 py-2.5 min-w-0">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] font-mono uppercase tracking-[.08em] text-[var(--color-text-muted)] truncate">{label}</span>
        <VotePill vote={vote} />
      </div>
      {children}
      {value != null && (
        <div className={`text-[17px] font-semibold tabular-nums leading-tight mt-0.5 ${muted ? 'text-[var(--color-text-muted)]' : 'text-[var(--color-text)]'}`}>
          {value}{unit && <span className="text-[13px] font-normal text-[var(--color-text-secondary)] ml-1">{unit}</span>}
          <Delta d={delta} digits={deltaDigits} />
        </div>
      )}
      {source && <div className="text-[11px] text-[var(--color-text-muted)] mt-0.5">{source}</div>}
    </div>
  )
}

/** B: the chart leads, three tiles ride with it — beside it when the chart is
 *  a plain graphic, under it when the chart carries its own controls (squeezing
 *  those into two-thirds width wraps the control row and shrinks the chart). */
function ChartThree({ chart, tiles, stacked }) {
  if (stacked) {
    return (
      <div className="flex flex-col gap-3">
        <div className="min-w-0">{chart}</div>
        <div className="grid grid-cols-[repeat(auto-fit,minmax(190px,1fr))] gap-2">{tiles}</div>
      </div>
    )
  }
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,2.2fr)_minmax(200px,1fr)] gap-3 items-start">
      <div className="min-w-0">{chart}</div>
      <div className="flex flex-col gap-2">{tiles}</div>
    </div>
  )
}

/** A: every reading is a tile. */
function Tiles({ children }) {
  return <div className="grid grid-cols-[repeat(auto-fill,minmax(172px,1fr))] gap-2">{children}</div>
}

const B = ({ children }) => <b className="font-semibold text-[var(--color-text)]">{children}</b>

/* ── verdict ───────────────────────────────────────────────────────────── */

function verdictOf(ml) {
  if (ml?.verdict && VERDICT[ml.verdict]) return ml.verdict
  if (ml?.spy?.light === 'red') return 'avoid'
  return null
}

export function Verdict({ ml, reads }) {
  const v = verdictOf(ml)
  const spy = ml?.spy
  const leaders = ml?.brightness?.leaders ?? []
  const broken = leaders.filter((l) => l.status === 'broken').length
  return (
    <div className="bg-[var(--color-surface)] rounded-3xl p-5">
      <div className="flex items-baseline justify-between pb-3 mb-3 border-b border-[var(--color-v2-ink)]">
        <h2 className="text-[11px] font-mono uppercase tracking-[.24em] text-[var(--color-text-muted)]">Today</h2>
        {ml?.date && <span className="text-[11px] text-[var(--color-text-muted)]">SPY daily · {ml.date}</span>}
      </div>
      {!v && spy?.light === 'green' && ml?.verdict_pending ? (
        <p className="m-0 text-[17px] text-[var(--color-text-secondary)]">
          <B>The light is green, and the call is not measured:</B> {ml.verdict_pending}
        </p>
      ) : !v ? (
        <p className="m-0 text-[13px] italic text-[var(--color-text-muted)]">{"Today's aggression — not measured."}</p>
      ) : (
        <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
          <div>
            <div className="text-[46px] leading-none font-bold tracking-[.02em] text-[var(--color-text)]"
                 style={{ fontFamily: 'var(--font-cond)' }}>{VERDICT[v].word}</div>
            <div className="mt-1.5 text-[11px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)]">today&rsquo;s aggression</div>
          </div>
          <div className="flex-1 min-w-[260px]">
            <p className="m-0 text-[17px] leading-snug text-[var(--color-text-secondary)]">
              {spy?.light === 'red'
                ? <B>The light is red — {spy.checks_passed} of 3 checks. </B>
                : <B>The light is green. </B>}
              {VERDICT[v].line}
            </p>
            {/* why — the three readings the call rests on, so the word is never alone */}
            {spy?.light === 'green' && (
              <p className="m-0 mt-1.5 text-[13px] text-[var(--color-text-secondary)]">
                Setups {ml?.brightness?.setups?.count ?? '—'} (a scan count, not the lesson&rsquo;s hand count) ·
                leaders {leaders.length ? `${leaders.length - broken} of ${leaders.length} holding` : '—'} ·
                {' '}{reads?.pct20 != null ? `${reads.pct20.toFixed(0)}% above the 20-day` : 'breadth —'} ·
                {' '}{reads?.width ? `${reads.width.Leading} of ${reads.width_n} themes Leading` : ''}
              </p>
            )}
            {ml?.verdict_synthetic && (
              <p className="m-0 mt-1 text-[11px] text-[var(--color-text-muted)]">
                synthetic — combined from Q2 and Q3 (either bad → avoid, both good → full, otherwise dim), a rule set
                with the course on 09-11, not in the lesson text. Q1 is shown but does not vote.
              </p>
            )}
            <div className="flex gap-1.5 mt-3" aria-hidden="true">
              {['full', 'dim', 'avoid'].map((k) => (
                <span key={k} className={`text-[11px] font-mono font-semibold tracking-[.1em] px-2.5 py-1.5 rounded-lg ${k === v
                  ? 'bg-[var(--color-text)] text-[var(--color-surface)]'
                  : 'bg-[var(--color-v2-off)] text-[var(--color-text-muted)]'}`}>{VERDICT[k].word}</span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/* ── ① index ───────────────────────────────────────────────────────────── */

export function StepIndex({ ml, signals, rows, votes }) {
  const spy = ml?.spy
  const fq = fourQuestions({ ml, signals, rows })
  const on = fq.items.filter((i) => i.state === 'on').length
  const answered = fq.items.filter((i) => i.state != null).length
  const streak = greenStreak(spy?.history)
  const neg = negativeStreak(rows)
  const ma = ml?.ma_type ?? 'EMA'
  const nh = vsPriorSpread(rows, 'new_highs_common', 'new_lows_common')
  const changed = !spy?.checks ? <span>The light is not measured.</span> : (
    <>
      <p className="m-0"><B>{on} of {answered} answered questions on the risk-on side</B>{answered < 4 ? `; ${4 - answered} not measured` : ''}.</p>
      {spy.light === 'green' && streak > 0 && (
        <p className="m-0 mt-1.5">New green light, day <B>{streak}</B>. The lesson&rsquo;s tally (§1.5, 166 new greens): still positive after 60 sessions 79.9%, an 8%+ run in weeks 6–12 39.6%, dead within two weeks 30.1%.</p>
      )}
      {neg > 0 && (
        <p className="m-0 mt-1.5">
          Net new highs negative <B>{neg} sessions running</B>
          {fq.items[3].state === 'on' ? ', but above where they were five sessions ago — the slowest question is turning.' : ' — the slowest question is still off while the fastest is on.'}
        </p>
      )}
    </>
  )
  return (
    <Step n="①" source="Foundations ch.1 · §1.7" title="Index" ask="Can this tape be traded?" changed={changed}>
      {!spy?.checks ? <Missing what="The light" /> : (
        <>
          <ChartThree
            chart={
              <div className="bg-[var(--color-surface)] rounded-xl p-3">
                <LightChart history={spy.history} />
                <p className="m-0 mt-1 text-[11px] leading-relaxed text-[var(--color-text-muted)]">
                  SPY close with the 10 / 20 {ma}. Strip: ink = all three checks yes, red = all three no,
                  hatched = the in-between days the course counts as red (§1.4).
                </p>
              </div>
            }
            tiles={[
              <Tile key="light" label={`The light · 10/20 ${ma}`} value={`${spy.checks_passed}/3`}
                    unit={spy.light === 'green' ? 'green' : 'red'}
                    source={streak > 0 && spy.light === 'green' ? `day ${streak} of this green light` : spy.checks_passed > 0 && spy.checks_passed < 3 ? 'in-between counts as red' : 'SPY daily, the course’s light'} />,
              <Tile key="weekly" label="Weekly · 50 over 200" value={fq.items[1].state === 'on' ? 'yes' : fq.items[1].state === 'off' ? 'no' : '—'}
                    source={fq.items[1].read ?? 'not measured'} />,
              <Tile key="nhnl" label="Net new highs · 52w" vote={voteFor(votes, 'nhnl')}
                    value={nh ? `${nh.now > 0 ? '+' : ''}${nh.now}` : '—'} delta={nh}
                    source={nh ? `${rows.at(-1).new_highs_common} highs / ${rows.at(-1).new_lows_common} lows · common stocks${neg > 0 ? ` · ${neg} sessions negative` : ''}` : 'common-stock counts not measured'} />,
            ]}
          />
          <details className="mt-2 text-[13px]">
            <summary className="cursor-pointer text-[var(--color-text-secondary)]">
              The four questions in full <span className="font-mono text-[var(--color-text-muted)]">{on}/{answered} on</span> — daily, weekly, last week, new highs − lows
            </summary>
            <div className="overflow-x-auto mt-2">
              <table className="w-full border-collapse text-[13px]">
                <thead>
                  <tr className="text-[11px] font-mono uppercase tracking-[.08em] text-[var(--color-text-muted)]">
                    <th className="text-left font-medium py-1 pr-2" />
                    <th className="text-left font-medium py-1 pr-2">Risk on</th>
                    <th className="text-left font-medium py-1 pr-2">Risk off</th>
                    <th className="text-left font-medium py-1">Today</th>
                  </tr>
                </thead>
                <tbody>
                  {fq.items.map((q) => (
                    <tr key={q.key} className="border-t border-[var(--color-border-light)] align-top">
                      <td className="py-1.5 pr-2 text-[var(--color-text)] whitespace-nowrap">{q.label}</td>
                      <td className={`py-1.5 pr-2 text-[var(--color-text-secondary)] ${q.state === 'on' ? 'bg-[color-mix(in_srgb,var(--color-took)_14%,transparent)]' : ''}`}>{q.on}</td>
                      <td className={`py-1.5 pr-2 text-[var(--color-text-secondary)] ${q.state === 'off' ? 'bg-[color-mix(in_srgb,var(--color-refused)_14%,transparent)]' : ''}`}>{q.off}</td>
                      <td className="py-1.5 font-mono tabular-nums">
                        {q.state == null
                          ? <span className="text-[var(--color-text-muted)]">— {q.missing ?? 'not measured'} <Chip tone="no">missing</Chip></span>
                          : <span className="text-[var(--color-text)] font-semibold">{q.state} · <span className="font-normal text-[var(--color-text-secondary)]">{q.read}</span></span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="m-0 mt-2 text-[11px] text-[var(--color-text-muted)]">
                Method: 10 / 20 {ma}, &ldquo;rising&rdquo; = today above yesterday — the course&rsquo;s method since Andy ruled EMA on 09-11.
                {ml?.qqq?.light ? ` QQQ side lamp: ${ml.qqq.light} (${ml.qqq.checks_passed}/3) — not part of the call.` : ''}
                {' '}{fq.rule}
              </p>
            </div>
          </details>
        </>
      )}
    </Step>
  )
}

/* ── ② breadth ─────────────────────────────────────────────────────────── */

export function StepBreadth({ reads, faded, w52, paneRows, loadingFull, rows, votes }) {
  const r = reads
  const p20 = vsPrior(rows, 'pct_above_20sma')
  const mco = vsPrior(rows, 'mcclellan_osc')
  const t2108 = vsPrior(rows, 't2108')
  const adv = vsPrior(rows, 'net_advances')
  const changed = (
    <>
      <p className="m-0">
        <B>{r.pct20 != null ? `${r.pct20.toFixed(0)}%` : '—'} above the 20-day</B>, McClellan {r.mco != null ? r.mco.toFixed(1) : '—'},
        NH−NL {r.nhnl != null ? (r.nhnl > 0 ? '+' : '') + r.nhnl : '—'}, {r.width.Leading} of {r.width_n} themes Leading
        {w52 != null ? ` — with the index ${Math.abs(w52).toFixed(1)}% from its 52-week high` : ''}.
      </p>
      {r.gainers20 != null && (
        <p className="m-0 mt-1.5">{r.gainers20} names up 20%+ in five days{r.gainers20 < 20 ? ' — under 20, the lesson\u2019s "washed out" mark' : r.gainers20 > 100 ? ' — over 100, the lesson\u2019s "overheated" mark' : ' — between the lesson\u2019s marks, nothing to act on'}.</p>
      )}
    </>
  )
  return (
    <Step n="②" source="Foundations ch.7 · §7.6" title="Breadth" ask="How many soldiers march with the general?" changed={changed} faded={faded}>
      <ChartThree
        stacked
        chart={<BreadthPanes rows={paneRows} loadingFull={loadingFull} />}
        tiles={[
          <Tile key="p20" label="Above the 20-day" value={r.pct20 != null ? r.pct20.toFixed(0) : '—'} unit="%"
                delta={p20} deltaDigits={1} source="half the market is the neutral line" />,
          <Tile key="mco" label="McClellan" vote={voteFor(votes, 'mco')}
                value={r.mco != null ? r.mco.toFixed(1) : '—'} delta={mco} deltaDigits={1}
                source="all-market pool · Nasdaq-100 version pending" />,
          <Tile key="width" label="Width · themes Leading" value={r.width.Leading} unit={`of ${r.width_n}`}
                source={`Improving ${r.width.Improving} · Weakening ${r.width.Weakening} · Lagging ${r.width.Lagging}`} />,
        ]}
      />
      <details className="mt-2 text-[13px]">
        <summary className="cursor-pointer text-[var(--color-text-secondary)]">
          The rest of §7.6&rsquo;s rulers <span className="font-mono text-[var(--color-text-muted)]">4</span> — T2108, net advances, the 20%-in-five-days count, the A/D line
        </summary>
        <div className="mt-2">
          <Tiles>
            <Tile label="T2108 · above the 40-day" vote={voteFor(votes, 't2108')}
                  value={r.t2108 != null ? r.t2108.toFixed(0) : rows?.at(-1)?.t2108?.toFixed(0) ?? '—'} unit="%"
                  delta={t2108} deltaDigits={1} source="under 20 oversold, over 80 overbought (Stockbee)" />
            <Tile label="Net advances" value={r.net_advances != null ? `${r.net_advances > 0 ? '+' : ''}${r.net_advances.toLocaleString()}` : '—'}
                  delta={adv} source="the A/D line's daily increment" />
            <Tile label="Up 20%+ in five days" value={r.gainers20 ?? '—'} unit={r.gainers20 != null ? 'names' : ''}
                  source="<20 washed out · >100 overheated · in between, ignore" />
            <Tile label="McClellan summation" value="—" muted source="MCSI is not in the pipeline; the 10-day-line read needs it" />
          </Tiles>
          <div className="mt-2 bg-[var(--color-surface)] rounded-xl px-3 py-2.5">
            <div className="text-[11px] font-mono uppercase tracking-[.08em] text-[var(--color-text-muted)]">Advance / decline line · 60 sessions</div>
            <Spark values={r.ad_line} width={220} height={44} title="A/D line, 60 sessions" />
          </div>
        </div>
      </details>
    </Step>
  )
}

/* ── ③ leaders ─────────────────────────────────────────────────────────── */

const LEADER_INK = { holding: 'var(--color-took)', extending: 'var(--color-took)', basing: 'var(--color-took)', broken: 'var(--color-refused)' }

export function StepLeaders({ ml, faded }) {
  const b = ml?.brightness
  const leaders = b?.leaders ?? []
  const broken = leaders.filter((l) => l.status === 'broken').length
  const themes = b?.leaders_meta?.themes ?? []
  const changed = !leaders.length ? <span>Leaders not measured.</span> : (
    <>
      <p className="m-0"><B>{broken} of {leaders.length} broken</B> below the 50-day.</p>
      <p className="m-0 mt-1.5">Ch.4&rsquo;s early warning is the weakest name in each group breaking first — a column this step does not have yet.</p>
    </>
  )
  return (
    <Step n="③" source="Foundations ch.7 · §7.2 (3) · ch.4" title="RS leadership" ask="Are the strongest 5–10 still standing?" changed={changed} faded={faded}>
      {!leaders.length ? <Missing what="Leaders" /> : (
        <>
          <Tiles>
            <Tile label="Holding the 50-day" value={leaders.length - broken} unit={`of ${leaders.length}`}
                  source="closed above the 50 SMA — the line the course gives to institutions" />
            <Tile label="Broken" value={broken} unit={broken === 1 ? 'name' : 'names'}
                  source={broken ? leaders.filter((l) => l.status === 'broken').map((l) => l.ticker).join(' · ') : 'none below the 50-day today'} />
            <Tile label="Themes represented" value={themes.length} unit={themes.length === 1 ? 'theme' : 'themes'}
                  source={themes.join(' · ') || 'not measured'} />
          </Tiles>
          <div className="flex flex-wrap gap-x-4 gap-y-1.5 mt-2.5 items-baseline">
            {leaders.map((l) => (
              <span key={l.ticker} className="flex items-baseline gap-1.5 text-[13px] font-mono" title={`${l.theme ?? ''} · ${l.status}`}>
                <i className="w-2.5 h-2.5 rounded-full inline-block self-center" style={{ background: LEADER_INK[l.status] ?? 'var(--color-text-muted)' }} />
                {l.ticker}{l.theme && <small className="text-[11px] text-[var(--color-text-muted)]">{l.theme}</small>}
              </span>
            ))}
            {b?.leaders_meta?.provisional !== false && (
              <span className="text-[11px] text-[var(--color-text-muted)]">
                provisional — the pipeline&rsquo;s list (members of 2-week Leading themes), not hand-ranked
              </span>
            )}
          </div>
        </>
      )}
    </Step>
  )
}

/* ── ④ themes ──────────────────────────────────────────────────────────── */

export function StepThemes({ transitions, faded }) {
  const t = transitions
  const Row = ({ x }) => (
    <div className="flex justify-between gap-3 border-b border-dotted border-[var(--color-border-light)] py-0.5 break-inside-avoid">
      <span className="text-[var(--color-text)]">{x.name}</span>
      <span className={`font-mono text-[11px] whitespace-nowrap ${x.dir === 'up' ? 'text-[var(--color-took)]' : 'text-[var(--color-refused)]'}`}>{x.from} → {x.to}</span>
    </div>
  )
  const changed = !t || !t.sessions ? <span>Theme history not loaded.</span> : (
    <>
      <p className="m-0"><B>{t.up.length} themes moved up, {t.down.length} moved down</B> over the last {t.lag} sessions.</p>
      {t.up.length > 0 && <p className="m-0 mt-1.5">Taking the lead: {t.up.slice(0, 4).map((x) => x.name).join(', ')}{t.up.length > 4 ? '…' : ''}.</p>}
      {t.down.length > 0 && <p className="m-0 mt-1.5">Losing it: {t.down.slice(0, 4).map((x) => x.name).join(', ')}{t.down.length > 4 ? '…' : ''}.</p>}
    </>
  )
  return (
    <Step n="④" source="Foundations ch.7 · §7.2 (4) · ch.2" title="RS themes" ask="Who just took the lead, who just lost it?" changed={changed} faded={faded}>
      {!t || !t.sessions ? <Missing what="Theme history" /> : (
        <>
          <Tiles>
            <Tile label={`Moved up · last ${t.lag}`} value={t.up.length} unit={t.up.length === 1 ? 'theme' : 'themes'}
                  source={t.up.slice(0, 3).map((x) => x.name).join(' · ') || 'none'} />
            <Tile label={`Moved down · last ${t.lag}`} value={t.down.length} unit={t.down.length === 1 ? 'theme' : 'themes'}
                  source={t.down.slice(0, 3).map((x) => x.name).join(' · ') || 'none'} />
            <Tile label="History depth" value={t.sessions} unit="sessions"
                  source="one row per theme per session since 2026-08-07" />
          </Tiles>
          {(t.up.length + t.down.length) > 0 && (
            <details className="mt-2 text-[13px]">
              <summary className="cursor-pointer text-[var(--color-text-secondary)]">
                Every theme that changed state <span className="font-mono text-[var(--color-text-muted)]">{t.up.length + t.down.length}</span>
              </summary>
              <div className="columns-1 md:columns-2 gap-6 text-[13px] mt-2">
                {t.up.map((x) => <Row key={x.name} x={x} />)}
                {t.down.map((x) => <Row key={x.name} x={x} />)}
              </div>
              <p className="m-0 mt-2 text-[11px] text-[var(--color-text-muted)]">Four states from the Themes page, compared with {t.lag} sessions ago.</p>
            </details>
          )}
        </>
      )}
    </Step>
  )
}

/* ── ⑤ news & sentinels ───────────────────────────────────────────────── */

export function StepNews({ s, faded }) {
  const changed = (
    <>
      <p className="m-0">The lesson&rsquo;s use: these set size and the setup bar, never which name to buy.</p>
      <p className="m-0 mt-1.5">Of the four sentinels the dollar has no data; oil, Korea and the defensives read every session.</p>
    </>
  )
  return (
    <Step n="⑤" source="Foundations ch.7 · §7.4 / §7.5 / §7.7" title="News & events" ask="Doubt or noise; is there follow-through?" changed={changed} faded={faded}>
      <Tiles>
        <Tile label="Oil · USO" value={pct(s.oil)} unit="1w" source="oil not rising, rates not rising — stocks find it easier" />
        <Tile label="Korea · EWY" value={pct(s.korea)} unit="1w" source="the Nasdaq-100's levered twin; Asia sees it first" />
        <Tile label="Defensives leading?" value={s.defense_leading == null ? '—' : s.defense_leading ? 'yes' : 'no'}
              source={`week: XLP ${pct(s.defense_reads.XLP)} · XLU ${pct(s.defense_reads.XLU)} · SPY ${pct(s.defense_reads.SPY)}`} />
        <Tile label="Offense · SMH" value={pct(s.offense.SMH)} unit="1w" source={`IGV ${pct(s.offense.IGV)} on the week`} />
        <Tile label="VIX" value={s.vix != null ? s.vix.toFixed(1) : '—'} unit={s.vix_band ?? ''}
              source={`under 15 raises the setup bar, it is not a sell signal (§7.7)${s.ts ? ` · VIX/VIX3M ${s.ts.value?.toFixed(2)} ${s.ts.label}` : ''}`} />
        <Tile label="Dollar" value="—" muted source="§7.4's first sentinel — not in the pipeline" />
        <Tile label="Follow-through" value="hand-noted" muted
              source="good news, high open, low close — no machine rule for it" />
      </Tiles>
      <p className="m-0 mt-2 text-[11px] text-[var(--color-text-muted)]">{s.rule}</p>
    </Step>
  )
}

/* ── ⑥ your book ───────────────────────────────────────────────────────── */

export function StepBook({ stopHit, faded }) {
  const changed = (
    <p className="m-0">The public page can only carry a stand-in — the watchlist&rsquo;s stop-hit count. The real reading lives in the private tracker.</p>
  )
  return (
    <Step n="⑥" source="Foundations ch.7 · §7.2 (6) / §7.5 (3)" title="Your book" ask="Which of your trades are working, which are not?" changed={changed} faded={faded}>
      <Tiles>
        <Tile label="Your recent trades" value="private" muted
              source="“strong when bought, stopped one after another” is the earliest read there is — and this repository is public" />
        <Tile label="Watchlist names that hit stops" value={stopHit ?? '—'} unit={stopHit != null ? 'names' : ''}
              source="the Stop Hit panel — the list, not your positions" />
      </Tiles>
    </Step>
  )
}

/* ── the whole read ────────────────────────────────────────────────────── */

export default function MorningRead({ ml, signals, rows, themes, groupsHistory, watchlist, etfs, correctionRisk, paneRows, loadingFull, votes }) {
  const reads = breadthReads({ rows, themes, watchlist })
  const transitions = themeTransitions(groupsHistory)
  const s = sentinels({ etfs, signals, correctionRisk })
  const red = ml?.spy?.light === 'red'
  const w52 = signals?.SPY?.trend_status?.['52w_high_dist']
  return (
    <div className="space-y-3">
      <Verdict ml={ml} reads={reads} />
      <div className="bg-[var(--color-surface)] rounded-3xl px-5 py-1">
        <StepIndex ml={ml} signals={signals} rows={rows} votes={votes} />
        {red && (
          <p className="m-0 mt-1 text-[11px] font-mono uppercase tracking-[.14em] text-[var(--color-refused)]">
            Light is red — the course says skip the rest today. Shown faded for context.
          </p>
        )}
        <StepBreadth reads={reads} faded={red} w52={w52} paneRows={paneRows ?? rows} loadingFull={loadingFull} rows={rows} votes={votes} />
        <StepLeaders ml={ml} faded={red} />
        <StepThemes transitions={transitions} faded={red} />
        <StepNews s={s} faded={red} />
        <StepBook stopHit={reads.stop_hit} faded={red} />
      </div>
    </div>
  )
}
