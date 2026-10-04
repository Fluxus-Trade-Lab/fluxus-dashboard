import { translations } from '../../i18n/translations'

/**
 * A scan's display name, in the reader's language.
 *
 * English keeps what it always printed: the base dictionary's `wlp.<key>`, or
 * the file's own label for a scan it does not know. Chinese looks at `wl2.panel`
 * first — the names the base dictionary never had, plus one it had with
 * English left in — then `wlp`, then the file's label, so a scan the pipeline
 * adds tomorrow still shows up rather than vanishing.
 */
export function panelName(t, lang, key, label) {
  // checked against the dictionary first, so a key zh simply does not
  // override is not reported as a missing translation
  if (lang === 'zh' && `wl2.panel.${key}` in translations.zh) return t(`wl2.panel.${key}`)
  const v = t(`wlp.${key}`)
  return v === `wlp.${key}` ? (label ?? key) : v
}

/** The same, starting from an English label (the shortlist tray stores the
 *  label a name was taken from, not the scan key). Unknown labels print as
 *  they arrived. */
export function panelNameFromLabel(t, lang, label) {
  if (lang !== 'zh' || label == null) return label
  for (const [k, v] of Object.entries(translations.en)) {
    if (v !== label) continue
    const m = k.match(/^(?:wlp|wl2\.panel)\.(.+)$/)
    if (m) return panelName(t, lang, m[1], label)
  }
  return label
}
