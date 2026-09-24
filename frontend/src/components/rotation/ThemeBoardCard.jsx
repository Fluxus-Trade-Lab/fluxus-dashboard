import { useMemo, useState } from 'react'
import { useThemeBoard } from '../../hooks/useThemeBoard'
import { barStyle } from '../groups/ThemeBars'

/**
 * 主题四态板 —— 50 个主题，每个读一只代理 ETF 的两周桶。
 *
 * 落在 Rotation 页（本来就是主题四态的明细页），不在 dashboard。
 * Andy 2026-09-24 原话：「不 设计上用原来的，不能改。你展现的成员分布是细节，
 * 需要在另外的页面上去展现。」—— dashboard 版面一个像素不动，三卡也不动，
 * 这块接在三卡下面。
 *
 * 三件事按 Andy 2026-09-23/24 的裁决排：
 *  · 并排两周：新读数在前、旧读数跟在后面，`parallel_until` 到了前端就不画旧列。
 *  · 成员分布常驻：不折叠、不用点开。代理是市值加权的，09-21 实测 Cloud
 *    Software 代理读 leading 而 70 只成员里 43 只走弱或落后 —— 只给一个绿灯会骗人。
 *  · 撤下的主题不在这里：没有可用代理的 4 个已从产线撤掉，2 个本来就是筛选规则的
 *    留在 screener。少一个主题比多一个读不准的主题好。
 *
 * 排序按本桶超额降序：这张卡回答"钱现在在哪一格"，不是"谁今天涨得多"
 * （那是隔壁 Theme Leaders and Laggards 的活）。
 */

const CN = { leading: 'Leading', weakening: 'Weakening', improving: 'Improving', lagging: 'Lagging' }
const CAP = { leading: 'Leading', weakening: 'Weakening', improving: 'Improving', lagging: 'Lagging' }
const ORDER = ['leading', 'improving', 'weakening', 'lagging']
const HEAD = 12

function Mark({ state, dim = false }) {
  if (!state) return <i className="w-[8px] h-[8px] rounded-[1px] opacity-30"
                        style={{ background: 'var(--color-text-muted)' }} />
  return (
    <i className="w-[8px] h-[8px] rounded-[1px] shrink-0"
       style={{ ...barStyle(CAP[state] ?? state), opacity: dim ? 0.45 : 1 }}
       title={CN[state] ?? state} />
  )
}

/** 成员四态的计数条。宽度＝该状态占成员数的比例，不带数字，数字在 title 里。 */
function MemberBar({ dist, count }) {
  const total = ORDER.reduce((s, k) => s + (dist?.[k] ?? 0), 0)
  if (!total) return <span className="text-[11px] text-[var(--color-text-muted)]">—</span>
  const label = ORDER.map((k) => `${CN[k]} ${dist[k] ?? 0}`).join(' · ')
  return (
    <span className="flex items-center gap-1.5 min-w-0" title={`${count} members — ${label}`}>
      <span className="flex h-[7px] w-[64px] shrink-0 overflow-hidden rounded-[2px]
                       bg-[var(--color-border-light)]">
        {ORDER.map((k) => (dist[k] ? (
          <i key={k} style={{ ...barStyle(CAP[k]), flex: dist[k] }} className="h-full" />
        ) : null))}
      </span>
      <span className="font-mono tabular-nums text-[11px] text-[var(--color-text-muted)]">
        {count}
      </span>
    </span>
  )
}

