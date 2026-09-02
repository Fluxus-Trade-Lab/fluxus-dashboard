import { MissingBlock } from './VerdictCard'

/**
 * The regime band — one word, one binding condition.
 *
 * Design: Fluxus_Brand/visual/2026-08-10_TSF_PAGE_MAP.md §三 (approved 2026-08-10)
 *
 * Three voters, each already computed elsewhere and only READ here:
 *
 *   breadth    verdict.score        the twelve votes, −12…+12
 *   structure  spy_state/qqq_state  price structure of the two decision benchmarks
 *   power      macro signal         POWER_3 · CAUTION · WARNING · RISK_OFF
 *
 * The reading is the WEAKEST of the three, never the average. Averaging dilutes
 * one danger into a caution, and that one danger is the most expensive
 * information on the page. The other two voters print beside it so the
 * disagreement — which is the actual content — stays visible.
 *
 * Five bands in position language, not emotion language: what the state permits
 * you to hold, not how it feels. The line under the band names the binding
 * voter and the specific condition it is failing on — the same grammar as
 * Market State's "what would change this".
 */

/**
 * ⚠ THERE ARE TWO BAND SCHEMES, AND THEY ARE NOT OVER THE SAME SCORE.
 * Deliberate, not a duplication — but not interchangeable, and mixing them up
 * silently produces wrong numbers (it already did once, in a trade-attribution
 * table):
 *
 *   THIS FILE — Defence / Caution / Neutral / Constructive / Euphoria, even
 *     cuts 18 / 40 / 62 / 84 over `conditions.today`, which counts FIFTEEN
 *     conditions. Position language: what the state permits you to hold.
 *     USE FOR DISPLAY (this band, any "how much can I carry today" reading).
 *
 *   pipeline/screeners/regime.py — Damaged / Mixed / Healthy / Extended, cuts
 *     47 / 63 / 75 over `regime.score`, which counts NINE. Empirical quartiles
 *     of 558 archived sessions, validated monotone against 5% drawdown
 *     frequency. USE FOR ANALYSIS (bucketing trades by regime, risk-budget
 *     work, anything statistical).
 *
 * The earlier version of this comment said "the same 0-100 score", which is
 * the mistake it was written to prevent: on 2026-08-20 the two read 76 and
 * 75.0. Different denominators, different cuts, different names.
 *
 * The seam is not narrow. `regime.py` calls >= 75 Extended and this file calls
 * >= 84 Euphoria, so on 39 of 260 archived sessions — 15% — the analysis layer
 * sits in its top band while the display does not. A comment cannot hold that
 * open; the analysis layer's own score used to print beside this one until
 * 2026-08-24 — see the note above `RegimeBand` for why it no longer does.
 */
/* Top band renamed Full -> Euphoria (Andy 2026-08-19). A name change only:
   the cuts, the five-band scheme and the voter binding are untouched, and
   nothing fires on it — no euphoria warning, no fitted rule. The research says
   there is nothing to fire: 27 drops from >=75 to <=60 ran +1.8% median over
   the next 20 days at an 81% win rate, which is not a warning
   (data/research/regime_study_2026-08/README.md). The word is a description of
   how full the tape is, and that is all it is. */
export const BANDS = ['Defence', 'Caution', 'Neutral', 'Constructive', 'Euphoria']

/** Market Conditions 0-100 -> a band. Cuts are even (width 22) because the
 *  score is an unweighted percentage; a clever curve here would be a second
 *  model. Shifted up 6 from 12/34/56/78 on the data session's occupancy audit
 *  (2026-08-15): the old cuts were top-heavy — Full held 35% of 558 archived
 *  sessions — and 18/40/62/84 reads near-equal occupancy (Full 25.8%), takes
 *  Defence from 3 days to 7 with all seven inside the April crash, and leaves
 *  forward stratification intact. Same-day readings unchanged. */
function bandFromScore(score) {
  if (score == null) return null
  return score >= 84 ? 4 : score >= 62 ? 3 : score >= 40 ? 2 : score >= 18 ? 1 : 0
}

