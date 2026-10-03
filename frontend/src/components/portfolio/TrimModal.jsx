import { useState, useEffect, useRef } from 'react'
import { usePortfolio } from './context/PortfolioContext'
import { todayStr } from './lib/portfolioFormat'
import InputField, { SelectField } from './ui/InputField'
import Button from './ui/Button'
import { useLanguage } from '../../i18n/LanguageContext'

export default function TrimModal({ trade, onClose }) {
  const { dispatch } = usePortfolio()
  const { t: tr } = useLanguage()
  const [trimType, setTrimType] = useState('trim_1_3')
  const [trimPrice, setTrimPrice] = useState('')
  const [trimDate, setTrimDate] = useState(todayStr())
  const modalRef = useRef(null)

  useEffect(() => {
    const handleKey = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [onClose])

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
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50" role="dialog" aria-modal="true" ref={modalRef}>
      <div className="bg-[var(--color-surface)] rounded-lg p-6 w-[340px] shadow-xl">
        <div className="font-bold mb-1">{tr('pf.trim.title', { ticker: trade.ticker })}</div>
        <div className="text-[13px] text-[var(--color-text-muted)] mb-4">
          {tr('pf.trim.remaining', { cur: trade.currentQty, orig: trade.originalQty })}
        </div>

        <SelectField label={tr('pf.trim.action')} value={trimType} onChange={e => setTrimType(e.target.value)}>
          <option value="trim_1_3">{tr('pf.trim.opt3', { q: Math.floor(trade.originalQty / 3) })}</option>
          <option value="trim_1_2">{tr('pf.trim.opt2', { q: Math.floor(trade.originalQty / 2) })}</option>
          <option value="trim_1_5">{tr('pf.trim.opt5', { q: Math.floor(trade.originalQty / 5) })}</option>
          <option value="sell_rest">{tr('pf.trim.optRest', { q: trade.currentQty })}</option>
        </SelectField>

        <div className="mt-2">
          <InputField label={tr('pf.trim.price')} type="number" step="0.01" value={trimPrice} onChange={e => setTrimPrice(e.target.value)} />
        </div>
        <div className="mt-2">
          <InputField label={tr('pf.trim.date')} type="date" value={trimDate} onChange={e => setTrimDate(e.target.value)} />
        </div>

        <div className="flex gap-2 mt-4">
          <Button onClick={handleTrim}>{tr('pf.trim.confirm')}</Button>
          <Button variant="ghost" onClick={onClose}>{tr('pf.btn.cancel')}</Button>
        </div>
      </div>
    </div>
  )
}
