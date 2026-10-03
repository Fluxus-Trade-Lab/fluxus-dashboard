/* global process */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { act, render } from '@testing-library/react'
import { LanguageProvider, useLanguage } from '../../i18n/LanguageContext'
import LibraryPage from './LibraryPage'

/* Andy 2026-10-03: 「整个网页需要有完整的中文和英文界面，而非个别地方才有中文或者英文」.
   The Library shelf on the real MRNA piece: Chinese mode speaks Chinese, English
   mode carries no Han characters. The body is Chinese-only and is not translated;
   its cover says so. */
const ART = JSON.parse(readFileSync(
  resolve(process.cwd(), '..', 'data/output/library/offense_ep_mrna.json'), 'utf8'))
const HOLDS = ['sizing', 'pyramiding', 'leverage', 'grading']

// the props Layout passes
function Offense({ entry }) {
  const { t } = useLanguage()
  return <LibraryPage entry={entry} page="offense" group="library" title={t('nav.offense')}
                      blurb={t('lib.blurb.offense')}
                      willHold={HOLDS.map((h) => t(`lib.hold.offense.${h}`))} />
}

async function draw(lang, entry) {
  localStorage.setItem('fluxus-lang', lang)
  vi.stubGlobal('fetch', (url) => {
    const key = String(url).split('/').pop()
    if (key === 'offense_ep_mrna.json') return Promise.resolve({ ok: true, json: async () => ART })
    return Promise.resolve({ ok: false })
  })
  let c
  await act(async () => { c = render(<LanguageProvider><Offense entry={entry} /></LanguageProvider>) })
  await act(async () => { await new Promise((r) => setTimeout(r, 0)) })
  return c.container.textContent
}

describe('Library — complete interface in each language', () => {
  afterEach(() => { vi.unstubAllGlobals(); localStorage.removeItem('fluxus-lang') })

  it('Chinese mode: page chrome and reserved topics in Chinese', async () => {
    const txt = await draw('zh')
    for (const s of ['进攻', '仓位多大', '1 篇', '还预留了', '金字塔加仓', '读全文 →', ART.title, ART.summary])
      expect(txt, s).toContain(s)
    for (const s of ['Offense', 'from the index', 'compiled-in list', 'Also reserved',
                     'Sizing', 'Pyramiding', 'Read', '(in Chinese)'])
      expect(txt, s).not.toContain(s)
  })

  it('English mode: no Han characters on the shelf, and the cover says the piece is Chinese', async () => {
    const txt = await draw('en')
    expect(txt).toContain('Offense')
    expect(txt).toContain('EP (Episodic Pivot)')
    expect(txt).toContain('Specimen: MRNA, 2026-08-19')
    expect(txt).toContain('1 piece')
    expect(txt).toContain('Read → (in Chinese)')
    expect(txt).toContain('Also reserved')
    expect(txt.match(/[㐀-鿿]/g)).toBeNull()
  })

  it('English mode, opened piece: the body stays Chinese and the page says so', async () => {
    const txt = await draw('en', 'ep_mrna')
    expect(txt).toContain('This piece is written in Chinese only.')
    expect(txt).toContain('← Offense')
  })

  it('Chinese mode, unknown piece: the not-found note is Chinese', async () => {
    const txt = await draw('zh', 'nope')
    expect(txt).toContain('没有这一篇')
    expect(txt).toContain('这一页没有叫 nope 的篇目。')
    expect(txt).not.toContain('No such piece')
  })
})
