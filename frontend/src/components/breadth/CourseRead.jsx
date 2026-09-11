/**
 * The course's morning read — the main screen of Market State since
 * 2026-09-11 (Studio Q's ruling, docs/plans/2026-09-11-market-state-by-the-
 * course.md §五; Andy picked the layout the same day, §六).
 *
 *   Verdict   one word — FULL / DIM / AVOID. Aggression, never direction:
 *             "the course never outputs a direction call" (§五.2).
 *   Step 1    Lesson 6's light: SPY daily, three checks, and beside it the
 *             Lesson 6B count and gear.
 *   Step 2    Lesson 7's brightness: setups, leaders, breadth. On a red light
 *             the course says skip it (L7.2 step 1); Andy chose to keep it
 *             visible but faded, so the reader can see WHY not — e.g. leaders
 *             holding while the light is red.
 *
 * Nothing here computes the light: market_light.json arrives composed (DATA
 * ALEX, §七 e5546418). A missing block renders "not measured", never a zero.
 */

const VERDICT = {
  full: { word: 'FULL', line: 'Bright green — the market is offering. Take the good ones at full size.' },
  dim: { word: 'DIM', line: 'Green, but thin — be picky, size smaller, or pass.' },
  avoid: { word: 'AVOID', line: 'Sit still today.' },
}
const CHECK_LABEL = {
  fast_above_slow: (ma) => `10 ${ma} above the 20 ${ma}`,
  fast_rising: (ma) => `10 ${ma} rising`,
  slow_rising: (ma) => `20 ${ma} rising`,
}
const fmt = (v, d = 2) => (v == null ? '—' : Number(v).toFixed(d))

function Card({ title, aside, children, faded }) {
  return (
    <div className="bg-[var(--color-surface)] rounded-3xl p-5">
      <div className="flex items-baseline justify-between pb-3 mb-3 border-b border-[var(--color-v2-ink)]">
        <h2 className="text-[11px] font-mono uppercase tracking-[.24em] text-[var(--color-text-muted)]">{title}</h2>
        {aside && <span className="text-[11px] text-[var(--color-text-muted)]">{aside}</span>}
      </div>
      {faded && (
        <p className="m-0 mb-3 text-[11px] font-mono uppercase tracking-[.14em] text-[var(--color-refused)]">
          Light is red — the course says skip this step today. Shown faded for context.
        </p>
      )}
      <div className={faded ? 'opacity-45' : undefined}>{children}</div>
    </div>
  )
}

function NotMeasured({ what }) {
  return <p className="m-0 text-[13px] italic text-[var(--color-text-muted)]">{what} — not measured.</p>
}

/* ── verdict ───────────────────────────────────────────────────────────── */

/** The one word. If the file carries no verdict but the light is red, the
 *  course already answers: red means sit still (L6:183). A green light with
 *  no synthesised verdict stays unsaid — the rule that combines the three
 *  Lesson 7 answers is Studio Q's and ALEX's to write, not this page's. */
function verdictOf(ml) {
  if (ml?.verdict && VERDICT[ml.verdict]) return ml.verdict
  if (ml?.spy?.light === 'red') return 'avoid'
  return null
}

