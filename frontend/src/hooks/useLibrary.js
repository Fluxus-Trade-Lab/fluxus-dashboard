import { useEffect, useState } from 'react'

/**
 * The Library's articles for one page.
 *
 * `data/output/library/<page>_<topic>.md` (DATA_CONTRACTS §四点十一). The data
 * side says more pieces are coming, and a naming convention alone cannot tell
 * a browser what exists — so this asks for an index first and falls back to a
 * list compiled in.
 *
 * The fallback is the honest kind of hardcoding: it is named, it is small, and
 * every new article needs a frontend deploy until `index.json` exists. That ask
 * is filed in DATA_CONTRACTS §七. When the index lands, this stops being a list
 * anyone has to maintain and nothing else changes.
 */
const BASE = '/data/output/library'

/** Known at build time. Superseded by index.json the moment it exists. */
export const COMPILED_IN = {
  offense: ['offense_ep_mrna.md'],
  defense: [],
  psychology: [],
  'portfolio-management': [],
  news: [],
}

let indexCache
async function loadIndex() {
  if (indexCache !== undefined) return indexCache
  try {
    const r = await fetch(`${BASE}/index.json`)
    const j = r.ok ? await r.json() : null
    indexCache = j && typeof j === 'object' ? j : null
  } catch { indexCache = null }
  return indexCache
}

/**
 * @returns { articles, loading, indexed }
 *   `indexed` says whether the list came from the file or from COMPILED_IN —
 *   the page prints it, because "this is everything" and "this is everything I
 *   was told about at build time" are different claims.
 */
export function useLibrary(page) {
  const [state, setState] = useState({ articles: null, loading: true, indexed: false })

  useEffect(() => {
    let dead = false
    setState({ articles: null, loading: true, indexed: false })
    ;(async () => {
      const idx = await loadIndex()
      const names = (idx?.[page] ?? COMPILED_IN[page] ?? [])
      const got = await Promise.all(names.map(async (name) => {
        /* Two files per article: the prose, and a sidecar holding whatever the
           prose cannot carry — 130 bars and their signal days are a payload,
           not a sentence. The sidecar is optional; an article without one is a
           normal article, and an article whose prose asks for a chart the
           sidecar does not hold says so where the chart would have been. */
        const side = name.replace(/\.md$/, '.json')
        const [text, assets] = await Promise.all([
          fetch(`${BASE}/${name}`).then((r) => (r.ok ? r.text() : null)).catch(() => null),
          fetch(`${BASE}/${side}`).then((r) => (r.ok ? r.json() : null)).catch(() => null),
        ])
        return { name, text, assets }
      }))
      if (!dead) setState({ articles: got, loading: false, indexed: !!idx })
    })()
    return () => { dead = true }
  }, [page])

  return state
}
