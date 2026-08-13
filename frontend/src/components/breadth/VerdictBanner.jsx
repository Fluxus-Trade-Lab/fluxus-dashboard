import { isWeekend } from './session'
import VoteGlyphs from './VoteGlyphs'

const ENV_LABEL = {
  BULLISH: 'Bullish market environment',
  BEARISH: 'Bearish market environment',
  MIXED: 'Mixed market environment',
  OVERSOLD: 'Oversold — reversal watch',
  OVERBOUGHT: 'Overbought — chase risk',
}

export default function VerdictBanner({ verdict, dataQuality, session }) {
  if (!verdict) return null
  const v = verdict
  // This block is the one he screenshots on its own, so a caveat printed further
  // down the page does not reach the reader. It carries its own.
  const offSession = isWeekend(session)

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
      <div className="flex items-baseline justify-between mb-3">
        <div className="flex items-baseline gap-3">
          <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
            Market Environment · Decision First
          </h3>
          {dataQuality?.stale && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-[color-mix(in_srgb,var(--color-signal-caution)_18%,transparent)] text-[var(--color-signal-caution)] uppercase tracking-wide">
              Stale data · as of {dataQuality.as_of ?? '—'}
            </span>
          )}
        </div>
        <span className="text-[10px] font-mono text-[var(--color-text-muted)]">
          score {v.score >= 0 ? `+${v.score}` : v.score} / 12
        </span>
      </div>

      {/* The verdict is a sentence, and sentences do not wear the encoding
          colour — the vote glyphs below already say it in took/refused. */}
      <div className="text-xl font-semibold text-[var(--color-text-bold)]">
        {ENV_LABEL[v.env] ?? v.env}
      </div>

      {offSession && (
        <p className="text-[11px] leading-relaxed text-[var(--color-signal-caution)] mt-1 mb-0">
          Computed from <b>{session}</b>, a weekend — the ±4% and advance/decline counts behind
          these votes are <b>zero because nothing was counted</b>, not because nothing moved.
        </p>
      )}

      <div className="mb-4" />

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-4">
        <Col label="Risk level" value={v.risk} sub={`${v.warn_total} total warnings`} />
        <Col label="Exposure" value={v.exposure} />
        <Col label="SPY" value={v.spy_state ?? '—'} />
        <Col label="QQQ" value={v.qqq_state ?? '—'} />
        <Col label="Alignment" value={v.alignment ?? '—'} />
        <Col label="Breadth confirmation" value={v.confirmation} />
        <Col label="Playbook" value={v.playbook} />
      </div>

      {/* The marks carry the reading; the sentence stays as the fallback for
          payloads written before vote_detail existed, and as the thing a
          screenshot of the top third can still be read from. */}
      {v.vote_detail?.length > 0 && (
        <div className="pt-1 pb-3 border-t border-[var(--color-border-light)] mt-1">
          <VoteGlyphs detail={v.vote_detail} />
        </div>
      )}

      <Falsification votes={v.votes} score={v.score} env={v.env} />

      <p className="text-[12px] text-[var(--color-text)] border-t border-[var(--color-border-light)] pt-3">
        <span className="font-medium">Guidance:</span> {v.guidance}
      </p>
      {v.notes?.length > 0 && (
        <ul className="mt-2 space-y-0.5">
          {v.notes.map((n) => (
            <li key={n} className="text-[11px] text-[var(--color-text-secondary)]">· {n}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

/** Human names for the twelve votes — the payload keys are engine-side. */
const VOTE_LABEL = {
  ratio_5d: '5-day ratio', ratio_10d: '10-day ratio', thrust: 'Thrust',
  qtr_spread: 'Quarterly spread', spread_13_34: '13%/34d spread', nh_nl: 'New highs vs lows',
  mcclellan: 'McClellan', pct200: '% above 200-day', t2108_zone: 'T2108 zone',
  spy_danger: 'SPY warnings', qqq_danger: 'QQQ warnings', bench_trend: 'Benchmark trend',
}

/**
 * The falsification condition — DESIGN.md §5.1 requires every page to carry one:
 * what would have to appear to change this judgment, current value against
 * required value.
 *
 * It is computable exactly, so it is stated exactly rather than described. The
 * engine is `score = bulls − bears`, BULLISH at ≥ 4 and BEARISH at ≤ −4
 * (pipeline/screeners/breadth_signals.py). A vote crossing all the way to the
 * other side moves the score by 2; a vote going neutral moves it by 1.
 *
 * What is NOT claimed: which votes are closest to turning. The payload carries
 * each vote's side, not its margin, so ranking them would be invention. The
 * ones already not on the verdict's side are named because that much is known.
 */
function Falsification({ votes, score, env }) {
  if (!votes || typeof score !== 'number') return null
  const entries = Object.entries(votes)
  const bull = entries.filter(([, s]) => s === 'bull')
  const bear = entries.filter(([, s]) => s === 'bear')
  const neutral = entries.filter(([, s]) => s === 'neutral')

  // distance to the nearest boundary the verdict would have to cross
  let target, need, side
  if (env === 'BULLISH') { target = 4; need = score - 3; side = bull }
  else if (env === 'BEARISH') { target = -4; need = -3 - score; side = bear }
  else { // MIXED sits between the two, so name whichever edge is closer
    const up = 4 - score, down = score + 4
    if (up <= down) { target = 4; need = up; side = bear }
    else { target = -4; need = down; side = bull }
  }
  const flips = Math.ceil(need / 2)
  const against = env === 'BEARISH' ? bull : bear

  return (
    <div className="border-t border-[var(--color-border-light)] pt-3 mt-1">
      <div className="text-[9px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] mb-1.5">
        What would change this
      </div>
      <p className="text-[12px] leading-relaxed text-[var(--color-text-secondary)] m-0">
        {env === 'MIXED' ? (
          <>Score is <b className="text-[var(--color-text)]">{score >= 0 ? `+${score}` : score}</b>.
            It becomes {target > 0 ? 'BULLISH' : 'BEARISH'} at{' '}
            <b className="text-[var(--color-text)]">{target > 0 ? '≥ +4' : '≤ −4'}</b> — {need} away.</>
        ) : (
          <>Score is <b className="text-[var(--color-text)]">{score >= 0 ? `+${score}` : score}</b>.
            This reading holds while it stays {target > 0 ? '≥ +4' : '≤ −4'}, so it takes{' '}
            <b className="text-[var(--color-text)]">{need} points</b> to break —{' '}
            <b className="text-[var(--color-text)]">{flips}</b> of the {side.length}{' '}
            {env === 'BEARISH' ? 'bear' : 'bull'} votes crossing all the way over, or {need} of them
            going undecided.</>
        )}
        {' '}
        {against.length > 0 ? (
          <>Already against it: {against.map(([k]) => VOTE_LABEL[k] ?? k).join(', ')}.</>
        ) : (
          <>Nothing is voting against it yet.</>
        )}
        {neutral.length > 0 && <> Undecided: {neutral.map(([k]) => VOTE_LABEL[k] ?? k).join(', ')}.</>}
      </p>
    </div>
  )
}

function Col({ label, value, sub }) {
  return (
    <div>
      <div className="text-[9px] font-medium uppercase tracking-wider text-[var(--color-text-muted)] mb-1">
        {label}
      </div>
      <div className="text-[12px] text-[var(--color-text)] leading-snug">{value}</div>
      {sub && <div className="text-[10px] text-[var(--color-text-secondary)]">{sub}</div>}
    </div>
  )
}
