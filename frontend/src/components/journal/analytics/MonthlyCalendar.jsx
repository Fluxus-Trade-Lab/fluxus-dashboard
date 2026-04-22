import { useMemo, useState } from 'react'

/**
 * Monthly calendar heat-map showing daily P&L in $ or R.
 * Each cell is a weekday colored green (gain) or red (loss).
 */

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

function fmt$(v) {
  if (v == null) return ''
  const abs = Math.abs(v)
  if (abs >= 1000) return `${v < 0 ? '-' : '+'}$${(abs / 1000).toFixed(1)}k`
  return `${v < 0 ? '-' : '+'}$${abs.toFixed(0)}`
}

function fmtR(v) {
  if (v == null) return ''
  return `${v >= 0 ? '+' : ''}${v.toFixed(1)}R`
}

function cellColor(value) {
  if (value == null) return ''
  if (value > 0) return 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300'
  if (value < 0) return 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300'
  return 'bg-[var(--color-surface-alt)] text-[var(--color-text-muted)]'
}

export default function MonthlyCalendar({ monthEquity, startingCapital, riskPct = 0.0025 }) {
  const [view, setView] = useState('dollar') // 'dollar' | 'r'

  // Compute daily P&L from consecutive equity curve points
  const dailyPnL = useMemo(() => {
    if (!monthEquity || monthEquity.length < 2) return []

    const riskAmount = startingCapital * riskPct // 1R in dollar terms

    return monthEquity.slice(1).map((pt, i) => {
      const prev = monthEquity[i]
      const dollarPnL = pt.value - prev.value
      const rMultiple = riskAmount > 0 ? dollarPnL / riskAmount : 0
      return {
        date: pt.date,
        dollar: dollarPnL,
        r: rMultiple,
      }
    })
  }, [monthEquity, startingCapital, riskPct])

  // Build calendar grid: weeks × 5 weekdays
  const { weeks, monthTotal } = useMemo(() => {
    if (!dailyPnL.length) return { weeks: [], monthTotal: { dollar: 0, r: 0 } }

    // Map date → pnl
    const byDate = {}
    let totalDollar = 0
    let totalR = 0
    for (const d of dailyPnL) {
      byDate[d.date] = d
      totalDollar += d.dollar
      totalR += d.r
    }

    // Find first day of the month
    const firstDate = new Date(dailyPnL[0].date + 'T00:00:00')
    const year = firstDate.getFullYear()
    const month = firstDate.getMonth()
    const firstOfMonth = new Date(year, month, 1)
    const lastOfMonth = new Date(year, month + 1, 0)

    // Build week rows
    const result = []
    let currentWeek = []

    // Find Monday of the week containing the 1st
    const startDay = firstOfMonth.getDay() // 0=Sun, 1=Mon...
    const mondayOffset = startDay === 0 ? -6 : 1 - startDay
    const startDate = new Date(year, month, 1 + mondayOffset)

    for (let d = new Date(startDate); d <= lastOfMonth || currentWeek.length > 0;) {
      if (d.getDay() >= 1 && d.getDay() <= 5) {
        const dateStr = d.toISOString().split('T')[0]
        const inMonth = d.getMonth() === month
        currentWeek.push({
          date: dateStr,
          day: d.getDate(),
          inMonth,
          pnl: inMonth ? byDate[dateStr] || null : null,
        })
      }

      d.setDate(d.getDate() + 1)

      // New week starts on Monday
      if (d.getDay() === 1 || d > lastOfMonth) {
        if (currentWeek.length > 0) {
          // Pad to 5 days if needed
          while (currentWeek.length < 5) currentWeek.push({ date: '', day: 0, inMonth: false, pnl: null })
          result.push(currentWeek)
          currentWeek = []
        }
        if (d > lastOfMonth) break
      }
    }

    return { weeks: result, monthTotal: { dollar: totalDollar, r: totalR } }
  }, [dailyPnL])

  if (!dailyPnL.length) return null

  const formatter = view === 'dollar' ? fmt$ : fmtR
  const valueKey = view === 'dollar' ? 'dollar' : 'r'

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Daily P&L Calendar
        </h4>
        <div className="flex items-center gap-1">
          {['dollar', 'r'].map(v => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`px-2 py-0.5 text-[9px] font-mono rounded cursor-pointer transition-colors ${
                view === v
                  ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'
              }`}
            >
              {v === 'dollar' ? '$' : 'R'}
            </button>
          ))}
        </div>
      </div>

      {/* Weekday headers */}
      <div className="grid grid-cols-5 gap-1 mb-1">
        {WEEKDAYS.map(d => (
          <div key={d} className="text-center text-[9px] font-medium text-[var(--color-text-muted)] uppercase">
            {d}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="space-y-1">
        {weeks.map((week, wi) => (
          <div key={wi} className="grid grid-cols-5 gap-1">
            {week.map((cell, ci) => {
              if (!cell.inMonth || !cell.day) {
                return <div key={ci} className="h-12 rounded" />
              }
              const value = cell.pnl?.[valueKey] ?? null
              const color = cellColor(value)
              return (
                <div
                  key={ci}
                  className={`h-12 rounded flex flex-col items-center justify-center ${color || 'bg-[var(--color-surface-alt)]'}`}
                  title={cell.date}
                >
                  <span className="text-[9px] text-[var(--color-text-muted)] leading-none">{cell.day}</span>
                  <span className="text-[10px] font-mono font-medium leading-tight">
                    {value != null ? formatter(value) : ''}
                  </span>
                </div>
              )
            })}
          </div>
        ))}
      </div>

      {/* Month total */}
      <div className="flex items-center justify-between mt-3 pt-2 border-t border-[var(--color-border-light)]">
        <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)]">Month Total</span>
        <span className={`text-xs font-semibold font-mono ${monthTotal.dollar >= 0 ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'}`}>
          {view === 'dollar' ? fmt$(monthTotal.dollar) : fmtR(monthTotal.r)}
        </span>
      </div>
    </div>
  )
}
