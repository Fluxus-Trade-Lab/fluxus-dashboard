/**
 * State board + propagation chain — the v2 decision-first block.
 *
 * Design: Fluxus_Brand/visual/Fluxus_Operator_Model.md
 * Data:   breadth.json → state_board (pipeline/screeners/state_board.py)
 *
 * Encoding rules this component exists to hold:
 *   · rank is carried by HOW MANY cells are filled, never by hue alone
 *   · failure carries a 45° hatch, so it survives greyscale and print
 *   · a level of null is NOT zero — it renders outside the scale, as an outline
 *   · every condition prints the numbers that produced it, in a lighter register
 */

import { isWeekend } from './session'

const HATCH =
  'repeating-linear-gradient(45deg,rgba(125,57,8,.55) 0 1.7px,transparent 1.7px 5px)'

/** Filled cells = rank. Colour only says which side of neutral. */
function Level({ level, count }) {
  if (level == null) {
    return (
      <div className="flex gap-[2px]" aria-label="not measured">
        {Array.from({ length: count }, (_, i) => (
          <i key={i} className="block w-[15px] h-[13px] border border-dashed"
             style={{ borderColor: 'var(--color-untested)' }} />
        ))}
      </div>
    )
  }
  const weak = level <= 1
  const strong = level >= 3
  return (
    <div className="flex gap-[2px]">
      {Array.from({ length: count }, (_, i) => {
        const on = i <= level
        const bg = !on ? 'var(--color-v2-off)'
          : weak ? 'var(--color-refused)'
          : strong ? 'var(--color-took)' : 'var(--color-text-muted)'
        return (
          <i key={i} className="block w-[15px] h-[13px]"
             style={{ background: bg, backgroundImage: on && weak ? HATCH : undefined }} />
        )
      })}
    </div>
  )
}

/* The four registers must be distinguishable without colour, so each gets a
   structural mark: measurement is plain, a read carries a solid left rule, an
   expectation a dashed one. The tag is suppressed when a row is unmeasured —
   printing "measured" beside "not measured" contradicts itself. */
const REG = { fact: 'measured', interpretation: 'read', anticipation: 'expected' }
const RULE = {
  fact: 'none',
  interpretation: '2px solid var(--color-border)',
  anticipation: '2px dashed var(--color-text-muted)',
}

function Row({ row, levels }) {
  const { key, level, level_label: label, evidence, layer } = row
  const colour = level == null ? 'var(--color-text-muted)'
    : level <= 1 ? 'var(--color-refused)'
    : level >= 3 ? 'var(--color-took)' : 'var(--color-text-secondary)'
  return (
    <div className="grid grid-cols-[132px_92px_1fr] gap-3 items-center py-2
                    border-b border-[var(--color-border-light)] min-h-[48px]">
      <div className="text-[17px] font-semibold capitalize"
             style={{ fontFamily: 'var(--font-cond)' }}>{key}</div>
      <Level level={level} count={levels.length} />
      <div>
        <div className="text-[11px] font-semibold uppercase tracking-wider mb-[3px]"
             style={{ color: colour }}>
          {label ?? 'not wired'}
          {level != null && (
            <span className="ml-2 font-normal tracking-[.16em] normal-case text-[11px]
                             text-[var(--color-text-muted)]">{REG[layer] ?? layer}</span>
          )}
        </div>
        <div className="text-[11px] leading-snug text-[var(--color-text-secondary)]"
             style={RULE[layer] === 'none' ? undefined
               : { borderLeft: RULE[layer], paddingLeft: '9px', marginLeft: '-11px' }}>
          {evidence}
        </div>
      </div>
    </div>
  )
}

/**
 * Minard: the band is `carrying`, which the pipeline already clamps to a running
 * minimum — a current that has stopped cannot resume. A link measured higher
 * than what reaches it is drawn detached, because it is real but not fed.
 */
