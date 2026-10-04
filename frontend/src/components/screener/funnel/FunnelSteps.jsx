import { useLanguage } from '../../../i18n/LanguageContext'
import { STEP_KEYS } from './stepMath'

const fmt = (n) => (n == null ? '—' : n.toLocaleString('en-US'))
const PRESS = 'transition-transform duration-100 ease-out active:scale-[0.97]'

/**
 * 可交易 → 形态 → 资格 → 过闸 → 水域. Each cell is a name and a number; pressing a
 * cell filters the table to it. 水域 is an on/off cell, default off.
 * `counts[k] == null` means the step has no reading for this scan: the cell
 * shows a dash and cannot be pressed.
 */
export function StepBar({ counts, step, onStep, water, onWater }) {
  const { t } = useLanguage()
  const cell = 'flex-1 basis-[110px] min-w-0 text-left px-3 py-2.5 border border-[var(--color-border-light)] -ml-px first:ml-0 first:rounded-l-[10px] last:rounded-r-[10px]'
  return (
    <div role="group" aria-label={t('scx.steps.aria')} className="flex flex-wrap mb-3" data-testid="step-bar">
      {STEP_KEYS.map((k, i) => {
        const n = counts[k]
        const on = step === k
        const dead = n == null
        return (
          <button key={k} type="button" disabled={dead} aria-current={on ? 'step' : undefined}
                  data-step={k} onClick={() => onStep(k)}
                  className={`${cell} ${dead ? 'cursor-default' : `cursor-pointer ${PRESS}`}
                              ${on ? 'bg-[var(--color-surface)] shadow-[inset_0_-2px_0_var(--color-accent)]'
                                   : 'bg-transparent hover:bg-[var(--color-hover-bg)]'}`}>
            <span className="block font-mono text-[11px] tracking-[0.08em] text-[var(--color-text-muted)]">{i + 1}</span>
            <span className="block text-[13px] text-[var(--color-text-secondary)]">{t(`scx.step.${k}`)}</span>
            <span className={`block mt-0.5 font-mono text-[26px] leading-tight tabular-nums
                              ${dead ? 'text-[var(--color-text-muted)]' : 'text-[var(--color-text-bold)]'}`}>{fmt(n)}</span>
          </button>
        )
      })}
      <button type="button" aria-pressed={water} data-step="water" disabled={counts.water == null}
              onClick={onWater}
              className={`${cell} ${counts.water == null ? 'cursor-default' : `cursor-pointer ${PRESS}`}
                          ${water ? 'bg-[var(--color-surface)] shadow-[inset_0_-2px_0_var(--color-accent)]'
                                  : 'bg-transparent hover:bg-[var(--color-hover-bg)]'}`}>
        <span className="block font-mono text-[11px] tracking-[0.08em] text-[var(--color-text-muted)]">5</span>
        <span className="block text-[13px] text-[var(--color-text-secondary)]">
          {t('scx.step.water')} · {t(water ? 'scx.on' : 'scx.off')}
        </span>
        <span className={`block mt-0.5 font-mono text-[26px] leading-tight tabular-nums
                          ${water ? 'text-[var(--color-text-bold)]' : 'text-[var(--color-text-muted)] line-through'}`}>
          {fmt(counts.water)}
        </span>
      </button>
    </div>
  )
}

/** One scan list: the funnel's setups and the Today's List panels; no-data scans dashed. */
export function ScanList({ scans, active, onPick }) {
  const { t } = useLanguage()
  return (
    <div role="group" aria-label={t('scx.scans.aria')} className="flex flex-wrap gap-1.5 mb-4" data-testid="scan-list">
      {scans.map((s) => {
        const base = 'inline-flex items-baseline gap-1.5 rounded-md px-2.5 py-1 text-[13px] border'
        if (!s.live) {
          return (
            <span key={s.key} data-scan={s.key} aria-disabled="true"
                  className={`${base} border-dashed border-[var(--color-border)] text-[var(--color-text-muted)]`}>
              {s.label}
            </span>
          )
        }
        const on = s.key === active
        return (
          <button key={s.key} type="button" data-scan={s.key} aria-pressed={on} onClick={() => onPick(s.key)}
                  className={`${base} cursor-pointer ${PRESS}
                              ${on ? 'bg-[var(--color-text-bold)] border-[var(--color-text-bold)] text-[var(--color-bg)]'
                                   : 'bg-transparent border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-hover-bg)]'}`}>
            {s.label}<span className="font-mono opacity-75">{fmt(s.count)}</span>
          </button>
        )
      })}
    </div>
  )
}
