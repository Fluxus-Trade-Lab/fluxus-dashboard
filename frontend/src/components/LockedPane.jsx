import { useLanguage } from '../i18n/LanguageContext'
import { BLURB, accessOf, BETA } from './access'

/* The closed-page card. Until 2026-09-28 this was a shop window — the real
   page rendered, then went soft behind the card. Andy took the blur down that
   day ("先把模糊的门禁撤了"): members pages now open in full, and only BETA
   pages (unfinished, closed to everyone) reach this component, as a card with
   nothing behind it. The notes below describe the blur as it was, kept so the
   reasoning is on file if a gate ever comes back.
 *
 * Andy, 2026-09-25: "可以点击这个栏目但是出现的是一个模糊的界面."
 *
 * Three things this has to get right, and one it must not pretend to do:
 *
 * 1. THE PAGE UNDERNEATH IS REAL. Not a mock, not a stock screenshot — this
 *    site's own dashboard with today's date in it. That is the whole argument
 *    for blurring instead of hiding: a competitor can fake a marketing
 *    screenshot, nobody can fake a page that is visibly live.
 * 2. IT MUST BE INERT. Blurred content still has focusable buttons and links
 *    underneath, and a keyboard user would tab straight into a page they
 *    cannot see. `inert` takes it out of the tab order and out of the
 *    accessibility tree in one attribute; `pointer-events:none` covers the
 *    mouse. Both, because they fail differently.
 * 3. THE CARD NAMES THE PAGE. "Members only" is a door. "This is the morning
 *    read: six steps, is today tradable and how big" is an advertisement. The
 *    blurb comes from `access.js` keyed per page.
 *
 * ⚠️ NOT SECURITY. The blur is CSS over data this site already serves publicly
 * from `data/output/`, out of a public repository. Anyone who opens devtools
 * reads every number. See the header of `access.js`. */

function LockGlyph({ size = 22 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="4.5" y="10.5" width="15" height="10" rx="2.5"
            stroke="currentColor" strokeWidth="1.6" />
      <path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" stroke="currentColor" strokeWidth="1.6"
            strokeLinecap="round" />
    </svg>
  )
}

export default function LockedPane({ page }) {
  const { t } = useLanguage()
  const blurbKey = BLURB[page]
  /* Two closed states, and the card must not blur them together. A members
     page is finished and one purchase away; a beta page is not finished and
     nobody is getting in, members included (Andy: "我没有再完成确认审核的板块
     那现在只是不对他们开放 只是写这是一个Beta"). Offering "see membership" on
     a beta page would be selling something that does not exist yet. */
  const beta = accessOf(page) === BETA

  /* 2026-09-28: no blur, and nothing rendered behind the card. Andy took the
     blurred gate down ("先把模糊的门禁撤了"); the only pages that still reach
     this component are BETA ones, which are closed, so there is no page to
     show through. The card sits in normal flow where the page would be.
     `children` is deliberately not rendered — an unfinished page should not
     mount (and fetch) just to be hidden. */
  return (
    <div className="relative">
      <div className="flex items-start justify-center px-4 pt-[10vh] pb-[16vh]">
        <div className="w-full max-w-[440px] rounded-2xl px-6 py-7 text-center"
             style={{ background: 'var(--color-surface)',
                      border: '1px solid var(--color-border)' }}>
          <div className="flex justify-center mb-3" style={{ color: 'var(--color-text-muted)' }}>
            <LockGlyph />
          </div>

          <p className="text-[17px] font-semibold m-0" style={{ color: 'var(--color-text-bold)' }}>
            {t(beta ? 'beta.title' : 'locked.title')}
          </p>

          {blurbKey && (
            <p className="text-[13px] leading-relaxed mt-2 mb-0"
               style={{ color: 'var(--color-text-secondary)' }}>
              {t(blurbKey)}
            </p>
          )}

          <p className="text-[13px] leading-relaxed mt-4 mb-0"
             style={{ color: 'var(--color-text-muted)' }}>
            {t(beta ? 'beta.note' : 'locked.freeHint')}
          </p>

          <div className="flex items-center justify-center gap-2 mt-5 flex-wrap">
            <a href="#/modelbooks"
               className="text-[13px] font-medium px-4 py-2 rounded-lg no-underline"
               style={{ background: 'var(--color-text-bold)', color: 'var(--color-bg)' }}>
              {t('locked.ctaFree')}
            </a>
            {!beta && (
              <a href="#/pricing"
                 className="text-[13px] font-medium px-4 py-2 rounded-lg no-underline"
                 style={{ background: 'var(--color-surface-raised)', color: 'var(--color-text-secondary)' }}>
                {t('locked.ctaJoin')}
              </a>
            )}
          </div>

          <p className="text-[11px] mt-4 mb-0" style={{ color: 'var(--color-text-muted)' }}>
            {beta ? '' : t('locked.beta')}
          </p>
        </div>
      </div>
    </div>
  )
}

export { LockGlyph }
