import { useRef, useCallback } from 'react'
import { WINDOWS } from './replayMath'

/* The transport under the chart. Its track is marked with the ACTS rather than
   with bar numbers: every model book chart has the same three moments — the
   low, the breakout, the high — and marking those is what lets you jump to the
   day before the breakout on any chart in the library and compare. An act the
   author of a model book stated is drawn solid; one our own rule found is
   drawn hollow, so the two are never confused for each other. */

const ACT_LABEL = {
  low: '底',
  pivot: '突破日',
  peak: '最高点',
}

export default function ReplayTransport({
  barCount, cursor, acts, playing, speed, windowSize,
  onSeek, onStep, onPlayToggle, onSpeed, onWindow, onJump,
}) {
  const trackRef = useRef(null)

  const seek = useCallback(e => {
    const r = trackRef.current?.getBoundingClientRect()
    if (!r || barCount < 2) return
    const p = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width))
    onSeek(Math.round(p * (barCount - 1)))
  }, [barCount, onSeek])

  const pct = barCount > 1 ? (cursor / (barCount - 1)) * 100 : 0
  const jumpable = acts.filter(a => a.kind !== 'stated' || a.key === 'pivot')
  const win = windowSize === 0 ? '全程' : `${windowSize / 21} 个月`

  return (
    <div className="px-3 pt-2 pb-3 bg-[var(--color-surface-alt)] border-t border-[var(--color-border-light)]">
      <div
        ref={trackRef}
        className="relative h-[30px] cursor-pointer select-none"
        onPointerDown={e => { e.currentTarget.setPointerCapture(e.pointerId); seek(e) }}
        onPointerMove={e => { if (e.buttons) seek(e) }}
      >
        <div className="absolute left-0 right-0 top-[13px] h-1 rounded-full bg-[var(--color-border)]" />
        <div className="absolute left-0 top-[13px] h-1 rounded-full bg-[var(--color-accent)]"
             style={{ width: `${pct}%` }} />
        <div className="absolute top-2 w-[3px] h-3.5 rounded-full bg-[var(--color-text-bold)] -ml-[1.5px]"
             style={{ left: `${pct}%` }} />
        {acts.map((a, i) => {
          const passed = cursor >= a.index
          const colour = a.kind === 'stated'
            ? 'var(--color-accent)'
            : passed ? 'var(--color-text-secondary)' : 'var(--color-text-muted)'
          return (
            <div key={`${a.key}-${a.kind}-${i}`}
                 className="absolute top-0 -translate-x-1/2 text-center whitespace-nowrap"
                 style={{ left: `${(a.index / Math.max(barCount - 1, 1)) * 100}%`, color: colour }}
                 title={a.kind === 'stated'
                   ? `${a.book || '模型册'} 写明的突破日${a.price ? ` · $${a.price}` : ''}`
                   : '本站按规则算出的'}>
              <span className="text-[11px]">
                {ACT_LABEL[a.key]}{a.kind === 'stated' ? '' : '·算'}
              </span>
              <span className="block w-px h-2.5 mx-auto mt-[3px]"
                    style={{ backgroundColor: colour, opacity: a.kind === 'stated' ? 1 : 0.6 }} />
            </div>
          )
        })}
      </div>

      <div className="flex items-center gap-1.5 flex-wrap mt-2">
        <button onClick={onPlayToggle}
                className="font-mono text-[11px] px-3 py-1 rounded border min-w-[76px] cursor-pointer
                           bg-[var(--color-text-bold)] text-[var(--color-bg)] border-[var(--color-text-bold)]">
          {playing ? '❚❚ 暂停' : '▶ 播放'}
        </button>
        <Btn onClick={() => onStep(-1)}>◀ 一根</Btn>
        <Btn onClick={() => onStep(1)}>一根 ▶</Btn>
        <Btn onClick={onSpeed}>{speed}×</Btn>
        <span className="w-2" />
        {jumpable.map((a, i) => (
          <Btn key={`j${i}`} onClick={() => onJump(a.index)}>
            {ACT_LABEL[a.key]}{a.kind === 'stated' ? '' : '·算'}
          </Btn>
        ))}
        <Btn onClick={() => onJump(barCount - 1)}>全部显示</Btn>
        <span className="w-2" />
        <Btn onClick={() => onWindow(-1)} title="拉近">−</Btn>
        <Btn onClick={() => onWindow(0)} title="回到三个月">{win}</Btn>
        <Btn onClick={() => onWindow(1)} title="拉远">+</Btn>
        <span className="ml-auto text-[11px] font-mono text-[var(--color-text-muted)]">
          第 {cursor + 1} / {barCount} 根
        </span>
      </div>
    </div>
  )
}

function Btn({ children, ...rest }) {
  return (
    <button {...rest}
            className="font-mono text-[11px] px-2.5 py-1 rounded border cursor-pointer
                       border-[var(--color-border)] bg-[var(--color-surface)]
                       text-[var(--color-text-secondary)] hover:text-[var(--color-text)]">
      {children}
    </button>
  )
}

export { WINDOWS }
