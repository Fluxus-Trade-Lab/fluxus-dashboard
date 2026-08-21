import { useGroupsHistory } from '../../hooks/useGroupsHistory'
import { barStyle } from './ThemeBars'

/**
 * The path, not the position.
 *
 * The four-state field answers "where is this theme now" and flattens ten weeks
 * into one dot. Two themes can sit on the same dot having arrived from opposite
 * directions, and the arrival is the rotation — which is the thing this page is
 * for. So the picked themes get their excess over SPY drawn through time, with
 * the benchmark as the zero line, and their state sequence under it.
 *
 * IT IS SHORT ON PURPOSE, AND SAYS SO. A theme has no price history: it is an
 * aggregate of a column that is overwritten nightly, so the only honest series
 * is the one recorded from the day recording started (2026-08-07). Every
 * reading here prints sessions-held against sessions-wanted, because a
 * ten-session line drawn without that denominator is a ten-week claim.
 *
 * Nothing is smoothed. A curve through ten points would draw shape the
 * measurement does not have — the line steps between the days that exist.
 */

const W = 1000, H = 210, PAD = { t: 14, r: 60, b: 22, l: 44 }
const pct = (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(1)}%`

function Empty({ note }) {
  return (
    <div className="rounded-2xl px-5 py-5"
         style={{ backgroundImage:
           'repeating-linear-gradient(45deg,var(--color-border-light) 0 1px,transparent 1px 7px)' }}>
      <div className="text-[10px] font-mono uppercase tracking-[.24em]
                      text-[var(--color-text-muted)] mb-2">Not enough sessions</div>
      <p className="m-0 text-[12.5px] leading-relaxed text-[var(--color-text-secondary)]">{note}</p>
    </div>
  )
}

export default function RsPath({ picks, colourOf }) {
  const { data, loading, failed, sessions, target } = useGroupsHistory()

  if (loading) return null
  if (failed || !data?.groups) {
    return (
      <Empty note={
        <>还没有 <code className="font-mono">groups_history.json</code>。一个主题没有价格历史
        —— 它是每晚被覆盖的那张横截面的聚合，所以唯一诚实的序列是从开始记录那天起攒的
        （2026-08-07）。归档在 <code className="font-mono">data/history/groups_archive.csv</code>
        里每晚都在长，但那个目录不发布，前端读不到。</>} />
    )
  }

  /* Counted, not measured by array length. Every array here is `dates` long
     and the days a group was not measured are null — Cloud Software is 7 of 10
     — so `length >= 2` would pass a group with one real point and draw a line
     through nothing. */
  const real = (a) => (a ?? []).filter((v) => v != null).length
  const series = picks
    .map((name) => ({ name, g: data.groups[name] }))
    .filter((s) => real(s.g?.excess) >= 2)

  if (!series.length) {
    return <Empty note={picks.length
      ? '选中的主题在归档里还不足两个交易日 —— 画不出一条线的是天数，不是主题。'
      : '在上面挑两三个主题，这里画它们各自相对 SPY 的走法。'} />
  }

  const dates = data.dates ?? []
  const n = Math.max(...series.map((s) => s.g.excess.length))
  const all = series.flatMap((s) => s.g.excess).filter((v) => v != null)
  const span = Math.max(Math.abs(Math.min(...all)), Math.abs(Math.max(...all)), 0.02)
  const x = (i) => PAD.l + (n < 2 ? 0 : (i / (n - 1)) * (W - PAD.l - PAD.r))
  const y = (v) => PAD.t + (1 - v / span) * ((H - PAD.t - PAD.b) / 2) * 1

  const ticks = [span, span / 2, 0, -span / 2, -span]

  return (
    <div>
      <div className="flex items-baseline gap-3 flex-wrap mb-1">
        <span className="text-[10px] font-mono uppercase tracking-[.24em]
                         text-[var(--color-text-muted)]">Path · 相对 SPY</span>
        {/* the denominator, always. This is the whole difference between a
            short series and a claim about a long one. */}
        <span className="text-[11px] font-mono text-[var(--color-text-secondary)]">
          {sessions}/{target} 个交易日
          {sessions < target && (
            <span className="text-[var(--color-text-muted)]">
              {' '}· 每晚长一格，攒满约 {Math.ceil((target - sessions) / 5)} 周
            </span>
          )}
        </span>
      </div>

      <div className="overflow-x-auto">
        {/* The floor is 1000px because the viewBox is 1000 wide: one user unit
            has to stay one pixel, or the 10px labels inside render smaller than
            10px. StateField learned this at 900, where 11px came out at 9.9.
            Narrower than that it scrolls in its own box; the page never does. */}
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto block min-w-[1000px]" role="img"
             aria-label={`${series.length} themes' excess over SPY across ${sessions} sessions`}>
          {ticks.map((t, i) => (
            <g key={i}>
              <line x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} strokeWidth="1"
                    stroke={t === 0 ? 'var(--color-text-muted)' : 'var(--color-border-light)'}
                    strokeDasharray={t === 0 ? '3 4' : undefined}
                    vectorEffect="non-scaling-stroke" />
              <text x={PAD.l - 6} y={y(t) + 3.5} textAnchor="end"
                    fill="var(--color-text-muted)"
                    style={{ fontSize: 10, fontFamily: 'var(--font-mono)' }}>{pct(t)}</text>
            </g>
          ))}

          {series.map((s) => {
            /* One polyline per unbroken run. Joining across a null would draw a
               value nobody computed — 4 of the 30 themes have interior holes
               and Cloud Software is 7 of 10. The same rule the card chart
               follows; it was written correctly there this morning and wrongly
               here this afternoon, which is why it is now a shared sentence. */
            const runs = []
            let cur = []
            s.g.excess.forEach((v, i) => {
              if (v == null) { if (cur.length > 1) runs.push(cur); cur = []; return }
              cur.push(`${x(i)},${y(v)}`)
            })
            if (cur.length > 1) runs.push(cur)

            const c = colourOf?.(s.name) ?? 'var(--color-text)'
            // the last day that was actually measured, which need not be the last day
            const li = s.g.excess.reduce((k, v, i) => (v == null ? k : i), -1)
            const last = li >= 0 ? s.g.excess[li] : null
            const stale = li >= 0 && li < s.g.excess.length - 1
            return (
              <g key={s.name}>
                {runs.map((r, i) => (
                  <polyline key={i} points={r.join(' ')} fill="none" strokeWidth="1.9"
                            stroke={c} strokeLinejoin="round" strokeLinecap="round"
                            vectorEffect="non-scaling-stroke" />
                ))}
                {/* a lone measured day still gets its dot; a line needs two */}
                {s.g.excess.map((v, i) => (v == null ? null : (
                  <circle key={i} cx={x(i)} cy={y(v)} r={i === li ? 3 : 1.4} fill={c}
                          fillOpacity={i === li ? 1 : .55} />
                )))}
                {last != null && (
                  <text x={W - PAD.r + 6} y={y(last) + 3.5} fill={c}
                        style={{ fontSize: 11, fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                    {pct(last)}{stale && <tspan fillOpacity=".6"> ·{s.g.excess.length - 1 - li}d</tspan>}
                  </text>
                )}
              </g>
            )
          })}

          {/* the two ends of the window, named. A line with no dates is a shape. */}
          {dates.length > 1 && (
            <>
              <text x={PAD.l} y={H - 6} fill="var(--color-text-muted)"
                    style={{ fontSize: 10, fontFamily: 'var(--font-mono)' }}>{dates[0]}</text>
              <text x={W - PAD.r} y={H - 6} textAnchor="end" fill="var(--color-text-muted)"
                    style={{ fontSize: 10, fontFamily: 'var(--font-mono)' }}>
                {dates[dates.length - 1]}
              </text>
            </>
          )}
        </svg>
      </div>

      {/* the state sequence — one cell per session, the site's own four-state
          grammar. Not a fortnight grid like the rotation ribbon: at ten sessions
          a fortnight bucket would be two blocks, and the daily cells ARE what
          the archive holds. */}
      <div className="mt-3 space-y-2">
        {series.map((s) => (
          <div key={s.name} className="flex items-center gap-2.5">
            <span className="w-2 h-2 rounded-full shrink-0"
                  style={{ background: colourOf?.(s.name) ?? 'var(--color-text)' }} />
            <span className="text-[11.5px] text-[var(--color-text-secondary)]
                             w-[150px] shrink-0 truncate">{s.name}</span>
            <span className="flex gap-[2px] flex-1">
              {(s.g.state ?? []).map((st, i) => (
                /* a day with no reading is not a fourth state — it is a gap,
                   and it wears the dashed frame this site uses for "could not
                   be counted" rather than a colour it never earned */
                <span key={i} className="h-[10px] flex-1 rounded-[1px]"
                      title={`${dates[i] ?? ''} · ${st ?? '没测到'}`}
                      style={st ? barStyle(st) : {
                        border: '1px dashed var(--color-untested)',
                        background: 'transparent' }} />
              ))}
            </span>
          </div>
        ))}
      </div>
      {/* JSX text is literal — the asterisks printed as asterisks */}
      <p className="m-0 mt-2 text-[10px] font-mono text-[var(--color-text-muted)]">
        一格 = 一个交易日<b className="font-semibold">当天发布</b>的态，不是事后重算的
        —— 从存下来的 perf 列反推过去的态，会把今天的窗口常数套到昨天的数据上。
      </p>
    </div>
  )
}
