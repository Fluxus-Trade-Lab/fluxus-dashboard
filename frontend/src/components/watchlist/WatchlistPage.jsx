import { useEffect, useMemo, useState } from 'react'
import PageHeader from '../PageHeader'
import DataFreshnessBadge from '../shared/DataFreshnessBadge'
import TickerLink from '../ticker/TickerLink'
import { useLanguage } from '../../i18n/LanguageContext'
import { useWatchlist } from '../../hooks/useWatchlist'
import ShortlistTray from '../shared/ShortlistTray'
import ShortListPage from './shortlist/ShortListPage'

/**
 * Today's list — six questions, already asked.
 *
 * WHY THIS IS NOT THE SCREENER. The Screener is a posture: a table, my filters,
 * my sort, and I go looking. This is the opposite posture — the questions were
 * asked overnight and what is here is the answer. You do not tune it; you read
 * it and take names away. Two postures, so two formats: rows and columns there,
 * question → recipe → names here.
 *
 * WHY CARDS RATHER THAN ONE LONG PAGE. The first build printed every panel in
 * full: 362 names, 2,786px, and the sixth question three screens below the
 * first. But a morning read is a CHOICE — which of six questions matters today
 * — and a page that makes you scroll past five answers to reach the sixth has
 * already made that choice for you. So the landing is six cards, one screen,
 * each showing what its question found and a taste of the names; the full lists
 * live behind the card at #/watchlist/<zone>. Same drill-down the Review page
 * uses, for the same reason.
 *
 * THREE THINGS THE PAGE MUST NOT DO, all of which the data makes possible:
 *
 *   1. A panel with `measured: false` reads NOT MEASURED, never zero. Drawing
 *      an unrun panel as "0 today" reports an absence of measurement as a
 *      measurement of absence.
 *   2. A truncated panel says what it truncated — 25 of 372. A silent cap reads
 *      as "this is all of them".
 *   3. The cross-zone block is described, not ranked. A name on four lists is
 *      on four lists; whether that makes it work more often is not something
 *      anyone has measured, and the wording stays that literal.
 */

const ZONE_ORDER = ['leaders', 'entries', 'compression', 'accumulation', 'moving', 'trouble']

/**
 * Questions this page does not ask.
 *
 * Andy, 2026-08-18: take the "What broke?" question card and its scans off,
 * with or without answers. The whole zone goes, not the empty cards in it —
 * Stop Hit and Lower Low Break are the two he pointed at, and Extended leaves
 * with them because an answer whose question has been retired has no place to
 * stand. The pipeline keeps computing all three; this is the page declining to
 * ask, which is a display decision and reversible by deleting one line.
 */
/**
 * 2026-08-19: nothing is hidden any more. The "What broke?" zone came off the
 * page on 08-18 because it was a question Andy did not want asked; the 08-19
 * step order asks it as the LAST step, and its three panels — Stop Hit, Lower
 * Low Break, Extended — are the only ones that answer 位置 and 出场. Andy's
 * call to put them back. The zone lens is gone with the question chips, so
 * they arrive as panels under the steps rather than as a sixth question.
 */
const HIDDEN_ZONES = new Set()

/**
 * The five steps (DATA_CONTRACTS §八, Andy 2026-08-19, off the scanner
 * validation report's §3).
 *
 * The premise: seventeen panels are not seventeen buy tickets, they are one
 * name read at different stages. So the page carries the order — water, then
 * footprint, then position, then the entry knife, then the exit — and picking
 * a step LIGHTS its panels while dimming the rest. Dimming, never hiding: the
 * other sixteen answers are still true, they are just not this step's.
 *
 * `wants` is what the step calls for in the report's words; `panels` is what
 * this file can actually point at today. Where those differ the step SAYS SO
 * rather than quietly covering less ground than it claims — three of the
 * report's instruments have no panel at all (ATR Matrix ≤4, 第一波, EP), and
 * the exit step's three were taken off the page by Andy on 08-18 when the
 * "What broke?" question was retired. Neither gets papered over here.
 */
