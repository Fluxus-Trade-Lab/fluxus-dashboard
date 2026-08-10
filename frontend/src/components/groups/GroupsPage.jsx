import { useState } from 'react'
import PageHeader from '../PageHeader'
import Reading, { readThemes } from '../Reading'
import { useGroups } from '../../hooks/useGroups'
import GroupTable from './GroupTable'
import ThemeBars from './ThemeBars'
import RsSegments from './RsSegments'
import Reference from '../Reference'
import HowToRead from '../HowToRead'

const TABS = [
  { key: 'themes', label: 'Themes' },
  { key: 'industries', label: 'Industries' },
  { key: 'provisional', label: 'Provisional' },
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

  return (
    <div className="space-y-4">
      <PageHeader group="market" title="Themes"
        blurb="Where the strength is, and where it is turning — two different questions, so two measurements. A board that only ranks what has already won cannot show a turn."
        meta={[`relative strength vs ${benchmark} · ${date}`,
               'tradeable universe only — cap ≥ $300M, $2M daily volume',
               'member count is printed: a theme of one stock is one stock',
               `${themes.length} published + ${provisional.length} provisional — the counts above cover the published set only`]} />
      <Reading text={readThemes(themes)} />
      <div className="flex justify-end">
        <StateCounts rows={rows} />
      </div>

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

      {/* The subject: one bar per theme, ranked, and nothing beside it. The
          eight-column table below holds the same rows plus method and
          validation — it answers «where does this come from», which is a
          different question and belongs behind a line, not in front of one. */}
      <ThemeBars rows={rows} />

      {/* Evidence for the bar above it: the same quarter, taken apart. The
          chart says which themes lead; this says when they earned it. */}
      <RsSegments rows={rows} />

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
          A theme's <b>level</b> is how it has performed against SPY over three
          months; its <b>acceleration</b> is whether that gap is still widening.
          The two are independent, and the interesting cases are where they
          disagree — a leader that has stopped accelerating is a leader that is
          being sold into.
        </p>
        <p>
          Every mark sits on a <b>shared zero rule</b>, and which side of that line
          it falls on is the sign. Bars are measured against the same scale across
          rows, so a bar twice as long is twice the number — never rescaled per row
          to fill the column.
        </p>
        <p>
          Each row prints its <b>member count</b>. A theme of three names is three
          names wearing a theme's clothes, and its average will swing on one of
          them; treat the denominator as part of the reading rather than as
          footnote. Themes whose members do not co-move more than a random basket
          of the same size are held in <b>Provisional</b> — visible, labelled, and
          kept out of the ranking.
        </p>
      </HowToRead>
    </div>
  )
}
