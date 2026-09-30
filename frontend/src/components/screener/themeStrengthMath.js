/**
 * Per-stock strength against ONE theme's proxy ETF — the screener's own
 * reading, built from the two raw series `pipeline/themes/proxy_board.py`
 * ships instead of a pre-multiplied (theme, ticker) table:
 *
 *   `themeBoard.member_returns[ticker]`  — [ret this bucket, ret prior bucket] %,
 *                                          plain, no benchmark subtracted
 *   `themeBoard.themes[].proxy_ret`      — the theme's own proxy ETF, same shape
 *
 * The pipeline module's own docstring gives the one-subtraction algorithm this
 * mirrors (`plain_return()` in proxy_board.py) — same classify() shape as the
 * theme-level `state` field (`leading`/`weakening`/`improving`/`lagging`), run
 * here per member instead of per proxy.
 *
 * Tickers proxy_board.py could not price are simply absent from
 * `member_returns` — they stay OUT of the ranking, not sunk to a false zero
 * that would read as "keeping pace with the theme".
 */

export function classifyThemeState(excess, momentum) {
  if (excess == null || momentum == null) return null
  if (excess > 0) return momentum >= 0 ? 'leading' : 'weakening'
  return momentum >= 0 ? 'improving' : 'lagging'
}

export const THEME_STATE_LABEL = {
  leading: 'Leading', weakening: 'Weakening', improving: 'Improving', lagging: 'Lagging',
}

/**
 * @param {object|null} themeBoard   theme_board.json payload (useThemeBoard().data)
 * @param {string|null} themeName    the one selected theme's group name
 * @param {string[]|undefined} memberTickers  the theme's full roster (groups.json themes[].tickers) — NOT the screener's filtered row set, so the ranking is the theme itself, not whatever scan/search happens to be on top of it
 * @returns {Map<string, {excess: number, momentum: number|null, state: string|null, topQuartile: boolean}>}
 */
export function computeThemeStrength(themeBoard, themeName, memberTickers) {
  const result = new Map()
  if (!themeBoard || !themeName || !memberTickers?.length) return result
  const row = (themeBoard.themes ?? []).find((r) => r.theme === themeName)
  const proxyRet = row?.proxy_ret
  if (!proxyRet || proxyRet[0] == null) return result
  const memberReturns = themeBoard.member_returns ?? {}

  const entries = []
  for (const t of memberTickers) {
    const mr = memberReturns[t]
    if (!mr || mr[0] == null) continue   // 缺价的票不参与排名 — not a 0
    const excess = mr[0] - proxyRet[0]
    const momentum = (mr[1] == null || proxyRet[1] == null)
      ? null
      : (mr[0] - mr[1]) - (proxyRet[0] - proxyRet[1])
    entries.push({ ticker: t, excess, momentum, state: classifyThemeState(excess, momentum) })
  }
  entries.sort((a, b) => b.excess - a.excess)
  const cutoff = Math.ceil(entries.length * 0.25)
  entries.forEach((e, i) => {
    result.set(e.ticker, { ...e, topQuartile: i < cutoff })
  })
  return result
}
