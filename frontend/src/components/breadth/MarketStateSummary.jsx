export default function MarketStateSummary({ mm, breadth, verdict }) {
  if (!mm || !breadth || !verdict) return null
  const ctx = verdict.context ?? {}
  const qtrSpread = (mm.up_25pct_qtr ?? 0) - (mm.down_25pct_qtr ?? 0)

  const thrustLabel =
    (mm.up_4pct ?? 0) >= 300 && (mm.down_4pct ?? 0) >= 300 ? 'churn / volatile'
    : (mm.up_4pct ?? 0) >= 300 ? 'bullish thrust'
    : (mm.down_4pct ?? 0) >= 300 ? 'bearish thrust'
    : 'no thrust'

  const t = breadth.t2108
  const t2108Zone =
    t == null ? '—' : t < 20 ? 'oversold' : t <= 40 ? 'weak' : t < 60 ? 'neutral'
    : t <= 80 ? 'strong' : 'overbought'

  return (
    <div className="bg-[var(--color-surface)] rounded-3xl p-5">
      <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
        Market State Summary
      </h3>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <Tile
          label="Up 4% / Down 4%"
          value={`${mm.up_4pct ?? '—'} / ${mm.down_4pct ?? '—'}`}
          note={thrustLabel}
          pct={ctx.down_4pct != null ? `down-4% ${ctx.down_4pct}th pctile` : null}
          tone={thrustLabel === 'bullish thrust' ? 'up' : thrustLabel === 'bearish thrust' ? 'down' : ''}
        />
        <Tile
          label="5-day / 10-day ratio"
          value={`${mm.ratio_5d?.toFixed(2) ?? '—'} / ${mm.ratio_10d?.toFixed(2) ?? '—'}`}
          note={mm.ratio_5d >= 1 === mm.ratio_10d >= 1 ? 'ratios agree' : 'ratios disagree'}
          pct={ctx.ratio_5d != null ? `5D ${ctx.ratio_5d}th pctile` : null}
          tone={mm.ratio_5d >= 1 && mm.ratio_10d >= 1 ? 'up' : mm.ratio_5d < 0.5 && mm.ratio_10d < 0.5 ? 'down' : ''}
        />
        <Tile
          label="Quarterly breadth (25%+)"
          value={`${mm.up_25pct_qtr ?? '—'} / ${mm.down_25pct_qtr ?? '—'}`}
          note={qtrSpread > 0 ? 'structural bull intact' : qtrSpread < 0 ? 'structural bear' : 'flat'}
          pct={ctx.qtr_spread != null ? `spread ${ctx.qtr_spread}th pctile` : null}
          tone={qtrSpread > 0 ? 'up' : qtrSpread < 0 ? 'down' : ''}
        />
        <Tile
          label="T2108"
          value={t != null ? `${t.toFixed(1)}%` : '—'}
          note={t2108Zone}
          pct={ctx.t2108 != null ? `${ctx.t2108}th pctile` : null}
          tone={t2108Zone === 'strong' ? 'up' : t2108Zone === 'weak' ? 'down' : ''}
        />
      </div>
      <p className="text-[13px] text-[var(--color-text)]">{verdict.guidance}</p>
    </div>
  )
}

function Tile({ label, value, note, pct }) {
  // A naked figure with no mark of its own does not take the encoding colour;
  // the note under it says which way, in words.
  return (
    <div className="bg-[var(--color-bg)] rounded p-3">
      <div className="text-[11px] text-[var(--color-text-secondary)] font-medium uppercase tracking-wide mb-1">
        {label}
      </div>
      <div className="text-[17px] font-mono tabular-nums text-[var(--color-text)]">{value}</div>
      <div className="text-[11px] text-[var(--color-text-secondary)]">{note}</div>
      {pct && <div className="text-[11px] text-[var(--color-text-muted)]">{pct}</div>}
    </div>
  )
}