const POWER_LEVEL = { POWER_3: 4, CAUTION: 3, WARNING: 1, RISK_OFF: 0 }

/** Human names for the five power-trend checks, used when power is binding. */
const CHECK_LABEL = {
  '3d_gt_20sma': 'close > 20sma (3d)',
  '3d_gt_50sma': 'close > 50sma (3d)',
  '3d_gt_200sma': 'close > 200sma (3d)',
  '20sma_gt_50sma': '20sma > 50sma',
  '50sma_gt_200sma': '50sma > 200sma',
}

function breadthVoter(verdict) {
  const s = verdict?.score
  if (s == null) return null
  const level = s >= 8 ? 4 : s >= 4 ? 3 : s >= -3 ? 2 : s >= -7 ? 1 : 0
  // votes to the next band up, in the "what would change this" grammar
  const nextAt = [-7, -3, 4, 8][level] // threshold of the band above, if any
  const gap = level >= 4 ? null : nextAt - s
  return {
    name: 'breadth', level,
    word: `${s > 0 ? '+' : ''}${s}/12`,
    binding: gap == null ? null : `${gap} more vote${gap === 1 ? '' : 's'} to the next band`,
  }
}

function structureVoter(verdict) {
  const states = [verdict?.spy_state, verdict?.qqq_state]
  if (states.some((x) => x == null)) return null
  const up = states.filter((x) => x === 'Uptrend').length
  const down = states.filter((x) => x === 'Downtrend').length
  const level = down === 2 ? 0 : down === 1 ? 1 : up === 2 ? 4 : up === 1 ? 3 : 2
  const failing = ['SPY', 'QQQ'].filter((_, i) => states[i] !== 'Uptrend')
  return {
    name: 'structure', level,
    word: up === 2 ? 'both uptrends' : `${failing.join('+')} not in uptrend`,
    binding: failing.length ? `${failing.join(' and ')} below trend` : null,
  }
}

function powerVoter(signals) {
  const rows = ['SPY', 'QQQ'].map((t) => ({ t, s: signals?.[t] })).filter((r) => r.s)
  if (rows.length < 2) return null
  const weakest = rows.reduce((a, b) =>
    (POWER_LEVEL[a.s.signal] ?? 2) <= (POWER_LEVEL[b.s.signal] ?? 2) ? a : b)
  const level = POWER_LEVEL[weakest.s.signal] ?? 2
  const failing = Object.entries(weakest.s.power_trend ?? {})
    .filter(([, ok]) => !ok).map(([k]) => CHECK_LABEL[k] ?? k)
  return {
    name: 'power', level,
    word: `${weakest.t} ${weakest.s.signal.replace('_', ' ')}`,
    binding: failing.length ? `${weakest.t}: ${failing.join(', ')}` : null,
  }
}

/**
 * Two years of the score behind today's, drawn as one line.
 *
 * The band alone says where the market is; it cannot say whether 67 is a good
 * day or an ordinary one for this market. The line is the denominator for the
 * number — Oratnek's Market Conditions chart does exactly this and it is the
 * part of his dashboard worth taking.
 *
 * The line steps rather than glides because nine binary votes have a
 * resolution of 100/9 ≈ 11 points. Smoothing would draw precision the
 * measurement does not have.
 */
/** Month ticks: the first session of each month, thinned so labels never
 *  collide, with January carrying the year instead of the month name. */
