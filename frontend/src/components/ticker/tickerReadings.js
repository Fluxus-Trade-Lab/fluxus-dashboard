/**
 * The readings on this page, and which file they actually come from.
 *
 * The ticker page loads two sources and has never said which is which:
 *
 *   universe.json        every name, rebuilt nightly, `bar_date` on each row
 *   tickers/<T>.json     one file per name, fetched separately
 *
 * On 2026-08-20 the second one was dead for half the site: 92 of 185 files
 * carried `ohlc_2y: []`, `info: {}`, `technicals: {}` — and every one of the 88
 * files fetched that day came back that way, news intact and price gone. The
 * 93 that still held prices had last succeeded on 08-08/08-09, eleven days
 * back. So MRNA's page printed a price in the header off universe.json and
 * fifteen rows of "—" underneath off the dead file, with nothing saying they
 * were different places.
 *
 * The dashes were never missing data. `universe.json` carries the 52-week
 * position, all three moving-average distances, ATR, the RS pair, VCS and the
 * Structure Pivot stop for MRNA, dated 2026-08-19. The page was asking a dead
 * file for readings a live one was already holding.
 *
 * A moving-average PRICE is recovered from the published distance:
 *   ma = close / (1 + dist)
 * Checked against the 418 technicals that still existed: the 200-day agrees to
 * 0.01% and the 20-day disagrees by 4–13%. The error scales with how fast the
 * average moves, which is what STALENESS looks like — the algebra is right and
 * the old file is old. That is also why this reads universe for every name and
 * not only for the broken ones.
 *
 * What universe genuinely does not carry — the 20-day high, the 10- and 5-day
 * lows, RSI — stays absent and says where it would have come from. Absent is
 * not zero and it is not a dash.
 */

/** A price implied by a published distance. Marked `derived` so the table can
 *  say so: this is algebra on the pipeline's own number, not a second model. */
function impliedPrice(close, dist) {
  if (close == null || dist == null) return null
  const p = close / (1 + dist)
  return Number.isFinite(p) ? p : null
}

const pct = (frac) => (frac == null ? null : frac * 100)

/**
 * Levels a stop or a target can be hung on.
 * `from` is the file, `derived` says the price was recovered from a distance.
 */
export function keyLevels(u) {
  if (!u) return []
  const c = u.close
  return [
    { label: '52 周高', price: impliedPrice(c, u.high_52w_dist), dist: pct(u.high_52w_dist),
      from: 'universe', derived: true, note: '突破位' },
    { label: 'MA20', price: impliedPrice(c, u.sma20_dist), dist: pct(u.sma20_dist),
      from: 'universe', derived: true, note: '第一支撑' },
    { label: 'MA50', price: impliedPrice(c, u.sma50_dist), dist: pct(u.sma50_dist),
      from: 'universe', derived: true, note: '趋势支撑' },
    { label: 'MA200', price: impliedPrice(c, u.sma200_dist), dist: pct(u.sma200_dist),
      from: 'universe', derived: true, note: '长期趋势' },
    // published as a price, not recovered from anything
    { label: 'EMA21', price: u.ema21 ?? null, dist: null,
      from: 'universe', note: '管线直接给的价，没有反推' },
    { label: 'Structure Pivot 止损', price: u.sp_stop ?? null, from: 'universe',
      note: u.sp_signal ? `sp_signal ${u.sp_signal}` : '管线给的止损位' },
    { label: '52 周低', price: impliedPrice(c, u.low_52w), dist: pct(u.low_52w),
      from: 'universe', derived: true, note: '参考' },
    { label: '20 日高', price: null, from: 'ticker_file', note: '收复=延续' },
    { label: '10 日低', price: null, from: 'ticker_file', note: '短线摆动低点' },
    { label: '5 日低', price: null, from: 'ticker_file', note: '上周结构底' },
  ]
}

/**
 * Readings, in the pipeline's vocabulary rather than in a verdict of ours.
 *
 * The version this replaced invented "Golden alignment", "Death cross
 * alignment", "Trending — near 52W high", "Pullback in uptrend" and an
 * overbought/oversold ladder — a second model living in the frontend, on a site
 * whose pipeline already publishes `sp_setup` / `sp_signal` / `sp_phase` for
 * exactly that question. The numbers are printed; the naming is the pipeline's.
 */
