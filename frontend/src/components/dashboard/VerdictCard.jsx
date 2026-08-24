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

/* `falsify()` and the FLOOR constant lived here: they computed how many votes
   had to turn before the word changed, for a paragraph this card printed under
   the glyph row. Andy removed that paragraph on 2026-08-24 — the page states a
   reading, it does not argue for one — and the maths went with it. The same
   answer is on Market State detail, which is linked beside the score.

   `conditionsChange()` went the same way and for a better reason: it fed
   "10 of 15 conditions met, +4 since Aug 20", which is the 62/100 card below
   said twice. Printing one reading in two denominators is what made that card
   need a line explaining it was a different count. */

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

export default function VerdictCard({ verdict, onNavigate }) {
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
        keys={['verdict']}
        onNavigate={onNavigate} />
    )
  }

  const detail = verdict.vote_detail

  return (
    <section className="rounded-3xl bg-[var(--color-surface)] px-6 py-6 sm:px-8 sm:py-7">
      {/* The conditions count used to print here — "10 of 15 market conditions
          met, +4 since Aug 20". Andy took it out on 2026-08-24 along with the
          rest of this page's prose. It is not lost: the same reading is the
          62/100 card below, which carries the count, the band and the history.
          Printing it twice was what made a denominator disclaimer necessary. */}


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
      {/* The "stops being BULL at +4 / MIXED is the absence of a call"
          paragraph lived here until 2026-08-24. Andy: the page states a
          reading, it does not argue for one. The threshold and the standing
          votes are on Market State detail, one click from the score above. */}
    </section>
  )
}
