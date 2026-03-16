import { useState } from 'react'
import { useHash } from '../hooks/useHash'
import Header from './Header'
import TabNav from './TabNav'
import MacroSection from './macro/MacroSection'
import EquitiesSection from './equities/EquitiesSection'
import ScreenersSection from './screeners/ScreenersSection'
import ScreenerPage from './screener/ScreenerPage'
import PortfolioPage from './portfolio/PortfolioPage'
import JournalPage from './journal/JournalPage'
import BriefingPage from './briefing/BriefingPage'
import BreadthPage from './breadth/BreadthPage'
import ModelBooksPage from './modelbooks/ModelBooksPage'
import Footer from './Footer'

function pageKey(hash) {
  const key = hash.replace('#/', '') || 'dashboard'
  return key
}

export default function Layout({ data, lastUpdated, isOffline }) {
  const [activeTab, setActiveTab] = useState('macro')
  const [page, navigate] = useHash()
  const current = pageKey(page)

  return (
    <div className="min-h-screen bg-[#fafaf9]">
      <Header
        lastUpdated={lastUpdated}
        isOffline={isOffline}
        currentPage={current}
        onNavigate={navigate}
      />

      {current === 'dashboard' ? (
        <>
          <TabNav activeTab={activeTab} onTabChange={setActiveTab} />

          <main className="max-w-[1800px] mx-auto px-2 py-3">
            {/* Desktop: 3-column grid */}
            <div className="hidden sm:grid sm:grid-cols-3 gap-3">
              <MacroSection data={data} />
              <EquitiesSection data={data} />
              <ScreenersSection data={data} />
            </div>

            {/* Mobile: tab content */}
            <div className="sm:hidden">
              {activeTab === 'macro' && <MacroSection data={data} />}
              {activeTab === 'equities' && <EquitiesSection data={data} />}
              {activeTab === 'screeners' && <ScreenersSection data={data} />}
            </div>
          </main>
        </>
      ) : (
        <main className="max-w-[1800px] mx-auto px-2 py-3">
          {current === 'screener' && <ScreenerPage />}
          {current === 'portfolio' && <PortfolioPage />}
          {current === 'journal' && <JournalPage />}
          {current === 'briefing' && <BriefingPage />}
          {current === 'breadth' && <BreadthPage data={data} />}
          {current === 'modelbooks' && <ModelBooksPage />}
        </main>
      )}

      <Footer lastUpdated={lastUpdated} isOffline={isOffline} />
    </div>
  )
}
