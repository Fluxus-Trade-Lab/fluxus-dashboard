/**
 * 传导 · Chain — how far a repair actually carried, in one line you can read
 * before you read the five rows under it.
 *
 * Data: breadth.json → state_board.chain (pipeline/screeners/state_board.py).
 * `carrying` is a running minimum — a link that goes unlit cannot make a later
 * link look lit again, which is why the connecting line is drawn once, behind
 * every node, rather than five independent bars: the CHAIN is the object, the
 * nodes are where you look closer.
 */

const HATCH =
  'repeating-linear-gradient(45deg,rgba(125,57,8,.55) 0 1.7px,transparent 1.7px 5px)'

function Dot({ l }) {
  const lit = l.state === 'lit'
  const partial = l.state === 'partial'
  const colour = lit ? 'var(--color-took)' : partial ? 'var(--color-text-muted)' : 'var(--color-untested)'
  return (
    <div className="flex flex-col items-center gap-1.5 flex-1 min-w-0">
      <div className="w-3 h-3 rounded-full shrink-0"
           style={{
             background: lit || partial ? colour : 'var(--color-v2-off)',
             border: lit || partial ? 'none' : `1.5px dashed ${colour}`,
           }} />
      <span className="text-[11px] font-mono uppercase tracking-[.08em] text-center leading-tight
                       text-[var(--color-text-muted)] truncate w-full">
        {l.label.replace(/^Indexes? |^Buyers |^Breadth |^New highs |^Confirmation /, '')}
      </span>
    </div>
  )
}

function LinkRow({ l }) {
  const lit = l.state === 'lit'
  const partial = l.state === 'partial'
  const colour = lit ? 'var(--color-took)' : partial ? 'var(--color-text-muted)' : 'var(--color-untested)'
  const pct = l.carrying == null ? null : Math.round(l.carrying * 100)
  return (
    <div className="py-1.5 border-b border-[var(--color-border-light)] last:border-b-0">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-[13px] font-semibold truncate" style={{ fontFamily: 'var(--font-cond)' }}>
          {l.label}
        </span>
        <span className="text-[11px] font-mono shrink-0" style={{ color: colour }}>
          {l.state === 'unmeasured' ? '未测' : `${pct}%`}
        </span>
      </div>
      <div className="h-[5px] mt-1 relative" style={{ background: 'var(--color-v2-off)' }}>
        <div className="h-full absolute left-0 top-0"
             style={{ width: `${pct ?? 0}%`, background: colour,
                       backgroundImage: l.state === 'unlit' ? HATCH : undefined }} />
      </div>
      {l.fed === false && (
        <div className="text-[11px] font-mono tracking-wider mt-1 text-[var(--color-text-muted)]">
          测到了，没传下来
        </div>
      )}
      <div className="text-[11px] leading-snug mt-1 text-[var(--color-text-secondary)] truncate"
           title={l.evidence}>
        {l.evidence}
      </div>
    </div>
  )
}

export default function ChainCard({ chain }) {
  if (!chain?.length) return null
  return (
    <div className="bg-[var(--color-surface)] rounded-3xl p-5 h-full flex flex-col">
      <div className="flex items-baseline justify-between pb-3 mb-3
                      border-b border-[var(--color-v2-ink)]">
        <h2 className="text-[11px] font-mono uppercase tracking-[.24em]
                       text-[var(--color-text-muted)]">传导 · Chain</h2>
        <span className="text-[11px] text-[var(--color-text-muted)]">断了不会自己接回来</span>
      </div>

      <div className="relative flex mb-4 px-1">
        <div className="absolute left-[10%] right-[10%] top-[6px] h-px bg-[var(--color-border)]" />
        {chain.map((l) => <Dot key={l.key} l={l} />)}
      </div>

      <div>{chain.map((l) => <LinkRow key={l.key} l={l} />)}</div>
    </div>
  )
}
