import VoteGlyphs, { VoteMarks } from '../breadth/VoteGlyphs'

/**
 * The largest card on the page — the read, and what would break it.
 *
 * Andy locked the size grading on 2026-08-18: on this page the verdict wins,
 * and it wins because §5.1 asks the top third of every page to survive on its
 * own as a screenshot. That is the whole reason this is one card rather than a
 * verdict card with a falsification card beside it: a claim and its exit
 * condition cropped apart are two different documents.
 *
 * Three lines, in the order every card in this system holds:
 *
 *   change    conditions met today against the last session that was measured
 *   strength  the word, and the count that produced it
 *   evidence  the twelve votes with their distance to their own lines, and the
 *             sentence naming exactly how many have to turn
 *
 * TWO DENOMINATORS, DELIBERATELY BOTH PRINTED. The change line counts
 * CONDITIONS (15 of them, `conditions.history`, the only daily series the
 * pipeline stores with a date on it). The strength line counts VOTES (12 of
 * them, `verdict.votes`). They are different instruments and the pipeline has
 * always kept them apart; collapsing them into one number here would be the
 * front end inventing a measurement. The twelve-vote verdict has NO stored
 * history — `history.rows` holds the raw inputs, not the tally, and rederiving
 * the tally in JavaScript would put a second copy of the thresholds outside
 * breadth_signals.py, which owns them.
 */

/** `score >= 4` is BULLISH and `score <= -4` is BEARISH, from
 *  pipeline/screeners/breadth_signals.py:667. Mirrored here for the sentence
 *  only — the side of every vote and the score itself both arrive decided. */
const FLOOR = 4

/**
 * How much of the margin has to go, spelled in votes rather than in points.
 *
 * A vote turning to the other side moves the score by two (it leaves one
 * column and joins the other); a vote going undecided moves it by one. Both
 * routes are given because they are genuinely different events, and neither is
 * ranked against the other.
 *
 * Nothing here says WHICH vote is closest to turning. Distance lives in each
 * vote's own unit — a ratio 0.048 above its line, 137 names, 2.53 McClellan
 * points — and ordering those against each other would be a number this
 * payload cannot support. The glyph row draws each one inside its own range
 * instead, which is the honest version of the same question.
 */
function falsify(score, votes) {
  if (score == null || !votes) return null
  const sides = Object.values(votes)
  const bulls = sides.filter((v) => v === 'bull').length
  const bears = sides.filter((v) => v === 'bear').length

  if (score >= FLOOR) {
    const room = score - (FLOOR - 1)          // the drop that ends BULLISH
    return {
      breaksAt: FLOOR - 1, word: 'BULLISH', standing: bulls, side: 'bull',
      toOther: Math.min(bulls, Math.ceil(room / 2)),
      toNeutral: Math.min(bulls, room),
    }
  }
  if (score <= -FLOOR) {
    const room = -FLOOR + 1 - score
    return {
      breaksAt: -(FLOOR - 1), word: 'BEARISH', standing: bears, side: 'bear',
      toOther: Math.min(bears, Math.ceil(room / 2)),
      toNeutral: Math.min(bears, room),
    }
  }
  // MIXED has no falsification in this grammar: it is the absence of a claim,
  // so there is nothing to break. Say what would make it a claim instead.
  return {
    breaksAt: null, word: 'MIXED',
    toBull: Math.ceil((FLOOR - score) / 2),
    toBear: Math.ceil((score + FLOOR) / 2),
  }
}

/** The last two dated points of the stored conditions series. Two, not one,
 *  because a count without its predecessor is a level, and this line's job is
 *  the change. */
function conditionsChange(conditions) {
  const h = conditions?.history
  if (!Array.isArray(h) || h.length < 2) return null
  const now = h[h.length - 1]
  const prev = h[h.length - 2]
  if (now?.positive == null || prev?.positive == null) return null
  return { now, prev, delta: now.positive - prev.positive }
}

