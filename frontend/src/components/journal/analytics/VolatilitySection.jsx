import { useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import StatCard from '../../portfolio/ui/StatCard'
import { fmt, fmtPct, fmtCur } from '../../portfolio/lib/portfolioFormat'
import { useLanguage } from '../../../i18n/LanguageContext'

export default function VolatilitySection({ volContrib, portfolioVol, spyVol, dailyPrices, spyHistory }) {
  const { t } = useLanguage()

  // Merge rolling vol series for chart
  const rollingData = useMemo(() => {
    if (!portfolioVol?.rolling?.length) return []

    const byDate = {}
    portfolioVol.rolling.forEach(r => {
      byDate[r.date] = { date: r.date, portfolioVol: Number(r.portfolioVol.toFixed(1)) }
    })
    if (spyVol?.rolling) {
      spyVol.rolling.forEach(r => {
        if (byDate[r.date]) byDate[r.date].spyVol = Number(r.spyVol.toFixed(1))
        else byDate[r.date] = { date: r.date, spyVol: Number(r.spyVol.toFixed(1)) }
      })
    }

    return Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date))
  }, [portfolioVol, spyVol])

  // High-beta watchlist
  const highBeta = useMemo(() =>
    volContrib.filter(v => v.beta != null && v.beta > 1.5),
    [volContrib]
  )

  return (
    <div className="space-y-5">
      {/* Portfolio vol summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          label={t('jn.vol.portfolio')}
          value={portfolioVol ? fmtPct(portfolioVol.annualizedVol) : '—'}
          colorClass={portfolioVol && portfolioVol.annualizedVol > 25 ? 'text-[var(--color-signal-caution)]' : ''}
        />
        <StatCard
          label={t('jn.vol.spy')}
          value={spyVol ? fmtPct(spyVol.annualizedVol) : '—'}
        />
        <StatCard
          label={t('jn.vol.ratio')}
          value={portfolioVol && spyVol ? fmt(portfolioVol.annualizedVol / spyVol.annualizedVol, 2) + 'x' : '—'}
          sub={portfolioVol && spyVol ? (portfolioVol.annualizedVol / spyVol.annualizedVol > 1.5 ? t('jn.vol.high') : t('jn.vol.moderate')) : ''}
          colorClass={portfolioVol && spyVol && portfolioVol.annualizedVol / spyVol.annualizedVol > 1.5 ? 'text-[var(--color-signal-caution)]' : ''}
        />
        <StatCard
          label={t('jn.vol.daily')}
          value={portfolioVol ? fmtPct(portfolioVol.dailyVol) : '—'}
        />
      </div>

      {/* Rolling vol chart */}
      {rollingData.length > 0 && (
        <div className="bg-[var(--color-surface)] rounded-3xl p-5">
          <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
            {t('jn.vol.rolling')}
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={rollingData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} tickFormatter={d => d.slice(5)} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} tickFormatter={v => `${v}%`} />
              <Tooltip
                contentStyle={{ fontSize: 11, background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }}
                formatter={(v, name) => [`${v}%`, name]}
                labelFormatter={l => l}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="portfolioVol" name={t('jn.k.portfolio')} stroke="var(--color-text-bold)" dot={false} strokeWidth={2.4} />
              <Line type="monotone" dataKey="spyVol" name="SPY" stroke="var(--color-text-muted)" dot={false} strokeWidth={1} strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Per-position vol contribution */}
      {volContrib.length > 0 && (
        <div className="bg-[var(--color-surface)] rounded-3xl p-5">
          <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
            {t('jn.vol.perPos')}
          </h3>
          {volContrib.slice(0, 3).some(v => v.volContribution != null) && (
            <div className="bg-[color-mix(in_srgb,var(--color-signal-caution)_10%,transparent)] border border-[color-mix(in_srgb,var(--color-signal-caution)_30%,transparent)] rounded-md px-3 py-2 text-[13px] text-[var(--color-signal-caution)] mb-4">
              {t('jn.vol.top3', { list: volContrib.slice(0, 3).filter(v => v.volContribution != null).map(v => `${v.ticker} (${fmt(v.volContribution, 2)}%)`).join(', ') })}
            </div>
          )}
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[13px]">
              <thead>
                <tr>
                  {['jn.k.ticker', 'jn.k.weightPct', 'jn.vol.h.dailyVol', 'jn.vol.h.annVol', 'jn.k.beta', 'jn.vol.h.contrib'].map(h => (
                    <th key={h} className="text-left px-2 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[11px] uppercase tracking-wide">{t(h)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {volContrib.map((v, i) => (
                  <tr key={v.id || v.ticker + i} className={i % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-bg)]'}>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] font-medium">{v.ticker}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmt(v.weight, 1)}%</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{v.dailyVol != null ? fmtPct(v.dailyVol) : '—'}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{v.annualizedVol != null ? fmtPct(v.annualizedVol) : '—'}</td>
                    <td className={`px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${v.beta != null && v.beta > 1.5 ? 'text-[var(--color-signal-caution)] font-semibold' : ''}`}>
                      {v.beta != null ? fmt(v.beta, 2) : '—'}
                    </td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums font-semibold">{v.volContribution != null ? fmtPct(v.volContribution) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* High-beta watchlist */}
      {highBeta.length > 0 && (
        <div className="bg-[var(--color-surface)] rounded-3xl p-5">
          <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
            {t('jn.vol.highBeta')}
          </h3>
          <div className="bg-[color-mix(in_srgb,var(--color-signal-caution)_10%,transparent)] border border-[color-mix(in_srgb,var(--color-signal-caution)_30%,transparent)] rounded-md px-3 py-2 text-[13px] text-[var(--color-signal-caution)] mb-4">
            {t(highBeta.length > 1 ? 'jn.vol.highBeta.many' : 'jn.vol.highBeta.one', { n: highBeta.length })}
          </div>
          <table className="w-full border-collapse text-[13px]">
            <thead>
              <tr>
                {['jn.k.ticker', 'jn.k.beta', 'jn.k.weightPct', 'jn.k.mktVal', 'jn.vol.h.spyEq'].map(h => (
                  <th key={h} className="text-left px-2 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[11px] uppercase tracking-wide">{t(h)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {highBeta.map((v, i) => (
                <tr key={v.id || v.ticker + i} className={i % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-bg)]'}>
                  <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] font-medium">{v.ticker}</td>
                  <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-[var(--color-signal-caution)] font-semibold">{fmt(v.beta, 2)}</td>
                  <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmt(v.weight, 1)}%</td>
                  <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(v.mktVal)}</td>
                  <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(v.mktVal * v.beta)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
