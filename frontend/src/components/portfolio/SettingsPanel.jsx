import { useState } from 'react'
import { usePortfolio } from './context/PortfolioContext'
import InputField from './ui/InputField'
import Button from './ui/Button'

export default function SettingsPanel({ onClose }) {
  const { state, dispatch } = usePortfolio()
  const [capitalInput, setCapitalInput] = useState(String(state.startingCapital))

  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-accent)]/20 p-5 mt-4">
      <div className="font-semibold mb-3 text-sm flex justify-between">
        <span>Settings</span>
        <button onClick={onClose} className="text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] cursor-pointer text-lg leading-none">&times;</button>
      </div>

      <div className="flex gap-3 items-end flex-wrap">
        <InputField
          label="GAS Proxy URL"
          value={state.gasUrl}
          onChange={e => dispatch({ type: 'SET_GAS_URL', url: e.target.value })}
          placeholder="https://script.google.com/macros/s/..."
          className="w-[360px]"
        />
        <InputField
          label="Starting Capital"
          type="number"
          value={capitalInput}
          onChange={e => setCapitalInput(e.target.value)}
          className="w-[120px]"
        />
        <Button variant="ghost" onClick={() => {
          const v = parseFloat(capitalInput)
          if (v > 0) dispatch({ type: 'SET_CAPITAL', capital: v })
        }}>
          Update
        </Button>
      </div>

      <div className="mt-3 text-[11px] text-[var(--color-text-muted)] space-y-1">
        <p>
          Deploy the <code className="bg-[var(--color-border)] px-1 rounded">gas/Code.gs</code> script as a Google Apps Script web app,
          then paste the URL above. See the README for setup instructions.
        </p>
        <p>
          Prices fetched via Yahoo Finance through your GAS proxy. Hit "Refresh" to update open positions.
        </p>
      </div>
    </div>
  )
}
