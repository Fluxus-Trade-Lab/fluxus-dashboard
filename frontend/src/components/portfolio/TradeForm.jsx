import { useState } from 'react'
import { usePortfolio } from './context/PortfolioContext'
import { usePrices } from './hooks/usePrices'
import { getPortfolioValueAtDate } from './lib/equityCurve'
import { fmtCur, todayStr } from './lib/portfolioFormat'
import InputField, { SelectField } from './ui/InputField'
import Button from './ui/Button'
import { useLanguage } from '../../i18n/LanguageContext'

export default function TradeForm({ onClose }) {
  const { state, dispatch } = usePortfolio()
  const { getPriceForSizing } = usePrices()
  const { t: tr } = useLanguage()

  const [form, setForm] = useState({
    ticker: '', direction: 'long', entryDate: todayStr(),
    entryPrice: '', quantity: '', stopPrice: '',
    sizeMode: 'weight', weight: '', sector: '',
  })
  const [adding, setAdding] = useState(false)

  const handleSubmit = async () => {
    const { ticker, direction, entryDate, entryPrice, quantity, stopPrice, sizeMode, weight, sector } = form
    if (!ticker || !entryPrice || !stopPrice) return

    const price = parseFloat(entryPrice)
    const stop = parseFloat(stopPrice)
    setAdding(true)

    let qty
    if (sizeMode === 'weight') {
      const prevDay = new Date(entryDate)
      prevDay.setDate(prevDay.getDate() - 1)
      const prevDayStr = prevDay.toISOString().split('T')[0]

      // Find held tickers on prevDay
      const heldTickers = [...new Set(
        state.trades
          .filter(t => new Date(t.entryDate) <= new Date(prevDayStr))
          .filter(t => {
            const sold = (t.trims || []).filter(tr => new Date(tr.date) <= new Date(prevDayStr)).reduce((s, tr) => s + tr.qty, 0)
            return t.originalQty - sold > 0
          })
          .map(t => t.ticker)
      )]

      // Fetch missing prices
      if (heldTickers.length > 0) {
        await getPriceForSizing(heldTickers, prevDayStr)
      }

      const sizingValue = getPortfolioValueAtDate(state.trades, state.startingCapital, prevDayStr, state.dailyPrices)
      qty = Math.floor((parseFloat(weight) / 100 * sizingValue) / price)
    } else {
      qty = parseInt(quantity)
    }

    if (!qty || qty <= 0) {
      setAdding(false)
      dispatch({ type: 'SET_FETCH_STATUS', status: tr('pf.form.noQty') })
      return
    }

    dispatch({
      type: 'ADD_TRADE',
      trade: {
        id: Date.now().toString(),
        ticker: ticker.toUpperCase(),
        sector: sector || 'Unknown',
        direction,
        entryDate,
        entryPrice: price,
        originalQty: qty,
        currentQty: qty,
        stopPrice: stop,       // current / trailing
        initialStop: stop,     // locked at entry — R denominator
        trims: [],
        isClosed: false,
      },
    })

    setAdding(false)
    onClose()
  }

  // Sizing preview
  const sizingPreview = (() => {
    if (form.sizeMode !== 'weight' || !form.weight || !form.entryPrice) return null
    const prevDay = new Date(form.entryDate)
    prevDay.setDate(prevDay.getDate() - 1)
    const prevDayStr = prevDay.toISOString().split('T')[0]
    const baseVal = getPortfolioValueAtDate(state.trades, state.startingCapital, prevDayStr, state.dailyPrices)
    const estQty = Math.floor((parseFloat(form.weight) / 100 * baseVal) / parseFloat(form.entryPrice))
    return (
      <div className="mt-2 text-[11px] text-[var(--color-text-secondary)]">
        {tr('pf.form.preview', { qty: estQty, w: form.weight, base: fmtCur(baseVal), price: fmtCur(parseFloat(form.entryPrice)) })}
      </div>
    )
  })()

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5 mt-4">
      <div className="font-semibold mb-3 text-[13px]">{tr('pf.form.title')}</div>
      <div className="flex gap-3 flex-wrap items-end">
        <InputField label={tr('pf.form.ticker')} value={form.ticker} onChange={e => setForm({ ...form, ticker: e.target.value.toUpperCase() })} placeholder="AAPL" className="w-[70px]" />
        <SelectField label={tr('pf.form.direction')} value={form.direction} onChange={e => setForm({ ...form, direction: e.target.value })}>
          <option value="long">{tr('pf.form.long')}</option>
          <option value="short">{tr('pf.form.short')}</option>
        </SelectField>
        <InputField label={tr('pf.form.entryDate')} type="date" value={form.entryDate} onChange={e => setForm({ ...form, entryDate: e.target.value })} />
        <InputField label={tr('pf.form.entryPrice')} type="number" step="0.01" value={form.entryPrice} onChange={e => setForm({ ...form, entryPrice: e.target.value })} placeholder="0.00" className="w-[90px]" />
        <SelectField label={tr('pf.form.sizeBy')} value={form.sizeMode} onChange={e => setForm({ ...form, sizeMode: e.target.value })}>
          <option value="quantity">{tr('pf.form.quantity')}</option>
          <option value="weight">{tr('pf.form.weight')}</option>
        </SelectField>
        {form.sizeMode === 'quantity' ? (
          <InputField label={tr('pf.form.quantity')} type="number" value={form.quantity} onChange={e => setForm({ ...form, quantity: e.target.value })} placeholder="100" className="w-[80px]" />
        ) : (
          <InputField label={tr('pf.form.weight')} type="number" step="0.1" value={form.weight} onChange={e => setForm({ ...form, weight: e.target.value })} placeholder="10" className="w-[70px]" />
        )}
        <InputField label={tr('pf.form.stopPrice')} type="number" step="0.01" value={form.stopPrice} onChange={e => setForm({ ...form, stopPrice: e.target.value })} placeholder="0.00" className="w-[90px]" />
        <InputField label={tr('pf.form.sector')} value={form.sector} onChange={e => setForm({ ...form, sector: e.target.value })} placeholder={tr('pf.form.sectorAuto')} className="w-[95px]" />
        <Button onClick={handleSubmit} disabled={adding}>{adding ? tr('pf.form.adding') : tr('pf.form.add')}</Button>
      </div>
      {sizingPreview}
    </div>
  )
}
