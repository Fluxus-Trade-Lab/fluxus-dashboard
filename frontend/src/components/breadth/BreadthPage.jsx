import { useMemo } from 'react'
import PageHeader from '../PageHeader'
import DataFreshnessBadge from '../shared/DataFreshnessBadge'
import BoardCard from './BoardCard'
import MarketStateSummary from './MarketStateSummary'
import ChainCard from './ChainCard'
import VoteCard from './VoteCard'
import RotationPanel from './RotationPanel'
import BenchmarkPanel from './BenchmarkPanel'
import CorrectionRiskPanel from './CorrectionRiskPanel'
import RatioChart from './RatioChart'
import SpreadChart from './SpreadChart'
import BreadthCharts from './BreadthCharts'
import BreadthTable from './BreadthTable'
import TimeMachineBar from './TimeMachineBar'
import { useTimeMachine } from './useTimeMachine'
import { useMarketLight } from '../../hooks/useMarketLight'
import { VerdictCard, LightStep, BrightnessStep } from './CourseRead'
import Reference from '../Reference'
import HowToRead from '../HowToRead'

/**
 * Market State, in the course's order (2026-09-11).
 *
 * Andy: 「market state页面还是非常奇怪。是整个组织架构出现了一些问题。」 The page's
 * two subjects — the nine-condition board and the propagation chain — came
 * from a member's review framework and a TSF teardown, not from the course,
 * and the course's own first two steps were nowhere on it. Studio Q ruled
 * (docs/plans/2026-09-11-market-state-by-the-course.md §五) and Andy picked the
 * layout (§六):
 *
 *   main screen = the course's Core — one verdict, Lesson 6's light, Lesson 7's
 *                 brightness (faded when the light is red)
 *   folds       = the course's Mastery — and everything that was never the
 *                 course's, labelled as such
 *
 * The old one-line reading at the top ("5 signals say no…") is gone: a second
 * verdict on the same page is the page arguing with itself (§五.2).
 */
