/**
 * Cover text for a piece written in one language, in the other one.
 *
 * Andy 2026-10-03: 「整个网页需要有完整的中文和英文界面」. The cover — title,
 * subtitle, one-line summary — is interface: a reader decides from it whether
 * to open the piece. The body is not translated; it opens in the language it
 * was written in, and the cover says which (lib.cover.inLang.*).
 *
 * Keyed by the payload's own text, not by slug: if the data side rewrites a
 * title, the lookup misses and the new text shows as written — a stale English
 * line over a changed article would be worse than an untranslated one.
 */
export const COVER = {
  // payload text (zh) → English
  zh: {
    'EP（Episodic Pivot）': 'EP (Episodic Pivot)',
    '以 MRNA 2026-08-19 为标本': 'Specimen: MRNA, 2026-08-19',
    '一天之内改变定价前提的事件：涨幅 ≥10%、量 ≥50 日均 3 倍。EP 第一天不进（42% 击穿 EP 日低点）；第二次入场（Delayed EP）是全系统精度最高的一把刀（20 日 61% vs 基线 41%）。':
      'An event that resets a stock’s pricing premise in a single day: up ≥10% on volume ≥3× its 50-day average. Do not buy EP day one (42% break the EP-day low); the second entry (Delayed EP) is the most precise tool in the whole system (61% at 20 days vs a 41% baseline).',
  },
  // payload text (en) → Chinese
  en: {},
}

const HAN = /[㐀-鿿]/g
const LATIN = /[A-Za-z]/g

/** The language a piece is written in, read off its body (not its cover). */
export function articleLang(entry) {
  const parts = [entry.title, entry.summary]
  for (const b of entry.blocks ?? []) {
    if (b.text) parts.push(b.text)
    if (b.items) parts.push(...b.items)
  }
  const s = parts.filter(Boolean).join(' ')
  const han = (s.match(HAN) ?? []).length
  const latin = (s.match(LATIN) ?? []).length
  // one Han character carries roughly a word; weigh it against Latin letters
  return han * 3 >= latin ? 'zh' : 'en'
}

/** A cover field in the reader's language, when it differs from the piece's. */
export function coverField(text, pieceLang, uiLang) {
  if (text == null || pieceLang === uiLang) return text
  return COVER[pieceLang]?.[text] ?? text
}
