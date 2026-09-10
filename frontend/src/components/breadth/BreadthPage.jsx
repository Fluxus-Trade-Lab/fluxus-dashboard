import { useMemo } from 'react'
import PageHeader from '../PageHeader'
import DataFreshnessBadge from '../shared/DataFreshnessBadge'
import Reading, { readMarketState } from '../Reading'
import BoardCard from './BoardCard'
import ChainCard from './ChainCard'
import VoteCard from './VoteCard'
import RotationPanel from './RotationPanel'
import HealthChart from './HealthChart'
import RatioChart from './RatioChart'
import SpreadChart from './SpreadChart'
import DangerPanel from './DangerPanel'
import MarketMonitor from './MarketMonitor'
import ClassicBreadth from './ClassicBreadth'
import BreadthCharts from './BreadthCharts'
import BreadthTable from './BreadthTable'
import TimeMachineBar from './TimeMachineBar'
import { useTimeMachine } from './useTimeMachine'
import Reference from '../Reference'
import HowToRead from '../HowToRead'
import TrendStatus from '../macro/TrendStatus'

export default function BreadthPage({ data }) {
  const tm = useTimeMachine()
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
      <Reading text={readMarketState(verdict)} />
      <TimeMachineBar tm={tm} />

      {/* SUBJECT — the board, first and alone, full width: nine conditions is
          a lot to compare at half a card's width, and it is the one card
          meant to be scanned top to bottom rather than glanced at. */}
      <BoardCard board={breadth.state_board} history={breadth.history} session={session} />

      {/* EVIDENCE — how far the board's repair carried (Chain), and the vote
          that turns it into a call (Votes). Unequal widths on purpose: the
          chain is five short rows, the ballot is twelve dense ones — each
          card gets the room its own content needs, not an even split. */}
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)] gap-3
                      items-stretch">
        <ChainCard chain={breadth.state_board?.chain} />
        <VoteCard verdict={verdict} session={session} />
      </div>

      {/* Teaching sits with the objects it explains. */}
      {breadth.state_board?.rows?.length > 0 && (
        <HowToRead>
          <p>
            盘面每行是一个条件，右边的格子是它走到了第几档——<b>数格子，不看颜色深浅</b>，
            因为深浅在四成人眼里读不出来。旁边的小走势线是这个条件过去 60 天的同一个数，
            读法是「在变好还是在变坏」，不是新数字。
          </p>
          <p>
            虚线格＝这一档<b>没测到</b>，跟「测到是零」是两回事——一个是没证据，
            一个是证据说什么都没发生。表头印着 {breadth.state_board.total} 项里实测了几项。
          </p>
          <p>
            盘面的顺序是一条<b>修复梯子</b>：越靠前的条件坏得越早、好得越晚。传导卡显示这股
            修复走到了第几步——宽度是个计数，断了不会自己接回来。
          </p>
          <p>
            这条线以下都是参考。答的是<i>在哪</i>，不是<i>所以呢</i>——折起来是因为它不是主体，
            留着是因为分母都在那儿。
          </p>
        </HowToRead>
      )}

      {/* REFERENCE — one card, the rows inside it demoted, not the card
          itself. Eight loose section dividers floating on the page ground
          read as unfinished; one surface with thin rules between rows reads
          as a place, the same idiom the three cards above already use. */}
      <div className="bg-[var(--color-surface)] rounded-3xl px-5 py-2">
        {/* Its own rail entry until now, which promised a page and delivered an
            empty one. Held here instead: named, reachable, and honest about
            being unbuilt. The rung is not published before it is earned. */}
        <Reference label="Correction risk" count={1}
                   note="not built yet — the slot is reserved, not missing">
          <div className="border border-dashed border-[var(--color-untested)]
                          px-4 py-4 text-[13px] leading-relaxed
                          text-[var(--color-text-muted)]">
            <p className="m-0 mb-2">Will hold:</p>
            <ul className="m-0 pl-4 space-y-1">
              <li>Distribution-day count against its own threshold, with the sessions named</li>
              <li>How far each benchmark sits below its own high, and for how many sessions</li>
              <li>What would have to break next, in the repair ladder&rsquo;s order</li>
            </ul>
            <p className="m-0 mt-2 text-[11px]">
              Reads breadth.json and market_health.json — both already on disk.
            </p>
          </div>
        </Reference>

        <Reference label="Style rotation" count={1}
                   note="risk-on / risk-off across three cuts — a different question from the nine">
          <RotationPanel />
        </Reference>

        {mh && !mh.stale && (
          <Reference label="Benchmark health" count={3}
                     note="SPY and QQQ price structure, the T2108 overlay, and the MA-distance table">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              <HealthChart title="SPY Market Health" block={mh.spy} state={verdict?.spy_state} t2108={t2108Overlay} />
              <HealthChart title="QQQ Market Health" block={mh.qqq} state={verdict?.qqq_state} t2108={t2108Overlay} />
            </div>
            {/* moved off the Dashboard 2026-08-11 (Andy) — the benchmarks' MA
                distances are state evidence, and this is the state page. Sits
                here rather than as its own row because it is the same two
                benchmarks HealthChart already draws, just as a table. */}
            <TrendStatus signals={data?.signals} />
          </Reference>
        )}

        <Reference label="Ratio and spread" count={2}
                   note="the two series the confirmation vote is computed from">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            <RatioChart rows={rows} />
            <SpreadChart rows={rows} />
          </div>
        </Reference>

        {mh && !mh.stale && (
          <Reference label="Danger signals" count={2}
                     note="the individual warnings behind the risk level above">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              <DangerPanel title="SPY danger signals" danger={mh.spy?.danger} />
              <DangerPanel title="QQQ danger signals" danger={mh.qqq?.danger} />
            </div>
          </Reference>
        )}

        <Reference label="Market monitor" count={1}
                   note="the raw ±4% and advance/decline counts, session by session">
          <MarketMonitor data={breadth} />
        </Reference>

        <Reference label="Classic breadth" count={1}
                   note="T2108, new highs and new lows, on their conventional definitions">
          <ClassicBreadth data={breadth} />
        </Reference>

        <Reference label="Historical series" count={2}
                   note="the full archive as charts and as a table — every row that produced the votes">
          <BreadthCharts data={breadth} />
          <BreadthTable data={breadth} />
        </Reference>
      </div>
    </div>
  )
}
