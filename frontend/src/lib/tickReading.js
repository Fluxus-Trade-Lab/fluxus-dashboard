/**
 * The TICK cycle reading in English — shared by the Dashboard's TICK band and
 * Market State's Correction risk fold (2026-09-11), so the two pages say the
 * same thing in the same words. Moved out of TickBand.jsx unchanged.
 */

/** `2026-08-06` → `Aug 6`. Parsed as UTC so the date string keeps its day. */
export function niceDate(iso) {
  if (!iso) return null
  const d = new Date(`${iso}T00:00:00Z`)
  return Number.isNaN(d.getTime()) ? iso : new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', timeZone: 'UTC' }).format(d)
}

const pc = (v) => (v == null ? null : `${v > 0 ? '+' : ''}${(v * 100).toFixed(1)}%`)
const pp = (v) => (v == null ? null : `${(v * 100).toFixed(1)}%`)

/**
 * The reading, in English, said as a conclusion.
 *
 * The payload ships its own sentence in Chinese (`data.reading`). Andy asked
 * for English here on 2026-08-24, and rather than wait on the data side this
 * builds the sentence from the same structured fields the Chinese one is built
 * from — `band`, `band_since`, `spread_rank252` and the `evidence` block — so
 * there is one source of numbers, not a translation that can drift from it.
 *
 * WHAT IT HAS TO GET ACROSS, because a colour would get it wrong: entering the
 * contracted band halves the next 21 days' median return AND lowers the odds
 * of a 5% drawdown. Thinner, not more dangerous. The last clause says so in
 * five words because that is the only part a reader must not miss.
 */
export function englishReading(d) {
  const e = d.evidence ?? {}
  const since = niceDate(d.band_since)
  const rank = d.spread_rank252 == null ? null
    : (d.spread_rank252 * 100 < 1 ? (d.spread_rank252 * 100).toFixed(1)
                                  : Math.round(d.spread_rank252 * 100))
  if (d.band === 'grind') {
    return [
      since && `Since ${since} the TICK's high–low band has been contracted`,
      rank != null && `${since ? ' — ' : "The TICK's high–low band is "}the tightest ${rank}% of the past year`,
      '. ',
      e.n_sell_entries && e.window_years
        && `In ${e.window_years} years there are ${e.n_sell_entries} entries into this band: `,
      e.sell_fwd21_med != null && e.base_fwd21_med != null
        && `the next 21 sessions returned ${pc(e.sell_fwd21_med)} at the median against ${pc(e.base_fwd21_med)} normally`,
      e.sell_p_dd5 != null && e.base_p_dd5 != null
        && `, and a 5% drawdown followed ${pp(e.sell_p_dd5)} of the time against ${pp(e.base_p_dd5)}`,
      '. Returns thin out; risk does not rise. A grind, not a break.',
    ].filter(Boolean).join('')
  }
  if (d.band === 'washout') {
    return [
      since && `Since ${since} the TICK's high–low band has been wide open`,
      rank != null && ` — the widest ${100 - rank}% of the past year`,
      '. That is the flush end of the cycle, where this indicator has historically been a buy window rather than a warning.',
    ].filter(Boolean).join('')
  }
  return `The TICK's high–low band is neither contracted nor open${
    since ? `, and has been since ${since}` : ''}. No timing read from this one today.`
}
