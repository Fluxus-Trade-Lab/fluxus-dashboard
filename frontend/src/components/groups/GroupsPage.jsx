import { useMemo, useState } from 'react'
import PageHeader from '../PageHeader'
import DataUnavailable from '../DataUnavailable'
import Reading, { readThemes } from '../Reading'
import { useGroups } from '../../hooks/useGroups'
import GroupTable from './GroupTable'
import ThemeBars, { barStyle } from './ThemeBars'
import RsSegments from './RsSegments'
import CompareBar from './CompareBar'
import DistributionStrip from './DistributionStrip'
import TrajectoryPanel from './TrajectoryPanel'
import ThemeMembers from './ThemeMembers'
import { useThemeCompare } from './useThemeCompare'
import { useSpyRow } from './useSpyRow'
import Reference from '../Reference'
import HowToRead from '../HowToRead'

/**
 * Themes — the rotation instrument. Three sections, one control bar.
 *
 * The controls live in ONE sticky bar: tabs, window, selection. Scattered
 * controls each grow a caption explaining themselves; gathered in one place
 * they explain each other, and the sticky bar doubles as the interaction's
 * receipt — a row clicked at rank 60 fills a slot that is still on screen.
 *
 * The sections, in reading order:
 *
 *   FIELD     is picking worth anything today?
 *   COMPARE   is your pick a trend or a bounce?
 *   RANKED    the full order, and the place selections are made from.
 *
 * Compare sits ABOVE the 70-row ranking although it depends on it, because
 * an instrument that responds three screens below the gesture reads as
 * broken. The empty state is one quiet line, not a lecture.
 *
 * All teaching lives in HowToRead at the bottom. The objects themselves are
 * silent — the page used to carry seven captions and two duplicate legends,
 * which is a textbook, not a panel.
 */

/**
 * All three windows use the pipeline's own excess construction — theme return
 * minus benchmark return over the same window. rs_0_1w IS that for one week
 * (the first disjoint bucket reduces to perf_1w − SPY.perf_1w); 3M ships as
 * excess_3m; 1M derives the same way and needs SPY's row, so the button waits
 * for it rather than guessing a zero line.
 */
const WINDOWS = [
  { key: '1W', hl: [3], value: (r) => r.rs_0_1w },
  {
    key: '1M', hl: [2, 3],
    value: (r, spy) => (r.perf_1m != null && spy?.perf_1m != null
      ? r.perf_1m - spy.perf_1m : null),
    needsSpy: true,
  },
  { key: '3M', hl: [1, 2, 3], value: (r) => r.excess_3m },
]

/** Legend and census in one object: each state's swatch wears its own count. */
function StateCensus({ rows }) {
  const counts = rows.reduce((acc, r) => {
    if (r.state) acc[r.state] = (acc[r.state] ?? 0) + 1
    return acc
  }, {})
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px]
                    text-[var(--color-text-muted)]">
      {['Leading', 'Weakening', 'Improving', 'Lagging'].map((s) => (
        <span key={s} className="flex items-center gap-1.5">
          <i className="inline-block w-3 h-[9px]" style={barStyle(s)} />
          {s} <span className="tabular-nums text-[var(--color-text-secondary)]">
            {counts[s] ?? 0}</span>
        </span>
      ))}
    </div>
  )
}

/**
 * The sentence Andy read off TSF's chart, computed instead of typed:
 * "AI - Datacenters is lagging based on past 1 week performance."
 *
 * Two rules keep it honest. It NAMES ITS WINDOW, because the same theme can
 * lead the week and trail the quarter — a verdict without its clock is how
 * two true readings turn into one false one. And the official state word
 * rides in parentheses with a tooltip saying it runs on month-scale windows
 * (FOUR_STATE_DESIGN: every faster scheme flipped sign between half-samples)
 * — the switch does not change it, and pretending it did would be a second
 * definition of the same word.
 */
function CompareReading({ picks, windowed, winKey }) {
  if (!picks.length) return null
  const byName = new Map(windowed.map((r) => [r.group, r]))
  const read = picks
    .map((pick) => ({ pick, row: byName.get(pick.name) }))
    .filter((x) => x.row && Number.isFinite(x.row._value))
    .sort((a, b) => b.row._value - a.row._value)
  if (!read.length) return null

  const word = (v) => (v > 0.01 ? 'leads SPY' : v < -0.01 ? 'trails SPY' : 'is even with SPY')
  const windowName = { '1W': 'the past week', '1M': 'the past month', '3M': 'the past quarter' }[winKey]

  return (
    <p className="m-0 mb-2.5 text-[12.5px] leading-relaxed border-l-2
                  border-[var(--color-border)] pl-3 text-[var(--color-text-secondary)]">
      Over {windowName}:{' '}
      {read.map(({ pick, row }, i) => (
        <span key={pick.name}>
          {i > 0 && (i === read.length - 1 ? ' while ' : ', ')}
          <span style={{ color: pick.colour, fontWeight: 600 }}>{pick.name}</span>
          {' '}{word(row._value)} at {row._value > 0 ? '+' : ''}{(row._value * 100).toFixed(1)}%
          {row.state && (
            <span className="text-[var(--color-text-muted)] cursor-help"
                  title="the state label runs on month-scale windows, not this switch — faster schemes flipped sign between half-samples">
              {' '}({row.state})
            </span>
          )}
        </span>
      ))}
      .
    </p>
  )
}