function monthTicks(history, maxLabels = 7) {
  const marks = []
  let prev = null
  history.forEach((d, i) => {
    const m = d.date?.slice(0, 7)
    if (!m || m === prev) return
    prev = m
    const [y, mm] = m.split('-')
    marks.push({
      i,
      label: mm === '01' ? y : new Date(`${m}-02T00:00:00Z`)
        .toLocaleString('en', { month: 'short', timeZone: 'UTC' }),
      isYear: mm === '01',
    })
  })
  const step = Math.max(1, Math.ceil(marks.length / maxLabels))
  // Always keep January: a year boundary is the one tick you cannot infer.
  const kept = marks
    .map((m, ord) => ({ ...m, ord }))
    .filter(({ ord, isYear }) => ord % step === 0 || isYear)

  // ...but forcing it in is what put "Dec 2026 Feb" on top of itself on a
  // phone: the year lands BETWEEN two ticks the step had already chosen, so
  // three consecutive months print in a row that has room for one. The year
  // wins the collision — it is the tick that cannot be inferred — and the
  // neighbour that is merely a month steps aside.
  const out = []
  for (const m of kept) {
    const prev = out[out.length - 1]
    // ord is the month's place in the sequence, not its day index — the
    // spacing rule is "how many months apart", and step counts months.
    if (prev && m.ord - prev.ord < step) {
      if (m.isYear && !prev.isYear) out[out.length - 1] = m
      continue
    }
    out.push(m)
  }
  return out
}

/**
 * Two years of the score behind today's, drawn as one line.
 *
 * The band alone says where the market is; it cannot say whether 67 is a good
 * day or an ordinary one for this market. The line is the denominator for the
 * number.
 *
 * The line steps rather than glides because nine binary votes have a
 * resolution of 100/9 ≈ 11 points. Smoothing would draw precision the
 * measurement does not have.
 *
 * Labels live in HTML rather than in the SVG: the plot uses
 * preserveAspectRatio="none" so it can stretch to any width, and text inside
 * it would stretch with it.
 */
