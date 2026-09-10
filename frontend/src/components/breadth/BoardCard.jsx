import { isWeekend } from './session'
import Spark from './Spark'

/**
 * 盘面 · Board — the nine-condition ladder, one card.
 *
 * Design: Fluxus_Brand/visual/Fluxus_Operator_Model.md
 * Data:   breadth.json → state_board (pipeline/screeners/state_board.py)
 *
 * This replaces the old two-column StateBoard table with the language the
 * Themes rotation cards settled on (Andy 2026-09-06 — greyscale rank, a
 * colour pair, one meaning per channel): rungs still carry rank (how many
 * cells are filled, never hue alone), and each row now also carries a 60-day
 * shape — not a new number, the SAME series the evidence text already quotes,
 * because "is this getting better or worse" was the one question nine rows of
 * numbers could not answer on their own (Andy 09-11, this page had "说明文字
 * 比数据多，同一个数印三遍" — the fix is not fewer numbers, it is not
 * printing the same one three times).
 *
 * Two rows carry no spark: Index repair is computed off the benchmarks' own
 * candles (health.spy/qqq), not off a `history.rows` column, and Rates has no
 * pipeline data at all. Both render the same dashed "not sparklined" mark
 * StateBoard already used for "not measured" — a placeholder, never a guess.
 */

const HATCH =
  'repeating-linear-gradient(45deg,rgba(125,57,8,.55) 0 1.7px,transparent 1.7px 5px)'

/** key (as state_board.py writes it) → the same series its evidence text
 *  quotes, pulled straight from history.rows. `damage` is the one derived
 *  value — the down-share the evidence sentence itself states in words — and
 *  it is computed with the exact formula state_board.py uses, not a proxy. */
const SPARK = {
  damage: (rows) => rows.map((r) => {
    const qu = r.up_25pct_qtr, qd = r.down_25pct_qtr
    return (qu == null || qd == null || qu + qd === 0) ? null : (100 * qd) / (qu + qd)
  }),
  'selling pressure': (rows) => rows.map((r) => r.down_4pct ?? null),
  breadth: (rows) => rows.map((r) => r.pct_above_20sma ?? null),
  trend: (rows) => rows.map((r) => r.pct_above_200sma ?? null),
  thrust: (rows) => rows.map((r) => r.up_4pct ?? null),
  extremes: (rows) => rows.map((r) => (
    r.new_highs == null || r.new_lows == null ? null : r.new_highs - r.new_lows)),
  confirmation: (rows) => rows.map((r) => r.ratio_5d ?? null),
}
const SPARK_WINDOW = 60

function Rungs({ level, count }) {
  if (level == null) {
    return (
      <div className="flex gap-[2px]" aria-label="not measured">
        {Array.from({ length: count }, (_, i) => (
          <i key={i} className="block w-[13px] h-[12px] border border-dashed"
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
          <i key={i} className="block w-[13px] h-[12px]"
             style={{ background: bg, backgroundImage: on && weak ? HATCH : undefined }} />
        )
      })}
    </div>
  )
}

function Row({ row, levelCount, spark }) {
  const { key, level, evidence } = row
  return (
    <div className="grid grid-cols-[104px_74px_1fr] sm:grid-cols-[104px_74px_1fr_140px]
                    gap-3 items-center py-[9px] border-b border-[var(--color-border-light)]
                    last:border-b-0">
      <div className="text-[13px] font-semibold capitalize truncate"
           style={{ fontFamily: 'var(--font-cond)' }}>{key}</div>
      <Rungs level={level} count={levelCount} />
      <div className="text-[11px] leading-snug text-[var(--color-text-secondary)] truncate"
           title={evidence}>
        {evidence}
      </div>
      <div className="hidden sm:block justify-self-end">
        <Spark values={spark} title={`${key}: ${evidence}`} />
      </div>
    </div>
  )
}

export default function BoardCard({ board, history, session }) {
  if (!board?.rows?.length) return null
  const { rows, levels, measured, total } = board
  const offSession = isWeekend(session)
  const win = (history?.rows ?? []).slice(-SPARK_WINDOW)

  return (
    <div className="bg-[var(--color-surface)] rounded-3xl p-5">
      <div className="flex items-baseline justify-between pb-3 mb-1
                      border-b border-[var(--color-v2-ink)]">
        <h2 className="text-[11px] font-mono uppercase tracking-[.24em]
                       text-[var(--color-text-muted)]">盘面 · Board</h2>
        <span className="text-[11px] text-[var(--color-text-secondary)] font-mono">
          {session && <span className="mr-3">{session}</span>}
          {measured}/{total}
        </span>
      </div>

      {offSession && (
        <div className="border border-dashed border-[var(--color-untested)] px-3 py-2 mb-2">
          <p className="text-[11px] leading-relaxed text-[var(--color-text-secondary)] m-0">
            <b className="text-[var(--color-signal-caution)]">{session} 是周末</b> ——
            当天 ±4% 和涨跌家数是零因为没有交易，不是因为没有波动；下面的读数在等一个真实交易日。
          </p>
        </div>
      )}

      <div>
        {rows.map((r) => (
          <Row key={r.key} row={r} levelCount={levels.length}
               spark={(SPARK[r.key]?.(win)) ?? null} />
        ))}
      </div>

      <div className="flex flex-wrap gap-x-5 gap-y-1.5 pt-3 mt-1 text-[11px]
                      text-[var(--color-text-secondary)]">
        <span><i className="inline-block w-5 h-[12px] align-[-2px] mr-1.5"
                 style={{ background: 'var(--color-took)' }} />接住了</span>
        <span><i className="inline-block w-5 h-[12px] align-[-2px] mr-1.5"
                 style={{ background: 'var(--color-refused)', backgroundImage: HATCH }} />
          给了没接住</span>
        <span><i className="inline-block w-5 h-[12px] align-[-2px] mr-1.5 border border-dashed"
                 style={{ borderColor: 'var(--color-untested)' }} />没测到</span>
        <span className="text-[var(--color-text-muted)]">档位＝填格数，不看颜色深浅</span>
      </div>
    </div>
  )
}
