/**
 * A data field that the pipeline ships in two languages: `why` (zh, the field
 * of record) + `why_en`, or `cross_zone_rule` (en) + `cross_zone_rule_zh`.
 * Picks the twin for the page language when it exists; otherwise the field as
 * it arrived (older files carry one language only — shown, never blanked).
 */
export function inLang(obj, field, lang) {
  if (!obj) return undefined
  const twin = obj[`${field}_${lang}`]
  return twin != null ? twin : obj[field]
}
