import { Fragment } from 'react'

/**
 * A translated string that carries markup: `**bold**` spans, and `{name}`
 * slots that take a React node (a link, a button, a bold number). The two
 * languages put those pieces in different places, so the whole sentence is
 * one key and the nodes are dropped into it — never a sentence glued from
 * fragments in one language's order.
 *
 * Call t() first (it fills the plain {placeholders}); slots t() left alone
 * are filled here from `nodes`.
 */
export function rich(str, nodes = {}, boldClass) {
  const out = []
  let k = 0
  for (const piece of String(str).split(/(\*\*[^*]+\*\*|\{\w+\})/)) {
    if (!piece) continue
    const bold = piece.match(/^\*\*([^*]+)\*\*$/)
    const slot = piece.match(/^\{(\w+)\}$/)
    if (bold) out.push(<b key={k++} className={boldClass}>{bold[1]}</b>)
    else if (slot && slot[1] in nodes) out.push(<Fragment key={k++}>{nodes[slot[1]]}</Fragment>)
    else out.push(piece)
  }
  return out
}

/** A key-or-raw lookup: a vocabulary word the dictionary does not know (a new
 *  state, regime or stance the pipeline started writing) prints as it
 *  arrived, never as its key. */
export function word(tr, key, raw) {
  if (raw == null) return raw
  const v = tr(key)
  return v === key ? raw : v
}
