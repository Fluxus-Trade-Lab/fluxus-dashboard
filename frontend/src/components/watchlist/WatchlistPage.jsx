import { useEffect, useState } from 'react'
import PageHeader from '../PageHeader'
import TickerLink from '../ticker/TickerLink'
import { useLanguage } from '../../i18n/LanguageContext'
import ShortListPage from './shortlist/ShortListPage'
import { dataName } from '../../i18n/names'
import { word } from '../screener/richText'
import watchlistPart from '../../i18n/parts/watchlist'

/**
 * Today's List — the six seats and my shortlist (Andy 2026-10-04, plan A).
 *
 * The morning brief's tab left with the merge: its five steps are the
 * Screener's step bar now. What stays in this file besides the page are the
 * row helpers other code and tests still read (gate wording, RS pick, the
 * healthcare view, the name chip).
 */

/** English by default — gateWords is called bare by its tests and must print
 *  what it always printed. */
const enT = (k, vars) => String(watchlistPart.en[k] ?? k)
  .replace(/\{(\w+)\}/g, (m, v) => (vars?.[v] != null ? String(vars[v]) : m))

/**
 * The gate, in the words its own keys imply.
 *
 * The pipeline swapped `min_avg_volume` (shares) for `min_dollar_volume` on
 * 2026-08-17 — a name-and-unit change, not a value change — and this line was
 * reading the old key straight into a division, so it would have printed
 * "$1B cap, NaNM average volume" the moment the new file landed. Reading a
 * missing key as a number is how a page starts lying quietly.
 *
 * So each key is named explicitly and an unknown one is dropped rather than
 * formatted. A gate clause we cannot describe should be absent from the
 * sentence, never present as NaN.
 */
export const gateWords = (gate = {}, t = enT) => {
  const out = []
  if (gate.min_market_cap) out.push(t('wl2.gate.cap', { v: (gate.min_market_cap / 1e9).toFixed(0) }))
  if (gate.min_dollar_volume) out.push(t('wl2.gate.dollarVol', { v: (gate.min_dollar_volume / 1e6).toFixed(0) }))
  else if (gate.min_avg_volume) out.push(t('wl2.gate.shares', { v: (gate.min_avg_volume / 1e6).toFixed(0) }))
  if (gate.min_adr_pct) {
    /* The exemption is named because the overview shows the exempt zone's
       panels on the same screen. An unqualified "ADR >= 3.5%" would claim a
       floor that visibly does not hold for the trouble rows two inches below:
       an exit signal does not stop mattering because the name went quiet. */
    const exempt = gate.adr_exempt_zones || []
    out.push(exempt.length
      ? t('wl2.gate.adrExcept', { v: gate.min_adr_pct,
          zones: exempt.map((z) => word(t, `wl2.zoneShort.${z}`, z)).join('/') })
      : t('wl2.gate.adr', { v: gate.min_adr_pct }))
  }
  return out.join(' · ')
}

/**
 * How many names the panels below could actually have drawn from.
 *
 * `universe_gated` counts everything past the liquidity gate. Since 2026-08-25
 * a third, universe-wide gate runs after it — `MIN_ADR_PCT = 3.5` — and the
 * panels draw from what survives THAT. On the 08-29 file the two numbers are
 * 2,055 and 975: printing the first beside a list built from the second
 * overstates the reader's universe by 2.1x.
 *
 * The fallback is deliberate and one-directional. A file written before
 * 2026-08-27 has no `universe_tradeable`, and `nf(undefined)` would print NaN
 * — the exact failure the gate-clause comment above was written about. Falling
 * back to the older, looser count keeps the sentence readable on an old file;
 * every current file carries the right one and never reaches the fallback.
 */
export const tradeableCount = (data = {}) =>
  (data.universe_tradeable ?? data.universe_gated)

/**
 * Which number sits beside a ticker, and what it is called.
 *
 * The file may carry two, and they answer different questions:
 *
 *   rs_1m              cross-sectional — "beats 90% of the tradeable field"
 *   rs_line_pctl_21    time-series — the close/SPY ratio's own percentile over
 *                      its last 21 readings, so 100 means its strength against
 *                      SPY is at a one-month high. This is the number oratnek
 *                      prints, decoded 2026-08-17 and reproduced 29/29 exactly.
 *
 * This page prefers the time-series one, because it is the one that is NOT
 * already implied by the panel a name sits in: several recipes gate on rs_1m
 * (the momentum panels are percentile cuts; True Market Leaders gates on
 * rs_rating >= 97 since the Moglen 2020 definition, 2026-09-18),
 * so printing rs_1m beside those rows repeats the entry condition, while the
 * 21-day reading adds something the membership did not already say.
 *
 * Whichever is drawn, the legend names it — the label is derived from the same
 * pick, so the page cannot print one number under the other one's name. Until
 * the new column ships this falls back to rs_1m and says rs_1m.
 */
