import { useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Cell, ResponsiveContainer } from 'recharts'
import { useLanguage } from '../../i18n/LanguageContext'
import { positionSizeStats } from './lib/positionSize'

/**
 * Position size per trade — notional at entry ÷ equity at entry (%), in the SAME
 * order as the RR chart (by exit date) so the bars line up one-to-one. Blue =
 * the trade won, red = it lost. Studies bet-sizing / conviction calibration: do
 * the big bets earn their size, or are the biggest positions the biggest mistakes?
 *
 * The arithmetic moved to lib/positionSize so the Review card that opens this
 * page shows the same avg and correlation instead of its own.
 */
export default function PositionSizeChart({ enrichedTrades, performanceData, startingCapital }) {
  const { t } = useLanguage()
  const { data, avg, corr, lossShareTopQ } = useMemo(
    () => positionSizeStats(enrichedTrades, performanceData, startingCapital),
    [enrichedTrades, performanceData, startingCapital],
  )

  if (data.length < 3) return null

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5">
      <div className="flex items-center justify-between mb-1">
        <span className="font-semibold text-[13px]">{t('size.title')}</span>
        <span className="text-[13px] text-[var(--color-text-muted)]">
          {t('size.read', {
            avg: `${avg.toFixed(1)}%`,
            corr: corr != null ? (corr >= 0 ? '+' : '') + corr.toFixed(2) : '—',
            share: `${lossShareTopQ.toFixed(0)}%`,
          })}
        </span>
      </div>
      <div className="text-[11px] text-[var(--color-text-muted)] mb-2">
        {t('size.legend')}
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 5, right: 8, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" vertical={false} />
          <XAxis dataKey="i" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} tickFormatter={() => ''} />
          <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} tickFormatter={v => `${v}%`} width={44} />
          <Tooltip
            cursor={{ fill: 'var(--color-border-light)' }}
            contentStyle={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 8, fontSize: 13 }}
            formatter={(v, n, p) => [
              t('size.tip', { v: `${v}%` }) + (p?.payload?.r != null ? ` · ${p.payload.r.toFixed(1)}R` : ''),
              t('size.tip.name'),
            ]}
            labelFormatter={(i) => data[i]?.ticker + ' · ' + data[i]?.exit}
          />
          <ReferenceLine y={avg} stroke="var(--color-text-muted)" strokeDasharray="4 4" strokeOpacity={0.6} />
          <Bar dataKey="size" isAnimationActive={false}>
            {data.map((d, i) => <Cell key={i} fill={d.pl > 0 ? 'var(--color-profit)' : 'var(--color-loss)'} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
