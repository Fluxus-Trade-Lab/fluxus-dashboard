import { useState } from 'react'
import { usePortfolio } from './context/PortfolioContext'
import { testConnection, pullFromSheets } from './services/sheetsSync'
import InputField from './ui/InputField'
import Button from './ui/Button'
import { useLanguage } from '../../i18n/LanguageContext'
import { rich } from '../screener/richText'

export default function SettingsPanel({ onClose }) {
  const { state, dispatch } = usePortfolio()
  const { t: tr } = useLanguage()
  const [capitalInput, setCapitalInput] = useState(String(state.startingCapital))
  const [testResult, setTestResult] = useState(null)
  const [testing, setTesting] = useState(false)

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    const result = await testConnection(state.gasUrl, state.syncToken)
    setTestResult(result)
    /* A successful test IS a successful sync — it pulled the sheet. Until
       2026-08-24 this only set local state, so the header could say "367
       trades, connected" while the ✕ from a cold start that morning stayed
       lit: nothing else clears that mark, because clearing it takes a push and
       a push takes a data change. Andy reported the ✕; the data side traced it
       and handed back two fixes (DATA_CONTRACTS §七). This is the first.
       A failed test leaves the mark alone — it is not new information. */
    if (result.ok) dispatch({ type: 'SET_SYNC_STATUS', status: 'success' })
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
      <div className="font-semibold mb-3 text-[13px] flex justify-between">
        <span>{tr('pf.btn.settings')}</span>
        <button onClick={onClose} className="text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] cursor-pointer text-[17px] leading-none">&times;</button>
      </div>

      <div className="flex gap-3 items-end flex-wrap">
        <InputField
          label={tr('pf.set.url')}
          value={state.gasUrl}
          onChange={e => dispatch({ type: 'SET_GAS_URL', url: e.target.value })}
          placeholder="https://script.google.com/macros/s/..."
          className="w-[360px]"
        />
        <InputField
          label={tr('pf.set.token')}
          value={state.syncToken}
          onChange={e => dispatch({ type: 'SET_SYNC_TOKEN', token: e.target.value })}
          placeholder={tr('pf.set.tokenPh')}
          className="w-[180px]"
        />
        <InputField
          label={tr('pf.set.capital')}
          type="number"
          value={capitalInput}
          onChange={e => setCapitalInput(e.target.value)}
          className="w-[120px]"
        />
        <Button variant="ghost" onClick={() => {
          const v = parseFloat(capitalInput)
          if (v > 0) dispatch({ type: 'SET_CAPITAL', capital: v })
        }}>
          {tr('pf.set.update')}
        </Button>
      </div>

      {state.gasUrl && state.syncToken && (
        <div className="flex gap-2 mt-3">
          <Button variant="ghost" onClick={handleTest} disabled={testing}>
            {testing ? tr('pf.set.testing') : tr('pf.set.test')}
          </Button>
          <Button variant="ghost" onClick={handleForcePull}>
            {tr('pf.set.forcePull')}
          </Button>
        </div>
      )}

      {testResult && (
        <div className={`mt-2 text-[13px] ${testResult.ok ? 'text-[var(--color-text-secondary)]' : 'text-[var(--color-loss)]'}`}>
          {testResult.ok
            ? tr('pf.set.connected', { stock: testResult.stockTradeCount, options: testResult.optionsTradeCount })
            : tr('pf.set.failed', { error: testResult.error })}
        </div>
      )}

      <div className="mt-3 text-[11px] text-[var(--color-text-muted)] space-y-1">
        <p>
          {rich(tr('pf.set.help1'), { code: <code className="bg-[var(--color-border)] px-1 rounded">Code.gs</code> })}
        </p>
        <p>
          {tr('pf.set.help2')}
        </p>
      </div>
    </div>
  )
}
