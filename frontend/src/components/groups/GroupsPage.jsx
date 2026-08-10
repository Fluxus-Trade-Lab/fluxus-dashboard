import { useMemo, useState } from 'react'
import PageHeader from '../PageHeader'
import Reading, { readThemes } from '../Reading'
import { useGroups } from '../../hooks/useGroups'
import GroupTable from './GroupTable'
import ThemeBars from './ThemeBars'
import RsSegments from './RsSegments'
import CompareChips from './CompareChips'
import DistributionStrip from './DistributionStrip'
import TrajectoryPanel from './TrajectoryPanel'
import { useThemeCompare } from './useThemeCompare'
import { useSpyRow } from './useSpyRow'
import Reference from '../Reference'
import HowToRead from '../HowToRead'

/**
 * Themes + RS Rotation, one page — TSF's Thematic Focus View absorbed into
 * the three-layer structure instead of being a fourth page.
 *
 * One SWITCH (the window) drives the distribution and the ranking together,
 * and shades the same stretch on the trajectory. They share an x-scale by
 * construction; two switches would let one instrument show two different
 * windows on what claims to be one axis.
 *
 * One SELECTION (up to three themes) has three entry points — chips by name,
 * dots by position, ranking rows by rank — and every layer answers it at
 * once. Selection carries identity colour only; the state grammar stays on
 * the bars and strips.
 *
 * The three layers answer, in order: is picking worth it today (distribution),
 * what to pick (ranking), and whether the pick is a trend or a bounce
 * (trajectory + heatstrip) — the last being the question a snapshot can never
 * answer.
 */

const TABS = [
  { key: 'themes', label: 'Themes' },
  { key: 'industries', label: 'Industries' },
  { key: 'provisional', label: 'Provisional' },
]

