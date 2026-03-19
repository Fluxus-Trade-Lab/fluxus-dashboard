import { useState } from 'react'
import { usePortfolio } from './context/PortfolioContext'
import { testConnection, pullFromSheets } from './services/sheetsSync'
import InputField from './ui/InputField'
import Button from './ui/Button'

export default function SettingsPanel({ onClose }) {
  const { state, dispatch } = usePortfolio()
  const [capitalInput, setCapitalInput] = useState(String(state.startingCapital))
  const [testResult, setTestResult] = useState(null)
  const [testing, setTesting] = useState(false)

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    const result = await testConnection(state.gasUrl, state.syncToken)
    setTestResult(result)
    setTesting(false)
  }

  const handleForcePull = async () => {
    dispatch({ type: 'SET_SYNC_STATUS', status: 'syncing' })
    const result = await pullFromSheets(state.gasUrl, state.syncToken)
    if (result.ok) {
      dispatch({ type: 'HYDRATE_FROM_SHEETS', ...result })
    } else {
      dispatch({ type: 'SET_SYNC_STATUS', status: 'error' })
    }
  }

  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-accent)]/20 p-5 mt-4">
      <div className="font-semibold mb-3 text-sm flex justify-between">
        <span>Settings</span>
        <button onClick={onClose} className="text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] cursor-pointer text-lg leading-none">&times;</button>
      </div>

      <div className="flex gap-3 items-end flex-wrap">
        <InputField
          label="Google Sheets Sync URL"
          value={state.gasUrl}
          onChange={e => dispatch({ type: 'SET_GAS_URL', url: e.target.value })}
          placeholder="https://script.google.com/macros/s/..."
          className="w-[360px]"
        />
        <InputField
          label="Sync Token"
          value={state.syncToken}
          onChange={e => dispatch({ type: 'SET_SYNC_TOKEN', token: e.target.value })}
          placeholder="your-secret-token"
          className="w-[180px]"
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

      {state.gasUrl && state.syncToken && (
        <div className="flex gap-2 mt-3">
          <Button variant="ghost" onClick={handleTest} disabled={testing}>
            {testing ? 'Testing...' : 'Test Connection'}
          </Button>
          <Button variant="ghost" onClick={handleForcePull}>
            Force Pull
          </Button>
        </div>
      )}

      {testResult && (
        <div className={`mt-2 text-xs ${testResult.ok ? 'text-green-600' : 'text-red-500'}`}>
          {testResult.ok
            ? `Connected — ${testResult.stockTradeCount} stock trades, ${testResult.optionsTradeCount} options trades`
            : `Failed: ${testResult.error}`}
        </div>
      )}

      <div className="mt-3 text-[11px] text-[var(--color-text-muted)] space-y-1">
        <p>
          Set up the Google Sheet "Fluxus Portfolio 2026 web" with tabs: Stock Trades, Options Trades, Meta.
          Deploy <code className="bg-[var(--color-border)] px-1 rounded">Code.gs</code> as a web app, then paste the URL and token above.
        </p>
        <p>
          Data syncs automatically. Changes push to Sheets within 2 seconds. On page load, data is pulled from Sheets.
        </p>
      </div>
    </div>
  )
}
