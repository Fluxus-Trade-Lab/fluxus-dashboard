import { QUESTIONS, QUESTION_LABEL, QUESTION_SORT, paces, momentumKind } from './rotationLogic'
import { fmtPct } from './TipBody'

const BLURB = {
  q1: 'behind → ahead: prior 3w up, this week up and faster; not strong 1–3m ago',
  q2: 'weak for months, quiet 3w, this week turned up and faster than the prior pace',
  q3: 'ahead for months, acceleration negative, still slowing this week',
}

/** the four stretches as a tiny bar shape, oldest first, this week darkest — each row's own scale */
export function Shape({ r, colour }) {
  const p = paces(r); const m = Math.max(...p.map(Math.abs)) || 1
  return (
    <span className="inline-flex items-end gap-[2px] h-[22px] relative" title={`per-week pace, oldest first: ${p.map((v) => fmtPct(v, 2)).join(' · ')}`}>
      <i className="absolute left-0 right-0 top-1/2 h-px" style={{ background: 'var(--rot-grid)' }} />
      {p.map((v, k) => { const h = Math.max(2, (Math.abs(v) / m) * 10)
        return <i key={k} className="block w-[8px] rounded-[1px] relative" style={{ height: h, marginBottom: v >= 0 ? 11 : 11 - h, background: k === 3 ? (colour ?? 'var(--rot-paper)') : 'var(--rot-muted)' }} /> })}
    </span>
  )
}

export default function QuestionLists({ lists, selected, onSelect, thresholds, onThresholds, colourOf }) {
  return (
    <div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {QUESTIONS.map((k) => (
          <div key={k}>
            <h3 className="m-0 text-[13px] font-extrabold">{QUESTION_LABEL[k]} <span className="font-semibold" style={{ color: 'var(--rot-muted)' }}>{lists[k].length}</span></h3>
            <div className="text-[11px] mb-2 min-h-[2.6em]" style={{ color: 'var(--rot-muted)' }}>{BLURB[k]}</div>
            {lists[k].length ? lists[k].map((r) => (
              <button key={r.group} type="button" aria-pressed={selected.includes(r.group)} onClick={() => onSelect(r.group)}
                      className="rot-row w-full text-left bg-transparent grid grid-cols-[1fr_52px_56px] gap-2 items-center py-[6px]">
                <span className="min-w-0">
                  <span className="block text-[13px] font-bold truncate">{r.group}</span>
                  <span className="block text-[11px]" style={{ color: 'var(--rot-muted)' }}>{r.members ?? r.tickers?.length ?? '—'} names · {r.state} · {momentumKind(r, k)} · persistence {r.persistence}/{r.persistence_of}</span>
                </span>
                <Shape r={r} colour={colourOf[r.state]} />
                <span className="text-[11px] font-extrabold text-right font-mono">{fmtPct(k === 'q3' ? r.rs_accel_rate : QUESTION_SORT[k](r))}</span>
              </button>
            )) : <div className="text-[11px] py-2" style={{ color: 'var(--rot-faint)', borderTop: '1px solid var(--rot-grid)' }}>none today — an empty list is a reading</div>}
          </div>
        ))}
      </div>
      <div className="flex flex-wrap gap-6 mt-4 text-[11px]" style={{ color: 'var(--rot-muted)' }}>
        <label className="grid grid-cols-[auto_1fr_auto] gap-2 items-center min-w-[280px]">
          <span>① "not strong before" cap</span>
          <input type="range" className="rot-range" min={0} max={0.15} step={0.005} value={thresholds.q1PriorCap} onChange={(e) => onThresholds({ ...thresholds, q1PriorCap: +e.target.value })} />
          <span className="font-mono font-bold" style={{ color: 'var(--rot-paper)' }}>{fmtPct(thresholds.q1PriorCap)}</span>
        </label>
        <label className="grid grid-cols-[auto_1fr_auto] gap-2 items-center min-w-[280px]">
          <span>② "prior 3w quiet" cap</span>
          <input type="range" className="rot-range" min={0} max={0.06} step={0.005} value={thresholds.q2PriorCap} onChange={(e) => onThresholds({ ...thresholds, q2PriorCap: +e.target.value })} />
          <span className="font-mono font-bold" style={{ color: 'var(--rot-paper)' }}>{fmtPct(thresholds.q2PriorCap)}</span>
        </label>
      </div>
    </div>
  )
}