export function VerdictCard({ ml }) {
  const v = verdictOf(ml)
  const spy = ml?.spy
  return (
    <Card title="Today" aside={ml?.date ? `SPY daily · ${ml.date}` : undefined}>
      {!v ? <NotMeasured what="Today's aggression" /> : (
        <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
          <div>
            <div className="text-[46px] leading-none font-bold tracking-[.02em] text-[var(--color-text)]"
                 style={{ fontFamily: 'var(--font-cond)' }}>{VERDICT[v].word}</div>
            <div className="mt-1.5 text-[11px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)]">
              today&rsquo;s aggression
            </div>
          </div>
          <div className="flex-1 min-w-[260px]">
            <p className="m-0 text-[17px] leading-snug text-[var(--color-text-secondary)]">
              {spy?.light === 'red' && (
                <b className="font-semibold text-[var(--color-text)]">
                  The light is red — {spy.checks_passed} of 3 checks.{' '}
                </b>
              )}
              {VERDICT[v].line}
            </p>
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
    </Card>
  )
}

/* ── step 1 · the light ────────────────────────────────────────────────── */

/** SPY with the two lines, and a strip under it: one cell per session —
 *  ink = 3/3, red = 0/3, hatched = the in-between days the course counts as
 *  red (24.8% of sessions 2015–2026, L6:89). Studio Q: don't hide them. */
export function LightChart({ history }) {
  const h = (history ?? []).filter((r) => r.close != null)
  if (h.length < 2) return null
  const W = 640, H = 150, P = 6
  const vals = h.flatMap((r) => [r.close, r.fast, r.slow]).filter(Number.isFinite)
  const lo = Math.min(...vals), hi = Math.max(...vals)
  const x = (i) => P + (i * (W - 2 * P)) / (h.length - 1)
  const y = (v) => P + (1 - (v - lo) / (hi - lo || 1)) * (H - 2 * P)
  const path = (k) => h.map((r, i) => (Number.isFinite(r[k]) ? `${i ? 'L' : 'M'}${x(i).toFixed(1)} ${y(r[k]).toFixed(1)}` : '')).join('')
  const bw = (W - 2 * P) / h.length
  return (
    <svg viewBox={`0 0 ${W} ${H + 40}`} className="w-full h-auto block" role="img"
         aria-label="SPY close with the 10 and 20 day averages, and each session's light">
      <defs>
        <pattern id="light-mid" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="5" height="5" fill="var(--color-v2-off)" />
          <line x1="0" y1="0" x2="0" y2="5" stroke="var(--color-refused)" strokeWidth="1.6" />
        </pattern>
      </defs>
      <path d={path('close')} fill="none" stroke="var(--color-border)" strokeWidth="1.2" />
      <path d={path('slow')} fill="none" stroke="var(--color-text-muted)" strokeWidth="1.6" strokeDasharray="4 3" />
      <path d={path('fast')} fill="none" stroke="var(--color-text)" strokeWidth="1.8" />
      {h.map((r, i) => (
        <rect key={r.date} x={x(i) - bw / 2 + 0.5} y={H + 8} width={Math.max(1, bw - 1)} height="14"
              fill={r.checks_passed === 3 ? 'var(--color-took)' : r.checks_passed === 0 ? 'var(--color-refused)' : 'url(#light-mid)'}>
          <title>{`${r.date}: ${r.checks_passed}/3`}</title>
        </rect>
      ))}
      <text x={P} y={H + 36} fontSize="11" style={{ fill: 'var(--color-text-muted)' }}>{h[0].date.slice(5)}</text>
      <text x={W - P} y={H + 36} fontSize="11" textAnchor="end" style={{ fill: 'var(--color-text-muted)' }}>{h.at(-1).date.slice(5)}</text>
    </svg>
  )
}

export function LightStep({ ml }) {
  const spy = ml?.spy
  const ma = ml?.ma_type ?? 'EMA'
  return (
    <Card title="Step 1 · The light" aside={`Lesson 6 · SPY 10 / 20 ${ma}`}>
      {!spy?.checks ? <NotMeasured what="The light" /> : (
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_240px] gap-5">
          <div>
            <div className="space-y-2">
              {spy.checks.map((c) => (
                <div key={c.key} className="grid grid-cols-[26px_1fr_auto] gap-2.5 items-center text-[13px]">
                  <span className={`w-[22px] h-[22px] rounded-md grid place-items-center text-[13px] font-bold font-mono ${c.pass
                    ? 'bg-[var(--color-took)] text-[var(--color-surface)]'
                    : 'border-[1.5px] border-[var(--color-refused)] text-[var(--color-refused)] bg-[var(--color-v2-off)]'}`}
                        aria-label={c.pass ? 'yes' : 'no'}>{c.pass ? '✓' : '✗'}</span>
                  <span className="text-[var(--color-text)]">{CHECK_LABEL[c.key]?.(ma) ?? c.key}</span>
                  <span className="font-mono text-[var(--color-text-secondary)]">
                    {c.key === 'fast_above_slow'
                      ? `${c.a > c.b ? '+' : ''}${fmt(c.a - c.b, 3)}`
                      : `${c.a - c.b > 0 ? '+' : ''}${fmt(c.a - c.b)} on the day`}
                  </span>
                </div>
              ))}
              <div className="grid grid-cols-[26px_1fr_auto] gap-2.5 items-center text-[13px]">
                <span />
                <span className="font-semibold text-[var(--color-text)]">
                  {spy.light === 'green' ? 'Green' : 'Red'} — {spy.checks_passed}/3
                </span>
                <span className="font-mono text-[var(--color-text-muted)]">
                  {spy.checks_passed > 0 && spy.checks_passed < 3 ? 'in-between: counts as red' : ''}
                </span>
              </div>
            </div>
            <div className="mt-4"><LightChart history={spy.history} /></div>
            <p className="m-0 mt-1 text-[11px] leading-relaxed text-[var(--color-text-muted)]">
              SPY close (thin grey) with the 10 {ma} (ink) and 20 {ma} (dashed). Strip: each session&rsquo;s light —
              blue = all three checks yes, red = all three no, hatched = the in-between days, which the course counts as red.
            </p>
          </div>
          <div className="lg:border-l lg:border-[var(--color-border-light)] lg:pl-5 space-y-4">
            <div>
              <div className="text-[11px] font-mono uppercase tracking-[.14em] text-[var(--color-text-muted)]">Sessions vs 21-day line</div>
              <div className="text-[38px] leading-none font-bold mt-1 tabular-nums text-[var(--color-text)]"
                   style={{ fontFamily: 'var(--font-cond)' }}>
                {spy.plus_n == null ? '—' : `${spy.plus_n > 0 ? '+' : ''}${spy.plus_n}`}
              </div>
              <div className="text-[13px] text-[var(--color-text-secondary)]">
                {spy.plus_n == null ? 'not measured' : `closes ${spy.plus_n > 0 ? 'above' : 'below'} the 21-day, in a row`}
              </div>
            </div>
            <div>
              <div className="text-[11px] font-mono uppercase tracking-[.14em] text-[var(--color-text-muted)]">Gear · Lesson 6B</div>
              <div className="text-[38px] leading-none font-bold mt-1 tabular-nums text-[var(--color-text)]"
                   style={{ fontFamily: 'var(--font-cond)' }}>
                {spy.gear?.n == null ? '—' : `${spy.gear.n} / 7`}
              </div>
              <div className="text-[13px] text-[var(--color-text-secondary)]">{spy.gear?.label ?? 'not measured'}</div>
            </div>
            {ml?.qqq?.light && (
              <p className="m-0 text-[11px] text-[var(--color-text-muted)]">
                QQQ side lamp: {ml.qqq.light} ({ml.qqq.checks_passed}/3) — not part of the call; the course&rsquo;s light is SPY.
              </p>
            )}
          </div>
        </div>
      )}
    </Card>
  )
}

/* ── step 2 · brightness ───────────────────────────────────────────────── */

const LEADER_INK = {
  holding: 'var(--color-took)', extending: 'var(--color-took)', basing: 'var(--color-took)',
  broken: 'var(--color-refused)',
}

function Breadth({ rows }) {
  const r = (rows ?? []).slice(-60)
  if (r.length < 2) return <NotMeasured what="Breadth" />
  const W = 300, H = 90, P = 4
  const norm = (k) => {
    const v = r.map((x) => x[k]).filter(Number.isFinite)
    const lo = Math.min(...v), hi = Math.max(...v)
    return r.map((x) => (Number.isFinite(x[k]) ? (x[k] - lo) / (hi - lo || 1) : null))
  }
  const x = (i) => P + (i * (W - 2 * P)) / (r.length - 1)
  const y = (v) => P + (1 - v) * (H - 2 * P)
  const line = (a) => a.map((v, i) => (v == null ? '' : `${i ? 'L' : 'M'}${x(i).toFixed(1)} ${y(v).toFixed(1)}`)).join('')
  const net = r.at(-1).net_advances
  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto block" role="img" aria-label="advance/decline line against the S&P 500, 60 sessions">
        <path d={line(norm('spx_close'))} fill="none" stroke="var(--color-border)" strokeWidth="1.4" />
        <path d={line(norm('ad_line'))} fill="none" stroke="var(--color-text)" strokeWidth="1.8" />
      </svg>
      <p className="m-0 mt-1 text-[13px] text-[var(--color-text-secondary)]">
        Today <b className="font-semibold text-[var(--color-text)]">{net > 0 ? '+' : ''}{net?.toLocaleString()}</b> net advances.
      </p>
      <p className="m-0 text-[11px] text-[var(--color-text-muted)]">A/D line (ink) against the S&amp;P 500 (grey), 60 sessions.</p>
    </div>
  )
}

