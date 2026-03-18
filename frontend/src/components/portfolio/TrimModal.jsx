import { useState } from 'react'
import { usePortfolio } from './context/PortfolioContext'
import { todayStr } from './lib/portfolioFormat'
import InputField, { SelectField } from './ui/InputField'
import Button from './ui/Button'

export default function TrimModal({ trade, onClose }) {
  const { dispatch } = usePortfolio()
  const [trimType, setTrimType] = useState('trim_1_3')
  const [trimPrice, setTrimPrice] = useState('')
  const [trimDate, setTrimDate] = useState(todayStr())

  const handleTrim = () => {
    const price = parseFloat(trimPrice)
    if (!price) return
    dispatch({
      type: 'TRIM_TRADE',
      id: trade.id,
      trimType,
      trimPrice: price,
      trimDate,
    })
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-[var(--color-surface)] rounded-lg p-6 w-[340px] shadow-xl">
        <div className="font-bold mb-1">Trim / Sell — {trade.ticker}</div>
        <div className="text-xs text-[var(--color-text-muted)] mb-4">
          Remaining: {trade.currentQty} of {trade.originalQty}
        </div>

        <SelectField label="Action" value={trimType} onChange={e => setTrimType(e.target.value)}>
          <option value="trim_1_3">Trim 1/3 ({Math.floor(trade.originalQty / 3)})</option>
          <option value="trim_1_2">Trim 1/2 ({Math.floor(trade.originalQty / 2)})</option>
          <option value="trim_1_5">Trim 1/5 ({Math.floor(trade.originalQty / 5)})</option>
          <option value="sell_rest">Sell Rest ({trade.currentQty})</option>
        </SelectField>

        <div className="mt-2">
          <InputField label="Sell Price" type="number" step="0.01" value={trimPrice} onChange={e => setTrimPrice(e.target.value)} />
        </div>
        <div className="mt-2">
          <InputField label="Sell Date" type="date" value={trimDate} onChange={e => setTrimDate(e.target.value)} />
        </div>

        <div className="flex gap-2 mt-4">
          <Button onClick={handleTrim}>Confirm</Button>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
        </div>
      </div>
    </div>
  )
}
