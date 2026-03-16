import { useState } from 'react'
import { usePortfolio } from './context/PortfolioContext'
import { todayStr } from './lib/portfolioFormat'
import InputField, { SelectField } from './ui/InputField'
import Button from './ui/Button'

const WEIGHT_OPTIONS = [
  { value: '0.25', label: '0.25 — Bird' },
  { value: '1', label: '1 — Cat' },
  { value: '2', label: '2 — Goat' },
  { value: '4', label: '4 — Elephant' },
]

export default function OptionsTradeForm({ onClose }) {
  const { dispatch } = usePortfolio()

  const [form, setForm] = useState({
    entryDate: todayStr(),
    ticker: '',
    strike: '',
    expiry: '',
    weight: '1',
    costAvg: '',
    notes: '',
  })

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const handleSubmit = () => {
    if (!form.ticker || !form.strike || !form.costAvg || !form.expiry) return

    dispatch({
      type: 'ADD_OPTIONS_TRADE',
      trade: {
        id: Date.now().toString(),
        entryDate: form.entryDate,
        ticker: form.ticker.toUpperCase(),
        strike: form.strike.toUpperCase(),
        expiry: form.expiry,
        weight: parseFloat(form.weight),
        costAvg: parseFloat(form.costAvg),
        exitPrice: null,
        exitDate: null,
        notes: form.notes,
      },
    })

    onClose()
  }

  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5 mt-4">
      <div className="font-semibold mb-3 text-sm">Log Options Trade</div>
      <div className="flex gap-3 flex-wrap items-end">
        <InputField label="Entry Date" type="date" value={form.entryDate} onChange={set('entryDate')} />
        <InputField
          label="Ticker"
          value={form.ticker}
          onChange={(e) => setForm({ ...form, ticker: e.target.value.toUpperCase() })}
          placeholder="AAPL"
          className="w-[70px]"
        />
        <InputField
          label="Strike"
          value={form.strike}
          onChange={(e) => setForm({ ...form, strike: e.target.value.toUpperCase() })}
          placeholder="11C"
          className="w-[100px]"
        />
        <InputField label="Expiry" type="date" value={form.expiry} onChange={set('expiry')} />
        <SelectField label="Weight" value={form.weight} onChange={set('weight')}>
          {WEIGHT_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </SelectField>
        <InputField
          label="Cost Avg"
          type="number"
          step="0.01"
          value={form.costAvg}
          onChange={set('costAvg')}
          placeholder="0.00"
          className="w-[90px]"
        />
        <InputField
          label="Notes"
          value={form.notes}
          onChange={set('notes')}
          placeholder=""
          className="w-[200px]"
        />
        <Button onClick={handleSubmit}>Add Trade</Button>
      </div>
    </div>
  )
}
