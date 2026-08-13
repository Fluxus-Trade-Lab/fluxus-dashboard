/**
 * How much of the interface actually speaks both languages.
 *
 * Counts two things per component: strings already going through `t()`, and
 * user-facing English still hard-coded in JSX. A missing key falls back to
 * English silently, so without this the interface looks finished in Chinese
 * while half of it is still in English — the same class of lie as an
 * unmeasured value rendering as zero.
 *
 *   node scripts/i18n-coverage.mjs          summary
 *   node scripts/i18n-coverage.mjs --list   every remaining string, by file
 */
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'

const ROOT = 'src/components'
const SKIP = /components\/public\//

function walk(dir, out = []) {
  for (const e of readdirSync(dir)) {
    const p = join(dir, e)
    if (statSync(p).isDirectory()) walk(p, out)
    else if (p.endsWith('.jsx') && !SKIP.test(p)) out.push(p)
  }
  return out
}

// Text a reader sees: JSX text nodes and the human-readable attributes.
const TEXT = />\s*([A-Z][A-Za-z][^<>{}\n]{3,90})\s*</g
const ATTR = /(?:title|placeholder|aria-label)="([A-Z][^"]{5,110})"/g

const rows = []
for (const f of walk(ROOT)) {
  const s = readFileSync(f, 'utf8')
  // both spellings: t('…') and the tr alias most components use
  const translated = (s.match(/\b(?:t|tr)\(['"`]/g) || []).length
  const hard = [
    ...[...s.matchAll(TEXT)].map((m) => m[1].trim()),
    ...[...s.matchAll(ATTR)].map((m) => m[1].trim()),
  ].filter((x) => !/^[\d\s.,%+\-—·/]*$/.test(x))
  if (translated || hard.length) rows.push({ f: f.replace(ROOT + '/', ''), translated, hard })
}

const T = rows.reduce((a, r) => a + r.translated, 0)
const H = rows.reduce((a, r) => a + r.hard.length, 0)
const pct = T + H ? ((T / (T + H)) * 100).toFixed(1) : '0.0'

if (process.argv.includes('--list')) {
  for (const r of rows.filter((r) => r.hard.length).sort((a, b) => b.hard.length - a.hard.length)) {
    console.log(`\n${r.f}  (${r.translated} translated, ${r.hard.length} left)`)
    for (const h of r.hard) console.log(`   ${h}`)
  }
  console.log()
}

console.log(`i18n coverage: ${T} translated / ${T + H} user-facing = ${pct}%`)
console.log(`${rows.filter((r) => r.hard.length).length} files still carry hard-coded English`)
