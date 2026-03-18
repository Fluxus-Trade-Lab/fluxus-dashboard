import { useState } from 'react'
import { usePortfolio } from './context/PortfolioContext'
import { usePrices } from './hooks/usePrices'
import { getPortfolioValueAtDate } from './lib/equityCurve'
import { fmtCur, todayStr } from './lib/portfolioFormat'
import InputField, { SelectField } from './ui/InputField'
import Button from './ui/Button'

export default function TradeForm({ onClose }) {
  const { state, dispatch } = usePortfolio()
  const { getPriceForSizing } = usePrices()

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
      dispatch({ type: 'SET_FETCH_STATUS', status: 'Could not compute qty. Check inputs.' })
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
        stopPrice: stop,
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
        ~ {estQty} shares = {form.weight}% x {fmtCur(baseVal)} / {fmtCur(parseFloat(form.entryPrice))}
      </div>
    )
  })()

  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5 mt-4">
      <div className="font-semibold mb-3 text-sm">Log New Trade</div>
      <div className="flex gap-3 flex-wrap items-end">
        <InputField label="Ticker" value={form.ticker} onChange={e => setForm({ ...form, ticker: e.target.value.toUpperCase() })} placeholder="AAPL" className="w-[70px]" />
        <SelectField label="Direction" value={form.direction} onChange={e => setForm({ ...form, direction: e.target.value })}>
          <option value="long">Long</option>
          <option value="short">Short</option>
        </SelectField>
        <InputField label="Entry Date" type="date" value={form.entryDate} onChange={e => setForm({ ...form, entryDate: e.target.value })} />
        <InputField label="Entry Price" type="number" step="0.01" value={form.entryPrice} onChange={e => setForm({ ...form, entryPrice: e.target.value })} placeholder="0.00" className="w-[90px]" />
        <SelectField label="Size By" value={form.sizeMode} onChange={e => setForm({ ...form, sizeMode: e.target.value })}>
          <option value="quantity">Quantity</option>
          <option value="weight">Weight %</option>
        </SelectField>
        {form.sizeMode === 'quantity' ? (
          <InputField label="Quantity" type="number" value={form.quantity} onChange={e => setForm({ ...form, quantity: e.target.value })} placeholder="100" className="w-[80px]" />
        ) : (
          <InputField label="Weight %" type="number" step="0.1" value={form.weight} onChange={e => setForm({ ...form, weight: e.target.value })} placeholder="10" className="w-[70px]" />
        )}
        <InputField label="Stop Price" type="number" step="0.01" value={form.stopPrice} onChange={e => setForm({ ...form, stopPrice: e.target.value })} placeholder="0.00" className="w-[90px]" />
        <InputField label="Sector" value={form.sector} onChange={e => setForm({ ...form, sector: e.target.value })} placeholder="Auto" className="w-[95px]" />
        <Button onClick={handleSubmit} disabled={adding}>{adding ? 'Adding...' : 'Add Trade'}</Button>
      </div>
      {sizingPreview}
    </div>
  )
}
