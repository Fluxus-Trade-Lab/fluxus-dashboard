import { isWeekend } from './session'
import VoteGlyphs from './VoteGlyphs'
import { readMarketState } from '../Reading'

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

/** The breadth engine's context fields — the seven columns the old
 *  VerdictBanner printed. Folding that banner into this card on 2026-09-11
 *  dropped five of them (warnings, alignment, confirmation, playbook, notes)
 *  and the stale-data badge; Andy caught it the same day: 「原有的数据它可能
 *  只是以不同的前端形式而呈现了。是不是这样子」. They are back, every one. */
function EngineFields({ v }) {
  const cols = [
    ['Risk level', v.risk, v.warn_total != null ? `${v.warn_total} total warnings` : null],
    ['Exposure', v.exposure],
    ['SPY', v.spy_state],
    ['QQQ', v.qqq_state],
    ['Alignment', v.alignment],
    ['Breadth confirmation', v.confirmation],
    ['Playbook', v.playbook],
  ]
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-2.5 mt-3 pt-3 border-t border-[var(--color-border-light)]">
      {cols.map(([label, value, sub]) => (
        <div key={label}>
          <div className="text-[11px] uppercase tracking-wider text-[var(--color-text-muted)]">{label}</div>
          <div className="text-[13px] leading-snug text-[var(--color-text)]">{value ?? '—'}</div>
          {sub && <div className="text-[11px] text-[var(--color-text-secondary)]">{sub}</div>}
        </div>
      ))}
    </div>
  )
}

/**
 * `evidence` (2026-09-11, Studio Q's ruling §五.2): on the course-ordered page
 * the ballot is Lesson 7-Q3's evidence — "is breadth confirming?" — not a
 * market call: the header says so and the tally comes first. The engine's own
 * word, score, falsification and guidance are NOT dropped — Andy 09-11, "the
 * old data, only presented differently" — they sit under a label that says
 * they are the engine's reading for reference, not the page's verdict.
 */
export default function VoteCard({ verdict, session, dataQuality, evidence = false }) {
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
          {dataQuality?.stale && (
            <span className="mr-2 px-1.5 py-0.5 rounded text-[var(--color-signal-caution)] bg-[color-mix(in_srgb,var(--color-signal-caution)_18%,transparent)] uppercase tracking-wide">
              Stale data · as of {dataQuality.as_of ?? '—'}
            </span>
          )}
          {evidence ? 'twelve votes — evidence for Q3, not a call' : `score ${v.score >= 0 ? `+${v.score}` : v.score} / 12`}
        </span>
      </div>

      {evidence && (() => {
        const tally = Object.values(v.votes ?? {}).reduce((a, s) => ({ ...a, [s]: (a[s] ?? 0) + 1 }), {})
        return (
          <p className="m-0 mb-1 text-[13px] text-[var(--color-text-secondary)]">
            <b className="font-semibold text-[var(--color-text)]">{tally.bull ?? 0}</b> confirming ·{' '}
            <b className="font-semibold text-[var(--color-text)]">{tally.bear ?? 0}</b> not confirming ·{' '}
            <b className="font-semibold text-[var(--color-text)]">{tally.neutral ?? 0}</b> undecided
          </p>
        )
      })()}

      {!evidence && <div className="flex items-baseline gap-3 mb-1">
        <span className="text-[17px] font-semibold text-[var(--color-text)]">
          {ENV_LABEL[v.env] ?? v.env}
        </span>
      </div>}

      {offSession && (
        <p className="text-[11px] leading-relaxed text-[var(--color-signal-caution)] mt-1 mb-0">
          Computed from <b>{session}</b>, a weekend — the ±4% and advance/decline counts behind
          these votes are zero because nothing was counted, not because nothing moved.
        </p>
      )}

      <div className="my-3">
        <VoteGlyphs detail={v.vote_detail} perRow={6} />
      </div>

      {/* Evidence mode moves the engine's own call into a labelled block rather
          than dropping it — Andy 09-11: the page may re-present the old data,
          not lose it. It is kept, and it is not the page's verdict. */}
      {evidence && (
        <div className="mt-1 pt-3 border-t border-[var(--color-border-light)]">
          <div className="text-[11px] font-mono uppercase tracking-[.14em] text-[var(--color-text-muted)] mb-1.5">
            The breadth engine&rsquo;s own reading — for reference, not today&rsquo;s call
          </div>
          <p className="m-0 mb-1.5 text-[13px] text-[var(--color-text-secondary)]">
            <b className="font-semibold text-[var(--color-text)]">{ENV_LABEL[v.env] ?? v.env}</b>
            {' '}· score {v.score >= 0 ? `+${v.score}` : v.score} / 12
          </p>
          {/* the sentence that used to head the whole page, 09-11 */}
          <p className="m-0 mb-1.5 text-[13px] text-[var(--color-text)]">{readMarketState(v)}</p>
        </div>
      )}

      <Falsification votes={v.votes} score={v.score} env={v.env} />

      <p className="text-[13px] text-[var(--color-text)] border-t border-[var(--color-border-light)]
                    pt-2.5 mt-2.5 mb-0">
        {v.guidance}
      </p>

      <EngineFields v={v} />
      {v.notes?.length > 0 && (
        <ul className="mt-2 mb-0 pl-0 list-none space-y-0.5">
          {v.notes.map((n) => <li key={n} className="text-[11px] text-[var(--color-text-secondary)]">· {n}</li>)}
        </ul>
      )}

      {ctx.length > 0 && (
        <p className="text-[11px] font-mono text-[var(--color-text-muted)] mt-2 mb-0">
          percentile · {ctx.map(([k, p]) => `${CTX_LABEL[k] ?? k} ${p}th`).join(' · ')}
        </p>
      )}
    </div>
  )
}