export default function BreadthPage({ data }) {
  const tm = useTimeMachine()
  const { data: ml } = useMarketLight()
  const liveBreadth = data?.breadth
  const breadth = (tm.active && tm.sliced) ? tm.sliced.breadth : liveBreadth
  const mh = (tm.active && tm.sliced) ? tm.sliced.marketHealth : data?.market_health

  // Memoised so the HealthChart setup closure (and therefore the chart redraw
  // effect) only sees a new overlay when the underlying history actually
  // changes — not on every render. Declared before the early return so hook
  // order stays stable.
  const history = breadth?.history
  const t2108Overlay = useMemo(
    () => (history
      ? { dates: history.dates, values: history.rows.map((r) => r.t2108) }
      : null),
    [history],
  )

  if (!liveBreadth) {
    return (
      <div className="space-y-3">
        <TimeMachineBar tm={tm} />
        <div className="text-[var(--color-text-muted)] text-[13px] font-medium uppercase tracking-wide py-8 text-center">
          No breadth data available
        </div>
      </div>
    )
  }

  const verdict = breadth.verdict
  const rows = breadth.history?.rows ?? []
  const session = rows[rows.length - 1]?.date

  return (
    <div className="space-y-3">
      <PageHeader group="market" title="Market State"
        meta={[<DataFreshnessBadge key="fresh" sessionDate={session} />]} />

      {/* CORE — the course's morning read, in Lesson 16 Block 1's order. The
          verdict sits on top because it is the result of reading the two
          steps under it (Lesson 7's IMG-2 draws it the same way). */}
      <VerdictCard ml={ml} />
      <LightStep ml={ml} />
      <BrightnessStep ml={ml} breadthRows={liveBreadth.history?.rows} />

      <HowToRead>
        <p>
          Read top to bottom, the way Lesson 16 reads the morning. <b>Step 1</b> is Lesson 6&rsquo;s traffic
          light: three checks on SPY&rsquo;s 10- and 20-day lines — all three yes is green, anything else is red.
          Beside it, Lesson 6B: how many sessions in a row SPY has closed on one side of its 21-day line, and
          which of the seven gears it is in.
        </p>
        <p>
          <b>Step 2</b> is Lesson 7&rsquo;s brightness — only read when the light is green: how many quality
          setups, whether the leaders are leading, whether breadth confirms. The one word on top is the answer:
          full, dim or avoid. It sets how aggressive to be; it never says which way the market goes.
        </p>
        <p>
          Everything below is the Mastery half — the deeper reads, and two frameworks that are not the
          course&rsquo;s (the board and the chain), kept and labelled as such.
        </p>
      </HowToRead>

      {/* Replay slices breadth only — it sits with the folds it replays. */}
      <TimeMachineBar tm={tm} />

      {/* MASTERY — folded, present but out of the way (§五.6). */}
      <div className="bg-[var(--color-surface)] rounded-3xl px-5 py-2">
        <Reference label="Breadth, advanced" count={4}
                   note="% above the averages, McClellan, the up/down ratios and the quarterly spread (Lesson 7 mastery)">
          <BreadthCharts data={breadth} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            <RatioChart rows={rows} />
            <SpreadChart rows={rows} />
          </div>
        </Reference>

        <Reference label="Votes" count={1}
                   note="twelve breadth and benchmark votes — evidence for Q3, no longer a verdict">
          <VoteCard verdict={verdict} session={session} dataQuality={breadth.data_quality} evidence />
        </Reference>

        {/* Not the course's (§五.3): kept, never the subject, source named. */}
        <Reference label="Board & chain" count={2}
                   note="nine-condition ladder and propagation — a member's review framework, not the course's">
          <div className="space-y-3">
            <BoardCard board={breadth.state_board} history={breadth.history} session={session} />
            <ChainCard chain={breadth.state_board?.chain} />
            {/* the board's own "how to read", restored with it (09-11) */}
            <div className="text-[13px] leading-relaxed text-[var(--color-text-secondary)] space-y-2 px-1">
              <p className="m-0">
                Each row is one condition, and the cells to its right are how far along it is.{' '}
                <b className="text-[var(--color-text)]">Rank is how many cells are filled</b> — count them rather than
                judging the colour. A row drawn as a <b className="text-[var(--color-text)]">dashed outline</b> was not
                measured this session, which is different from a row measured at zero. The board&rsquo;s header prints how
                many of the {breadth.state_board?.total} were actually measured.
              </p>
              <p className="m-0">
                The order is a <b className="text-[var(--color-text)]">repair ladder</b>: conditions near the top break
                first and mend last. The chain shows how far the repair carried — a current that stops does not resume
                later in the same chain.
              </p>
            </div>
          </div>
        </Reference>

        {/* Restored 09-11 (Andy: deleted content goes back into a fold first). */}
        <Reference label="Summary tiles" count={4}
                   note="the old four-tile summary — ±4% thrust, 5/10-day ratio, quarterly 25%, T2108, with their words and percentiles">
          <MarketStateSummary mm={breadth.mm} breadth={breadth.breadth} verdict={verdict} />
        </Reference>

        {/* RND Linda's ruling, DATA_CONTRACTS §七 2026-09-11 (v1 + v2) —
            unchanged by the course reorder (§五.6). */}
        <Reference label="Correction risk" count={3}
                   note="how often a 5% drawdown followed a day like today — a tail reading, not a direction call">
          <CorrectionRiskPanel session={session} />
        </Reference>

        <Reference label="Style rotation" count={1}
                   note="risk-on / risk-off across three cuts">
          <RotationPanel />
        </Reference>

        {mh && !mh.stale && (
          <Reference label="Benchmarks" count={3}
                     note="SPY and QQQ with their five warnings, and how far four indexes sit from each average">
            <BenchmarkPanel mh={mh} verdict={verdict} t2108={t2108Overlay} signals={data?.signals} />
          </Reference>
        )}

        {/* Market monitor (15 tiles) and Classic breadth (9 tiles) were this
            table's first row printed twice more. Andy 09-11: 「并成一张表：今天钉在
            第一行、加粗；不上色，仍然按照原有的上色方式」. */}
        <Reference label="Archive" count={1}
                   note="every session's raw counts — today pinned on top">
          <BreadthTable data={breadth} />
        </Reference>
      </div>
    </div>
  )
}