export const pickRs = (rows = []) =>
  (rows.some((r) => r?.rs_line_pctl_21 != null) ? 'rs_line_pctl_21' : 'rs_1m')

/**
 * The number beside a ticker, inked — and the bands belong to the MEASURE.
 *
 * Two measures can appear here and they are shaped differently, so one set of
 * cuts cannot serve both.
 *
 * rs_1m is a cross-sectional percentile, uniform by construction: >= 80 is the
 * top fifth of the tradeable field and <= 40 the bottom two fifths. Those cuts
 * mean what they say because the distribution is flat.
 *
 * rs_line_pctl_21 is a percentile of a name against ITSELF over 21 sessions,
 * and its distribution is nothing like flat — on the only sample of it that
 * exists (the 29 values transcribed from oratnek's screen), the same >= 80 cut
 * would have inked 76% of the names blue and nothing red. Three quarters of a
 * page in one colour is decoration, not a reading. That sample is also
 * selection-biased — they are names his scans surfaced, so they skew strong —
 * which means it cannot be used to calibrate a replacement cut either.
 *
 * So this measure is not given a calibrated cut at all. It is inked at its
 * DEFINITIONAL endpoints, which need no calibration and cannot drift: 21/21 is
 * "today is the highest relative strength of the last month" and 1/21 is "today
 * is the lowest". Both are events. Everything between them is a matter of
 * degree and stays grey, which is what grey is for.
 *
 * WHY WEIGHT AS WELL. Measured on the dark ground the three inks are 8.92 /
 * 5.64 / 6.73 against #1a1715, so each clears 4.5 — but the greyscale
 * separations are took-refused 14.4, took-muted 9.1, refused-muted only 5.3.
 * Three identities on one channel with two of them 5.3 apart is fine in colour
 * and gone in greyscale, and gone for a red-blind reader. Dimming the middle to
 * open the gap was measured too and just trades the fault: at 60% the middle
 * falls to 3.24 contrast. So weight is the second channel — both poles semibold,
 * the middle not.
 */
export const RS_BANDS = {
  rs_1m: { hi: 80, lo: 40 },
  // 21/21 and 1/21 — the two ends of the count. IN THE UNITS THE FILE REPORTS,
  // which are rounded whole numbers: 1/21 arrives as 5, not 4.76. A band set
  // at exactly 100/21 therefore never fired, and the ten names that were at a
  // one-month low in relative strength — every one of them in Stop Hit or
  // Lower Low Break, which is where you would want to see them — stayed grey.
  // The threshold sits between 1/21 and 2/21 so rounding cannot close it.
  rs_line_pctl_21: { hi: 100, lo: 100 * 1.5 / 21 },
}

const rsInk = (v, key = 'rs_1m') => {
  const b = RS_BANDS[key] || RS_BANDS.rs_1m
  return v == null ? 'text-[var(--color-text-muted)]'
    : v >= b.hi ? 'text-[var(--color-took)] font-semibold'
      : v <= b.lo ? 'text-[var(--color-refused)] font-semibold'
        : 'text-[var(--color-text-muted)]'
}


/**
 * One name as a CELL, not an inline run.
 *
 * Inline-wrapped names were the page's untidiness: nothing lined up, so the
 * eye had to re-find the left edge on every row. Ticker left, number right, in
 * a fixed column — which is the whole reason a table of names reads faster
 * than a paragraph of them.
 */
