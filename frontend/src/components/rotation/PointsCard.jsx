import { useLanguage } from '../../i18n/LanguageContext'
import { BOARDS, LINE, fmtPct, radius, pack, spreadLabels } from './rotationLogic'
import { STRIP_W as W, STRIP_H as H, STRIP_PAD as PAD, STRIP_X0 as X0, LABEL_DX, LABEL_FS, squeezeTo, textWidth } from './stripLayout'

/**
 * MOMENTUM & ACCELERATION · 两种动能和加速度 · 点 — three vertical axes,
 * every theme one dot on each. 爆发 RS 0–2w, 转折 Acceleration, 持续 Quarter.
 * The dot grows with the value so the leaders read first; the top five and
 * bottom two are named with their value, the rest are the lightest grey.
 * Click a dot or a name to put that theme on the Flux line.
 */
function Strip({ board, items, selected, onSelect, t }) {
  const vals = items.map((it) => it[board.key])
  const lo = Math.min(0, ...vals), hi = Math.max(0, ...vals)
  const y = (v) => PAD.t + ((hi - v) / (hi - lo || 1)) * (H - PAD.t - PAD.b)
  const dots = pack(items.map((it) => ({ y: y(it[board.key]), r: radius(it[board.key], lo, hi) })), X0)
  const named = items.map((it, j) => j < 5 || j >= items.length - 2 || selected.includes(it.r.group))
  const labels = spreadLabels(items.map((it, j) => ({ it, j })).filter(({ j }) => named[j]), ({ j }) => dots[j].y, 16)

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="rot-strip" preserveAspectRatio="xMinYMin meet" role="img" aria-label={`${t(board.word)} ${board.title}`}>
      <text className="rot-ink" x="0" y="13" style={{ fontSize: 13 }}>{t(board.word)} <tspan style={{ fill: 'var(--color-text-muted)', fontWeight: 500 }}>· {board.title}</tspan></text>
      <line x1={X0} x2={X0} y1={PAD.t} y2={H - PAD.b} stroke="var(--color-border-light)" />
      <line x1={X0 - 30} x2={X0 + 30} y1={y(0).toFixed(1)} y2={y(0).toFixed(1)} stroke="var(--color-text-secondary)" strokeWidth="1" strokeDasharray="3 3" />
      {items.map((it, j) => {
        const k = selected.indexOf(it.r.group)
        return (
          <circle key={it.r.group} cx={dots[j].x.toFixed(1)} cy={dots[j].y.toFixed(1)} r={radius(it[board.key], lo, hi).toFixed(1)}
                  fill={k >= 0 ? LINE[k] : named[j] ? 'var(--color-text)' : 'var(--color-slot-4, var(--color-border))'}
                  stroke="var(--color-surface)" strokeWidth="1.5" style={{ cursor: 'pointer' }} onClick={() => onSelect(it.r.group)}>
            <title>{it.r.group} · {fmtPct(it[board.key])}</title>
          </circle>
        )
      })}
      {labels.map(({ item: { it }, y: ly }) => {
        const k = selected.indexOf(it.r.group)
        const squeeze = squeezeTo(textWidth(`${it.r.group} ${fmtPct(it[board.key])}`))
        return (
          <text key={it.r.group} x={X0 + LABEL_DX} y={(ly + 4).toFixed(1)} textLength={squeeze} lengthAdjust={squeeze ? 'spacingAndGlyphs' : undefined}
                style={{ cursor: 'pointer', fontSize: LABEL_FS, fill: k >= 0 ? LINE[k] : 'var(--color-text)' }} onClick={() => onSelect(it.r.group)}>
            {it.r.group} <tspan className="rot-mono" style={{ fill: 'var(--color-text-muted)', fontSize: 12 }}>{fmtPct(it[board.key])}</tspan>
          </text>
        )
      })}
    </svg>
  )
}

export default function PointsCard({ boards, selected, onSelect }) {
  const { t } = useLanguage()
  return (
    <div className="rot-card">
      <div className="rot-head"><h2 className="rot-title">{t('rot.points')}</h2></div>
      <div className="rot-three">
        {BOARDS.map((b) => (boards[b.key]?.length ? <Strip key={b.key} board={b} items={boards[b.key]} selected={selected} onSelect={onSelect} t={t} /> : <div key={b.key} className="rot-empty">{b.title}: nothing measurable.</div>))}
      </div>
    </div>
  )
}
