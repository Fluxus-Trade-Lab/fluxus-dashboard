/**
 * A small markdown reader, producing a block list — never HTML.
 *
 * The Library renders files the data side writes (DATA_CONTRACTS §四点十一).
 * Two ways not to do this:
 *
 *   A dependency. There is no markdown renderer in this repo and one article
 *   is not a reason to add one. The subset these files use is small and fixed —
 *   headings, paragraphs, a pipe table, ordered and unordered lists, bold,
 *   italic, inline code, a horizontal rule — and it is written by us.
 *
 *   `dangerouslySetInnerHTML`. Rendering a fetched file as HTML makes every
 *   article an injection surface for whatever ends up in that directory. This
 *   returns a plain data structure that the page turns into React elements, so
 *   every character of the file is text by construction and there is no path
 *   from file contents to markup.
 *
 * One construct is ours rather than markdown's: a line holding only
 * `[[chart:key]]` marks where a chart goes. The data cannot live in the prose —
 * 130 bars and their signal days are a payload, not a sentence — so the article
 * says WHERE and a sidecar JSON says WHAT. An article that asks for a chart
 * nobody shipped says so at that spot instead of leaving a hole.
 *
 * It parses what our files contain and no more. A construct it does not know
 * comes through as a paragraph — visible and wrong-looking, which is the right
 * failure: silence would hide that an article had stopped rendering.
 */

/** Inline spans: **bold**, *italic*, `code`. Returns an array of
 *  {t: 'text'|'b'|'i'|'code', s: string}. */
export function inline(text) {
  const out = []
  // one pass, longest marker first, so **x** never reads as *(*x*)*
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g
  let last = 0, m
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push({ t: 'text', s: text.slice(last, m.index) })
    const tok = m[0]
    if (tok.startsWith('**')) out.push({ t: 'b', s: tok.slice(2, -2) })
    else if (tok.startsWith('`')) out.push({ t: 'code', s: tok.slice(1, -1) })
    else out.push({ t: 'i', s: tok.slice(1, -1) })
    last = m.index + tok.length
  }
  if (last < text.length) out.push({ t: 'text', s: text.slice(last) })
  return out.length ? out : [{ t: 'text', s: text }]
}

const cells = (line) => line.replace(/^\||\|$/g, '').split('|').map((c) => c.trim())
const isDivider = (line) => /^\|?[\s:|-]+\|[\s:|-]*$/.test(line) && line.includes('-')

/** Markdown source -> a list of blocks. */
export function parse(md) {
  const lines = (md ?? '').replace(/\r\n?/g, '\n').split('\n')
  const blocks = []
  let para = []

  const flush = () => {
    if (para.length) { blocks.push({ type: 'p', spans: inline(para.join(' ')) }); para = [] }
  }

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i]
    const trimmed = line.trim()

    if (!trimmed) { flush(); continue }

    const h = /^(#{1,4})\s+(.*)$/.exec(trimmed)
    if (h) { flush(); blocks.push({ type: 'h', level: h[1].length, spans: inline(h[2]) }); continue }

    if (/^(-{3,}|\*{3,})$/.test(trimmed)) { flush(); blocks.push({ type: 'hr' }); continue }

    const chart = /^\[\[chart:([\w-]+)\]\]$/.exec(trimmed)
    if (chart) { flush(); blocks.push({ type: 'chart', key: chart[1] }); continue }

    // a table: a header row, a divider, then rows until a non-pipe line
    if (trimmed.startsWith('|') && isDivider(lines[i + 1]?.trim() ?? '')) {
      flush()
      const head = cells(trimmed)
      const rows = []
      i += 2
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        rows.push(cells(lines[i].trim()).map(inline)); i += 1
      }
      i -= 1
      blocks.push({ type: 'table', head: head.map(inline), rows })
      continue
    }

    const li = /^(\d+)\.\s+(.*)$/.exec(trimmed) || /^[-*]\s+(.*)$/.exec(trimmed)
    if (li) {
      flush()
      const ordered = /^\d/.test(trimmed)
      const text = ordered ? li[2] : li[1]
      const prev = blocks[blocks.length - 1]
      if (prev?.type === 'list' && prev.ordered === ordered) prev.items.push(inline(text))
      else blocks.push({ type: 'list', ordered, items: [inline(text)] })
      continue
    }

    para.push(trimmed)
  }
  flush()
  return blocks
}