const STEPS = [
  {
    key: 'water', label: '水域',
    find: '只在 Leading / Improving 的主题里找票',
    with: '顶部池子切到「3M 领先」；哪些主题在 Leading 去 Themes 页看',
    dont: '不在这些主题里的票，后面四步都不做',
    wants: ['主题四态', '池子开关'], panels: [], switches: ['pool3m'],
  },
  {
    key: 'footprint', label: '脚印',
    find: '同一天 20 日新高 + RS 线新高的票 —— 起涨最早最广的确认',
    with: '开「只看 RS 新高」；三格本身只说「今天在动」，加这个开关才是「在领先地动」',
    dont: '当日涨幅 ≥15% 的 4% 日不追（−9.3%、胜率 36%）',
    switches: ['highOnly'],
    wants: ['Weekly 20%+', '4% Bullish', 'PP 三格'],
    panels: ['weekly_20_gainers', 'bullish_4pct', 'pp_today', 'pp_2plus_10d', 'morales_pp_10d'],
  },
  {
    key: 'position', label: '位置',
    find: '离 50 日线几个 ATR：0–4 建仓区，5–7 持有，≥7 只减不买',
    with: '票旁的 ATR 位数字',
    dont: 'ATR 4–5 时 momentum 与 4% 密集亮起，20 日后 −17～−38% —— 那不是买点是顶',
    wants: ['ATR Matrix ≤4', 'Extended ≥7'], panels: ['extended'],
  },
  {
    key: 'entry', label: '入场',
    find: '第一波（4% × ATR≤4 × 新高 × RS 新高）precision 48%、EP 61%，基线 41%',
    with: '回踩用 Liquid Leader Pullback —— 只在第 1 步的水域里做',
    dont: 'EP 第一天不进：42% 会击穿 EP 日低点。第 3 个交易日起进 Delayed-EP 观察',
    wants: ['第一波', 'EP', 'Liquid Leader Pullback'],
    panels: ['episodic_pivot', 'liquid_leader_pullback',
             'll_hl_1st', 'll_hl_2nd', 'll_hl_trend_break'],
  },
  {
    key: 'exit', label: '出场',
    find: 'Structure Pivot 给的 21EMA Low 是止损；stop_hit / ll_break 亮 = 走',
    with: 'Extended ≥7 亮 = 开始减',
    dont: 'Structure Pivot 的入场信号在领头股上并不比 20 日新高早 —— 它值钱的是止损位',
    wants: ['Structure Pivot', 'Extended'], panels: ['stop_hit', 'll_break', 'extended'],
  },
]
const DEFAULT_STEP = 'footprint'

const nf = (n) => n.toLocaleString()