function Section({ label, note, right, children }) {
  return (
    <section className="pt-2">
      <div className="flex items-baseline gap-3 pb-2.5">
        <span className="text-[10px] font-mono font-medium uppercase tracking-[.24em]
                         text-[var(--color-text-muted)]">{label}</span>
        {note && <span className="text-[11px] text-[var(--color-text-muted)]">{note}</span>}
        <i className="flex-1 h-px bg-[var(--color-border)]" />
        {right}
      </div>
      {children}
    </section>
  )
}

export default function GroupsPage() {
  const { industries, themes, provisional, stocks, summary, date, benchmark, loading, error } =
    useGroups()
  const [winKey, setWinKey] = useState('3M')
  // Which picks have their member table open. Keyed by name, survives
  // re-picks; the panel itself only mounts (and only fetches the universe)
  // while open.
  const [openMembers, setOpenMembers] = useState(() => new Set())
  const spy = useSpyRow()
  const compare = useThemeCompare()

  const byName = useMemo(() => {
    const m = new Map()
    for (const r of [...themes, ...provisional, ...industries]) m.set(r.group, r)
    return m
  }, [themes, provisional, industries])

  if (loading) {
    return <div className="text-[var(--color-text-muted)] text-[14px] py-8 text-center">
      Loading groups…
    </div>
  }
  if (error) {
    return <DataUnavailable
      group="market" title="Themes"
      what="The theme rankings did not load."
      why="They are read from a file the daily pipeline writes; if today's run has not finished, or did not finish, there is nothing here to rank."
      command="python -m pipeline.themes.build_groups" />
  }

  // Themes only. The tabs are gone by subtraction: Industries was one chart
  // with no interaction wearing a page's worth of rows — that layer already
  // lives on the Dashboard's industry and sector cards — and Provisional's
  // honest home is the count in the header, not a tab. Both datasets stay in
  // groups.json untouched.
  const rows = themes
  const win = WINDOWS.find((w) => w.key === winKey)
  const windowed = rows.map((r) => ({ ...r, _value: win.value(r, spy) }))
  const measured = windowed.filter((r) => Number.isFinite(r._value)).length
  // One scale for the dots and the bars — one axis, one instrument.
  const scale = windowed.reduce(
    (m, r) => (Number.isFinite(r._value) ? Math.max(m, Math.abs(r._value)) : m), 0) || 1

  const colourOf = compare.colourOf
  const onToggle = compare.toggle

  // Controls are typography, not boxes: state is carried by weight and an
  // underline, never by a filled pill. Borders on this page are reserved for
  // separating data from data.
  const seg = (active) => `px-0.5 pb-[3px] text-[12.5px] bg-transparent border-0
    border-b-2 cursor-pointer transition-colors
    ${active ? 'text-[var(--color-text)] font-semibold border-[var(--color-text)]'
             : 'text-[var(--color-text-muted)] border-transparent hover:text-[var(--color-text)]'}`

  return (
    <div className="space-y-5">
      <PageHeader group="market" title="Themes"
        meta={[`vs ${benchmark} · ${date} · ${themes.length} themes`]} />
      <Reading text={readThemes(themes)} />

      {/* THE CONTROL BAR — every control on the page, in one sticky line. */}
      <div className="sticky top-0 z-20 -mx-3 px-3 py-2.5 border-b border-[var(--glass-edge)]"
           style={{ background: 'var(--glass)', backdropFilter: 'var(--glass-blur)',
                    WebkitBackdropFilter: 'var(--glass-blur)' }}>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
          <div className="flex gap-3.5">
            {WINDOWS.map((w) => {
              const waiting = w.needsSpy && !spy
              return (
                <button key={w.key} type="button"
                        onClick={() => !waiting && setWinKey(w.key)}
                        disabled={waiting}
                        className={`${seg(w.key === winKey)} font-mono
                                    ${waiting ? 'opacity-40 cursor-wait' : ''}`}>
                  {w.key}
                </button>
              )
            })}
          </div>
          <i aria-hidden className="h-[14px] w-px bg-[var(--color-border)]" />
          <CompareBar rows={rows} picks={compare.picks} atLimit={compare.atLimit}
                      onToggle={compare.toggle} />
        </div>
      </div>

      <Section label="Field">
        <DistributionStrip rows={windowed} scale={scale}
                           colourOf={colourOf} onToggle={onToggle}
                           atLimit={compare.atLimit} dim={compare.picks.length > 0} />
      </Section>

      <Section label="Compare">
        <CompareReading picks={compare.picks} windowed={windowed} winKey={winKey} />
        <TrajectoryPanel picks={compare.picks} byName={byName} highlight={win.hl} />

        {/* The set behind each chosen average. A theme's bar is a claim about
            members you cannot see; one fold per pick opens them on the
            screener's own measurements. Mounted lazily — the 5,615-row
            universe is fetched the first time a fold opens, not on page load. */}
        {compare.picks.map((pick) => {
          const row = byName.get(pick.name)
          if (!row?.tickers?.length) return null
          const open = openMembers.has(pick.name)
          return (
            <div key={pick.name} className="mt-2">
              <button type="button"
                      onClick={() => setOpenMembers((prev) => {
                        const next = new Set(prev)
                        if (next.has(pick.name)) next.delete(pick.name)
                        else next.add(pick.name)
                        return next
                      })}
                      className="w-full flex items-baseline gap-2.5 bg-transparent border-0
                                 p-0 cursor-pointer text-left group">
                <span className="text-[10px] font-mono text-[var(--color-text-muted)]
                                 group-hover:text-[var(--color-text)] w-3">
                  {open ? '−' : '+'}
                </span>
                <span className="text-[11px] font-medium" style={{ color: pick.colour }}>
                  {pick.name}
                </span>
                <span className="text-[10px] font-mono text-[var(--color-text-muted)]">
                  {row.members} members
                </span>
              </button>
              {open && (
                <div className="pl-[22px] pt-1.5">
                  <ThemeMembers theme={row} colour={pick.colour} rsByTicker={stocks} />
                </div>
              )}
            </div>
          )
        })}
      </Section>

      <Section label="Ranked"
               note={`${measured} of ${rows.length} measured · scale ±${(scale * 100).toFixed(0)}%`}
               right={<StateCensus rows={rows} />}>
        <ThemeBars rows={windowed} scale={scale}
                   colourOf={colourOf} onToggle={onToggle}
                   atLimit={compare.atLimit} dim={compare.picks.length > 0} />
      </Section>

      <Reference label="Where the lead was earned" count={20}
                 note="top 20, all four stretches">
        <RsSegments rows={rows} />
      </Reference>

      <Reference label="Full table" count={rows.length}
                 note="all columns, sortable">
        <GroupTable rows={rows} showMethod emptyNote="No groups" />
      </Reference>

      <HowToRead>
        <p>
          One control bar, three layers. The <b>window</b> (1W / 1M / 3M) moves the dots
          and the ranking together — they share one axis — and shades the same stretch on
          the compare chart. All three windows are the same construction: theme return
          minus SPY&rsquo;s over that window. The universe is tradeable names only
          (cap ≥ $300M, $2M daily volume), and every row prints its member count because
          a theme of one stock is one stock.
        </p>
        <p>
          <b>Selecting</b>: search in the bar, or click a dot in the field, or click a
          row in the ranking — one gesture, three doors. Three at most, because three
          overlaid lines are what an eye can follow through a crossing; at the cap the
          pointer refuses (⃠) before the click does. The three slots in the bar show
          capacity without a caption, and colour only ever answers &laquo;which line is
          which&raquo; — it never grades a theme.
        </p>
        <p>
          <b>Field</b>: one dot per theme, zero is SPY, the box is the middle half. A
          narrow box says most themes ARE the market today and picking barely matters; long
          tails say being right pays. <b>Compare</b>: straight lines between the four
          measured stretches — nothing is smoothed, a curve through four samples would
          invent readings between them. A line that climbed to its rank is a trend; one
          that fell and snapped back is a bounce. The heatstrip repeats those stretches as
          state: tone is ahead/behind, solid is widening, outlined is narrowing — the same
          grammar as the ranking bars, so Leading / Weakening / Improving / Lagging read
          identically everywhere. A first cell at half strength means direction unknown,
          not flat.
        </p>
        <p>
          <b>State is descriptive, not a signal.</b> Over 10 years and 112 non-overlapping
          periods, filtering a momentum-ranked list by acceleration subtracted −0.18pp,
          and Weakening beat Leading by +0.37pp. Read where a group sits; do not trade the
          label.{summary && ` ${summary.publishable_themes} published, ${summary.provisional_themes} provisional.`}
        </p>
      </HowToRead>
    </div>
  )
}