function Row({ row, parallel }) {
  const rs = Number.isFinite(row.rs) ? row.rs : null
  const changed = parallel && row.state_prev
    && String(row.state).toLowerCase() !== String(row.state_prev).toLowerCase()
  return (
    <div className="h-[26px] flex items-center gap-2 min-w-0">
      <Mark state={row.state} />
      {parallel && (
        <span className="flex items-center gap-1 shrink-0" title={`旧读数：${row.state_prev ?? '—'}`}>
          <span className="text-[11px] text-[var(--color-text-muted)]">was</span>
          <Mark state={String(row.state_prev ?? '').toLowerCase()} dim />
        </span>
      )}
      <span className="min-w-0 flex-1 truncate text-[13px] font-medium
                       text-[var(--color-text-bold)]" title={`${row.theme} · ${row.etf}`}>
        {row.theme}
        {changed && <span className="ml-1.5 text-[11px] text-[var(--color-text-muted)]">changed</span>}
      </span>
      <MemberBar dist={row.members} count={row.member_count} />
      <span className="shrink-0 w-[58px] text-right text-[13px] font-mono tabular-nums font-medium"
            style={{ color: rs === null ? 'var(--color-text-muted)'
                          : rs > 0 ? 'var(--color-took)' : 'var(--color-refused)' }}>
        {rs === null ? '—' : `${rs > 0 ? '+' : ''}${rs.toFixed(1)}%`}
      </span>
    </div>
  )
}

export default function ThemeBoardCard() {
  const { data, loading, failed } = useThemeBoard()
  const [open, setOpen] = useState(false)

  const rows = useMemo(() => {
    const t = data?.themes ?? []
    return [...t].sort((a, b) => (b.rs ?? -999) - (a.rs ?? -999))
  }, [data])

  const parallel = useMemo(() => {
    if (!data?.parallel_until) return false
    return new Date(data.asof) <= new Date(data.parallel_until)
  }, [data])

  const shown = open ? rows : rows.slice(0, HEAD)
  const counts = data?.counts ?? {}
  const staleMembers = data && data.members_asof && data.members_asof !== data.asof

  return (
    <div className="flex flex-col min-w-0">
      <div className="text-[17px] font-semibold leading-tight text-[var(--color-text-bold)]
                      mb-3 px-1">
        Proxy Board
      </div>
      <section className="bg-[var(--color-surface)] rounded-3xl overflow-hidden
                          flex flex-col flex-1 pt-4">
        <div className="px-5 pb-4 flex-1 flex flex-col">
          {loading ? (
            <p className="m-0 py-6 text-[11px] text-[var(--color-text-muted)]">
              Loading the theme board&hellip;
            </p>
          ) : failed || !rows.length ? (
            <p className="m-0 py-6 text-[11px] leading-relaxed text-[var(--color-text-muted)]">
              theme_board.json did not load — the board is not measured this session.
            </p>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mb-2.5
                              text-[11px] text-[var(--color-text-muted)]">
                {ORDER.map((k) => (
                  <span key={k} className="flex items-center gap-1.5">
                    <i className="w-[8px] h-[8px] rounded-[1px]" style={barStyle(CAP[k])} />
                    {CN[k]} <span className="font-mono tabular-nums">{counts[k] ?? 0}</span>
                  </span>
                ))}
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-2 gap-x-8">
                {shown.map((r) => <Row key={r.theme} row={r} parallel={parallel} />)}
              </div>

              {rows.length > HEAD && (
                <button type="button" id="theme-board-fold" onClick={() => setOpen((v) => !v)}
                        className="mt-2 self-start text-[11px] font-mono
                                   text-[var(--color-text-muted)] hover:text-[var(--color-text-bold)]
                                   focus-visible:outline focus-visible:outline-1">
                  {open ? 'Show fewer' : `All ${rows.length} themes`}
                </button>
              )}

              <p className="m-0 mt-3 text-[11px] leading-relaxed text-[var(--color-text-muted)]">
                Each theme reads one proxy ETF: excess over {data.benchmark} across the last
                two weeks, momentum against the two weeks before. The bar on each row is that
                theme&rsquo;s own constituents, counted by state — a cap-weighted proxy can lead
                while most of its names do not.
                {parallel && ` Both readings run side by side until ${data.parallel_until}; the old one comes off then.`}
                {staleMembers && ` Constituent states are ${data.members_asof} closes, one session behind the theme reading.`}
              </p>
            </>
          )}
        </div>
      </section>
    </div>
  )
}