/** Translate by key, fall back to whatever the file called it. */
const tr = (t, key, fallback) => {
  const out = t(key)
  return out === key ? fallback : out
}

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
export const gateWords = (gate = {}) => {
  const out = []
  if (gate.min_market_cap) out.push(`$${(gate.min_market_cap / 1e9).toFixed(0)}B cap`)
  if (gate.min_dollar_volume) out.push(`$${(gate.min_dollar_volume / 1e6).toFixed(0)}M/day traded`)
  else if (gate.min_avg_volume) out.push(`${(gate.min_avg_volume / 1e6).toFixed(0)}M shares/day`)
  if (gate.min_adr_pct) {
    /* The exemption is named because the overview shows the exempt zone's
       panels on the same screen. An unqualified "ADR >= 3.5%" would claim a
       floor that visibly does not hold for the trouble rows two inches below:
       an exit signal does not stop mattering because the name went quiet. */
    const exempt = gate.adr_exempt_zones || []
    const skip = exempt.length ? ` except ${exempt.join('/')}` : ''
    out.push(`ADR ≥ ${gate.min_adr_pct}%${skip}`)
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
 * (True Market Leaders needs >= 80, the momentum panels are percentile cuts),
 * so printing rs_1m beside those rows repeats the entry condition, while the
 * 21-day reading adds something the membership did not already say.
 *
 * Whichever is drawn, the legend names it — the label is derived from the same
 * pick, so the page cannot print one number under the other one's name. Until
 * the new column ships this falls back to rs_1m and says rs_1m.
 */
export const pickRs = (rows = []) =>
  (rows.some((r) => r?.rs_line_pctl_21 != null) ? 'rs_line_pctl_21' : 'rs_1m')

const go = (zone) => { window.location.hash = zone ? `#/watchlist/${zone}` : '#/watchlist' }

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

const atrTitle = (v) => v == null || !Number.isFinite(v)
  ? 'ATR 位未测量'
  : v < 0 ? `${v.toFixed(1)} ATR — 在 50 日线下方，不在扩张刻度上`
  : v <= 4 ? `${v.toFixed(1)} ATR — 0–4 建仓区`
  : v <= 7 ? `${v.toFixed(1)} ATR — 5–7 持有，不加`
  : `${v.toFixed(1)} ATR — ≥7 只减不买`


function Name({ row, rsKey = 'rs_1m' }) {
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
                  title={atrTitle(row.atr_from_sma50)}
                  style={fill ? { background: fill.bg, color: fill.fg,
                                  padding: '1px 4px', borderRadius: '3px' } : undefined}
                  className={`shrink-0 text-[11.5px] font-mono font-semibold
                              ${fill ? '' : 'text-[var(--color-text-bold)]'}`} />
      {withTheme && (
        <i title={`${row.group} · ${row.group_state}`}
           className="shrink-0 w-[3px] h-[3px] rounded-full translate-y-[-3px]
                      bg-[var(--color-text-secondary)]" />
      )}
      <span className={`ml-auto text-[10.5px] font-mono tabular-nums ${rsInk(v, rsKey)}`}
            title={alt || undefined}>
        {v ?? '—'}
      </span>
    </span>
  )
}

/**
 * A field of names on a column grid.
 *
 * Ruled by ROW, not by column. Vertical rules have to know how many columns
 * there are, and the count changes at every breakpoint — the first version
 * pinned its nth-child rules to four and drew them in the wrong places as soon
 * as the grid went to six. A horizontal hairline is column-count-independent
 * and reads as a table either way.
 */
function Names({ rows, wide = false, rsKey }) {
  return (
    <span className={`grid ${wide
      ? 'grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 2xl:grid-cols-8'
      : 'grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4'}
      [&>*]:border-b [&>*]:border-[var(--color-border-light)]`}>
      {rows.map((r) => <Name key={r.ticker} row={r} rsKey={rsKey} />)}
    </span>
  )
}

/**
 * One switch, three uses — pool, RS highs, strength floor.
 *
 * They are three views of one file and none of them re-screens anything, so
 * they get one form and sit in one row. Three differently-shaped controls would
 * imply three different kinds of thing.
 */
function Switch({ on, set, label, note, cued }) {
  return (
    <button type="button" onClick={() => set(!on)}
            /* `cued` is the current step pointing at this control. Step 1 owns
               the pool and step 2 owns the RS-high switch — without the cue
               those steps would light nothing at all and read as broken, when
               in fact the thing they operate is a switch rather than a card. */
            className={`flex items-center gap-2 bg-transparent border-none cursor-pointer
                        text-[11px] whitespace-nowrap rounded
                        ${cued ? 'ring-1 ring-[var(--color-accent)] px-1.5 py-0.5 -mx-1.5' : 'p-0'}
                        ${on ? 'text-[var(--color-text)]' : 'text-[var(--color-text-muted)]'}`}>
      <i className={`w-7 h-[15px] rounded-full relative transition-colors shrink-0 ${on
        ? 'bg-[var(--color-accent-solid)]' : 'bg-[var(--color-hover-bg)]'}`}>
        <i className={`absolute top-[2px] w-[11px] h-[11px] rounded-full bg-white
                       transition-all ${on ? 'left-[14px]' : 'left-[2px]'}`} />
      </i>
      {label}
      {note && <span className="text-[var(--color-text-muted)] opacity-70">{note}</span>}
    </button>
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
const EX_HEALTH_EXEMPT = new Set(['episodic_pivot'])
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

/** The count, or the reason there isn't one. */
/**
 * The count — and, when the file knows it, how many of those are at a 21-day
 * RS high. Both numbers, always, so switching the view never hides a quantity:
 * the panel counted what it counted whichever rows are on screen.
 */
function Count({ panel, view = {}, zoneKey }) {
  const { t } = useLanguage()
  if (!panel.measured) {
    return <span className="text-[10px] font-mono uppercase tracking-[.12em]
                            text-[var(--color-text-muted)]">{t('wl.unmeasured')}</span>
  }
  const n = shown(panel, { ...view, zoneKey }).length
  const anyView = view.highOnly || view.pool3m || view.exHealth
    || (view.floor && floorApplies(zoneKey))
  return (
    <span className="text-[11px] font-mono tabular-nums whitespace-nowrap"
          title={[
            view.floor && !floorApplies(zoneKey) ? t('wl.floor.exempt') : null,
            // a view that skips a panel has to admit it, or the count silently
            // means something different here than on the card beside it
            view.exHealth && !exHealthApplies(panel.key)
              ? 'the healthcare view does not apply to this scan — an EP is a repricing and biotech is where those happen'
              : null,
          ].filter(Boolean).join(' · ') || undefined}>
      {/* Both numbers, always. The views hide rows; the panel still counted
          what it counted, and a page that shows only the survivors of its own
          filters cannot tell you how much it is holding back. */}
      {anyView && (
        <span className="text-[var(--color-took)] font-semibold">
          {nf(n)}<span className="opacity-50 font-normal">/</span>
        </span>
      )}
      <span className="text-[var(--color-text-secondary)]">{nf(panel.count)}</span>
    </span>
  )
}

/* ── Landing: five steps, every scan on the table ────────────────────────── */


/** One scan, with its names on the table. */
/**
 * A scan, open or quiet.
 *
 * Dimming the scans a step does not use was the first answer and it was not
 * enough: eighteen cards of names at 40% opacity is still eighteen cards of
 * names, and Andy's word for the result was 太杂乱. A quiet scan keeps its
 * title and its count — so nothing is hidden and every number is still on the
 * page — and gives up its names until you ask. One click opens it without
 * leaving the step.
 *
 * Quiet, not hidden, because the contract is explicit about it and because a
 * scan that vanished when it was not this step's would make the page look like
 * it found nothing on the questions you are not asking right now.
 */
function ScanCard({ panel, zoneKey, view, rsKey, quiet = false }) {
  const { t } = useLanguage()
  const [openRecipe, setOpenRecipe] = useState(false)
  const [opened, setOpened] = useState(false)
  const rows = shown(panel, { ...view, zoneKey })
  const exempt = view.floor && !floorApplies(zoneKey)

  if (quiet && !opened) {
    return (
      <button type="button" onClick={() => setOpened(true)} aria-expanded="false"
              className="w-full flex items-baseline gap-2 text-left px-3 py-[7px]
                         rounded-xl border border-[var(--color-border-light)]
                         bg-transparent cursor-pointer
                         hover:bg-[var(--color-surface)] transition-colors">
        <span className="text-[10px] font-mono text-[var(--color-text-muted)] shrink-0">+</span>
        <span className="min-w-0 flex-1 truncate text-[12px] text-[var(--color-text-secondary)]">
          {tr(t, `wlp.${panel.key}`, panel.label)}
        </span>
        <span className="shrink-0"><Count panel={panel} view={view} zoneKey={zoneKey} /></span>
      </button>
    )
  }

  return (
    <div className="flex flex-col rounded-xl overflow-hidden border
                    border-[var(--color-border-light)] bg-[var(--color-surface)]">
      <div className="flex items-baseline gap-2 px-3 py-2 border-b border-[var(--color-border-light)]">
        {/* A scan you opened by hand can be shut by hand. It was one-way for a
            revision — once open it stayed open for the rest of the session,
            and a control that only goes one direction is not a control. Only
            the quiet ones carry it; a scan the current step lights has no
            business being closable, it is what you asked to see. */}
        {quiet ? (
          <button type="button" onClick={() => setOpened(false)}
                  aria-expanded="true"
                  className="flex items-baseline gap-2 min-w-0 bg-transparent border-none p-0
                             cursor-pointer text-left font-inherit">
            <span className="text-[10px] font-mono text-[var(--color-text-muted)] shrink-0">−</span>
            <b className="text-[12.5px] font-semibold leading-tight
                          text-[var(--color-text-bold)]">
              {tr(t, `wlp.${panel.key}`, panel.label)}
            </b>
          </button>
        ) : (
          <b className="text-[12.5px] font-semibold leading-tight">
            {tr(t, `wlp.${panel.key}`, panel.label)}
          </b>
        )}
        <span className="ml-auto shrink-0">
          <Count panel={panel} view={view} zoneKey={zoneKey} />
        </span>
        <button type="button" onClick={() => setOpenRecipe(!openRecipe)}
                className="shrink-0 text-[10px] font-mono bg-transparent border-none p-0
                           cursor-pointer text-[var(--color-text-muted)]
                           hover:text-[var(--color-text)]">
          {openRecipe ? '−' : t('wl.recipe')}
        </button>
      </div>

      {openRecipe && (
        <p className="text-[10.5px] font-mono text-[var(--color-text-muted)] m-0 px-3 py-2
                      border-b border-[var(--color-border-light)]">{panel.recipe}</p>
      )}

      {rows.length > 0 ? (
        /* CHASERS TO THE BOTTOM, NOT OUT (DATA_CONTRACTS §八.4). A 4% day that
           is already up 15% on the session backtested at −9.3% over 20 days
           with a 36% win rate — so it is a warning, and a warning you delete is
           a warning nobody reads. The names stay, in their own greyed block
           under a stated rule. Splitting only bites where the field exists;
           everywhere else `chase` is undefined and this is one list, as now. */
        (() => {
          const chase = rows.filter((r) => r.chase)
          const rest = rows.filter((r) => !r.chase)
          if (!chase.length) return <Names rows={rows} rsKey={rsKey} />
          return (
            <>
              <Names rows={rest} rsKey={rsKey} />
              <p className="m-0 px-3 pt-2 pb-1 text-[10px] font-mono uppercase tracking-[.14em]
                            text-[var(--color-text-muted)]">
                {chase.length} 当日 ≥15% &mdash; 不追
              </p>
              <span className="opacity-45">
                <Names rows={chase} rsKey={rsKey} />
              </span>
            </>
          )
        })()
      ) : (
        <p className="text-[11px] text-[var(--color-text-muted)] m-0 px-3 py-3">
          {!panel.measured ? t('wl.pending')
            : exempt ? t('wl.none') : t('wl.none.floor')}
        </p>
      )}

      {rows.length > 0 && (
        <button type="button"
                onClick={() => navigator.clipboard?.writeText(
                  rows.map((r) => r.ticker).join(',')).catch(() => {})}
                className="mt-auto text-left px-3 py-1.5 text-[10px] font-mono uppercase
                           tracking-[.14em] bg-transparent border-none cursor-pointer
                           text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
          {t('wl.copy')} {rows.length}
        </button>
      )}
    </div>
  )
}

/* ── Detail: one question, every name ────────────────────────────────────── */

function Panel({ panel, explainPending, rsKey, view, zoneKey }) {
  const { t } = useLanguage()
  const [openRecipe, setOpenRecipe] = useState(false)
  const rows = shown(panel, { ...view, zoneKey })

  return (
    <div className="py-3 border-t border-[var(--color-border-light)] first:border-t-0">
      <div className="flex items-baseline gap-2.5 mb-1.5">
        {/* The file's label is English. A key we know gets the reader's
            language; one we do not gets the file's own words, so a panel the
            pipeline adds tomorrow shows up rather than disappearing. */}
        <b className="text-[13px] font-semibold">{tr(t, `wlp.${panel.key}`, panel.label)}</b>

        {panel.measured ? (
          <span className="text-[11px] font-mono tabular-nums text-[var(--color-text-secondary)]">
            {panel.truncated > 0
              ? t('wl.showing', { shown: rows.length, total: nf(panel.count) })
              : nf(panel.count)}
          </span>
        ) : <Count panel={panel} view={view} zoneKey={zoneKey} />}

        {rows.length > 0 && (
          <button type="button"
                  onClick={() => navigator.clipboard?.writeText(
                    rows.map((r) => r.ticker).join(',')).catch(() => {})}
                  className="text-[10px] font-mono uppercase tracking-[.14em] bg-transparent
                             border-none p-0 cursor-pointer text-[var(--color-text-muted)]
                             hover:text-[var(--color-text)]">
            {t('wl.copy')}
          </button>
        )}

        <button type="button" onClick={() => setOpenRecipe(!openRecipe)}
                className="ml-auto text-[10px] font-mono bg-transparent border-none p-0
                           cursor-pointer text-[var(--color-text-muted)]
                           hover:text-[var(--color-text)]">
          {t('wl.recipe')} {openRecipe ? '−' : '+'}
        </button>
      </div>

      {/* The rule that produced the list, in the pipeline's own words. A list
          you cannot audit is a list you have to take on faith. */}
      {openRecipe && (
        <p className="text-[11px] font-mono text-[var(--color-text-muted)] mb-2 max-w-[80ch]
                      border-l-2 border-[var(--color-border)] pl-3">
          {panel.recipe}
        </p>
      )}

      {rows.length > 0 ? (
        <div className="-mx-1">
          <Names rows={rows} wide rsKey={rsKey} />
        </div>
      ) : panel.measured ? (
        <p className="text-[11.5px] text-[var(--color-text-muted)] m-0">{t('wl.none')}</p>
      ) : explainPending ? (
        <p className="text-[11.5px] text-[var(--color-text-muted)] m-0">{t('wl.pending')}</p>
      ) : null}
    </div>
  )
}

function ZoneDetail({ zone, index, total, view }) {
  const { t } = useLanguage()
  const rsKey = pickRs(zone.panels.flatMap((p) => p.tickers || []))
  const live = zone.panels.filter((p) => p.measured).length
  // One fact, said once: when the whole question is waiting, the question says
  // so; in a mixed question the first waiting panel carries it.
  const allPending = live === 0
  const firstPending = zone.panels.find((p) => !p.measured)?.key

  return (
    <div className="py-6 px-1">
      <button type="button" onClick={() => go(null)}
              className="text-[11px] font-mono text-[var(--color-text-muted)] bg-transparent
                         border-none p-0 cursor-pointer hover:text-[var(--color-text)]">
        ‹ {t('nav.watchlist')}
      </button>
      <div className="flex items-baseline gap-3 mt-1 mb-4">
        <span className="text-[13px] font-mono tabular-nums text-[var(--color-text-muted)]">
          {String(index + 1).padStart(2, '0')}
        </span>
        <h1 className="text-[30px] font-bold leading-tight m-0">
          {tr(t, `wlz.${zone.key}`, zone.label)}
        </h1>
        <span className="ml-auto text-[10px] font-mono uppercase tracking-[.16em]
                         text-[var(--color-text-muted)]">{index + 1} / {total}</span>
      </div>

      {allPending && (
        <p className="text-[11.5px] text-[var(--color-text-muted)] mb-3 max-w-[70ch]">
          {t('wl.pending')}
        </p>
      )}

      <p className="text-[11px] text-[var(--color-text-muted)] mb-3">
        {t(`wl.rskey.${rsKey}`)}
      </p>
      <div className="rounded-3xl bg-[var(--color-surface)] px-4 py-1">
        {zone.panels.map((p) => (
          <Panel key={p.key} panel={p} rsKey={rsKey} view={view} zoneKey={zone.key}
                 explainPending={!allPending && p.key === firstPending} />
        ))}
      </div>
    </div>
  )
}

/* ── Page ────────────────────────────────────────────────────────────────── */

/**
 * The step bar. One row of five words, the chosen one carrying its three lines.
 *
 * The three lines are the report's own, not a rewrite: what this step looks
 * for, what it is used with, and the way it is misread. The third line is the
 * one worth the ink — every step in the source has a documented way of going
 * wrong, and a beginner's page that prints the method without the trap is
 * teaching half of it.
 */
function StepBar({ step, onStep, missing, counts }) {
  const cur = STEPS.find((s) => s.key === step) ?? STEPS[0]
  return (
    <div className="mb-4">
      <div className="flex flex-wrap items-center gap-x-1 gap-y-1">
        {STEPS.map((s, i) => (
          <span key={s.key} className="flex items-center gap-1">
            {i > 0 && <i aria-hidden className="text-[10px] text-[var(--color-text-muted)]">&rarr;</i>}
            <button type="button" onClick={() => onStep(s.key)} aria-pressed={s.key === step}
                    className={`px-2 py-[3px] text-[12.5px] bg-transparent border-none cursor-pointer
                                border-b-2 border-solid transition-colors
                                ${s.key === step
                                  ? 'text-[var(--color-text-bold)] font-semibold border-[var(--color-accent)]'
                                  : 'text-[var(--color-text-muted)] border-transparent hover:text-[var(--color-text)]'}`}>
              {i + 1} {s.label}
              {/* what the chips used to carry: how much is behind each step,
                  before you point at it. Muted, and always both numbers —
                  scans lit and names in them. */}
              {counts?.[s.key] != null && (
                <span className="ml-1 text-[10px] font-mono tabular-nums opacity-70">
                  {counts[s.key]}
                </span>
              )}
            </button>
          </span>
        ))}
      </div>

      {/* three lines, and only for the step you are on */}
      <div className="mt-2 pl-3 border-l-2 border-[var(--color-accent)] max-w-[104ch]">
        <p className="m-0 text-[14px] leading-snug text-[var(--color-text)]">{cur.find}</p>
        <p className="m-0 text-[11px] leading-relaxed text-[var(--color-text-secondary)]">{cur.with}</p>
        <p className="m-0 text-[11px] leading-relaxed text-[var(--color-text-muted)]">
          <b className="text-[var(--color-text-secondary)]">别这么用：</b>{cur.dont}
        </p>
        {/* what this step calls for and cannot point at. A step quietly
            covering less than it claims is the failure this page is built
            against. */}
        {/* What the step calls for and cannot point at — and WHY, per item.
            The blanket sentence that used to sit here blamed the 08-18 removal
            of the "What broke?" zone; those panels came back on 08-19, so the
            only thing that sentence still explained was itself. */}
        {missing.length > 0 && (
          <p className="m-0 mt-1 text-[11px] leading-relaxed text-[var(--color-text-muted)]">
            {missing.map((m) => (
              <span key={m} className="mr-3">
                <b className="text-[var(--color-text-secondary)]">{m}</b>
                {m === 'ATR Matrix ≤4'
                  ? ' 不是一格 — 它是每个名字旁边那个 ATR 位数字'
                  : ' 管线没有单独出这一格'}
              </span>
            ))}
          </p>
        )}
      </div>
    </div>
  )
}

const MORNING = null
const SHORTLIST = 'shortlist'

/** The two tabs. Underline, not a pill: this is a place in the page, not a
 *  state of the data, and the page's chrome does not get to look like a
 *  reading. */
function Tabs({ active }) {
  const items = [[MORNING, '晨报'], [SHORTLIST, 'Short List']]
  return (
    <div className="flex items-baseline gap-6 mt-1 mb-4
                    border-b border-[var(--color-border-light)]">
      {items.map(([key, label]) => {
        const on = active === key
        return (
          <button key={label} type="button" onClick={() => go(key)}
                  className={`bg-transparent border-0 p-0 pb-2 -mb-px cursor-pointer
                              text-[13px] font-mono uppercase tracking-[.16em]
                              border-b-2 transition-colors ${on
                    ? 'text-[var(--color-text-bold)] border-[var(--color-text-bold)]'
                    : 'text-[var(--color-text-muted)] border-transparent hover:text-[var(--color-text)]'}`}>
            {label}
          </button>
        )
      })}
    </div>
  )
}

export default function WatchlistPage({ zone: routeZone }) {
  const { t } = useLanguage()
  const { data, failed } = useWatchlist()
  /**
   * "RS highs only" — a view, never a screen.
   *
   * Andy's ruling on rs_high was detect, do not filter: no panel's membership
   * changes because of it. So this hides rows rather than re-running anything,
   * every count stays the count of the full panel, and the header prints both
   * numbers so what is hidden is always visible as a quantity.
   *
   * Default off. A page that opens already filtered is a page that has made a
   * decision on your behalf before you have looked.
   */
  /* All four views open by default (Andy 2026-08-19). The page used to arrive
     showing everything and let you narrow; it arrives narrowed now, which is
     the posture the five steps assume — you are walking an order, not browsing
     a file. Every switch is still a VIEW: it hides rows, never re-screens, and
     every count on the page stays the count of the full panel. */
  const [highOnly, setHighOnly] = useState(true)
  const [pool3m, setPool3m] = useState(true)
  const [exHealth, setExHealth] = useState(true)
  // Andy asked for the floor as a rule, not an option, so it opens on. The
  // switch stays because every count on the page is of the FULL panel and he
  // must be able to see what the floor is holding back.
  const [floor, setFloor] = useState(true)
  // The step (DATA_CONTRACTS §八). Opens on 脚印, which is where the report
  // says a morning actually starts once the water is chosen.
  const [step, setStep] = useState(DEFAULT_STEP)

  const zones = useMemo(() => {
    if (!data?.zones) return []
    const byKey = new Map(data.zones.map((z) => [z.key, z]))
    // Declared order, then anything the pipeline adds later — a new zone should
    // appear rather than vanish because this file had not heard of it.
    const known = ZONE_ORDER.map((k) => byKey.get(k)).filter(Boolean)
    const extra = data.zones.filter((z) => !ZONE_ORDER.includes(z.key))
    return [...known, ...extra].filter((z) => !HIDDEN_ZONES.has(z.key))
  }, [data])

  if (failed) {
    return (
      <div className="py-6 px-1">
        <PageHeader group="market" title={t('nav.watchlist')} />
        <p className="text-[13px] text-[var(--color-text-muted)]">{t('wl.nofile')}</p>
      </div>
    )
  }
  if (!data) return null

  /**
   * Two tabs over one page, and only one of them alive at a time.
   *
   * Andy asked for a tab inside Today's List rather than a page of its own, so
   * it is a tab. It rides the sub-route this page already had for its zone
   * drill-downs (`#/watchlist/<zone>`), which means `#/watchlist/shortlist`
   * costs nothing and still survives a reload and can be linked to.
   *
   * The tab swaps the WHOLE body — the five-step bar does not exist inside the
   * Short List. Two selectors stacked over one set of objects is the thing the
   * design charter refuses, and this is how it stays refused: they are never
   * both on screen.
   */
  if (routeZone === SHORTLIST) {
    return (
      <div className="py-6 px-1">
        <PageHeader group="market" title={t('nav.watchlist')} />
        <Tabs active={SHORTLIST} />
        <ShortListPage />
      </div>
    )
  }

  const at = zones.findIndex((z) => z.key === routeZone)
  if (at >= 0) {
    return (
      <ZoneDetail zone={zones[at]} index={at} total={zones.length} view={view} />
    )
  }

  const cross = data.cross_zone || []
  const view = { highOnly, floor, pool3m, exHealth }

  /**
   * Which panels this step lights, and what it asked for and did not get.
   *
   * `wants` is the report's vocabulary and `panels` is ours; the gap is
   * computed rather than written down, so a panel arriving (or being taken
   * off) changes the sentence instead of leaving it wrong.
   */
  const curStep = STEPS.find((s) => s.key === step) ?? STEPS[0]
  const onPage = new Set(zones.flatMap((z) => z.panels.map((p) => p.key)))
  const lit = new Set(curStep.panels.filter((k) => onPage.has(k)))
  const missingSteps = curStep.panels.filter((k) => !onPage.has(k))
  // the report's names for instruments that have no panel here at all
  const NAMED = { extended: 'Extended', stop_hit: 'Stop Hit', ll_break: 'Lower Low Break',
                  episodic_pivot: 'EP' }
  /** names behind each step, under the current view — the chips' number, kept */
  const stepCounts = Object.fromEntries(STEPS.map((st) => {
    const keys = new Set(st.panels)
    const n = zones.flatMap((z) => z.panels
      .filter((p) => keys.has(p.key) && p.measured)
      .map((p) => shown(p, { ...view, zoneKey: z.key }).length))
      .reduce((a, b) => a + b, 0)
    return [st.key, st.panels.length ? n : null]
  }))

  const missing = [
    ...curStep.wants.filter((w) => ['ATR Matrix ≤4', '第一波'].includes(w)),
    ...missingSteps.map((k) => NAMED[k] ?? k),
  ]

  // Which scans are on the table, and which the current view emptied. A panel
  // that has not run is neither — it stays, and says so.
  const all = zones.flatMap((z) => z.panels.map((panel) => ({ zone: z, panel })))
  const isEmptied = ({ zone, panel }) =>
    panel.measured && shown(panel, { ...view, zoneKey: zone.key }).length === 0
  const visible = all.filter((x) => !isEmptied(x))
  const emptied = all.filter(isEmptied)
  const rule = data.cross_zone_rule

  return (
    <div className="py-6 px-1">
      <PageHeader group="market" title={t('nav.watchlist')}
                  meta={[<DataFreshnessBadge key="fresh" sessionDate={data.date} />]} />
      <Tabs active={MORNING} />

      {/* Provenance first: which close this is, and how many names were even
          eligible. A list without its universe is a list you cannot size up. */}
      <div className="flex items-baseline gap-4 flex-wrap mt-1 mb-5">
      <p className="text-[12px] font-mono text-[var(--color-text-muted)] m-0">
        {t('wl.provenance', {
          date: data.date,
          n: nf(tradeableCount(data)),
          gate: gateWords(data.gate),
        })}
      </p>
      <Switch on={pool3m} set={setPool3m} label={t('wl.pool3m')}
              cued={curStep.switches?.includes('pool3m')} />
      <Switch on={highOnly} set={setHighOnly} label={t('wl.highOnly')}
              cued={curStep.switches?.includes('highOnly')} />
      <Switch on={floor} set={setFloor} label={t('wl.floor', { n: RS_FLOOR })}
              note={t('wl.floor.note')} />
      <Switch on={exHealth} set={setExHealth} label="exclude healthcare" />
      </div>

      {/* The five steps: the order a name is read in, not five more filters. */}
      <StepBar step={step} onStep={setStep} missing={missing} counts={stepCounts} />

      {/* THE SIX QUESTION CHIPS ARE GONE (Andy 2026-08-19: 页面 UI 太杂乱).
          They were a second lens over the same scans — unordered, and asking
          the reader which of two rows to point at before either had done
          anything. The five steps are the ordered model and they subsume the
          job; what the chips carried that nothing else did was a per-question
          count, and the step bar carries a count of what it lights instead. */}

      {/* No chart on this page (Andy, 2026-08-18: 暂时也不一定需要). The
          Screener is where a name gets looked at; this page is where the six
          questions are read, and seventeen scans do not need a chart parked
          beside them to be read.

          The shortlist stays, and keeps the right-hand column to itself. It is
          the page's OUTPUT and it belongs in sight while you scan — carrying
          it to the bottom of twelve cards would make it a footnote. Names are
          added to it from the Screener's chart card; here you can see it,
          prune it and take it away. */}
      <div className="flex flex-col xl:grid xl:grid-cols-[minmax(0,1fr)_320px]
                      xl:gap-x-4 xl:items-start">
        <div className="min-w-0 order-2 xl:order-none">

      {/* Every scan on the table. The lens narrows which ones, never what any
          of them counted.
          A scan the current view has emptied is taken off the table rather
          than left as a card saying nothing (Andy) — but never silently: the
          line underneath counts them, and the question chips keep reporting
          the true totals, so an emptied scan is still on screen as a number.
          A scan that has not RUN is a different state and stays, because
          "not measured" is not "found none". */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3
                      items-start">
        {visible.map(({ zone, panel }) => (
          /* `step` in the key: changing step remounts the scans, which returns
             anything opened by hand to the state the new step puts it in. A
             card left open from two steps ago is clutter the reader did not
             ask for twice. */
          <ScanCard key={`${step}/${zone.key}/${panel.key}`} panel={panel} zoneKey={zone.key}
                    view={view} rsKey={pickRs(panel.tickers || [])}
                    quiet={!lit.has(panel.key)} />
        ))}
      </div>
      {emptied.length > 0 && (
        <p className="text-[11px] text-[var(--color-text-muted)] mt-2.5">
          {t('wl.emptied', { n: emptied.length })}{' '}
          <span className="font-mono opacity-80">
            {emptied.map((e) => tr(t, `wlp.${e.panel.key}`, e.panel.label)).join(' · ')}
          </span>
        </p>
      )}

        </div>
        <div className="min-w-0 order-1 xl:order-none mb-4 xl:mb-0 xl:sticky xl:top-3">
          <ShortlistTray />
        </div>
      </div>

      {/* Names that answer more than one question. Described, not ranked, and
          below the questions rather than above them — it is a by-product of the
          six answers, not a seventh answer. */}
      {cross.length > 0 && (
        <details className="mt-6">
          <summary className="text-[11px] font-mono uppercase tracking-[.18em]
                              text-[var(--color-text-muted)] cursor-pointer list-none
                              hover:text-[var(--color-text)]">
            {t('wl.cross')} · {cross.length} +
          </summary>
          <div className="rounded-3xl bg-[var(--color-surface)] px-4 py-3.5 mt-2">
            <div className="leading-relaxed mb-2">
              {cross.map((c) => (
                <span key={c.ticker} className="inline-flex items-baseline gap-1 mr-3 mb-1">
                  <TickerLink symbol={c.ticker}
                              className="text-[12px] font-mono font-semibold
                                         text-[var(--color-text-bold)]" />
                  <span className="text-[10px] font-mono tabular-nums
                                   text-[var(--color-text-muted)]">×{c.count}</span>
                </span>
              ))}
            </div>
            <p className="text-[11.5px] text-[var(--color-text-muted)] m-0 max-w-[70ch]">
              {t('wl.cross.legend')}
            </p>
            {/* The threshold is the file's to state, not this page's to
                remember: it moved from 2 zones to 3 on 2026-08-17 and a page
                carrying its own copy of the number would now be lying. */}
            {rule && (
              <p className="text-[10.5px] font-mono text-[var(--color-text-muted)] mt-1.5 m-0">
                {rule}
              </p>
            )}
          </div>
        </details>
      )}

      {/* Three hundred numbers sat beside three hundred tickers with nothing
          on the page saying what they were. The label is derived from the same
          pick that draws them, so the two cannot drift apart. */}
      <p className="text-[11px] text-[var(--color-text-muted)] mt-5 max-w-[72ch]">
        {t(`wl.rskey.${pickRs(zones.flatMap((z) => z.panels.flatMap((p) => p.tickers || [])))}`)}
        {' '}{t('wl.dot')}{' '}{t('wl.foot')}
      </p>
    </div>
  )
}
