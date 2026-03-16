import { useState } from 'react'
import DateNav from './DateNav'
import RecapViewer from './RecapViewer'
import DailyNotes from './DailyNotes'

export default function BriefingPage() {
  const [selectedDate, setSelectedDate] = useState(todayStr())

  return (
    <div className="max-w-4xl mx-auto py-6 px-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-[10px] font-medium uppercase tracking-wide text-stone-500">
          Market Briefing
        </h2>
        <DateNav date={selectedDate} onChange={setSelectedDate} />
      </div>
      <RecapViewer date={selectedDate} />
      <DailyNotes date={selectedDate} />
    </div>
  )
}

function todayStr() {
  return new Date().toISOString().split('T')[0]
}