function Chain({ chain }) {
  return (
    <div className="mt-5">
      <div className="grid border border-[var(--color-v2-ink)]"
           style={{ gridTemplateColumns: `repeat(${chain.length},1fr)` }}>
        {chain.map((l) => {
          const pct = l.carrying == null ? null : Math.round(l.carrying * 100)
          const lit = l.state === 'lit'
          const partial = l.state === 'partial'
          const colour = lit ? 'var(--color-took)'
            : partial ? 'var(--color-text-muted)' : 'var(--color-untested)'
          return (
            <div key={l.key}
                 className="px-3 py-3 border-r border-[var(--color-border)] last:border-r-0">
              <div className="h-[9px] mb-2 relative"
                   style={{ background: 'var(--color-v2-off)' }}>
                <div className="h-full absolute left-0 top-0"
                     style={{
                       width: `${pct ?? 0}%`,
                       background: colour,
                       backgroundImage: l.state === 'unlit' ? HATCH : undefined,
                     }} />
              </div>
              <div className="text-[13px] font-semibold leading-tight">{l.label}</div>
              <div className="text-[11px] font-mono tracking-widest mt-1"
                   style={{ color: colour }}>
                {l.state === 'unmeasured' ? 'NOT MEASURED' : `${pct}% CARRYING`}
              </div>
              {l.fed === false && (
                <div className="text-[11px] font-mono tracking-wider mt-1
                                text-[var(--color-text-muted)]">
                  MEASURED, NOT FED
                </div>
              )}
              <div className="text-[11px] leading-snug mt-2
                              text-[var(--color-text-secondary)]">{l.evidence}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function StateBoard({ board, session }) {
  if (!board?.rows?.length) return null
  const { rows, levels, chain, measured, total } = board
  const half = Math.ceil(rows.length / 2)
  const offSession = isWeekend(session)

  return (
    <section className="space-y-1">
      <div className="flex items-baseline justify-between pb-2
                      border-b border-[var(--color-v2-ink)]">
        <h2 className="text-[11px] font-mono uppercase tracking-[.24em]
                       text-[var(--color-text-muted)]">State board</h2>
        <span className="text-[11px] text-[var(--color-text-secondary)]">
          {session && <span className="font-mono mr-3">{session}</span>}
          {measured} of {total} measured — the rest is left blank on purpose
        </span>
      </div>

      {/* Counts of zero read as "the market did not move". On a row that was
          never a session they mean "nothing was counted", which is the opposite
          kind of fact — and the board would otherwise render an all-clear off it. */}
      {offSession && (
        <div className="border border-dashed border-[var(--color-untested)] px-3 py-2 mt-2">
          <div className="text-[11px] font-mono uppercase tracking-[.2em]
                          text-[var(--color-signal-caution)] mb-1">
            This row is not a trading session
          </div>
          <p className="text-[11px] leading-relaxed text-[var(--color-text-secondary)] m-0">
            The last row in the archive is <b>{session}</b>, a weekend. Its advance, decline and
            ±4% counts are <b>zero because nothing was counted</b>, not because nothing moved — so
            every state below that leans on those counts is reading absence as calm.
            Wait for a real session before acting on this board.
          </p>
        </div>
      )}

      <div className="grid md:grid-cols-2 md:gap-x-10">
        <div>{rows.slice(0, half).map((r) => <Row key={r.key} row={r} levels={levels} />)}</div>
        <div>{rows.slice(half).map((r) => <Row key={r.key} row={r} levels={levels} />)}</div>
      </div>

      <div className="flex flex-wrap gap-x-6 gap-y-2 pt-3 text-[11px]
                      text-[var(--color-text-secondary)]">
        <span><i className="inline-block w-6 h-[13px] align-[-2px] mr-2"
                 style={{ background: 'var(--color-took)' }} />took the chance offered</span>
        <span><i className="inline-block w-6 h-[13px] align-[-2px] mr-2"
                 style={{ background: 'var(--color-refused)', backgroundImage: HATCH }} />
          offered and refused</span>
        <span><i className="inline-block w-6 h-[13px] align-[-2px] mr-2 border border-dashed"
                 style={{ borderColor: 'var(--color-untested)' }} />not measured — outside the scale</span>
        <span className="text-[var(--color-text-muted)]">
          rank is carried by how many cells are filled, never by hue alone
        </span>
      </div>

      {chain?.length > 0 && (
        <>
          <div className="flex items-baseline justify-between pt-8 pb-2
                          border-b border-[var(--color-v2-ink)]">
            <h2 className="text-[11px] font-mono uppercase tracking-[.24em]
                           text-[var(--color-text-muted)]">Propagation</h2>
            <span className="text-[11px] text-[var(--color-text-secondary)]">
              The width is the count — a current that stops does not resume
            </span>
          </div>
          <Chain chain={chain} />
        </>
      )}
    </section>
  )
}
