import { useMemo, useState } from 'react'
import PageHeader from '../PageHeader'
import DataFreshnessBadge from '../shared/DataFreshnessBadge'
import DataUnavailable from '../DataUnavailable'
import Reading, { readThemes } from '../Reading'
import { useGroups } from '../../hooks/useGroups'
import GroupTable from './GroupTable'
import RsPath from './RsPath'
import StateField from './StateField'
import ThemeBars from './ThemeBars'
import CompareBar from './CompareBar'
import TrajectoryPanel from './TrajectoryPanel'
import ThemeMembers from './ThemeMembers'
import { useThemeCompare, SLOT_COLOURS } from './useThemeCompare'
import { changeLookup } from './stateChange'
import { useGroupsHistory } from '../../hooks/useGroupsHistory'
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
 * 2026-08-18 — SIZE IS NOW THE PAGE'S FOURTH CHANNEL (Andy, across all three
 * morning pages). The three tiers here, largest first:
 *
 *   LARGE   the four-state field. It is not a view OF the four states, it is
 *           their definition — classify(excess_3m, rs_accel) reproduced,
 *           75 of 75, as two axes cut at zero. See StateField.
 *   MID     the comparison: is a theme a trend or a bounce.
 *   SMALL   the ranking, the members behind each theme, the full table —
 *           the names tier. A single stock never takes a large card here;
 *           this page's output is themes, and stocks are only their evidence.
 *
 * Compare sits ABOVE the 70-row ranking although it depends on it, because
 * an instrument that responds three screens below the gesture reads as broken.
 * It NEVER shows empty: with nothing picked it draws the three fastest
 * accelerators and says that is what it is doing.
 *
 * All teaching lives in HowToRead at the bottom. The objects themselves are
 * silent — the page used to carry seven captions and two duplicate legends,
 * which is a textbook, not a panel.
 */

/**
 * All three windows use the pipeline's own excess construction — theme return
 * minus benchmark return over the same window — and all three now ARRIVE that
 * way: rs_0_1w for the week (the first disjoint bucket reduces to
 * perf_1w − SPY.perf_1w), excess_1m for the month, excess_3m for the quarter.
 *
 * 1M used to be derived here instead, from perf_1m and a SPY row fetched from
 * a second file. Same construction, written twice, in two languages — the
 * shape that put two disagreeing accelerations on this page. It belongs with
 * its siblings, so `rs_engine.score_row` ships it (tests/test_rs_engine_excess).
 *
 * TRANSITIONAL: the fallback below covers the hours between this deploy and
 * the next pipeline run, when the live groups.json still predates the field.
 * Once a run has shipped excess_1m, delete the fallback, `needsSpy`, and
 * useSpyRow.js — nothing else reads that hook.
 */
