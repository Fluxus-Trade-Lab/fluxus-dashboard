import { useState } from 'react'
import { useLanguage } from '../../i18n/LanguageContext'
import CoachTab from './CoachTab'

/**
 * One chat, with the setup picked inside it.
 *
 * Episodic Pivot, VCP and Breakout were three sections rendering one component
 * with a different prop — three entries in the navigation for one thing. Their
 * conversations live in `useState` and have never survived a navigation, so
 * folding them destroys nothing that was not already lost on every click.
 *
 * The `key` forces a fresh conversation per setup, which is the behaviour that
 * existed before: switching setups never carried the thread across.
 */
const SETUPS = ['episodic-pivot', 'vcp', 'breakout']

export default function SetupChat() {
  const { t } = useLanguage()
  const [setup, setSetup] = useState(SETUPS[0])

  return (
    <div>
      <div className="flex gap-1 mb-4 flex-wrap">
        {SETUPS.map((k) => (
          <button key={k} type="button" onClick={() => setSetup(k)}
            className={`px-2.5 py-1 text-[11px] rounded cursor-pointer transition-colors ${
              setup === k
                ? 'text-[var(--color-text)] font-semibold bg-[var(--color-hover-bg)]'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'}`}>
            {t(`rev.sec.${k}`)}
          </button>
        ))}
      </div>
      <CoachTab strategy={setup} key={setup} />
    </div>
  )
}