/**
 * The ATR position, as the ticker's own ground (Andy, 2026-08-19).
 *
 * It was a number beside the name and it is a FILL under the name now: how far
 * a stock has run from its 50-day is the one reading that decides whether you
 * can still get on, and it should be legible before you have read anything.
 * Cool where you can build, hot where you cannot.
 *
 * THE RAMP FALLS IN LIGHTNESS AS IT WARMS, and that is the whole craft of it.
 * A hue ramp alone dies in greyscale — and greyscale is this brand's
 * load-bearing column, because the page travels as screenshots. Every stop
 * below is darker than the one before it, so a black-and-white copy still
 * reads the magnitude off the ink density even with the hue gone. Measured, not
 * asserted: the L* values are checked in the browser after every change.
 *
 * The anchors are the documented bands, not a smooth guess: 0–4 build, 5–7
 * hold, ≥7 scale out. Between them it interpolates, so two names in the same
 * band still separate.
 *
 * BELOW THE 50-DAY LEAVES THE SCALE. A negative reading is not "very
 * un-extended", it is a different situation — no fill, and the name keeps its
 * ordinary ink. Same rule the number followed, same reason.
 *
 * The exact figure is not lost, it moved into the tooltip. A fill answers "can
 * I get on" at a glance; the digit answers "by how much" when you ask.
 */
const ATR_STOPS = {
  /* Dark: lightness RISES with the reading. On an ink page the alarming end
     should be the luminous one, and rising is the only direction that keeps
     the greyscale monotonic against a near-black ground. */
  dark:  [[0, '#16304d'], [4, '#2b6ea8'], [7, '#c06a2a'], [10, '#f0705a']],
  /* Light: it FALLS, for the same reason inverted — on paper the alarming end
     is the heavy one. */
  light: [[0, '#dbe9f6'], [4, '#8fbfe0'], [7, '#e09a72'], [10, '#c9432b']],
}

/**
 * The foreground is CHOSEN, never interpolated: a first pass ramped the ink
 * alongside the ground and it passed through mid-grey on a mid-lightness fill
 * — measured 1.61:1 at ATR 8. Picking whichever ink the ground can carry is
 * simpler and correct at every point on the ramp.
 *
 * Pure white and pure black, not the page's near-inks. Measured with
 * #fbf9f5/#12110f the worst point on the ramp came to 4.40 — a fill in the
 * middle of a lightness range is the hardest ground there is, and the last
 * fraction of ink contrast is exactly what buys it back. This is a small
 * coloured chip, not body copy: it can afford the strongest pair.
 */
const ATR_INK = ['#ffffff', '#000000']

const hexToRgb = (c) => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16))
const mix = (a, b, t) => {
  const [x, y] = [hexToRgb(a), hexToRgb(b)]
  return '#' + x.map((v, i) => Math.round(v + (y[i] - v) * t)
    .toString(16).padStart(2, '0')).join('')
}
const relLum = (rgb) => {
  const f = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4 }
  return 0.2126 * f(rgb[0]) + 0.7152 * f(rgb[1]) + 0.0722 * f(rgb[2])
}
const contrast = (a, b) => {
  const [x, y] = [relLum(hexToRgb(a)), relLum(hexToRgb(b))]
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05)
}

const lStar = (c) => {
  const y = relLum(hexToRgb(c))
  return y > 0.008856 ? 116 * Math.cbrt(y) - 16 : 903.3 * y
}

/**
 * Pull a colour to a target lightness without touching its hue much.
 *
 * Straight RGB interpolation between a blue and an orange dips in lightness on
 * the way — measured, the ramp went 44.9 at ATR 4 and 44.6 at 4.5, so the
 * greyscale reading briefly ran backwards. Blending toward white or black to
 * hit the linearly-interpolated L* makes the monotonicity a property of the
 * construction rather than of the anchors happening to line up.
 */
function toLightness(c, target) {
  const cur = lStar(c)
  if (Math.abs(cur - target) < 0.5) return c
  const up = cur < target
  const towards = up ? '#ffffff' : '#000000'
  let lo = 0, hi = 1
  for (let i = 0; i < 14; i++) {
    const mid = (lo + hi) / 2
    // the predicate has to flip with the direction: blending toward white
    // RAISES L*, toward black it lowers it, and a single comparison sent the
    // search to the far end. It did, and two of today's fills came out pure
    // black at exactly the stop boundaries.
    const overshot = up ? lStar(mix(c, towards, mid)) > target
                        : lStar(mix(c, towards, mid)) < target
    if (overshot) hi = mid
    else lo = mid
  }
  return mix(c, towards, (lo + hi) / 2)
}