export function BrightnessStep({ ml, breadthRows }) {
  const b = ml?.brightness
  const red = ml?.spy?.light === 'red'
  const leaders = b?.leaders ?? []
  const count = (s) => leaders.filter((l) => l.status === s).length
  return (
    <Card title="Step 2 · Brightness" aside="Lesson 7 · read when the light is green" faded={red}>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-[.14em] text-[var(--color-text-muted)]">Q1 · Quality setups</div>
          {b?.setups?.count == null ? <NotMeasured what="Setup count" /> : (
            <>
              <div className="text-[38px] leading-none font-bold mt-1 tabular-nums" style={{ fontFamily: 'var(--font-cond)' }}>{b.setups.count}</div>
              <div className="text-[13px] text-[var(--color-text-secondary)]">10+ bright · 1–3 dim · 0 avoid</div>
            </>
          )}
        </div>
        <div>
          <div className="text-[11px] font-mono uppercase tracking-[.14em] text-[var(--color-text-muted)]">Q2 · Are the leaders leading?</div>
          {!leaders.length ? <NotMeasured what="Leaders" /> : (
            <>
              <div className="flex flex-wrap gap-x-3 gap-y-1.5 mt-2">
                {leaders.map((l) => (
                  <span key={l.ticker} className="flex items-center gap-1.5 text-[13px] font-mono" title={`${l.theme ?? ''} · ${l.status}`}>
                    <i className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: LEADER_INK[l.status] ?? 'var(--color-text-muted)' }} />
                    {l.ticker}
                  </span>
                ))}
              </div>
              <div className="text-[13px] text-[var(--color-text-secondary)] mt-2">
                {leaders.length - count('broken')} of {leaders.length} holding up · {count('broken')} broken
              </div>
            </>
          )}
        </div>
        <div>
          <div className="text-[11px] font-mono uppercase tracking-[.14em] text-[var(--color-text-muted)]">Q3 · Is breadth confirming?</div>
          <div className="mt-2"><Breadth rows={breadthRows} /></div>
        </div>
      </div>
    </Card>
  )
}