/**
 * The three windows, all in the pipeline's own construction: theme return
 * minus benchmark return over the same window (rs_engine's excess).
 * rs_0_1w IS that quantity for one week — the first disjoint bucket minus the
 * benchmark's reduces to perf_1w − SPY.perf_1w. 1M needs SPY's row, so it
 * stays disabled until that row has loaded rather than guessing a zero line.
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

function StateCounts({ rows }) {
  const counts = rows.reduce((acc, r) => {
    if (r.state) acc[r.state] = (acc[r.state] ?? 0) + 1
    return acc
  }, {})
  const order = ['Leading', 'Weakening', 'Improving', 'Lagging']
  return (
    <div className="flex gap-4 text-[11px] uppercase tracking-wide
                    text-[var(--color-text-muted)]">
      {order.map((s) => (
        <span key={s}>{s} <span className="tabular-nums font-medium
          text-[var(--color-text)]">{counts[s] ?? 0}</span></span>
      ))}
    </div>
  )
}

export default function GroupsPage() {
  const { industries, themes, provisional, summary, date, benchmark, loading, error } =
    useGroups()
  const [tab, setTab] = useState('themes')
  const [winKey, setWinKey] = useState('3M')
  const spy = useSpyRow()
  const compare = useThemeCompare()

  // Selection survives tab switches: a picked theme resolves against every
  // group on the page, so flipping to Industries does not blank the chart.
  const byName = useMemo(() => {
    const m = new Map()
    for (const r of [...themes, ...provisional, ...industries]) m.set(r.group, r)
    return m
  }, [themes, provisional, industries])

  if (loading) {
    return <div className="text-[var(--color-text-muted)] text-sm py-8 text-center">
      Loading groups…
    </div>
  }
  if (error) {
    return <div className="text-rose-400 text-sm py-8 text-center">
      groups.json unavailable — run <code>python -m pipeline.themes.build_groups</code>
    </div>
  }

  const rows = tab === 'themes' ? themes
    : tab === 'industries' ? industries
    : provisional

  const win = WINDOWS.find((w) => w.key === winKey)
  const windowed = rows.map((r) => ({ ...r, _value: win.value(r, spy) }))
  // One scale for the strip and the bars — one axis, one instrument.
  const scale = windowed.reduce(
    (m, r) => (Number.isFinite(r._value) ? Math.max(m, Math.abs(r._value)) : m), 0) || 1

  // The comparison instrument lives on the theme tabs. Industries are a
  // different cohort with a different denominator; mixing them into one
  // chart would compare ranks that are not the same claim.
  const comparable = tab !== 'industries'

  return (
    <div className="space-y-4">
      <PageHeader group="market" title="Themes"
        blurb="Where the strength is, and where it is turning — two different questions, so two measurements. A board that only ranks what has already won cannot show a turn."
        meta={[`relative strength vs ${benchmark} · ${date}`,
               'tradeable universe only — cap ≥ $300M, $2M daily volume',
               'member count is printed: a theme of one stock is one stock',
               `${themes.length} published + ${provisional.length} provisional — the counts above cover the published set only`]} />
      <Reading text={readThemes(themes)} />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-1 border-b border-[var(--color-border)]">
          {TABS.map((t) => {
            const n = t.key === 'themes' ? themes.length
              : t.key === 'industries' ? industries.length
              : provisional.length
            return (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-3 py-1.5 text-sm font-medium border-b-2 -mb-px transition
                  ${tab === t.key
                    ? 'border-[var(--color-accent)] text-[var(--color-text)]'
                    : 'border-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text)]'}`}
              >
                {t.label} <span className="tabular-nums opacity-60">{n}</span>
              </button>
            )
          })}
        </div>
        <StateCounts rows={rows} />
      </div>

      {tab === 'provisional' && (
        <div className="text-[12px] leading-relaxed text-[var(--color-text-muted)]
                        border-l-2 border-amber-500/40 pl-3 py-1">
          Held back from the main list. Either their members do not co-move more
          than a random basket of the same size — so the grouping is a label
          rather than a driver — or there are too few tradeable names to read a
          group at all. Shown here because a withheld theme should look
          withheld, not missing.
        </div>
      )}

      {/* THE SWITCH. One control, three layers. It sits above everything it
          governs and names what it governs, so nobody has to discover the
          coupling by accident. */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex border border-[var(--color-border)] rounded overflow-hidden">
          {WINDOWS.map((w) => {
            const waiting = w.needsSpy && !spy
            return (
              <button key={w.key} type="button"
                      onClick={() => !waiting && setWinKey(w.key)}
                      disabled={waiting}
                      title={waiting ? 'waiting for the benchmark row' : undefined}
                      className={`px-4 py-[5px] text-[12px] font-mono border-r
                                  border-[var(--color-border)] last:border-r-0
                                  ${w.key === winKey
                                    ? 'bg-[var(--color-accent)] text-white font-bold'
                                    : waiting
                                      ? 'bg-transparent text-[var(--color-text-muted)] opacity-40 cursor-wait'
                                      : 'bg-transparent text-[var(--color-text-secondary)] cursor-pointer hover:text-[var(--color-text)]'}`}>
                {w.key}
              </button>
            )
          })}
        </div>
        <span className="text-[10.5px] text-[var(--color-text-muted)]">
          one window for the dots and the ranking; the trajectory always shows all
          four stretches and shades this one
        </span>
      </div>

      {comparable && (
        <CompareChips rows={rows} picks={compare.picks} atLimit={compare.atLimit}
                      onToggle={compare.toggle} onClear={compare.clear} />
      )}

      {/* LAYER 1 — the field. Worth picking at all today? */}
      <DistributionStrip rows={windowed} scale={scale}
                         colourOf={comparable ? compare.colourOf : () => null}
                         onToggle={comparable ? compare.toggle : () => {}}
                         atLimit={compare.atLimit} />

      {/* LAYER 2 — the order. Same axis as the dots above. */}
      <ThemeBars rows={windowed} scale={scale}
                 colourOf={comparable ? compare.colourOf : () => null}
                 onToggle={comparable ? compare.toggle : () => {}}
                 atLimit={compare.atLimit} />

      {/* LAYER 3 — the history of the chosen few: trend or bounce. */}
      {comparable && (
        <TrajectoryPanel picks={compare.picks} byName={byName} highlight={win.hl} />
      )}

      <Reference label="Where the lead was earned" count={20}
                 note="the four stretches for the top 20 by 3m — the wide view of what the trajectory shows for your picks">
        <RsSegments rows={rows} />
      </Reference>

      <Reference label="Full table" count={rows.length}
                 note="every column — accel, persistence, method, validation — and sortable">
        <GroupTable
          rows={rows}
          showMethod={tab !== 'industries'}
          emptyNote={tab === 'provisional' ? 'Nothing withheld' : 'No groups'}
        />
      </Reference>

      <p className="text-[11px] text-[var(--color-text-muted)] leading-relaxed">
        <strong>State is descriptive, not a signal.</strong> Over 10 years and
        112 non-overlapping periods, filtering a momentum-ranked list by
        acceleration subtracted −0.18pp and Weakening beat Leading by +0.37pp.
        Use these to read where a group sits, not as an entry rule.
        {summary && ` · ${summary.publishable_themes} published, ${summary.provisional_themes} provisional.`}
      </p>

      <HowToRead>
        <p>
          One switch, one selection, three layers. The <b>window switch</b> (1W / 1M / 3M)
          moves the dots and the ranking together — they share one axis — and shades the
          same stretch on the trajectory. The <b>selection</b> (up to three themes) can be
          made three ways: chips by name, dots by position, ranking rows by rank. All
          three are the same gesture.
        </p>
        <p>
          Read the layers in order. The <b>dots</b> say whether picking is worth anything
          today: a narrow middle box means most themes are the market, long tails mean
          being right pays. The <b>ranking</b> says what to pick. The <b>trajectory</b>{' '}
          says what kind of strength you picked — a line that climbed there is a trend, a
          line that fell and snapped back is a bounce, and the ranking cannot tell those
          apart by construction.
        </p>
        <p>
          The <b>heatstrip</b> under each chosen theme is the same four stretches as
          state: tone for ahead/behind SPY, solid for widening, outlined for narrowing —
          the exact grammar of the ranking bars. Lines are straight between measured
          points; nothing is smoothed, because a curve through four samples would invent
          readings between them.
        </p>
        <p>
          Selection colour answers only <b>which line is which</b> — it never grades a
          theme. Grades stay with the state grammar, and the sign stays with which side
          of the zero rule a mark sits on.
        </p>
      </HowToRead>
    </div>
  )
}
