import { useEffect, useState } from 'react'

let cache = null
let inflight = null

/**
 * 主题四态板（`pipeline/themes/proxy_board.py`），每晚发成 `theme_board.json`。
 *
 * 每个主题读的是一只代理 ETF 的两周桶，不是成分股等权篮子。payload 里：
 * `state` 是新读数，`state_prev` 是并排期内一起带着的旧读数，`parallel_until`
 * 是撤旧列的日子；`members` 是该主题成分股各自四态的计数 —— 代理是市值加权的，
 * 主题绿而名单红是常有的事，所以这一列常驻，不折叠。
 *
 * `members_asof` 可能比 `asof` 早一天（两边是两次下载）。早了就在卡片上写出来，
 * 不把昨天的分布默默挂在今天的四态旁边。
 */
export function useThemeBoard() {
  const [state, setState] = useState({ data: cache, loading: !cache, failed: false })

  useEffect(() => {
    let dead = false
    if (cache) return () => { dead = true }
    if (!inflight) {
      inflight = fetch('/data/output/theme_board.json')
        .then((r) => (r.ok ? r.json() : null))
        .then((j) => { cache = j; return j })
        .catch(() => null)
    }
    inflight.then((j) => {
      if (!dead) setState({ data: j, loading: false, failed: !j })
    })
    return () => { dead = true }
  }, [])

  return state
}