/**
 * The shape a card takes when its data did not arrive: the frame is real,
 * hatched so it cannot be mistaken for a card that computed an empty answer,
 * and it names the keys so the absence is actionable rather than mysterious.
 */
export function MissingBlock({ what, keys, onNavigate }) {
  return (
    <section className="rounded-3xl bg-[var(--color-surface)] px-6 py-6 sm:px-8 sm:py-7">
      <div className="rounded-2xl p-6"
           style={{ backgroundImage:
             'repeating-linear-gradient(45deg,var(--color-border-light) 0 1px,transparent 1px 7px)' }}>
        <div className="text-[10px] font-mono uppercase tracking-[.24em]
                        text-[var(--color-text-muted)] mb-3">Not measured</div>
        <p className="m-0 text-[17px] leading-snug text-[var(--color-text-bold)]">{what}</p>
        <p className="mt-2 mb-0 text-[11px] leading-relaxed text-[var(--color-text-secondary)] max-w-[68ch]">
          The nightly file arrived and{' '}
          <span className="font-mono">{keys.join(' · ')}</span>{' '}
          {keys.length === 1 ? 'is' : 'are'} missing from it. That is different from a
          reading of zero: nothing was measured, so nothing is shown. Everything else on
          this page comes from other blocks of the same file and is unaffected.
        </p>
        {onNavigate && (
          <button type="button" onClick={() => onNavigate('#/breadth')}
                  className="mt-4 text-[11px] bg-transparent border-0 p-0 cursor-pointer underline
                             text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
            Market State detail &rarr;
          </button>
        )}
      </div>
    </section>
  )
}

