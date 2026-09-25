import { describe, it, expect } from 'vitest'
import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'

/**
 * T-0925-61: 69 notes.json entries had no matching OHLCV bars ("only a comment,
 * no candles" cards). Before this data landed, every id below was absent from
 * index.json and this test fails on `.find(...) is undefined`. 4 of the 69 stay
 * absent on purpose (BLD/COUP/CYBR/RNA — Yahoo has no history left for any of
 * them, see the T-0925-61 run notes); the other 65 must have survived the
 * quality gate with real bars.
 */
const DIR = resolve(process.cwd(), 'public/data/modelbooks')
const index = JSON.parse(readFileSync(resolve(DIR, 'index.json'), 'utf8'))
const excluded = JSON.parse(readFileSync(resolve(DIR, 'excluded.json'), 'utf8')).entries
const analysis = JSON.parse(readFileSync(resolve(DIR, 'analysis.json'), 'utf8')).entries

const EXPECTED_IDS = [
  'tl-deck-2018', 'tl-fnko-2018', 'tl-bep-2019', 'tl-cdlx-2019', 'tl-inmd-2019',
  'tl-rare-2020', 'tl-sq-2020', 'tl-camt-2023', 'tl-s-2023', 'tl-tol-2023',
  'tl-avgo-2024', 'tl-cort-2024', 'tl-inod-2024', 'tl-isrg-2024', 'tl-s-2024',
  'tl-spot-2024',
  'ml-crox-2006', 'ml-panw-2013', 'ml-tsla-2013', 'ml-sq-2016', 'ml-anab-2017',
  'ml-chgg-2017', 'ml-etsy-2017', 'ml-goos-2017', 'ml-mdgl-2017', 'ml-nktr-2017',
  'ml-sedg-2017', 'ml-crox-2018', 'ml-gshd-2018', 'ml-insp-2018', 'ml-arvn-2019',
  'ml-docu-2019', 'ml-plmr-2019', 'ml-beam-2020', 'ml-celh-2020', 'ml-meli-2020',
  'ml-mstr-2020', 'ml-pltr-2020', 'ml-shop-2020', 'ml-spce-2020', 'ml-tdoc-2020',
  'ml-twlo-2020', 'ml-zs-2020', 'ml-amd-2021', 'ml-cubi-2021', 'ml-dvn-2021',
  'ml-net-2021', 'ml-prta-2021', 'ml-pton-2021', 'ml-rblx-2021', 'ml-roku-2021',
  'ml-shop-2021', 'ml-tdoc-2021', 'ml-ceg-2022', 'ml-elf-2022', 'ml-nflx-2022',
  'ml-stng-2022', 'ml-tmdx-2022', 'ml-arm-2023', 'ml-vst-2023', 'ml-ggal-2024',
  'ml-ibit-2024', 'ml-rbrk-2024', 'ml-sn-2024', 'ml-vitl-2024',
]

const STILL_MISSING = ['tl-bld-2019', 'tl-coup-2019', 'ml-cybr-2018', 'tl-rna-2024']

describe('T-0925-61 model book OHLCV backfill', () => {
  it('has exactly the 65 fetchable ids in index.json, each pointing at a real bars file', () => {
    expect(EXPECTED_IDS).toHaveLength(65)
    for (const id of EXPECTED_IDS) {
      const entry = index.find(e => e.id === id)
      expect(entry, `${id} missing from index.json`).toBeDefined()
      expect(entry.gain_pct, `${id} must not invent gain_pct`).toBeNull()
      expect(existsSync(resolve(DIR, entry.ohlcv_file)), `${id} ohlcv file missing on disk`).toBe(true)
    }
  })

  it('survives the four-rule quality gate with zero exclusions', () => {
    for (const id of EXPECTED_IDS) {
      expect(excluded[id], `${id} should not be excluded: ${JSON.stringify(excluded[id])}`).toBeUndefined()
      expect(analysis[id], `${id} missing from analysis.json`).toBeDefined()
    }
  })

  it('picks up the model-book-stated breakout date for the three spot-checked entries', () => {
    const cases = {
      'tl-avgo-2024': '2023-11-02',
      'tl-cort-2024': '2024-05-09',
      'tl-spot-2024': '2023-11-09',
    }
    for (const [id, pivotDate] of Object.entries(cases)) {
      expect(analysis[id].pivot_source).toBe('stated')
      expect(analysis[id].pivot_date).toBe(pivotDate)
    }
  })

  it('the 4 tickers with no recoverable Yahoo history stay out of index.json', () => {
    for (const id of STILL_MISSING) {
      expect(index.find(e => e.id === id), `${id} should not exist yet — no source data`).toBeUndefined()
    }
  })
})
