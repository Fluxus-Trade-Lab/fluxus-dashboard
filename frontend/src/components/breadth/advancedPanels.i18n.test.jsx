/* global process */
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { render, screen } from '@testing-library/react'
import { LanguageProvider } from '../../i18n/LanguageContext'
import BreadthTable from './BreadthTable'

// Andy 2026-10-03: one language at a time. The archive table on the real
// breadth.json, in Chinese, must not leave English column heads behind.
const breadth = JSON.parse(readFileSync(resolve(process.cwd(), '..', 'data/output/breadth.json'), 'utf8'))

describe('archive table in Chinese', () => {
  beforeEach(() => localStorage.setItem('fluxus-lang', 'zh'))
  afterEach(() => localStorage.removeItem('fluxus-lang'))

  it('prints Chinese column heads and legend, no English heads', () => {
    render(<LanguageProvider><BreadthTable data={breadth} /></LanguageProvider>)
    for (const h of ['日期', '涨4%', '跌4%', '5日比', '季涨25%', '上涨家数', '新高', '新低']) {
      expect(screen.getByText(h)).toBeInTheDocument()
    }
    expect(screen.queryByText('Date')).toBeNull()
    expect(screen.queryByText('Up 4%')).toBeNull()
    expect(screen.getByText('灰色斜体')).toBeInTheDocument()
    // proper nouns stay Latin
    expect(screen.getByText('A/D line')).toBeInTheDocument()
  })
})
