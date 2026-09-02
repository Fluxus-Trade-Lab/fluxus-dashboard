import { useEffect, useState } from 'react'
import { getStatus, subscribe } from '../lib/writingStatus'
import { useLanguage } from '../i18n/LanguageContext'

const clock = (ts) => new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

/**
 * Save, and say which of the two saves has happened.
 *
 * The button exists because autosave is invisible and these words cannot be
 * regenerated. What it reports is deliberately two-part: local first, because
 * that is instant and already enough not to lose the sentence; the Sheet
 * after, because that takes seconds through Apps Script and is the copy that
 * survives this machine. Reporting one as if it were both would be a lie in
 * the one place on the site where a lie costs writing.
 *
 * Nothing here claims a sync that was never configured — `sheet: 'off'` shows
 * the local half alone.
 */
export default function SaveState({ onSave, dirty }) {
  const { t } = useLanguage()
  const [s, setS] = useState(getStatus)
  useEffect(() => subscribe(setS), [])

  const word =
    s.sheet === 'syncing' ? t('rev.saving.sheet')
    : s.sheet === 'error' ? t('rev.save.failed')
    : s.sheet === 'saved' && s.at ? t('rev.saved.sheet', { time: clock(s.at) })
    : s.local === 'saved' && s.at ? t('rev.saved', { time: clock(s.at) })
    : ''

  return (
    <span className="flex items-center gap-2">
      {word && (
        <span className={`text-[11px] font-mono ${
          s.sheet === 'error'
            ? 'text-[var(--color-refused)]'
            : 'text-[var(--color-text-muted)]'}`}>{word}</span>
      )}
      <button
        type="button"
        onClick={onSave}
        disabled={!dirty}
        title={dirty ? 'Save now' : 'Nothing unsaved'}
        className="text-[11px] font-mono uppercase tracking-[.14em] px-2 py-0.5 rounded
                   border border-[var(--color-border)] bg-transparent cursor-pointer
                   text-[var(--color-text-secondary)] hover:text-[var(--color-text)]
                   hover:bg-[var(--color-hover-bg)]
                   disabled:opacity-35 disabled:cursor-default disabled:hover:bg-transparent">
        {t('rev.save')}
      </button>
    </span>
  )
}