function ConditionsLine({ history, score, binds }) {
  if (!history?.length) return null
  const W = 1000, H = 130, PAD = 4
  const x = (i) => PAD + (i / Math.max(1, history.length - 1)) * (W - PAD * 2)
  const y = (v) => PAD + (1 - v / 100) * (H - PAD * 2)
  /* Stem weight comes from how many sessions have to fit, not from a taste
     call — and it is a plain stroke, NOT `non-scaling-stroke`. The rules above
     use non-scaling because a 1px rule should stay 1px at any width; a stem
     must stay in proportion to its own pitch or the barcode fills in. At 260
     sessions in a 628px card the pitch is 2.4px, and a non-scaling 1.46px stem
     is a 61% duty cycle — a grey block, not 260 readings.
     THE HEADS ARE DENSITY-GATED. L3 puts a lollipop head on every stem, which
     works at its stated 90-day scale. At 260 they touch — and under
     `preserveAspectRatio="none"` they are squashed into eggs besides. So they
     appear only when the pitch can hold one; below that the stem tip IS the
     reading, which is what a barcode is. */
  const gap = (W - PAD * 2) / Math.max(1, history.length - 1)
  const stem = Math.max(0.7, Math.min(2.2, gap * 0.38))
  const head = gap >= 6 ? Math.min(3.2, gap * 0.42) : 0
  const ticks = monthTicks(history)
  const pos = (i) => `${(x(i) / W) * 100}%`

  return (
    <div className="mt-5 pr-9">
      <div className="relative">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-[150px] block" role="img"
             aria-label={`Market conditions ${score} of 100 over ${history.length} sessions`}
             preserveAspectRatio="none">
          {/* v3 chart grammar: three rules, not seven — the frame is 0/100
              and the 50 line; month ticks live in the label row below, so the
              vertical gridlines go too. The line steps (vote resolution) but
              steps BOLDLY, and it ends in a dot: the reader's eye lands where
              the data does. */}
          {[0, 50, 100].map((lvl) => (
            <line key={lvl} x1={PAD} x2={W - PAD} y1={y(lvl)} y2={y(lvl)} strokeWidth="1"
                  stroke={lvl === 50 ? 'var(--color-text-muted)' : 'var(--color-border)'}
                  strokeDasharray={lvl === 50 ? '3 5' : undefined}
                  vectorEffect="non-scaling-stroke" />
          ))}
          {/* ONE SESSION, ONE STEM — a barcode, not a curve.
              The note above already said the line "steps rather than glides
              because nine binary votes have a resolution of ~11 points". Right
              observation, wrong shape: a polyline still draws a continuous path
              through days nobody measured between. This score is a COUNT — 15
              conditions met or not — so every session is its own reading and
              gets its own stem.
              Geometry after lieflat-charts L3 Barcode Lollipop, tried against
              this exact series on 2026-08-23 and scored highest of eight. The
              accent stays OURS: red only when the band binds, never an
              imported orange — red already means one thing on this page. */}
          {history.map((d, i) => (
            <line key={d.date} x1={x(i)} x2={x(i)} y1={y(0)} y2={y(d.score)}
                  strokeWidth={stem} stroke="var(--color-text)" opacity={0.7} />
          ))}
          {head > 0 && history.map((d, i) => (
            <circle key={`h${d.date}`} cx={x(i)} cy={y(d.score)} r={head}
                    fill="var(--color-text)" />
          ))}
        </svg>

        {/* right-hand scale, outside the plot so it never sits over the line */}
        {[100, 50, 0].map((lvl) => (
          // hidden when today's badge would sit on top of it — two numbers in
          // the same place is worse than one missing tick
          score != null && Math.abs(score - lvl) < 6 ? null : (
            <span key={lvl} className="absolute left-full ml-1.5 -translate-y-1/2
                                       text-[11px] font-mono text-[var(--color-text-muted)]"
                  style={{ top: `${(y(lvl) / H) * 100}%` }}>{lvl}</span>
          )
        ))}

        {score != null && (
          <span className="absolute w-[9px] h-[9px] rounded-full -translate-y-1/2 -translate-x-1/2"
                style={{ top: `${(y(score) / H) * 100}%`, left: '100%',
                         background: binds ? 'var(--color-refused)' : 'var(--color-text)' }} />
        )}
        {/* today's value, pinned to where the line ends */}
        {score != null && (
          <span className="absolute -translate-y-1/2 px-1.5 py-[1px] text-[11px] font-mono
                           font-semibold tabular-nums whitespace-nowrap"
                style={{ top: `${(y(score) / H) * 100}%`, left: '100%',
                         background: binds ? 'var(--color-refused)' : 'var(--color-text)',
                         color: 'var(--color-bg)' }}>
            {score}
          </span>
        )}
      </div>

      <div className="relative h-[13px] mt-0.5">
        {ticks.map((t) => {
          // A centred label at either extreme hangs half outside the box and
          // gets clipped; the edge ones align to the edge instead.
          const frac = x(t.i) / W
          const edge = frac < 0.03 ? 'left' : frac > 0.97 ? 'right' : null
          return (
            <span key={t.i}
                  className={`absolute text-[11px] font-mono whitespace-nowrap
                              ${edge ? '' : '-translate-x-1/2'}
                              ${t.isYear ? 'text-[var(--color-text-secondary)] font-semibold'
                                         : 'text-[var(--color-text-muted)]'}`}
                  style={edge === 'left' ? { left: 0 }
                       : edge === 'right' ? { right: 0 }
                       : { left: pos(t.i) }}>
              {t.label}
            </span>
          )
        })}
      </div>
    </div>
  )
}

/* `bandShare()` counted how often the score's own band occurred over the
   loaded history — "as did 32% of the last 260 sessions". It fed one clause of
   the paragraph Andy removed on 2026-08-24 and has no other reader. */


/* `SchemeSeam` printed the analysis layer's own score beside this one —
   "analysis scheme 72 / 100 Healthy". Two schemes really do score this page:
   this file cuts Defence/Caution/Neutral/Constructive/Euphoria over
   `conditions.today` (fifteen conditions, fixed thresholds, for position size),
   and `regime.py` cuts Damaged/Mixed/Healthy/Extended over `regime.score`
   (nine conditions, empirical quartiles, for bucketing trades in analysis).
   The seam is wide — on 39 of 260 sessions one is in its top band and the
   other is not.

   Andy took the line off on 2026-08-24, and the reason it can go is that only
   one of the two is ACTIONABLE from this page. The other is a statistics tool,
   and a statistics tool does not need a seat on the morning dashboard to be
   used correctly by the notebook that calls it. `regime` is still in the
   payload; nothing on this card reads it now. */

