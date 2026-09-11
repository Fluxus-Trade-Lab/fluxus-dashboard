import { isWeekend } from './session'
import VoteGlyphs from './VoteGlyphs'

/**
 * Votes — the twelve-way ballot that produces the score, one card.
 *
 * Folds what used to be three separate blocks (VerdictBanner, its own
 * Falsification note, and MarketStateSummary's four duplicate tiles) into
 * one: MarketStateSummary printed up_4pct/down_4pct, the 5/10-day ratio, the
 * quarterly spread and T2108 again — all four already sit inside the board
 * and the ballot below. The one thing that block had that nothing else on
 * the page did was PERCENTILE CONTEXT, so that survives as one line
 * (`Context`) instead of four cards.
 */

const ENV_LABEL = {
  BULLISH: 'Bullish', BEARISH: 'Bearish', MIXED: 'Mixed',
  OVERSOLD: 'Oversold — reversal watch', OVERBOUGHT: 'Overbought — chase risk',
}

const VOTE_LABEL = {
  ratio_5d: '5-day ratio', ratio_10d: '10-day ratio', thrust: 'Thrust',
  qtr_spread: 'Quarterly spread', spread_13_34: '13%/34d spread', nh_nl: 'New highs vs lows',
  mcclellan: 'McClellan', pct200: '% above 200-day', t2108_zone: 'T2108 zone',
  spy_danger: 'SPY warnings', qqq_danger: 'QQQ warnings', bench_trend: 'Benchmark trend',
}

const CTX_LABEL = {
  up_4pct: 'up 4%', down_4pct: 'down 4%', ratio_5d: '5-day ratio',
  qtr_spread: 'qtr spread', t2108: 'T2108', mcclellan_osc: 'McClellan', nh_nl_net: 'NH−NL',
}

function Falsification({ votes, score, env }) {
  if (!votes || typeof score !== 'number') return null
  const entries = Object.entries(votes)
  const bull = entries.filter(([, s]) => s === 'bull')
  const bear = entries.filter(([, s]) => s === 'bear')
  const neutral = entries.filter(([, s]) => s === 'neutral')

  let target, need, side
  if (env === 'BULLISH') { target = 4; need = score - 3; side = bull }
  else if (env === 'BEARISH') { target = -4; need = -3 - score; side = bear }
  else {
    const up = 4 - score, down = score + 4
    if (up <= down) { target = 4; need = up; side = bear } else { target = -4; need = down; side = bull }
  }
  const flips = Math.ceil(need / 2)
  const against = env === 'BEARISH' ? bull : bear

  return (
    <p className="text-[13px] leading-relaxed text-[var(--color-text-secondary)] m-0">
      {env === 'MIXED' ? (
        <>Score <b className="text-[var(--color-text)] font-mono">{score >= 0 ? `+${score}` : score}</b>.
          It turns {target > 0 ? 'bullish' : 'bearish'} at <b className="text-[var(--color-text)] font-mono">
          {target > 0 ? '+4' : '−4'}</b> — {need} away.</>
      ) : (
        <>Score <b className="text-[var(--color-text)] font-mono">{score >= 0 ? `+${score}` : score}</b>.
          It holds while {target > 0 ? '≥ +4' : '≤ −4'}; <b className="text-[var(--color-text)]">{need}</b> points
          break it — <b className="text-[var(--color-text)]">{flips}</b> of the {side.length}{' '}
          {env === 'BEARISH' ? 'bear' : 'bull'} votes crossing over, or {need} going undecided.</>
      )}
      {' '}
      {against.length > 0 ? (
        <>Against: {against.map(([k]) => VOTE_LABEL[k] ?? k).join(', ')}.</>
      ) : (
        <>Nothing is voting against it yet.</>
      )}
      {neutral.length > 0 && <> Undecided: {neutral.map(([k]) => VOTE_LABEL[k] ?? k).join(', ')}.</>}
    </p>
  )
}

export default function VoteCard({ verdict, session }) {
  if (!verdict) return null
  const v = verdict
  const offSession = isWeekend(session)
  const ctx = Object.entries(v.context ?? {})

  return (
    <div className="bg-[var(--color-surface)] rounded-3xl p-5 h-full flex flex-col">
      <div className="flex items-baseline justify-between pb-3 mb-3
                      border-b border-[var(--color-v2-ink)]">
        <h2 className="text-[11px] font-mono uppercase tracking-[.24em]
                       text-[var(--color-text-muted)]">Votes</h2>
        <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
          score {v.score >= 0 ? `+${v.score}` : v.score} / 12
        </span>
      </div>

      <div className="flex items-baseline gap-3 mb-1">
        <span className="text-[17px] font-semibold text-[var(--color-text)]">
          {ENV_LABEL[v.env] ?? v.env}
        </span>
        <span className="text-[13px] text-[var(--color-text-secondary)]">{v.risk} risk · {v.exposure} exposure</span>
      </div>

      {offSession && (
        <p className="text-[11px] leading-relaxed text-[var(--color-signal-caution)] mt-1 mb-0">
          Computed from <b>{session}</b>, a weekend — the ±4% and advance/decline counts behind
          these votes are zero because nothing was counted, not because nothing moved.
        </p>
      )}

      <div className="my-3">
        <VoteGlyphs detail={v.vote_detail} perRow={6} />
      </div>

      <Falsification votes={v.votes} score={v.score} env={v.env} />

      <p className="text-[13px] text-[var(--color-text)] border-t border-[var(--color-border-light)]
                    pt-2.5 mt-2.5 mb-0">
        {v.guidance}
      </p>

      {ctx.length > 0 && (
        <p className="text-[11px] font-mono text-[var(--color-text-muted)] mt-2 mb-0">
          percentile · {ctx.map(([k, p]) => `${CTX_LABEL[k] ?? k} ${p}th`).join(' · ')}
        </p>
      )}
    </div>
  )
}
