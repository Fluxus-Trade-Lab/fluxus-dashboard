/**
 * The old four-tile summary, restored into a fold on 2026-09-11 (Andy: 「如果是
 * 有内容被删除了, 那我希望被删除的内容先放在折叠页里面」). Its numbers also sit in
 * the Archive's first row; what only this card had are the four readings in
 * words (thrust, ratio votes, T2108 zone) and their percentiles.
 * Its closing guidance sentence is the same field the Votes fold prints, so it
 * is printed there once rather than twice.
 */
/*
 * Every judgement on this card is the engine's, read from its votes — none is
 * recomputed here (DATA ALEX's 09-18 audit, Andy: 「全部按原文」). Two earlier
 * copies of the thrust rule drifted: a flat 300 on the price-only count, then
 * 0.113 × universe; the engine now follows Stockbee as written — back-to-back
 * 300+ days on his Market Monitor count (volume legs included). Reading the
 * vote means the card changes the night the engine does, and never argues.
 */
const VOTE_WORD = { bull: 'bull', bear: 'bear', neutral: 'neutral' }

export default function MarketStateSummary({ mm, breadth, verdict, lastRow }) {
  if (!mm || !breadth || !verdict) return null
  const ctx = verdict.context ?? {}
  const votes = verdict.votes ?? {}

  // Stockbee's own count (the engine's numerator); the price-only count only
  // as a labelled fallback for payloads that predate the column.
  const sbUp = lastRow?.up_4pct_stockbee, sbDown = lastRow?.down_4pct_stockbee
  const hasSb = Number.isFinite(sbUp) && Number.isFinite(sbDown)
  const up = hasSb ? sbUp : mm.up_4pct, down = hasSb ? sbDown : mm.down_4pct
  const churn = (verdict.notes ?? []).some((n) => /^Churn\/volatile/.test(n))
  const tDetail = verdict.vote_detail?.find((d) => d.key === 'thrust')
  const thrustLabel = tDetail && tDetail.measurable === false ? 'not measured'
    : churn ? 'churn / volatile'
    : votes.thrust === 'bull' ? 'bullish thrust'
    : votes.thrust === 'bear' ? 'bearish thrust'
    : 'no thrust'

  // T2108: <20 oversold and >80 overbought are Stockbee's; the three middle
  // bands (40/60) have no published source — they are ours, and say so.
  const t = breadth.t2108
  const t2108Zone =
    t == null ? '—' : t < 20 ? 'oversold' : t <= 40 ? 'weak · our band' : t < 60 ? 'neutral · our band'
    : t <= 80 ? 'strong · our band' : 'overbought'

  return (
    <div className="bg-[var(--color-bg)] rounded-2xl p-4">
      <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
        Market State Summary
      </h3>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <Tile
          label={hasSb ? 'Up 4% / Down 4% (Stockbee)' : 'Up 4% / Down 4% (price only)'}
          value={`${up ?? '—'} / ${down ?? '—'}`}
          note={thrustLabel}
          pct={ctx.down_4pct != null ? `down-4% ${ctx.down_4pct}th pctile` : null}
        />
        <Tile
          label="5-day / 10-day ratio"
          value={`${mm.ratio_5d?.toFixed(2) ?? '—'} / ${mm.ratio_10d?.toFixed(2) ?? '—'}`}
          note={votes.ratio_5d && votes.ratio_10d
            ? (votes.ratio_5d === votes.ratio_10d ? `both vote ${VOTE_WORD[votes.ratio_5d]}` : `5D ${VOTE_WORD[votes.ratio_5d]} · 10D ${VOTE_WORD[votes.ratio_10d]}`)
            : '—'}
          pct={ctx.ratio_5d != null ? `5D ${ctx.ratio_5d}th pctile` : null}
        />
        <Tile
          label="Quarterly breadth (25%+)"
          value={`${mm.up_25pct_qtr ?? '—'} / ${mm.down_25pct_qtr ?? '—'}`}
          note={votes.qtr_spread ? `votes ${VOTE_WORD[votes.qtr_spread]}` : '—'}
          pct={ctx.qtr_spread != null ? `spread ${ctx.qtr_spread}th pctile` : null}
        />
        <Tile
          label="T2108"
          value={t != null ? `${t.toFixed(1)}%` : '—'}
          note={t2108Zone}
          pct={ctx.t2108 != null ? `${ctx.t2108}th pctile` : null}
        />
      </div>
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
