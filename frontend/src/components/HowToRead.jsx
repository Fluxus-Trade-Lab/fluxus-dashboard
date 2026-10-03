import { useState } from 'react'
import { useLanguage } from '../i18n/LanguageContext'

/**
 * A translated string with `**bold**` runs. Lets each language put its bold
 * phrase where its own word order needs it, instead of the sentence being
 * cut into fragments around a <b> that only fits one order.
 */
export function Rich({ text }) {
  const parts = String(text).split('**')
  return parts.map((p, i) => (i % 2 ? <b key={i}>{p}</b> : p))
}

/**
 * Teaching attached to the object it explains, not exiled to its own page.
 *
 * TSF puts "How To Interpret The Groups" inline on the overview rather than in
 * their tutorials section, and that is the better instinct: the moment someone
 * needs the definition is the moment they are looking at the thing.
 *
 * Collapsed by default. An explanation that is always open competes with the
 * reading for the top of the page, and the reader who already knows should not
 * have to scroll past it every session.
 */
export default function HowToRead({ children, video }) {
  const [open, setOpen] = useState(false)
  const { t } = useLanguage()

  return (
    <div className="border-t border-[var(--color-border-light)] mt-3 pt-2">
      <button type="button" onClick={() => setOpen((v) => !v)}
              className="flex items-baseline gap-2 text-[11px] font-mono uppercase
                         tracking-[.2em] text-[var(--color-text-muted)]
                         hover:text-[var(--color-text)] bg-transparent border-0 p-0
                         cursor-pointer">
        <span>{open ? '−' : '+'}</span>
        {t('db.howto.title')}
      </button>

      {open && (
        <div className="mt-3 text-[13px] leading-relaxed text-[var(--color-text-secondary)]
                        max-w-[72ch] space-y-2">
          {children}
          {video && (
            /* accent, not --color-took: that token means "quality" on this
               dashboard, and a link is not a signal. */
            <a href={video} target="_blank" rel="noreferrer"
               className="inline-block mt-1 text-[13px] text-[var(--color-accent)] underline">
              {t('db.howto.video')}
            </a>
          )}
        </div>
      )}
    </div>
  )
}
