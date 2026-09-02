import { useState } from 'react'
import DateNav from './DateNav'
import RecapViewer from './RecapViewer'
import DailyNotes from './DailyNotes'
import { todayET } from '../../lib/tradingDate'

export default function BriefingPage() {
  const [selectedDate, setSelectedDate] = useState(todayStr())

  return (
    <div className="max-w-4xl mx-auto py-6 px-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Market Briefing
        </h2>
        <DateNav date={selectedDate} onChange={setSelectedDate} />
      </div>
      <RecapViewer date={selectedDate} />
      <DailyNotes date={selectedDate} />
    </div>
  )
}

// The briefing is a SESSION's, so the default is the session's day in New
// York. On a UTC default the JST morning asked for tomorrow's briefing, which
// does not exist yet, and the page opened empty.
function todayStr() {
  return todayET()
}
