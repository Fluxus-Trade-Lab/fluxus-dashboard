import { useMemo } from 'react'
import PageHeader from '../PageHeader'
import DataFreshnessBadge from '../shared/DataFreshnessBadge'
import Reading, { readMarketState } from '../Reading'
import VerdictBanner from './VerdictBanner'
import StateBoard from './StateBoard'
import RotationPanel from './RotationPanel'
import MarketStateSummary from './MarketStateSummary'
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
import Tier from '../Tier'
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
        <div className="text-[var(--color-text-muted)] text-[14px] font-medium uppercase tracking-wide py-8 text-center">
          No breadth data available
        </div>
      </div>
    )
  }

  const verdict = breadth.verdict
  const rows = breadth.history?.rows ?? []

  return (
    <div className="space-y-3">
      <PageHeader group="market" title="Market State"
        meta={['rank is how many cells are filled, never hue alone',
               'an unmeasured condition renders outside the scale',
               'every condition prints the numbers that produced it',
               <DataFreshnessBadge key="fresh"
                 sessionDate={rows[rows.length - 1]?.date} />]} />
      <Reading text={readMarketState(verdict)} />
      <TimeMachineBar tm={tm} />

      {/* SUBJECT — the nine-cell board, first and alone.
          It used to sit third, behind the verdict banner and a full-width style
          ribbon, which meant the page's stated subject was the third thing you
          saw. Nothing is deleted by moving it; the banner becomes what it
          always was, which is a summary OF this. */}
      <StateBoard board={breadth.state_board} session={rows[rows.length - 1]?.date} />

      {/* EVIDENCE — open, but underneath, and smaller. */}
      <Tier label="Evidence" supports="what the board adds up to, and the numbers under it">
        <div className="space-y-3">
          <VerdictBanner verdict={verdict} dataQuality={breadth.data_quality}
                         session={rows[rows.length - 1]?.date} />
          <MarketStateSummary mm={breadth.mm} breadth={breadth.breadth} verdict={verdict} />
          {/* moved off the Dashboard 2026-08-11 (Andy) — the benchmarks' MA
              distances are state evidence, and this is the state page */}
          <TrendStatus signals={data?.signals} />
        </div>
      </Tier>

      {/* Teaching sits with the objects it explains — the board, the chain and
          the summary are one subject, and this closes it before the reference
          begins. */}
      {breadth.state_board?.rows?.length > 0 && (
        <HowToRead>
          <p>
            Each row is one condition, and the cells to its right are how far along
            it is. <b>Rank is how many cells are filled</b> — count them rather than
            judging the colour, because the same fill is used at every level and hue
            alone would be unreadable to a third of people.
          </p>
          <p>
            A row drawn as a <b>dashed outline sitting outside the scale</b> was not
            measured this session. That is different from a row measured at zero:
            one is missing evidence, the other is evidence of nothing happening. The
            board's header prints how many of the {breadth.state_board.total} were
            actually measured.
          </p>
          <p>
            The order is a <b>repair ladder</b>. Conditions near the top break first
            and mend last, so a market repairing from the bottom up is not yet the
            same market as one that never broke. Propagation shows which currents
            carried through — its width is a count, and a current that stops does
            not resume later in the same chain.
          </p>
          <p>
            Everything below this line is reference. It answers <i>where</i> — the
            series, the raw counts, the full archive — never <i>so what</i>. Folded
            because it is not the subject, kept because the denominators live there.
          </p>
        </HowToRead>
      )}

      {/* Its own rail entry until now, which promised a page and delivered an
          empty one. Held here instead: named, reachable, and honest about
          being unbuilt. The rung is not published before it is earned. */}
      <Reference label="Correction risk" count={1}
                 note="not built yet — the slot is reserved, not missing">
        <div className="border border-dashed border-[var(--color-untested)]
                        px-4 py-4 text-[12.5px] leading-relaxed
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

      {/* Everything below answers «where», never «so what».
          This page rendered thirteen objects at equal weight, so none of them
          was the subject. The subject is the verdict, the board and the chain;
          these seven are the reference behind them. Demoted, not deleted — the
          numbers and their denominators are all still here, one click away, and
          each line says what it holds so that skipping it is a decision. */}
      {mh && !mh.stale && (
        <Reference label="Benchmark health" count={2}
                   note="SPY and QQQ price structure with the T2108 overlay">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            <HealthChart title="SPY Market Health" block={mh.spy} state={verdict?.spy_state} t2108={t2108Overlay} />
            <HealthChart title="QQQ Market Health" block={mh.qqq} state={verdict?.qqq_state} t2108={t2108Overlay} />
          </div>
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
  )
}
