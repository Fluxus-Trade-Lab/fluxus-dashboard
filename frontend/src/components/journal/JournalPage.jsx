import AnalyticsTab from './AnalyticsTab'
import CoachTab from './CoachTab'
import RiskTab from './RiskTab'
import SizingTab from './SizingTab'
import PageHeader from '../PageHeader'
import { useLanguage } from '../../i18n/LanguageContext'
import StageCard from './StageCard'
import Verdict from './Verdict'
import Zone, { Tool } from './Zone'
import { useTradeJournal } from '../../hooks/useTradeJournal'
import { stageLeaks, STAGES } from './lib/headCoach'
import HoldCaptureSection from './analytics/HoldCaptureSection'
import AfterLossSection from './analytics/AfterLossSection'
import SetupEdgeSection from './analytics/SetupEdgeSection'
import SetupChat from './SetupChat'
import { PortfolioProvider } from '../portfolio/context/PortfolioContext'


/**
 * Four coaches and one head coach — formerly eighteen tabs.
 *
 * The eighteen were sorted by KIND of metric, so several answered the same
 * question and four were empty shells with "Coming soon" under them. These
 * four are sorted by WHEN the decision happens in a trade's life, which means
 * any trade lands in exactly one of them and the overlaps dissolve.
 *
 * The head coach does not add a fifth reading. It ranks these four by what
 * each left on the table per trade and names one, because a person changes one
 * thing at a time.
 *
 * The LLM chats (Episodic Pivot, VCP, Breakout) are setup conversations and
 * belong to Selection. News Failure, Option Positioning and Tape Reading were
 * never built and are gone rather than promised.
 */
/**
 * A stage is three bands, not a strip of tabs.
 *
 *   test    the reading — one per stage, the reason the stage exists
 *   ledger  where the money went, and it has to add up
 *   tools   things you open when you want them; no numbers on the outside
 *
 * The eighteen tabs became four stages became this. What changed at each step
 * was not how many things there are — it was whether the page says what KIND
 * of thing each one is.
 */
const ZONES = {
  select: { test: 'setup-edge', ledger: null, tools: ['setup-chat'] },
  size:   { test: 'size-vs-r',  ledger: null, tools: ['sizing'] },
  hold:   { test: 'hold-capture', ledger: null, tools: ['stop-sim', 'trim-stops'] },
  stop:   { test: 'after-loss', ledger: 'behavior', tools: ['demon-finder', 'diagnosis'] },
}

/** Sections that live inside AnalyticsTab and are reached by its own key. */
const ANALYTICS_KEYS = new Set(['trim-stops', 'demon-finder', 'behavior',
                                'diagnosis', 'size-vs-r'])

/** One place that maps a section key to its component. */
function render(key) {
  switch (key) {
    case 'hold-capture': return <HoldCaptureSection />
    case 'after-loss': return <AfterLossSection />
    case 'setup-edge': return <SetupEdgeSection />
    case 'sizing': return <SizingTab />
    case 'stop-sim': return <RiskTab />
    case 'setup-chat': return <SetupChat />
    default: return <AnalyticsTab initialSection={key} key={key} />
  }
}

export default function JournalPage({ stage: routeStage }) {
  const { t } = useLanguage()
  const { trades } = useTradeJournal()

  const go = (key) => { window.location.hash = key ? `#/review/${key}` : '#/review' }

  // The stage the ranking points at. It decides which card wears the flag —
  // and that flag, plus the four readings beside it, is the whole verdict.
  // The sentence that used to sit above them said the same thing again.
  const lead = stageLeaks(trades)[0]?.stage

  // ── Overview ───────────────────────────────────────────────────────────
  if (!routeStage || !ZONES[routeStage]) {
    return (
      <div className="max-w-5xl mx-auto py-6 px-4">
        <PageHeader group="book" title={t('nav.journal')} />
        <Verdict onGo={go} />
        <p className="text-[13px] text-[var(--color-text-secondary)] mt-1 mb-5 max-w-[62ch]">
          {t('rev.overview.lede')}
        </p>
        {/* One store for the page. The sizing card reads the portfolio's own
            trades, and the monthly-review panel below mounts a provider of its
            own — hoisting it here means both share a single store instead of
            two writers pushing the same Sheet. */}
        <PortfolioProvider>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
            {STAGES.map(({ key }) => (
              <StageCard key={key} stageKey={key} trades={trades}
                         lead={key === lead} onOpen={go} />
            ))}
          </div>

        {/* Andy's own words about the period. Not inside a stage — it is about
            all four — and its own entrance, per his call. */}
        <details className="mt-6">
          <summary className="text-[11px] font-mono uppercase tracking-[.18em]
                              text-[var(--color-text-muted)] cursor-pointer list-none
                              hover:text-[var(--color-text)]">{t('rev.monthly')} +</summary>
            <div className="mt-3"><AnalyticsTab initialSection="monthly-review" /></div>
          </details>
        </PortfolioProvider>

        <p className="text-[11px] text-[var(--color-text-muted)] mt-5 max-w-[70ch]">
          {t('rev.report.hint')}
        </p>
        <code className="inline-block mt-1.5 text-[10.5px] font-mono
                         text-[var(--color-text-secondary)]
                         bg-[var(--color-hover-bg)] rounded px-2 py-1">
          {t('rev.report.cmd')}
        </code>
      </div>
    )
  }

  // ── One stage ──────────────────────────────────────────────────────────
  const z = ZONES[routeStage]

  return (
    <div className="max-w-5xl mx-auto py-6 px-4">
      <button type="button" onClick={() => go(null)}
              className="text-[11px] font-mono text-[var(--color-text-muted)] bg-transparent
                         border-none p-0 cursor-pointer hover:text-[var(--color-text)]">
        ‹ {t('nav.journal')}
      </button>
      <h1 className="text-[34px] font-bold leading-tight mt-1 mb-0.5">
        {t(`rev.stage.${routeStage}`)}
      </h1>
      <p className="text-[12.5px] text-[var(--color-text-muted)] m-0">
        {t(`rev.asks.${routeStage}`)}
      </p>

      <Zone kind="test">{render(z.test)}</Zone>

      {z.ledger && <Zone kind="ledger">{render(z.ledger)}</Zone>}

      {z.tools.length > 0 && (
        <Zone kind="tool">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {z.tools.map((k) => (
              <Tool key={k} title={t(`rev.sec.${k}`)} blurb={t(`tool.blurb.${k}`)}>
                {render(k)}
              </Tool>
            ))}
          </div>
        </Zone>
      )}
    </div>
  )
}
