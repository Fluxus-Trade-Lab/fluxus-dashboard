/**
 * Conditions catalog — one screen listing every row the nine-row board and
 * the fifteen-condition Market Conditions score read, so Andy can pick which
 * stay (T-0923-60, Andy 2026-09-21: 「先放上去，然后我们做筛选」).
 *
 * Static reference, not live data: what each row measures never changes
 * session to session, only the cut belongs to today. Sourced from
 * `pipeline/screeners/state_board.py` (the board) and `breadth_signals.py`'s
 * `conditions_series` (the fifteen), cross-checked against the provenance
 * already registered in `data/reference/METRIC_SOURCES.md` — this file does
 * not re-decide standard vs. ours, it only prints what that table already
 * says, so a change there must be echoed here by hand.
 *
 * `status` is a provenance tag, not a quality score, and deliberately does
 * not borrow the board's took/refused/untested colours — those mean rank
 * strength on this page already; a second meaning on the same three colours
 * is the confusion HowToRead.jsx's own comment warns against.
 */

const STATUS_LABEL = {
  standard: 'standard',
  mixed: 'standard input · our cut',
  custom: 'ours',
  no_data: 'no data',
}

const BOARD = [
  { key: 'damage', measures: 'Share of names down 25%+ on the quarter vs. up 25%+',
    source: 'Stockbee quarterly 25% scan (input) — cut points 0.55/0.45/0.35 are ours',
    status: 'mixed' },
  { key: 'selling pressure', measures: "Today's 4%-down count against its own 5-day peak",
    source: 'Stockbee 4% decliner count (input) — 0.5/0.8 ratio cuts are ours',
    status: 'mixed' },
  { key: 'breadth', measures: '% of names above the 20-day average, plus net advances',
    source: '% Above Moving Average family (formula) — pool is our Finviz universe, not a named index; level cuts are ours',
    status: 'mixed' },
  { key: 'trend', measures: '% of names above the 200-day average',
    source: 'Same family as breadth — pool mismatch, cuts ours',
    status: 'mixed' },
  { key: 'thrust', measures: 'Back-to-back 300+ names up or down 4% in a day',
    source: "Stockbee's own thrust rule, followed as published since 2026-09-18 — no local cut on top",
    status: 'standard' },
  { key: 'extremes', measures: 'Common-stock new highs vs. new lows',
    source: 'Common-stock NH/NL pool (standard since 2026-08-31) — the 2× ratio cuts are ours',
    status: 'mixed' },
  { key: 'index repair', measures: 'How many of SPY/QQQ are back above their own 50-day',
    source: 'No published source — internal design (Fluxus_Operator_Model.md)',
    status: 'custom' },
  { key: 'confirmation', measures: "Stockbee's 5-day ratio against 1.0 / 1.2",
    source: 'Stockbee 5-day ratio (input) — the 1.0/1.2 split is ours; Stockbee only publishes the 10-day thresholds',
    status: 'mixed' },
  { key: 'rates', measures: 'Long-end yields',
    source: 'Not wired into the pipeline — filled by hand',
    status: 'no_data' },
]

