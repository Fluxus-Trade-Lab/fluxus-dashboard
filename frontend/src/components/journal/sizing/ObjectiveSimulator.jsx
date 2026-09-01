import { useState, useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { bootstrapObjective } from '../lib/sizingStats'

const RISK_CHIPS = [
  { value: 0.25, label: '0.25% target' },
  { value: 0.37, label: '0.37% his actual (÷entry-day eq)' },
  { value: 1.0, label: '1.0%' },
  { value: 2.0, label: '2.0%' },
]

/**
 * Fixed path count. bootstrapObjective() only guards an empty `rs` — a paths of
 * 0 divides by zero and hands back NaN probabilities plus undefined
 * percentiles, so this is deliberately a constant and never a user input.
 */
const PATHS = 2000

/**
 * Upper bound on the horizon. Each path walks `horizon` trades, so the inner
 * loop runs PATHS × horizon times synchronously — an unbounded field would let
 * a stray keystroke (e.g. 1000000) lock the tab.
 */
const MAX_HORIZON = 5000

function NumField({ label, value, onChange, step = 1, suffix, min, max }) {
  return (
    <div>
      <label className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1">
        {label}{suffix ? ` (${suffix})` : ''}
      </label>
      <input
        type="number"
        value={value}
        step={step}
        min={min}
        max={max}
        // parseFloat('') is NaN, so a cleared field falls back to 0 rather than
        // pushing NaN into the simulator. The 0 case is caught by the `sim`
        // guard below, which renders a prompt instead of a broken chart.
        onChange={e => {
          const next = parseFloat(e.target.value) || 0
          onChange(max != null ? Math.min(next, max) : next)
        }}
        className="w-full text-[12.5px] bg-[var(--color-bg)] rounded-3xl px-2 py-1.5 text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
      />
    </div>
  )
}

export default function ObjectiveSimulator({ rs }) {
  const [riskPct, setRiskPct] = useState(0.25)
  const [horizon, setHorizon] = useState(300)
  const [targetReturnPct, setTargetReturnPct] = useState(50)
  const [maxDDPct, setMaxDDPct] = useState(20)

  const hasSample = !!rs?.length
  const inputsValid = riskPct > 0 && horizon > 0

  const sim = useMemo(() => {
    // Both guards matter: bootstrapObjective returns null on an empty sample,
    // but a riskPct of 0 makes every path flat and a horizon of 0 collapses the
    // histogram to a single degenerate bucket. Neither is worth rendering.
    if (!rs?.length || riskPct <= 0 || horizon <= 0) return null
    return bootstrapObjective(rs, {
      riskPct,
      horizon,
      paths: PATHS,
      targetReturnPct,
      maxDDPct,
      seed: 42,
    })
  }, [rs, riskPct, horizon, targetReturnPct, maxDDPct])

  const targetSign = targetReturnPct >= 0 ? '+' : ''

  return (
    <div className="bg-[var(--color-surface)] rounded-3xl p-4 space-y-4">
      <div>
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Size to Objectives — Monte-Carlo
        </h3>
        <p className="text-[10px] text-[var(--color-text-muted)] mt-1">
          Tharp&rsquo;s key move: don&rsquo;t size to maximize — size to hit YOUR objective with an acceptable chance of YOUR worst drawdown.
          This resamples this account&rsquo;s own {rs?.length ?? 0} closed-trade R-distribution over {PATHS.toLocaleString()} paths.
        </p>
      </div>

      {/* Risk chips + inputs */}
      <div className="flex flex-wrap gap-1.5">
        {RISK_CHIPS.map(chip => (
          <button
            key={chip.value}
            onClick={() => setRiskPct(chip.value)}
            className={`px-2 py-1 text-[10px] font-medium rounded cursor-pointer transition-colors ${
              riskPct === chip.value
                ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] bg-[var(--color-surface-raised)]'
            }`}
          >
            {chip.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <NumField label="Risk / Trade" suffix="%" value={riskPct} step={0.05} min={0} onChange={setRiskPct} />
        <NumField label="Horizon" suffix="trades" value={horizon} step={50} min={0} max={MAX_HORIZON} onChange={setHorizon} />
        <NumField label="Target Return" suffix="%" value={targetReturnPct} step={10} onChange={setTargetReturnPct} />
        <NumField label="Max Acceptable DD" suffix="%" value={maxDDPct} step={5} min={0} onChange={setMaxDDPct} />
      </div>

      {!sim ? (
        <p className="text-[12.5px] text-[var(--color-text-muted)]">
          {!hasSample
            ? 'Not enough closed trades with stops to simulate.'
            : !inputsValid
              ? 'Set risk / trade and horizon above zero to run the simulation.'
              : 'Nothing to simulate.'}
        </p>
      ) : (
        <>
          {/* Verdict */}
          <p className="text-[12.5px] text-[var(--color-text)] leading-relaxed bg-[var(--color-bg)] rounded px-3 py-2">
            At <span className="font-semibold font-mono">{riskPct}%</span> risk over <span className="font-mono">{horizon}</span> trades:
            median <span className={`font-semibold font-mono ${sim.medianReturn >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>{sim.medianReturn >= 0 ? '+' : ''}{sim.medianReturn.toFixed(0)}%</span>,
            reaches ≥ {targetSign}{targetReturnPct}% in <span className="font-semibold font-mono">{sim.pReachTarget.toFixed(0)}%</span> of paths,
            with a <span className={`font-semibold font-mono ${sim.pBreachDD > 25 ? 'text-[var(--color-loss)]' : 'text-[var(--color-text)]'}`}>{sim.pBreachDD.toFixed(0)}%</span> chance of a drawdown greater than {maxDDPct}%.
          </p>

          {/* Stat tiles */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div>
              <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Median Return</span>
              <span className="text-[14px] font-semibold font-mono text-[var(--color-text)]">{sim.medianReturn >= 0 ? '+' : ''}{sim.medianReturn.toFixed(0)}%</span>
            </div>
            <div>
              <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">5th – 95th pctile</span>
              <span className="text-[12.5px] font-mono text-[var(--color-text)]">{sim.p5.toFixed(0)}% … {sim.p95.toFixed(0)}%</span>
            </div>
            <div>
              <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Median Max DD</span>
              <span className="text-[14px] font-medium font-mono text-[var(--color-text)]">−{sim.medianMaxDD.toFixed(1)}%</span>
            </div>
            <div>
              <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">P(≥ Target)</span>
              <span className="text-[14px] font-semibold font-mono text-[var(--color-profit)]">{sim.pReachTarget.toFixed(0)}%</span>
            </div>
            <div>
              <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">P(DD &gt; {maxDDPct}%)</span>
              <span className={`text-[14px] font-semibold font-mono ${sim.pBreachDD > 25 ? 'text-[var(--color-loss)]' : 'text-[var(--color-text)]'}`}>{sim.pBreachDD.toFixed(0)}%</span>
            </div>
          </div>

          {/* Ending-return histogram; bars at/above target tinted green */}
          <div className="h-36">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sim.histogram} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
                <XAxis
                  dataKey="x"
                  tickFormatter={v => `${Math.round(v)}%`}
                  tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }}
                  interval="preserveStartEnd"
                  tickLine={false}
                />
                <YAxis hide />
                <Tooltip
                  formatter={(v) => [`${v} paths`, 'Count']}
                  labelFormatter={v => `~${Math.round(v)}% ending return`}
                  contentStyle={{ fontSize: 10, background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}
                />
                <Bar dataKey="count" isAnimationActive={false}>
                  {sim.histogram.map((b, i) => (
                    <Cell key={i} fill={b.x >= targetReturnPct ? 'var(--color-profit)' : 'var(--color-border)'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <p className="text-[10px] text-[var(--color-text-muted)] leading-relaxed">
            Model note: i.i.d. bootstrap of realized R — ignores serial correlation, regime shifts, and that this R-sample comes from a bull half-year (it overstates the forward edge). Median and percentiles are order statistics of the {PATHS.toLocaleString()} simulated paths, not interpolated quantiles. That limitation is Tharp&rsquo;s point too: size to objectives, and respect what the sample can&rsquo;t tell you.
          </p>
        </>
      )}
    </div>
  )
}
