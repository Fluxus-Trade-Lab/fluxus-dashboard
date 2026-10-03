import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { LanguageProvider, useLanguage } from '../i18n/LanguageContext'
import Placeholder from './Placeholder'
import LockedPane from './LockedPane'

// Andy 2026-10-03: one language at a time. RS Live and the Masterclass sit
// behind the beta lock, so the live audit only ever sees the lock card; this
// renders the lock card AND the reserved page underneath it, in both languages.
const HAN = /\p{Script=Han}/u

function RsLive() {
  const { t } = useLanguage()
  return (
    <Placeholder group="market" title={t('nav.rs-live')} blurb={t('mem.rsLive.blurb')}
      willHold={[t('mem.rsLive.hold.bars'), t('mem.rsLive.hold.refresh'), t('mem.rsLive.hold.count')]}
      source="data/output/groups.json" />
  )
}
function Masterclass() {
  const { t } = useLanguage()
  return (
    <Placeholder group="course" title={t('nav.masterclass')} blurb={t('mem.mc.blurb')}
      willHold={[t('mem.mc.hold.lessons'), t('mem.mc.hold.gears'), t('mem.mc.hold.drafted')]} />
  )
}

function renderAll(lang) {
  localStorage.setItem('fluxus-lang', lang)
  render(
    <LanguageProvider>
      <LockedPane page="rs-live" />
      <LockedPane page="dashboard" />
      <RsLive />
      <Masterclass />
    </LanguageProvider>,
  )
}

describe('member pages — one language at a time', () => {
  afterEach(() => { cleanup(); localStorage.removeItem('fluxus-lang') })

  it('zh shows Chinese and none of the English labels', () => {
    renderAll('zh')
    for (const zh of ['RS 实时追踪', '波段交易大师课', '预留', '还没做', '这块还没做完', '这页暂时只给会员']) {
      expect(screen.getAllByText(zh).length).toBeGreaterThan(0)
    }
    for (const en of ['Reserved', 'not built yet', 'RS Live Tracker', 'Swing Trading Masterclass',
                      'Not finished yet', 'Members only, for now', 'Open Model Books']) {
      expect(screen.queryAllByText(en)).toHaveLength(0)
    }
    expect(document.body.textContent).not.toContain('Data it will read')
  })

  it('en shows no Han characters', () => {
    renderAll('en')
    expect(document.body.textContent).not.toMatch(HAN)
    expect(screen.getAllByText('Reserved').length).toBe(2)
    expect(screen.getByText('RS Live Tracker')).toBeInTheDocument()
  })
})