const CONDITIONS = [
  { key: 'ratio_5d', measures: '5-day Stockbee breadth ratio, sign vs. 1.0',
    source: 'Stockbee ratio (input) — 1.0 neutral line is ours; Stockbee publishes no 5-day threshold',
    status: 'mixed' },
  { key: 'ratio_10d', measures: '10-day Stockbee breadth ratio, sign vs. 1.0',
    source: 'Stockbee publishes >2 / <0.5 for this one — 1.0 here is a looser midpoint, ours',
    status: 'mixed' },
  { key: 't2108', measures: '% above the 40-day average, sign vs. 50',
    source: 'Worden T2108 (formula) — pool is Finviz, not NYSE',
    status: 'mixed' },
  { key: 'pct_above_200sma', measures: '% above the 200-day average, sign vs. 50',
    source: '% Above Moving Average family — pool mismatch',
    status: 'mixed' },
  { key: 'pct_above_50sma', measures: '% above the 50-day average, sign vs. 50',
    source: 'Same family — pool mismatch',
    status: 'mixed' },
  { key: 'pct_above_20sma', measures: '% above the 20-day average, sign vs. 50',
    source: 'Same family — pool mismatch',
    status: 'mixed' },
  { key: 'mcclellan_osc', measures: 'McClellan Oscillator, sign vs. 0',
    source: 'Formula matches — the summed pool is Finviz, not NYSE',
    status: 'mixed' },
  { key: 'net_advances', measures: "Today's advances minus declines, sign vs. 0",
    source: 'Advance-Decline Line’s own daily term — standard',
    status: 'standard' },
  { key: 'nh_nl', measures: 'Common-stock new highs minus new lows, sign vs. 0',
    source: 'Common-stock NH/NL pool — standard since 2026-08-31',
    status: 'standard' },
  { key: 'qtr_spread', measures: 'Stockbee quarterly 25%+ up minus down, sign vs. 0',
    source: 'Stockbee quarterly scan — standard since 2026-09-18',
    status: 'standard' },
  { key: 'spread_13_34', measures: 'Stockbee 13%/34-day up minus down, sign vs. 0',
    source: 'Stockbee 13%/34d scan — standard since 2026-09-18',
    status: 'standard' },
  { key: 'net_4pct', measures: "Today's 4% up minus down count, sign vs. 0",
    source: 'Stockbee 4% counts (input, standard) — the net-against-zero condition itself has no '
      + "Stockbee definition; renamed off 'thrust' because it shares none with his back-to-back "
      + '300+ rule',
    status: 'mixed' },
  { key: 'px_1m', measures: 'SPX trailing return over 21 sessions, sign vs. 0',
    source: 'No published source — 21 sessions is our stand-in for a month',
    status: 'custom' },
  { key: 'px_3m', measures: 'SPX trailing return over 63 sessions, sign vs. 0',
    source: 'No published source — 63 sessions is our stand-in for a quarter',
    status: 'custom' },
  { key: 'px_1y', measures: 'SPX trailing return over 252 sessions, sign vs. 0',
    source: 'No published source — 252 sessions is our stand-in for a year',
    status: 'custom' },
]

function StatusBadge({ status }) {
  return (
    <span data-testid="status-badge"
          className="inline-block shrink-0 text-[11px] font-mono uppercase tracking-wide
                     text-[var(--color-text-muted)] border border-[var(--color-border-light)]
                     rounded px-1.5 py-0.5">
      {STATUS_LABEL[status] ?? status}
    </span>
  )
}

function CatalogRow({ row }) {
  return (
    <div className="grid grid-cols-[110px_1fr] sm:grid-cols-[110px_1fr_auto] gap-x-3 gap-y-1
                    items-start py-[9px] border-b border-[var(--color-border-light)]
                    last:border-b-0">
      <div className="text-[13px] font-semibold capitalize text-[var(--color-text)]"
           style={{ fontFamily: 'var(--font-cond)' }}>{row.key}</div>
      <div className="text-[13px] leading-snug text-[var(--color-text-secondary)]">
        {row.measures}
        <div className="text-[11px] text-[var(--color-text-muted)] mt-0.5">{row.source}</div>
      </div>
      <div className="sm:justify-self-end sm:pt-[1px]"><StatusBadge status={row.status} /></div>
    </div>
  )
}

function CatalogGroup({ title, rows }) {
  return (
    <div>
      <div className="text-[11px] font-mono uppercase tracking-[.14em] text-[var(--color-text-muted)]
                      mb-1 pt-2">
        {title}
      </div>
      {rows.map((r) => <CatalogRow key={r.key} row={r} />)}
    </div>
  )
}

export default function ConditionsCatalog() {
  return (
    <div className="space-y-1">
      <p className="text-[13px] leading-relaxed text-[var(--color-text-secondary)] m-0 mb-2">
        Every row the board and the Market Conditions score read, one line each: what it
        measures, where the cut comes from, and whether that cut is a published standard or
        ours. Awaiting Andy&rsquo;s cut — what he drops here comes off the board and the
        Votes fold too.
      </p>
      <CatalogGroup title={`Board (${BOARD.length})`} rows={BOARD} />
      <CatalogGroup title={`Market Conditions (${CONDITIONS.length})`} rows={CONDITIONS} />
    </div>
  )
}
