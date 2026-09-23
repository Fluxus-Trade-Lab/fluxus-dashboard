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
import MorningRead from './MorningRead'
import { useGroups } from '../../hooks/useGroups'
import { useGroupsHistory } from '../../hooks/useGroupsHistory'
import { useWatchlist } from '../../hooks/useWatchlist'
import { useCorrectionRisk } from '../../hooks/useCorrectionRisk'
import Reference from '../Reference'
import HowToRead from '../HowToRead'

/**
 * Market State — the course's morning walk (2026-09-23).
 *
 * 09-11 put the old course's Core (light → brightness) on top and folded the
 * rest. Then the course was rewritten as 地基篇 ch.1–7, and Andy (09-23):
 * 「整个页面包括折叠的部分，形式太乱，内容没有逻辑和思考脉络」. Two previews later he
 * picked the skeleton: 「A 的骨架，把B它的「四问对照表」搬进 A 的第①段当指数那格的正文」.
 *
 *   main screen = MorningRead: verdict, then ch.7 §7.2's six steps in its
 *                 fixed order, each with a "what changed" column
 *   folds       = ch.1 §1.10's advanced read — the nine-row board and the
 *                 fifteen conditions (awaiting Andy's cut), Stockbee's rulers,
 *                 the engine's votes, Correction risk, rotation, benchmarks,
 *                 and the archive
 */
export default function BreadthPage({ data }) {
  const tm = useTimeMachine()
  const { data: ml } = useMarketLight()
  const groups = useGroups()
  const gh = useGroupsHistory()
  const { data: watchlist } = useWatchlist()
  const { data: correctionRisk } = useCorrectionRisk()
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

      {/* CORE — the morning walk, ch.7 §7.2's order. */}
      <MorningRead ml={ml} signals={data?.signals} rows={liveBreadth.history?.rows}
                   themes={groups.themes} groupsHistory={gh.data} watchlist={watchlist}
                   etfs={data?.etf_data} correctionRisk={correctionRisk} />

      <HowToRead>
        <p>
          Read top to bottom, in the order Foundations ch.7 §7.2 fixes for the morning: index, breadth, RS
          leadership, RS themes, news, your own book. The one word on top is the answer — full, dim or avoid. It
          sets how aggressive to be; it never says which way the market goes.
        </p>
        <p>
          <b>Step ①</b> is ch.1&rsquo;s four questions on one table (daily, weekly, last week, new highs − lows) with
          the light&rsquo;s own history under it. <b>Steps ②–⑥</b> are the rest of the walk; the column on the right
          of each says what changed, because that is what a morning read is for.
        </p>
        <p>
          Below the walk is ch.1 §1.10&rsquo;s advanced read, folded: the nine-row board and the fifteen conditions
          (awaiting Andy&rsquo;s cut), Stockbee&rsquo;s rulers, the engine&rsquo;s votes, and the research panels.
        </p>
      </HowToRead>

      {/* Replay slices breadth only — it sits with the folds it replays. */}
      <TimeMachineBar tm={tm} />

      {/* ADVANCED — ch.1 §1.10, folded: present but out of the way. */}
      <div className="bg-[var(--color-surface)] rounded-3xl px-5 py-2">
        <Reference label="Breadth, advanced" count={4}
                   note="% above the averages, McClellan, the up/down ratios and the quarterly spread (§7.6 rulers, as charts)">
          <BreadthCharts data={breadth} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            <RatioChart rows={rows} />
            <SpreadChart rows={rows} />
          </div>
        </Reference>

        <Reference label="Votes" count={1}
                   note="the engine's twelve votes — evidence for step ②, never a verdict">
          <VoteCard verdict={verdict} session={session} dataQuality={breadth.data_quality} evidence />
        </Reference>

        {/* ch.1 §1.10 lists this board's nine rows and the fifteen conditions as the
            advanced read — pending Andy's cut (09-21: 「先放上去，然后我们做筛选」). */}
        <Reference label="Board & chain" count={2}
                   note="the nine-row board and its chain — ch.1 §1.10's advanced read, awaiting Andy's cut">
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
        <Reference label="Stockbee rulers" count={4}
                   note="±4% thrust, 5/10-day ratio, quarterly 25%, T2108 — §7.6's count-based rulers, with their votes and percentiles">
          <MarketStateSummary mm={breadth.mm} breadth={breadth.breadth} verdict={verdict} lastRow={rows[rows.length - 1]} />
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