export const WINDOWS = [
  { key: '1W', hl: [3], value: (r) => r.rs_0_1w },
  {
    key: '1M', hl: [2, 3],
    value: (r, spy) => (r.excess_1m != null ? r.excess_1m
      : (r.perf_1m != null && spy?.perf_1m != null ? r.perf_1m - spy.perf_1m : null)),
    needsSpy: true,
  },
  { key: '3M', hl: [1, 2, 3], value: (r) => r.excess_3m },
]

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
    <p className="m-0 mb-2.5 text-[13px] leading-relaxed border-l-2
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
        <span className="text-[11px] font-mono font-medium uppercase tracking-[.24em]
                         text-[var(--color-text-muted)]">{label}</span>
        {/* the slot beside the label: a control belongs here, next to the
            thing it controls. The state legend is an annotation of the marks
            below and lives on the right, away from it — they were crammed
            together and read as one row of chips. */}
        {typeof note === 'string'
          ? <span className="text-[11px] text-[var(--color-text-muted)]">{note}</span>
          : note}
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
  // Opens on the week. The narrator's line follows the window now, and the
  // week is where the news is — a page that opens on the quarter opens on a
  // sentence that was already true yesterday. Andy's call. It also changes
  // what the ranking sorts by on arrival, which is the same decision twice.
  const [winKey, setWinKey] = useState('1W')
  // Which picks have their member table open. Keyed by name, survives
  // re-picks; the panel itself only mounts (and only fetches the universe)
  // while open.
  // One at a time. Three tables open at once pushed the comparison column
  // hundreds of pixels past the ranking and turned a paired layout into a
  // scroll; and a members table is a thing you read one of, not three of.
  const [openMember, setOpenMember] = useState(null)
  // Rank by the window the page is set to, or by how the pace has changed —
  // the second question the stretch cells answer.
  const [rankSort, setRankSort] = useState('window')
  const spy = useSpyRow()
  const compare = useThemeCompare()
  /* Same module-level cache RsPath reads, so this is not a second fetch. */
  const { data: history, sessions: histSessions } = useGroupsHistory()
  /* The graded channel (Andy, 2026-08-24: colour grades now). It comes from the
     history file, not from groups.json — "did it change sides" is a statement
     about two sessions, and today's row holds one. When the file is missing the
     lookup returns null for everything and every mark falls back to ink, which
     is the same thing the page did before this existed.

     IT LIVES UP HERE WITH THE OTHER HOOKS ON PURPOSE. Written next to the code
     that uses it, it sat below `if (loading) return` — the third time this
     lane has shipped a hook under an early return. React counted 17 hooks then
     18 and threw. */
  const changeOf = useMemo(() => changeLookup(history), [history])

  const byName = useMemo(() => {
    const m = new Map()
    for (const r of [...themes, ...provisional, ...industries]) m.set(r.group, r)
    return m
  }, [themes, provisional, industries])

  if (loading) {
    return <div className="text-[var(--color-text-muted)] text-[13px] py-8 text-center">
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
  /**
   * THIS PAGE COMPARES THEMES (Andy, 2026-08-19), decided on the numbers.
   *
   * On the acceleration axis — the page's whole question, "what suddenly came
   * from behind" — sectors and factors never appear: the top ten by rs_accel
   * are ten themes, and dropping the other twenty-six changes the axis extreme
   * not at all (+0.574 / −0.278 either way). They only occupy the top of the
   * excess axis, and there they are tautological: High Octane, 52-Week High
   * Leaders and Growth Factor lead a momentum tape by construction. That is a
   * restatement of the market's own regime, which is page 1's reading, not a
   * statement about where money is rotating between theses.
   *
   * The scale gap says the same thing more bluntly: a factor holds 132 names
   * at the median and up to 1,579; a theme holds 24. Plotting them on one pair
   * of axes invites a comparison between a size bucket and an argument.
   *
   * NOTHING IS DELETED. The full table below still carries all 56 with their
   * kind, and the field says so on itself. This is a decision about what the
   * figure compares, not about what the file holds.
   */
  const rows = themes.filter((t) => t.kind === 'theme')
  const win = WINDOWS.find((w) => w.key === winKey)
  const windowed = rows.map((r) => ({ ...r, _value: win.value(r, spy) }))
  const measured = windowed.filter((r) => Number.isFinite(r._value)).length
  // One scale for the dots and the bars — one axis, one instrument.
  const scale = windowed.reduce(
    (m, r) => (Number.isFinite(r._value) ? Math.max(m, Math.abs(r._value)) : m), 0) || 1

  const colourOf = compare.colourOf
  const onToggle = compare.toggle

  /**
   * What Compare draws when nothing is picked.
   *
   * The mid card used to be an empty box occupying half the page on arrival —
   * the same defect Andy rejected for page 3's chart, in a different costume.
   * His call (2026-08-18): default to the three fastest accelerators, because
   * "what suddenly came from behind" is half of what this page is for and
   * should not require a click to see.
   *
   * It is a DEFAULT, not a selection: `picks` stays empty, the bar still shows
   * three free slots, and the first real pick replaces the trio entirely.
   * Seeding the selection instead would have made Clear do nothing visible and
   * would have put a choice in the reader's mouth that they never made.
   */
  const fallback = rows
    .filter((r) => Number.isFinite(r.rs_accel))
    .sort((a, b) => b.rs_accel - a.rs_accel)
    .slice(0, SLOT_COLOURS.length)
    .map((r, i) => ({ name: r.group, colour: SLOT_COLOURS[i] }))
  const shown = compare.picks.length ? compare.picks : fallback
  const isDefault = compare.picks.length === 0

  // Controls are typography, not boxes: state is carried by weight and an
  // underline, never by a filled pill. Borders on this page are reserved for
  // separating data from data.
  const seg = (active) => `px-0.5 pb-[3px] text-[13px] bg-transparent border-0
    border-b-2 cursor-pointer transition-colors
    ${active ? 'text-[var(--color-text)] font-semibold border-[var(--color-text)]'
             : 'text-[var(--color-text-muted)] border-transparent hover:text-[var(--color-text)]'}`

  return (
    <div className="space-y-5">
      <PageHeader group="market" title="Themes"
        meta={[`vs ${benchmark} · ${date} · ${rows.length} themes of ${themes.length} groups`,
               <DataFreshnessBadge key="fresh" sessionDate={date} />]} />
      <Reading text={readThemes(windowed, winKey)} />

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

      {/* ── LARGE ─────────────────────────────────────────────────────────
          The field gets the whole width and no neighbour, because it is the
          definition of the four words the rest of the page uses. Everything
          below it is either a closer look at one dot (Compare) or the same
          themes as a list (Rank). */}
      <Section label="Field"
               note={`${rows.length} themes · quarter × acceleration`}>
        <StateField rows={rows} colourOf={colourOf} onToggle={onToggle}
                    atLimit={compare.atLimit} changeOf={changeOf}
                    changeSessions={histSessions} />

        {/* The field says where each theme stands; this says how it got there.
            Two themes on the same dot can have arrived from opposite
            directions, and the arrival is the rotation. */}
        <div className="mt-6">
          <RsPath picks={shown.map((p) => p.name)} colourOf={colourOf}
                  changeOf={changeOf} />
        </div>
      </Section>

      {/* ── MID and SMALL ─────────────────────────────────────────────────
          Compare is the middle tier and Rank the small one, so Compare leads
          on every width — including the two-column one, where it takes the
          left column that the eye reaches first. Below xl they stack in the
          same order.

          The split waits for xl, not lg: at 1024 each column came out about
          400px and the comparison's end labels ran 3px past the edge. */}
      <div className="xl:grid xl:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] xl:gap-x-8 xl:items-start">
        <div className="min-w-0">
        <Section label="Compare">
          {/* The default announces itself. A chart that quietly draws
              something you did not choose is a chart you will misread once. */}
          {isDefault && (
            <p className="m-0 mb-2 text-[11px] leading-relaxed text-[var(--color-text-muted)]">
              Nothing picked, so this is the <b className="text-[var(--color-text-secondary)]">three
              fastest accelerating themes</b> — the ones that came from behind. Pick any
              theme, in the bar or on the field, and it replaces them.
            </p>
          )}
          <CompareReading picks={shown} windowed={windowed} winKey={winKey} />
          <TrajectoryPanel picks={shown} byName={byName} highlight={win.hl} />

          {/* The set behind each chosen average. A theme's bar is a claim about
              members you cannot see; one fold per pick opens them on the
              screener's own measurements. Mounted lazily — the 5,615-row
              universe is fetched the first time a fold opens, not on page load. */}
          {shown.map((pick) => {
            const row = byName.get(pick.name)
            if (!row?.tickers?.length) return null
            const open = openMember === pick.name
            return (
              <div key={pick.name} className="mt-2">
                <button type="button"
                        onClick={() => setOpenMember((cur) =>
                          cur === pick.name ? null : pick.name)}
                        className="w-full flex items-baseline gap-2.5 bg-transparent border-0
                                   p-0 cursor-pointer text-left group">
                  <span className="text-[11px] font-mono text-[var(--color-text-muted)]
                                   group-hover:text-[var(--color-text)] w-3">
                    {open ? '−' : '+'}
                  </span>
                  <span className="text-[11px] font-medium" style={{ color: pick.colour }}>
                    {pick.name}
                  </span>
                  <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
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
        </div>
        <div className="min-w-0">
        <Section label="Rank"
                 note={
                   <div className="flex gap-1" role="group" aria-label="rank by">
                     {/* "by Time" rather than "by 1W": the label names the KIND of sort, not
                          the window, so it stops changing under the reader every time
                          they switch window — and it sits parallel to "by Acceleration",
                          which is the choice actually being offered. */}
                     {[['window', 'by Time'], ['pace', 'by Acceleration']].map(([k, label]) => (
                       <button key={k} type="button" onClick={() => setRankSort(k)}
                               aria-pressed={rankSort === k}
                               className={`px-2 py-[2px] text-[11px] font-mono rounded cursor-pointer
                                           border-none transition-colors whitespace-nowrap ${rankSort === k
                                 ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                                 : 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'}`}>
                         {label}
                       </button>
                     ))}
                   </div>
                 }
                 /* the state census moved into the Field figure, which is
                    where those four words are defined */
                 >
          {/* One list again. The kind sections solved a problem that no longer
              exists here — with sectors and factors off the figure there is
              only one kind of object left to rank — and they cost the thing a
              ranking is for: four separate lists mean the eye cannot compare
              adjacent places, even with the global numbers kept. */}
          <ThemeBars rows={windowed} scale={scale} sortKey={rankSort}
                     colourOf={colourOf} onToggle={onToggle}
                     atLimit={compare.atLimit} dim={compare.picks.length > 0} />
        </Section>
        </div>
      </div>

      {/* ALL 56, not the 30 the figure compares. This is where the page keeps
          its promise that sectors and factors were set aside rather than
          dropped — pointing it at the filtered set would have made that
          sentence false the moment it was written. */}
      <Reference label="Full table" count={themes.length}
                 note={`all ${themes.length} groups — themes, sectors and factors — all columns, sortable`}>
        <GroupTable rows={themes} showMethod emptyNote="No groups" />
        {/* The one column on this page whose reading is counter-intuitive
            enough that leaving it to a tooltip would guarantee it is read
            backwards. Numbers quoted from the measurement, not rounded up. */}
        <p className="text-[11px] text-[var(--color-text-muted)] mt-3 max-w-[80ch]">
          <b>Extended</b> is the share of a group&rsquo;s members sitting 4+ ATR above
          their SMA50 — an expiry date on the Leading label, not a return forecast.
          Across 48 themes × 293 days, Leading groups under 20% extended were still
          Leading 21 days later 28% of the time; 20–40% → 14%, 40–60% → 6%, above
          60% → 0%. The 21-day excess return did <i>not</i> fall across those buckets
          (+1.6% → +2.5–3.8%): the label expires because acceleration turns negative
          after a two-month run, not because the group stops paying. The damage lands
          later — Leading → Weakening from above 40% extended ran +3.1% at 21 days and
          −4.1% at 63 (n=31). So it reads &ldquo;don&rsquo;t add here, take some off
          over the next month or two&rdquo;, never &ldquo;sell now&rdquo;. The notch
          marks members past 7 ATR; <span className="font-mono">n/m</span> is a group with
          no members to measure, which is not the same as 0%.
        </p>
      </Reference>

      <HowToRead>
        <p>
          Read this page by size. The <b>field</b> is largest because it is where the four
          words come from; the <b>comparison</b> is the middle tier; the <b>ranking</b>, the
          members and the full table are the names tier. The <b>window</b> (1W / 1M / 3M)
          moves the ranking and shades the matching stretch on the compare chart —
          <b>it does not move the field</b>, which is defined on the quarter and says so on
          itself. All three windows are the same construction: theme return minus
          SPY&rsquo;s over that window. The universe is tradeable names only (cap ≥ $300M,
          $2M daily volume), and every row prints its member count because a theme of one
          stock is one stock.
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
          <b>Field</b>: one dot per theme, placed on quarterly excess against
          acceleration, both cut at zero — so the quadrant a dot lands in <i>is</i> its
          state, which is why nothing on that figure is coloured by state. Size is how many
          of the five horizons the theme leads on at once: the big dots are durable, the
          high ones came from behind, and the crowd around the origin is the honest reading
          that most themes are the market. <b>Compare</b>: straight lines between the four
          measured stretches — nothing is smoothed, a curve through four samples would
          invent readings between them. A line that climbed to its rank is a trend; one
          that fell and snapped back is a bounce. The heatstrip repeats those stretches as
          state: tone is ahead/behind, solid is widening, outlined is narrowing — the same
          grammar as the ranking bars, so Leading / Weakening / Improving / Lagging read
          identically everywhere. A first cell at half strength means direction unknown,
          not flat.
        </p>
        <p>
          <b>A dashed name did not clear its own construction test.</b> Most groups are
          either validated — the market agrees their members co-move — or definitional, a
          factor or sector slice that never claimed co-movement in the first place. The few
          that are neither are on this page because they were asked for, not because they
          passed, and their names carry a dashed underline with the raw verdict in the
          tooltip. The full table prints that verdict as a column.
        </p>
        <p>
          <b>State is descriptive, not a signal.</b> Over 10 years and 112 non-overlapping
          periods, filtering a momentum-ranked list by acceleration subtracted −0.18pp,
          and Weakening beat Leading by +0.37pp. Read where a group sits; do not trade the
          label.{' '}
          {/* COUNT WHAT IS ON THE PAGE. This printed summary.publishable_themes
              and summary.provisional_themes straight through — trusting a
              precomputed total to describe rows it does not itself contain. It
              reads the rows now, so the page cannot state a count it is unable
              to show, and the clause below fires only if the two ever diverge.
              Written after a false alarm of my own: I read groups.json twice
              while the data side was rebuilding it and took the two answers
              for a contradiction inside one file. They agree (74 and 5). The
              guard stays because the failure it watches for is real even
              though that instance of it was not. */}
          <b className="text-[var(--color-text-bold)]">{themes.length}</b> published,{' '}
          <b className="text-[var(--color-text-bold)]">{provisional.length}</b> provisional
          {provisional.length > 0
            ? <> &mdash; withheld because the market has not shown their members co-moving.</>
            : '.'}
          {summary && (summary.publishable_themes !== themes.length
                    || summary.provisional_themes !== provisional.length) && (
            <> The file&rsquo;s own summary says {summary.publishable_themes} and{' '}
            {summary.provisional_themes} against a taxonomy of {summary.taxonomy?.total ?? '—'};
            it is counted over the taxonomy, and{' '}
            <b>{(summary.publishable_themes + summary.provisional_themes) - (themes.length + provisional.length)} row
            {(summary.publishable_themes + summary.provisional_themes) - (themes.length + provisional.length) === 1 ? '' : 's'} in
            it produced nothing to rank</b>. Which ones is not in this payload.</>
          )}
        </p>
      </HowToRead>
    </div>
  )
}