/** `2026-08-14` → `Aug 14`. The year is on the header already. */
function shortDate(iso) {
  if (!iso) return null
  const [, m, d] = iso.split('-')
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${MONTHS[Number(m) - 1]} ${Number(d)}`
}

export default function VerdictCard({ verdict, conditions, onNavigate }) {
  /**
   * A MISSING BLOCK IS SAID, NOT SKIPPED.
   *
   * This returned null when `verdict` was absent, and on 2026-08-19 that is
   * exactly what happened: a one-line inversion in the pipeline (an `if`
   * stealing a try's `else`) shipped breadth.json without verdict, conditions,
   * regime or state_board, and the two largest objects on this page simply
   * were not there. The page did not look broken. It looked shorter.
   *
   * That is the failure this whole dashboard is built against — absent must
   * not render as nothing — and the guard was on the wrong side of it. It now
   * names the keys the payload is missing, because the person who can act on
   * that is usually the person looking at the screen.
   */
  if (!verdict) {
    return (
      <MissingBlock
        what="Today's verdict is not in tonight's file."
        keys={['verdict', 'conditions']}
        onNavigate={onNavigate} />
    )
  }

  const change = conditionsChange(conditions)
  const broken = falsify(verdict.score, verdict.votes)
  const detail = verdict.vote_detail

  return (
    <section className="rounded-3xl bg-[var(--color-surface)] px-6 py-6 sm:px-8 sm:py-7">
      {/* ── change ──────────────────────────────────────────────────────
          Above the word, small, because it is the least of the three and
          still has to come first: the page's question is what changed.
          Absent rather than zero when the series is too short to difference —
          a change line that prints 0 for "we have one point" is a lie the
          rest of this card is built to avoid. */}
      <div className="text-[11px] leading-snug text-[var(--color-text-muted)] mb-5">
        {change ? (
          <>
            <span className="font-mono tabular-nums text-[var(--color-text)]">
              {change.now.positive} of {change.now.of}
            </span>{' '}
            market conditions met
            {change.delta !== 0 && (
              <>
                {' '}&mdash;{' '}
                <span className="font-mono tabular-nums text-[var(--color-text)]">
                  {change.delta > 0 ? '+' : ''}{change.delta}
                </span>{' '}
                since {shortDate(change.prev.date)}, when it was {change.prev.positive} of {change.prev.of}
              </>
            )}
            {change.delta === 0 && <> &mdash; unchanged since {shortDate(change.prev.date)}</>}
            {/* the denominators are different instruments; say so once, here,
                where the two numbers are three lines apart */}
            <span className="block mt-0.5">
              Conditions are a different count from the votes below.
            </span>
          </>
        ) : (
          <span>Conditions series too short to difference &mdash; not measured.</span>
        )}
      </div>

      {/* ── strength ────────────────────────────────────────────────────
          The word is the biggest thing on the page and wears no encoding
          colour: the marks under it already say bull or bear in took/refused,
          and saying it twice is what the 2026-08-13 split was for. Weight,
          size and the condensed face carry it instead. */}
      <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
        <h2 className="m-0 text-[clamp(3.25rem,9vw,5.5rem)] leading-[.86]
                       font-bold tracking-[-.018em] text-[var(--color-text-bold)]"
            style={{ fontFamily: 'var(--font-cond)' }}>
          {verdict.env}
        </h2>
        <span className="text-[26px] leading-none font-mono tabular-nums
                         text-[var(--color-text)]">
          {verdict.score > 0 ? '+' : ''}{verdict.score}
          <span className="text-[13px] text-[var(--color-text-muted)]"> / 12 votes</span>
        </span>
        {onNavigate && (
          <button type="button" onClick={() => onNavigate('#/breadth')}
                  className="text-[11px] bg-transparent border-0 p-0 cursor-pointer underline
                             text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
            Market State detail &rarr;
          </button>
        )}
      </div>

      {/* ── evidence: the twelve, each against its own line ─────────────
          vote_detail has been in the payload all along while this page
          rendered the one-bit fallback. The full glyph is what makes the
          falsification visible rather than merely stated: the ringed marks
          are the votes sitting on their lines. */}
      <div className="mt-7">
        {detail?.length ? <VoteGlyphs detail={detail} stretch />
                        : <VoteMarks votes={verdict.votes} />}
      </div>

      {/* ── the exit condition ──────────────────────────────────────────
          Expected register: dashed rule on the left (DESIGN §3). It is a
          condition on the future, not a measurement, and the structure has to
          survive a greyscale screenshot. */}
      {broken && (
        <p className="mt-7 mb-0 pl-4 text-[14px] leading-relaxed max-w-[68ch]
                      text-[var(--color-text-secondary)]
                      border-l border-dashed border-[var(--color-text-muted)]">
          {broken.breaksAt != null ? (
            <>
              Stops being <b className="text-[var(--color-text-bold)]">{broken.word}</b> at{' '}
              <span className="font-mono tabular-nums">
                {broken.breaksAt > 0 ? '+' : ''}{broken.breaksAt}
              </span>{' '}
              &mdash; the floor is{' '}
              <span className="font-mono tabular-nums">
                {broken.side === 'bull' ? `+${FLOOR}` : `−${FLOOR}`}
              </span>. From{' '}
              <span className="font-mono tabular-nums">
                {verdict.score > 0 ? '+' : ''}{verdict.score}
              </span>{' '}
              that is{' '}
              <b className="text-[var(--color-text-bold)]">
                {broken.toOther} of the {broken.standing} standing votes turning the other way
              </b>, or{' '}
              <b className="text-[var(--color-text-bold)]">{broken.toNeutral} going undecided</b>.
              Which ones is not on this card: distance lives in each vote&rsquo;s own unit, and
              ranking a ratio against a count of names would be a number this data cannot carry.
            </>
          ) : (
            <>
              <b className="text-[var(--color-text-bold)]">MIXED</b> is the absence of a call,
              so there is nothing here to break. It becomes a call at{' '}
              <span className="font-mono tabular-nums">±{FLOOR}</span> &mdash;{' '}
              {broken.toBull} more votes turning bull, or {broken.toBear} turning bear.
            </>
          )}
        </p>
      )}
    </section>
  )
}
