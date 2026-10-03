import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, cleanup } from '@testing-library/react'
import { LanguageProvider } from '../i18n/LanguageContext'
import Rail, { NAV_ITEMS } from './Rail'
import { hasRailIcon } from './railIcons'

/* Andy 2026-10-04: 「左侧导航栏，折叠起来的时候能否用小图标来表示，而不是缩写」.
   Collapsed, every rail row is an icon with a spoken name — no three-letter codes. */

function renderRail(collapsed) {
  localStorage.setItem('rail-collapsed', collapsed ? '1' : '0')
  return render(
    <LanguageProvider>
      <Rail currentPage="dashboard" onNavigate={() => {}} />
    </LanguageProvider>,
  )
}

describe('Rail icons', () => {
  beforeEach(() => localStorage.clear())
  afterEach(cleanup)

  it('every rail item has an icon', () => {
    const missing = NAV_ITEMS.filter((i) => !hasRailIcon(i.key)).map((i) => i.key)
    expect(missing).toEqual([])
  })

  it('collapsed rail renders an icon per item and no abbreviation text', () => {
    const { container } = renderRail(true)
    const rail = container.querySelector('nav')
    expect(rail.querySelectorAll('svg[data-rail-icon]').length).toBe(NAV_ITEMS.length)
    const buttons = [...rail.querySelectorAll('button')]
    for (const { short } of NAV_ITEMS) {
      // the hover tooltip holds the full name; the code itself must be gone
      for (const b of buttons) {
        const own = [...b.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join('')
        expect(own).not.toContain(short)
      }
      expect(rail.textContent).not.toMatch(new RegExp(`\\b${short}\\b`))
    }
  })

  it('every collapsed item has an accessible name and a title', () => {
    const { container } = renderRail(true)
    const buttons = [...container.querySelector('nav').querySelectorAll('button')]
    expect(buttons.length).toBe(NAV_ITEMS.length)
    for (const b of buttons) {
      const name = b.getAttribute('aria-label')
      expect(name && name.trim().length).toBeGreaterThan(3)
      expect(b.getAttribute('title')).toBe(name)
    }
  })

  it('active item keeps aria-current when collapsed', () => {
    const { container } = renderRail(true)
    const on = container.querySelector('nav button[aria-current="page"]')
    expect(on.getAttribute('aria-label')).toBeTruthy()
    expect(on.querySelector('svg[data-rail-icon="dashboard"]')).not.toBeNull()
  })

  it('locked pages keep a lock mark when collapsed', () => {
    const { container } = renderRail(true)
    expect(container.querySelectorAll('nav svg[data-rail-lock]').length).toBeGreaterThan(0)
  })

  it('expanded rail still shows labels', () => {
    const { container } = renderRail(false)
    expect(container.querySelector('nav').textContent).toContain('Dashboard')
  })
})
