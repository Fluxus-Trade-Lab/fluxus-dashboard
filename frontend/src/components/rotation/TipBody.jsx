export const fmtPct = (x, d = 1) => (x == null || !Number.isFinite(x) ? '—' : `${x >= 0 ? '+' : '−'}${Math.abs(x * 100).toFixed(d)}%`)

/** the hover readout for one group — the four stretches, the position, the names count */
export function TipBody({ r, state, x, y, colourOf }) {
  return (
    <>
      <b className="font-extrabold">{r.group}</b>{' '}
      <span className="font-bold" style={{ color: state === 'Leading' || state === 'Weakening' ? '#3159ad' : '#9c4f14' }}>{state ?? '—'}</span>
      <br />quarter {fmtPct(x ?? r.excess_3m)} · accel {fmtPct(y ?? r.rs_accel)}
      <br />this week {fmtPct(r.rs_0_1w)} · prior 3w {fmtPct(r.rs_1w_1m)} · 1–3m {fmtPct(r.rs_1m_3m)} · 3–6m {fmtPct(r.rs_3m_6m)}
      <br />{r.members ?? r.tickers?.length ?? '—'} names · persistence {r.persistence ?? '—'}/{r.persistence_of ?? '—'}
      {colourOf ? null : null}
    </>
  )
}