/** {bg, fg} for a reading, or null when it is off the scale. */
export function atrFill(v, dark) {
  if (v == null || !Number.isFinite(v) || v < 0) return null
  const stops = ATR_STOPS[dark ? 'dark' : 'light']
  const x = Math.min(v, stops[stops.length - 1][0])
  let bg = stops[stops.length - 1][1]
  for (let i = 1; i < stops.length; i++) {
    if (x <= stops[i][0]) {
      const [x0, c0] = stops[i - 1]
      const [x1, c1] = stops[i]
      const t = x1 === x0 ? 0 : (x - x0) / (x1 - x0)
      bg = toLightness(mix(c0, c1, t), lStar(c0) + (lStar(c1) - lStar(c0)) * t)
      break
    }
  }
  const fg = contrast(ATR_INK[0], bg) >= contrast(ATR_INK[1], bg) ? ATR_INK[0] : ATR_INK[1]
  return { bg, fg }
}

/** Which theme is on, kept live — the ramp has a light set and a dark set, and
 *  the fill is computed at render rather than handed to CSS, so it cannot be
 *  flipped by a token. */
function useDarkTheme() {
  const [dark, setDark] = useState(() =>
    document.documentElement.classList.contains('dark'))
  useEffect(() => {
    const el = document.documentElement
    const obs = new MutationObserver(() => setDark(el.classList.contains('dark')))
    obs.observe(el, { attributes: true, attributeFilter: ['class'] })
    return () => obs.disconnect()
  }, [])
  return dark
}

const atrTitle = (v, t) => v == null || !Number.isFinite(v)
  ? t('wl2.atr.none')
  : v < 0 ? t('wl2.atr.below', { v: v.toFixed(1) })
  : v <= 4 ? t('wl2.atr.build', { v: v.toFixed(1) })
  : v < 7 ? t('wl2.atr.hold', { v: v.toFixed(1) })   // 7.0 itself is Extended, as watchlist.py:246 (>= 7)
  : t('wl2.atr.ext', { v: v.toFixed(1) })


export function Name({ row, rsKey = 'rs_1m' }) {
  const { t, lang } = useLanguage()
  const v = row[rsKey]
  const alt = rsKey !== 'rs_1m' && row.rs_1m != null ? `RS 1M ${row.rs_1m}` : null
  /**
   * Alone, or with the whole theme?
   *
   * Andy's bonus condition for a name: it is worth more when its theme is
   * moving too. The file already answers it — every row carries its home group
   * and that group's four-state — so the page can say it without a second
   * lookup and without sending you back to Themes.
   *
   * A MARK, not a label. The theme's name was here this morning and it
   * squeezed the ticker out of its own cell; this says the one bit that
   * matters (is the water moving) and puts the name of the water in the
   * tooltip. Presence is the whole encoding — one bit needs one channel, and
   * grey keeps it out of the took/refused pair, which is about the number.
   *
   * Descriptive, not predictive. Nobody here has measured whether a name
   * carried by its theme works more often; the legend says so in those words.
   */
  const withTheme = row.group_state === 'Leading' || row.group_state === 'Improving'
  const fill = atrFill(row.atr_from_sma50, useDarkTheme())
  return (
    <span className="flex items-baseline gap-1.5 px-2 py-[3px] min-w-0">
      {/* THE TICKER NEVER SHRINKS — it carried `truncate` next to a label that
          demanded the whole width, and collapsed to "U…".
          It also carries the ATR reading as its own ground now, so its ink is
          chosen against that ground rather than from the token: white-on-blue
          and white-on-red are two different foregrounds and only one of them
          is legible on each. Off the scale it falls back to the token. */}
      <TickerLink symbol={row.ticker}
                  title={atrTitle(row.atr_from_sma50, t)}
                  style={fill ? { background: fill.bg, color: fill.fg,
                                  padding: '1px 4px', borderRadius: '3px' } : undefined}
                  className={`shrink-0 text-[11px] font-mono font-semibold
                              ${fill ? '' : 'text-[var(--color-text-bold)]'}`} />
      {/* Moglen 2020: a true market leader is "often in the Top 20 Industry
          groups" — a flag the pipeline ships on every panel row, not a filter.
          Muted text, not a colour: one bit, and it is not about the number. */}
      {row.top20_industry && (
        <span title={t('wl2.t20.title')}
              className="shrink-0 text-[11px] font-mono text-[var(--color-text-muted)]">
          T20
        </span>
      )}
      {withTheme && (
        <i title={`${dataName(row.group, lang)} · ${word(t, `state.${row.group_state}`, row.group_state)}`}
           className="shrink-0 w-[3px] h-[3px] rounded-full translate-y-[-3px]
                      bg-[var(--color-text-secondary)]" />
      )}
      <span className={`ml-auto text-[11px] font-mono tabular-nums ${rsInk(v, rsKey)}`}
            title={alt || undefined}>
        {v ?? '—'}
      </span>
    </span>
  )
}

