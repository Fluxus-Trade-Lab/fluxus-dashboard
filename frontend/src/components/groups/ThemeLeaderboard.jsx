import { useMemo } from 'react'
import PageHeader from '../PageHeader'
import { useGroups } from '../../hooks/useGroups'
import HowToRead from '../HowToRead'

/**
 * The strongest themes right now — two clocks, two lists.
 *
 * Design: Fluxus_Brand/visual/2026-08-10_TSF_PAGE_MAP.md §二 (Theme Leaderboard)
 *
 * TSF's page does exactly one thing and that is the part worth keeping. Two
 * rankings, because a board that ranks only what has already won cannot show a
 * turn:
 *
 *   short  the last week against SPY, with acceleration printed beside it —
 *          the turn you would want to catch early
 *   long   three months against SPY (Andy: 10 weeks ≈ 50 sessions; rs 63d
 *          stands in for it) — the trend that has already proven itself
 *
 * No archive needed: both windows are trailing computations off price history
 * the pipeline already does every session. The two lists usually disagree, and
 * the names on the short list that are absent from the long one are the page's
 * actual content.
 */

const TOP = 10

function Row({ r, value, accel, rank }) {
  return (
    <div className="grid grid-cols-[18px_1fr_38px_72px_64px] gap-2 items-baseline py-[5px]
                    border-b border-[var(--color-border-light)]">
      <span className="text-[10px] font-mono text-[var(--color-text-muted)]">{rank}</span>
      <span className="text-[13px] truncate" title={r.tickers?.join(' · ')}>{r.group}</span>
      <span className="text-[10px] tabular-nums text-right text-[var(--color-text-muted)]"
            title="members — a theme of one stock is one stock">{r.members}</span>
      <span className="text-[13px] font-mono tabular-nums text-right">
        {value > 0 ? '+' : ''}{(value * 100).toFixed(1)}%
      </span>
      {accel != null
        ? <span className="text-[11px] font-mono tabular-nums text-right"
                style={{ color: accel > 0 ? 'var(--color-took)' : 'var(--color-text-muted)' }}
                title="acceleration — is the gap still widening">
            {accel > 0 ? '+' : ''}{(accel * 100).toFixed(1)}
          </span>
        : <span className="text-[11px] text-right text-[var(--color-text-muted)]">·</span>}
    </div>
  )
}

function Board({ title, note, rows, metric, showAccel }) {
  return (
    <section>
      <div className="flex items-baseline gap-3 pb-2 border-b border-[var(--color-v2-ink)]">
        <h2 className="text-[15px] font-semibold m-0" style={{ fontFamily: 'var(--font-cond)' }}>
          {title}
        </h2>
        <span className="text-[11px] text-[var(--color-text-muted)]">{note}</span>
      </div>
      <div className="grid grid-cols-[18px_1fr_38px_72px_64px] gap-2 pt-2 pb-1 text-[9px]
                      font-mono uppercase tracking-wider text-[var(--color-text-muted)]">
        <span>#</span><span>Theme</span><span className="text-right">n</span>
        <span className="text-right">RS</span>
        <span className="text-right">{showAccel ? 'Accel' : ''}</span>
      </div>
      {rows.map((r, i) => (
        <Row key={r.group} r={r} rank={i + 1} value={r[metric]}
             accel={showAccel ? r.rs_accel : null} />
      ))}
    </section>
  )
}

export default function ThemeLeaderboard() {
  const { themes, benchmark, date, loading, error } = useGroups()

  const { short, long, ranked } = useMemo(() => {
    const ok = (k) => (themes ?? []).filter((t) => t[k] != null)
    return {
      short: ok('rs_0_1w').sort((a, b) => b.rs_0_1w - a.rs_0_1w).slice(0, TOP),
      long: ok('excess_3m').sort((a, b) => b.excess_3m - a.excess_3m).slice(0, TOP),
      ranked: (themes ?? []).length,
    }
  }, [themes])

  if (loading) return <div className="text-[var(--color-text-muted)] text-sm py-8 text-center">Loading…</div>
  if (error) return <div className="text-rose-400 text-sm py-8 text-center">groups.json unavailable</div>

  const shortSet = new Set(short.map((r) => r.group))
  const newcomers = short.filter((r) => !long.some((l) => l.group === r.group)).length

  return (
    <div className="space-y-4">
      <PageHeader group="market" title="RS Leaderboard"
        blurb="The strongest themes on two clocks. A board that ranks only what has already won cannot show a turn — the short list is where the turn appears first."
        meta={[`relative strength vs ${benchmark ?? 'SPY'} · ${date ?? ''}`,
               `top ${TOP} of ${ranked} ranked — the denominator is part of the reading`,
               `${newcomers} of the short list are not on the long list`]} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-10 gap-y-6">
        <Board title="Short — last week" note="with acceleration beside it"
               rows={short} metric="rs_0_1w" showAccel />
        <Board title="Long — three months" note="the trend that has proven itself"
               rows={long} metric="excess_3m" showAccel={false} />
      </div>

      <HowToRead>
        <p>
          Both lists measure the same thing — excess return against SPY — over two
          different windows. The <b>long list is the record</b>; the <b>short list
          is the rumour</b>, and the acceleration column says whether the rumour is
          still building.
        </p>
        <p>
          The names worth your attention are the disagreements: a theme on the
          short list but not the long one is money arriving; a long-list leader
          with negative acceleration is a leader being sold into.
        </p>
        <p>
          Member count prints on every row. A theme of one stock is one stock, and
          its rank is that stock&rsquo;s rank wearing a theme&rsquo;s name.
        </p>
      </HowToRead>
    </div>
  )
}
