import { isWeekend } from './session'
import VoteGlyphs from './VoteGlyphs'

/**
 * 投票 · Votes — the twelve-way ballot that produces the score, one card.
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
  BULLISH: '偏多', BEARISH: '偏空', MIXED: '混合',
  OVERSOLD: '超卖 — 等反弹', OVERBOUGHT: '超买 — 追涨有风险',
}

const VOTE_LABEL = {
  ratio_5d: '5日比率', ratio_10d: '10日比率', thrust: '推力',
  qtr_spread: '季度价差', spread_13_34: '13/34天价差', nh_nl: '新高新低',
  mcclellan: 'McClellan', pct200: '200日以上占比', t2108_zone: 'T2108',
  spy_danger: 'SPY 警报', qqq_danger: 'QQQ 警报', bench_trend: '基准趋势',
}

const CTX_LABEL = {
  up_4pct: '涨4%', down_4pct: '跌4%', ratio_5d: '5日比率',
  qtr_spread: '季度价差', t2108: 'T2108', mcclellan_osc: 'McClellan', nh_nl_net: '新高新低净额',
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
        <>score <b className="text-[var(--color-text)] font-mono">{score >= 0 ? `+${score}` : score}</b>，
          变成{target > 0 ? '偏多' : '偏空'}需要到 <b className="text-[var(--color-text)] font-mono">
          {target > 0 ? '+4' : '−4'}</b> —— 还差 {need}。</>
      ) : (
        <>score <b className="text-[var(--color-text)] font-mono">{score >= 0 ? `+${score}` : score}</b>，
          守住 {target > 0 ? '≥+4' : '≤−4'} 才成立，差 <b className="text-[var(--color-text)]">{need}</b> 分会破 ——
          {' '}{side.length} 票{env === 'BEARISH' ? '偏空' : '偏多'}里翻 <b className="text-[var(--color-text)]">{flips}</b> 票
          到对面，或 {need} 票变中立就破。</>
      )}
      {' '}
      {against.length > 0 ? (
        <>已经反对：{against.map(([k]) => VOTE_LABEL[k] ?? k).join('、')}。</>
      ) : (
        <>目前没有票反对。</>
      )}
      {neutral.length > 0 && <> 中立：{neutral.map(([k]) => VOTE_LABEL[k] ?? k).join('、')}。</>}
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
                       text-[var(--color-text-muted)]">投票 · Votes</h2>
        <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
          score {v.score >= 0 ? `+${v.score}` : v.score} / 12
        </span>
      </div>

      <div className="flex items-baseline gap-3 mb-1">
        <span className="text-[17px] font-semibold text-[var(--color-text-bold)]">
          {ENV_LABEL[v.env] ?? v.env}
        </span>
        <span className="text-[11px] text-[var(--color-text-secondary)]">{v.risk} · {v.exposure}</span>
      </div>

      {offSession && (
        <p className="text-[11px] leading-relaxed text-[var(--color-signal-caution)] mt-1 mb-0">
          算的是 <b>{session}</b>，周末 —— 背后 ±4% 和涨跌家数是零因为没交易，不是没波动。
        </p>
      )}

      <div className="my-3">
        <VoteGlyphs detail={v.vote_detail} />
      </div>

      <Falsification votes={v.votes} score={v.score} env={v.env} />

      <p className="text-[13px] text-[var(--color-text)] border-t border-[var(--color-border-light)]
                    pt-2.5 mt-2.5 mb-0">
        {v.guidance}
      </p>

      {ctx.length > 0 && (
        <p className="text-[11px] font-mono text-[var(--color-text-muted)] mt-2 mb-0">
          分位：{ctx.map(([k, p]) => `${CTX_LABEL[k] ?? k} ${p}th`).join(' · ')}
        </p>
      )}
    </div>
  )
}