export default function RegimeBand({ verdict, signals, conditions, onNavigate }) {
  const cast = { breadth: breadthVoter(verdict), structure: structureVoter(verdict),
                 power: powerVoter(signals) }
  const voters = Object.values(cast).filter(Boolean)

  /**
   * A reading off partial voters would lie by omission — but so did returning
   * null, which is what this did until 2026-08-19. When the pipeline shipped
   * breadth.json without its four enrichment blocks, this card and the verdict
   * above it both vanished and the page just looked shorter. Refusing to
   * compute is right; refusing to SAY SO is the thing this dashboard exists
   * not to do. It names which voters did not report.
   */
  if (voters.length < 3) {
    const missing = Object.entries(cast).filter(([, v]) => !v).map(([k]) => k)
    return (
      <MissingBlock
        what="The regime reading needs three voters and did not get them."
        keys={missing}
        onNavigate={onNavigate} />
    )
  }

  const score = conditions?.today ?? null
  const scoreBand = bandFromScore(score)
  const weakest = voters.reduce((a, b) => (a.level <= b.level ? a : b))

  /* The score sets the band and the weakest voter can only pull it DOWN, never
     up. Breadth can be broad and still be riding a benchmark that has lost its
     50-day; averaging that away turns one danger into a caution, and the
     danger is the expensive half. When the two disagree the line underneath
     names which voter did the pulling and on what condition. */
  const level = scoreBand == null ? weakest.level : Math.min(scoreBand, weakest.level)

  return (
    <section className="rounded-3xl px-6 py-5 bg-[var(--color-surface)]">
      <div className="flex items-baseline justify-between gap-4 flex-wrap">
        <div className="flex items-baseline gap-3">
          <span className="text-[11px] font-mono uppercase tracking-[.24em]
                           text-[var(--color-text-muted)]">Market conditions</span>
          {score != null && (
            <span className="text-[26px] font-semibold tabular-nums leading-none"
                  style={{ fontFamily: 'var(--font-cond)' }}>
              {score}<span className="text-[13px] text-[var(--color-text-muted)]"> / 100</span>
            </span>
          )}
        </div>
        {/* The regime word, top right — the one thing to read if you read
            nothing else. Which is exactly why it cannot be the only thing
            printed: on 76 of the 260 sessions in the file — 29% — this word
            disagrees with the number two inches to its left, because a voter
            pulled the reading below what the score alone would give. Structure
            did 63 of those 76, and 25 of them were pulls of two or three whole
            bands. A comment here used to claim the reasoning was "a tooltip
            now"; there was no tooltip, and there never had been. It is a line
            under the header now, where a line can be read.
            v3: ink when the state permits carrying risk, red only when it does
            not (Defence/Caution) — a lone red means the band itself is what
            binds you today. Blue is gone: a band alone is one pole, and blue
            never appears without its red twin. */}
        <span
              className="text-[13px] font-semibold uppercase tracking-wide px-2.5 py-[3px]"
              style={{ background: level <= 1 ? 'var(--color-refused)' : 'var(--color-text-bold)',
                       color: 'var(--color-bg)' }}>
          {BANDS[level]}
        </span>
      </div>

      {/* A paragraph stood here explaining which band the score alone reads,
          how common that is, and which voter pulled the word away from it.
          Andy removed it on 2026-08-24 with the rest of this page's prose. The
          three voters below still print, and the binding one still carries the
          ink weight — which is the same fact, said in three words instead of
          thirty. */}

      {/* The three voters printed here as a row — "breadth +2/12 · structure
          SPY+QQQ not in uptrend · power SPY POWER 3". Andy removed it on
          2026-08-24 with the last of this page's chrome. They have not stopped
          voting: `weakest` still sets the band word above, and the guard below
          still refuses to compute a reading off fewer than three of them. What
          went is the printout. */}

      {/* rule three, same as the badge: the endpoint wears red only when
          the band itself binds (Defence/Caution); an all-clear day stays ink */}
      <ConditionsLine history={conditions?.history} score={score} binds={level <= 1} />

    </section>
  )
}
