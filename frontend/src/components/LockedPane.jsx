import { useLanguage } from '../i18n/LanguageContext'
import { LOCKED_BLURB } from './access'

/* The shop window: the real page renders, then goes soft behind a card that
   says what it is.
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

export default function LockedPane({ page, children }) {
  const { t } = useLanguage()
  const blurbKey = LOCKED_BLURB[page]

  return (
    <div className="relative">
      {/* The page itself. `inert` is what actually stops the keyboard getting
          in; the filter is only what the eye sees. */}
      <div
        inert=""
        aria-hidden="true"
        className="pointer-events-none select-none"
        style={{ filter: 'blur(5px) saturate(0.85)', transform: 'scale(1.01)' }}
      >
        {children}
      </div>

      {/* A wash, kept deliberately thin. The first version faded to 92% of
          the background and the page underneath went black — which defeats the
          entire point: this is a shop window, and a shop window you cannot see
          into is a wall. Enough to seat the card, not enough to hide the
          product. */}
      <div className="absolute inset-0 pointer-events-none"
           style={{ background:
             'linear-gradient(to bottom, color-mix(in srgb, var(--color-bg) 12%, transparent) 0%,'
             + ' color-mix(in srgb, var(--color-bg) 34%, transparent) 40%,'
             + ' color-mix(in srgb, var(--color-bg) 52%, transparent) 100%)' }} />

      <div className="absolute inset-0 flex items-start justify-center px-4 pt-[14vh] sm:pt-[18vh]">
        <div className="w-full max-w-[440px] rounded-2xl px-6 py-7 text-center"
             style={{ background: 'color-mix(in srgb, var(--color-surface) 96%, transparent)',
                      border: '1px solid var(--color-border)',
                      backdropFilter: 'blur(10px)',
                      boxShadow: '0 18px 50px -12px rgba(0,0,0,.55)' }}>
          <div className="flex justify-center mb-3" style={{ color: 'var(--color-text-muted)' }}>
            <LockGlyph />
          </div>

          <p className="text-[17px] font-semibold m-0" style={{ color: 'var(--color-text-bold)' }}>
            {t('locked.title')}
          </p>

          {blurbKey && (
            <p className="text-[13px] leading-relaxed mt-2 mb-0"
               style={{ color: 'var(--color-text-secondary)' }}>
              {t(blurbKey)}
            </p>
          )}

          <p className="text-[13px] leading-relaxed mt-4 mb-0"
             style={{ color: 'var(--color-text-muted)' }}>
            {t('locked.freeHint')}
          </p>

          <div className="flex items-center justify-center gap-2 mt-5 flex-wrap">
            <a href="#/modelbooks"
               className="text-[13px] font-medium px-4 py-2 rounded-lg no-underline"
               style={{ background: 'var(--color-text-bold)', color: 'var(--color-bg)' }}>
              {t('locked.ctaFree')}
            </a>
            <a href="#/pricing"
               className="text-[13px] font-medium px-4 py-2 rounded-lg no-underline"
               style={{ background: 'var(--color-surface-raised)', color: 'var(--color-text-secondary)' }}>
              {t('locked.ctaJoin')}
            </a>
          </div>

          <p className="text-[11px] mt-4 mb-0" style={{ color: 'var(--color-text-muted)' }}>
            {t('locked.beta')}
          </p>
        </div>
      </div>
    </div>
  )
}

export { LockGlyph }