/**
 * The strength floor, and where it does not belong.
 *
 * Andy: hide anything under 80. On this measure 80 is 17 of 21 sessions — the
 * name's strength against SPY is in the top fifth of its own month — so the
 * floor reads "only names that are actually working right now".
 *
 * It is exempt in two zones, and the data chose which. Measured 2026-08-14 on
 * the rows the page shows:
 *
 *   leaders 83% survive · moving 95% · accumulation 78% · entries 23%
 *   compression 0% · trouble 19% (Lower Low Break 0%)
 *
 * COMPRESSION is exempt because the floor contradicts its question: that zone
 * asks who is QUIET, and a name coiling on falling volatility is by
 * construction not printing relative-strength highs, so the floor empties the
 * card. Andy named the last card; this one is worse and he had not seen it.
 *
 * TROUBLE is exempt from the other side — it asks what BROKE, and demanding
 * strength of a broken name is asking a question and refusing the answer.
 */
const RS_FLOOR = 80
const FLOOR_EXEMPT = new Set(['compression', 'trouble'])
const floorApplies = (zoneKey) => !FLOOR_EXEMPT.has(zoneKey)

/**
 * Rows a panel shows under the current view. Never changes what it counted —
 * all three switches hide rows, none of them re-screens anything.
 */
const rsOf = (r) => r?.rs_line_pctl_21 ?? r?.rs_1m ?? null

/**
 * Panels the healthcare view does not touch.
 *
 * Episodic Pivot is a REPRICING — a gap on news — and biotech is where that
 * lives; the data side built the panel without the healthcare exclusion on
 * purpose (DATA_CONTRACTS §四点七, 08-20). A global view that quietly emptied
 * it would be this page overriding the screen's own definition, which is the
 * one thing a view is not allowed to do. Same shape as the RS floor's zone
 * exemptions, and the count says so on the card.
 */
const EX_HEALTH_EXEMPT = new Set(['ep_stockbee', 'ep_qullamaggie'])   // EP split by author 2026-09-18
const exHealthApplies = (panelKey) => !EX_HEALTH_EXEMPT.has(panelKey)

export const shown = (panel, { highOnly, floor, pool3m, exHealth, zoneKey } = {}) => {
  let rows = panel.tickers || []
  if (pool3m) rows = rows.filter((r) => r.top_3m)
  if (highOnly) rows = rows.filter((r) => r.rs_high)
  // Same test the Screener's gate uses (ScreenerPage GATES.exHealth), so the
  // two pages mean the same thing by the same words. 118 of today's 348 rows
  // are Healthcare, which is why it earns a switch rather than a footnote.
  if (exHealth && exHealthApplies(panel.key)) rows = rows.filter((r) => r.sector !== 'Healthcare')
  if (floor && floorApplies(zoneKey)) rows = rows.filter((r) => (rsOf(r) ?? 0) >= RS_FLOOR)
  // Sorted by the number the reader can see, strongest first (Andy). The file
  // arrives sorted by hybrid_rs, which is a different quantity and is not on
  // screen — a list ordered by something invisible reads as unordered. A name
  // with no reading sinks rather than sorting as zero, because "not measured"
  // is not "weakest". Ties break on ticker so the order is stable across days.
  return [...rows].sort((a, b) => {
    const x = rsOf(a), y = rsOf(b)
    if (x == null && y == null) return a.ticker < b.ticker ? -1 : 1
    if (x == null) return 1
    if (y == null) return -1
    return y - x || (a.ticker < b.ticker ? -1 : 1)
  })
}

const SHORTLIST = 'shortlist'

export default function WatchlistPage({ zone: routeZone }) {
  const { t } = useLanguage()

  /* Andy 2026-10-04 (plan A): the morning brief's five steps moved to the
     Screener's step bar, so the 晨报 tab is taken down and this page is the
     six seats plus my shortlist. Old links (#/watchlist, #/watchlist/<zone>)
     land here; a zone link is rewritten to #/watchlist/shortlist without a
     reload, so a bookmark keeps working and the address says where you are. */
  useEffect(() => {
    if (routeZone && routeZone !== SHORTLIST) {
      try { window.history.replaceState(null, '', `#/watchlist/${SHORTLIST}`) } catch { /* no history */ }
    }
  }, [routeZone])

  return (
    <div className="py-6 px-1">
      <PageHeader group="market" title={t('nav.watchlist')} />
      <ShortListPage />
    </div>
  )
}