export function indicators(u) {
  if (!u) return []
  const n1 = (v, d = 1) => (v == null ? null : v.toFixed(d))
  /* Position in the 52-week range, from the two published distances.
     With hd = close/high - 1 and ld = close/low - 1,
       (close - low) / (high - low)  reduces to  ld(1 + hd) / (ld - hd).
     The (1 + hd) is not decorative: dropping it read MRNA at 99.8% of its
     range when the bars say 98.5%. */
  const hd = u.high_52w_dist, ld = u.low_52w
  const range52 = (hd == null || ld == null || ld === hd) ? null
    : (ld * (1 + hd)) / (ld - hd) * 100
  return [
    { label: 'ATR', value: u.atr == null ? null
        : `$${u.atr.toFixed(2)}${u.atr_pct == null ? '' : ` · ${u.atr_pct.toFixed(1)}% of price`}`,
      from: 'universe' },
    { label: 'ATR 位（离 MA50）', value: n1(u.atr_from_sma50),
      from: 'universe', note: '全站同一个口径；≥7 是减仓区' },
    { label: 'EMA21 距离（ATR）', value: n1(u.ema21_atr_dist), from: 'universe' },
    { label: '52 周位置', value: range52 == null ? null : `${range52.toFixed(1)}%（低→高）`,
      from: 'universe', derived: true },
    { label: 'RS 1M / 3M', value: u.rs_1m == null && u.rs_3m == null ? null
        : `${u.rs_1m ?? '—'} / ${u.rs_3m ?? '—'}`, from: 'universe' },
    { label: 'RS 线 21d / 63d', value: u.rs_line_pctl_21 == null ? null
        : `${n1(u.rs_line_pctl_21)} / ${n1(u.rs_line_pctl_63)}`,
      from: 'universe', note: '和 RS 1M 不是同一个量' },
    { label: 'VCS 波动收缩', value: n1(u.vcs), from: 'universe' },
    { label: 'Structure Pivot', value: u.sp_signal == null ? null
        : `${u.sp_signal}${u.sp_phase == null ? '' : ` · phase ${u.sp_phase}`}`,
      from: 'universe', note: '管线的判定，不是本页算的' },
    { label: '资格', value: [u.liquid_leader && 'liquid leader', u.trend_base && 'trend base',
        u.momentum_97 && 'momentum 97'].filter(Boolean).join(' · ') || null,
      from: 'universe', note: 'liquid_leader / trend_base / momentum_97' },
    { label: 'H / I / F 分', value: u.h_score == null ? null
        : `${u.h_score} / ${u.i_score ?? '—'} / ${u.f_score ?? '—'}`, from: 'universe' },
    { label: 'RSI(14)', value: null, from: 'ticker_file' },
  ]
}

/**
 * What each half of the page is standing on, and how old it is.
 * `alive` is about PRICE: a file holding ten news items and no bars is not a
 * feed that half-worked, it is a price feed that failed.
 */
export function provenance(u, tickerData, now = null) {
  const bars = tickerData?.ohlc_2y?.length || tickerData?.ohlc_1y?.length || 0
  const fetched = tickerData?.fetched_at ?? null
  const barDate = u?.bar_date ?? null
  let ageDays = null
  if (fetched && barDate) {
    const f = Date.parse(fetched.slice(0, 10)), b = Date.parse(barDate)
    if (Number.isFinite(f) && Number.isFinite(b)) ageDays = Math.round((b - f) / 86400000)
  }
  /* A SECOND CLOCK ON THE SAME FILE. `info_as_of` appears only when the
     fundamentals were carried forward — the fetch throttled, and rather than
     overwrite good values with `{}` the writer keeps the last ones and stamps
     the day they were taken (data side, 2026-08-21). So a page can be showing
     yesterday's bars beside fundamentals from a week ago, and without this the
     valuation block would print carried numbers with today's date implied.
     Right numbers, wrong clock is the failure this whole page was rebuilt to
     stop making. */
  const infoAsOf = tickerData?.info_as_of ?? null
  let infoAgeDays = null
  if (infoAsOf && barDate) {
    const i = Date.parse(infoAsOf.slice(0, 10)), b = Date.parse(barDate)
    if (Number.isFinite(i) && Number.isFinite(b)) infoAgeDays = Math.round((b - i) / 86400000)
  }
  return {
    universe: { barDate, stale: u?.bars_stale ?? null, present: !!u },
    tickerFile: {
      present: !!tickerData, bars, fetched,
      alive: bars > 0,
      hasInfo: !!(tickerData?.info && Object.keys(tickerData.info).length),
      hasNews: !!(tickerData?.news?.length),
      ageDays,
      // absent when the fundamentals came from this fetch, which is the
      // ordinary case and needs no note
      infoAsOf, infoAgeDays,
    },
  }
}
