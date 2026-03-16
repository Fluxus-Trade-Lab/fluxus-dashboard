import { useState } from 'react'
import { usePortfolio } from './context/PortfolioContext'
import { todayStr } from './lib/portfolioFormat'
import InputField, { SelectField } from './ui/InputField'
import Button from './ui/Button'

export default function OptionsTradeForm({ onClose }) {
  const { dispatch } = usePortfolio()

  const [form, setForm] = useState({
    date: todayStr(),
    ticker: '',
    strategy: 'call',
    strike: '',
    expiry: '',
    direction: 'long',
    contracts: '',
    premium: '',
    notes: '',
  })

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const handleSubmit = () => {
    if (!form.ticker || !form.strike || !form.premium || !form.contracts || !form.expiry) return

    dispatch({
      type: 'ADD_OPTIONS_TRADE',
      trade: {
        id: Date.now().toString(),
        date: form.date,
        ticker: form.ticker.toUpperCase(),
        strategy: form.strategy,
        strike: parseFloat(form.strike),
        expiry: form.expiry,
        direction: form.direction,
        contracts: parseInt(form.contracts),
        premium: parseFloat(form.premium),
        closeDate: null,
        closePremium: null,
        notes: form.notes,
      },
    })

    onClose()
  }

  return (
    <div className="bg-stone-50 rounded-lg border border-stone-200 p-5 mt-4">
      <div className="font-semibold mb-3 text-sm">Log Options Trade</div>
      <div className="flex gap-3 flex-wrap items-end">
        <InputField label="Date" type="date" value={form.date} onChange={set('date')} />
        <InputField
          label="Ticker"
          value={form.ticker}
          onChange={(e) => setForm({ ...form, ticker: e.target.value.toUpperCase() })}
          placeholder="AAPL"
          className="w-[70px]"
        />
        <SelectField label="Strategy" value={form.strategy} onChange={set('strategy')}>
          <option value="call">Call</option>
          <option value="put">Put</option>
          <option value="call_spread">Call Spread</option>
          <option value="put_spread">Put Spread</option>
          <option value="iron_condor">Iron Condor</option>
          <option value="straddle">Straddle</option>
          <option value="strangle">Strangle</option>
          <option value="other">Other</option>
        </SelectField>
        <InputField
          label="Strike"
          type="number"
          step="0.01"
          value={form.strike}
          onChange={set('strike')}
          placeholder="0.00"
          className="w-[90px]"
        />
        <InputField label="Expiry" type="date" value={form.expiry} onChange={set('expiry')} />
        <SelectField label="Direction" value={form.direction} onChange={set('direction')}>
          <option value="long">Long</option>
          <option value="short">Short</option>
        </SelectField>
        <InputField
          label="Contracts"
          type="number"
          value={form.contracts}
          onChange={set('contracts')}
          placeholder="1"
          className="w-[70px]"
        />
        <InputField
          label="Premium /sh"
          type="number"
          step="0.01"
          value={form.premium}
          onChange={set('premium')}
          placeholder="0.00"
          className="w-[90px]"
        />
        <InputField
          label="Notes"
          value={form.notes}
          onChange={set('notes')}
          placeholder=""
          className="w-[120px]"
        />
        <Button onClick={handleSubmit}>Add Trade</Button>
      </div>
    </div>
  )
}
