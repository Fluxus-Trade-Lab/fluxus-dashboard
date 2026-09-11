/**
 * A sentence with its numbers set in ink.
 *
 * The board's evidence strings arrive as prose from the pipeline ("768 names
 * −25% on the quarter against 737 up 25% — 51% on the down side"). Read at a
 * glance, the words are scaffolding and the numbers are the reading, so the
 * words stay in the secondary grey and every figure steps up to the body ink
 * and a heavier weight. Figure/ground by weight and shade — no new colour.
 *
 * Added 2026-09-11 after the page audit (Andy: 「大多都是同意粗细字体，颜色相近。
 * 不适宜阅读吧」): 72% of the page's characters were 11px regular in the two
 * lighter greys, with the figures sitting in the same weight as the words
 * around them.
 */
// A figure is a number standing on its own: not the tail of a name (T2108)
// and not the head of a unit-word (20-day, 52-week) — those are labels.
const NUM = /((?<![A-Za-z\d])[−+-]?\d[\d,]*(?:\.\d+)?%?(?![\w-]))/

export default function Figures({ text }) {
  if (!text) return null
  return text.split(NUM).map((part, i) => (
    i % 2 === 1
      ? <b key={i} className="font-semibold text-[var(--color-text)]">{part}</b>
      : part
  ))
}
