import { useState, useRef, useEffect, useCallback } from 'react'

const STRATEGY_DESCRIPTIONS = {
  'episodic-pivot': {
    name: 'Episodic Pivot',
    description: 'Gap-up breakouts on significant news (earnings, FDA, contracts). High reward-to-risk entries.',
    samplePrompts: [
      'Review this setup: AAPL gapped up 8% on earnings beat',
      'What makes a good episodic pivot vs a news trap?',
      'My last EP trade got stopped out — how do I set better stops?',
    ]
  },
  'vcp': {
    name: 'Volatility Contraction Pattern',
    description: 'Bases with decreasing price contractions indicating institutional accumulation before breakout.',
    samplePrompts: [
      'How many contractions should I look for?',
      'Is a 3-week base too short for a VCP?',
      'Review: MSFT has 4 contractions with 15%→8%→4%→2% depth',
    ]
  },
  'breakout': {
    name: 'Breakout Trading',
    description: 'Classic breakouts from proper bases — cup with handle, flat base, double bottom.',
    samplePrompts: [
      'What volume should I look for on a breakout day?',
      'How do I tell a proper base from a faulty one?',
      'Should I buy the breakout or wait for a pullback?',
    ]
  },
}

function buildCopyPrompt(strategy, config, messages, newMessage) {
  const historyBlock = messages.length > 0
    ? '\n## Conversation so far\n' + messages.map(m =>
        `${m.role === 'user' ? 'Me' : 'Coach'}: ${m.content}`
      ).join('\n\n') + '\n'
    : ''

  return `You are an expert trading coach specializing in ${config.name}. ${config.description}

Be direct, specific, and actionable. Reference concrete examples when possible. Keep responses under 300 words.
${historyBlock}
## My question
${newMessage}`
}

export default function CoachTab({ strategy }) {
  const config = STRATEGY_DESCRIPTIONS[strategy] || {}
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [apiDisabled, setApiDisabled] = useState(false)
  const [copied, setCopied] = useState(false)
  const [pendingMessage, setPendingMessage] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Reset when strategy changes
  useEffect(() => {
    setMessages([])
    setInput('')
    setPendingMessage(null)
    setCopied(false)
  }, [strategy])

  const callApi = useCallback(async (userMessage, history) => {
    try {
      const res = await fetch('/api/coach', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          strategy,
          message: userMessage,
          history: history.map(m => ({ role: m.role, content: m.content })),
        }),
      })

      if (res.status === 503) {
        // API disabled — switch to copy-paste mode
        setApiDisabled(true)
        return null
      }

      if (!res.ok) return null

      const data = await res.json()
      return data.reply || null
    } catch {
      // Network error or no API route — fall back to copy-paste
      setApiDisabled(true)
      return null
    }
  }, [strategy])

  const handleSend = useCallback(async () => {
    if (!input.trim()) return
    const userMessage = input.trim()
    const userMsg = { role: 'user', content: userMessage }

    setMessages(prev => [...prev, userMsg])
    setInput('')

    if (apiDisabled) {
      // Copy-paste mode: show pending state
      setPendingMessage(userMessage)
      return
    }

    // Try API
    setLoading(true)
    const reply = await callApi(userMessage, [...messages, userMsg])
    setLoading(false)

    if (reply) {
      setMessages(prev => [...prev, { role: 'assistant', content: reply }])
    } else if (apiDisabled) {
      // API just became disabled — show copy prompt
      setPendingMessage(userMessage)
    }
  }, [input, messages, apiDisabled, callApi])

  const handleCopyPrompt = useCallback(() => {
    const prompt = buildCopyPrompt(strategy, config, messages.slice(0, -1), pendingMessage)
    navigator.clipboard.writeText(prompt)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [strategy, config, messages, pendingMessage])

  const handlePasteResponse = useCallback(() => {
    navigator.clipboard.readText().then(text => {
      if (text.trim()) {
        setMessages(prev => [...prev, { role: 'assistant', content: text.trim() }])
        setPendingMessage(null)
      }
    }).catch(() => {
      // Clipboard read denied — show textarea fallback
      const text = window.prompt('Paste Claude\'s response:')
      if (text?.trim()) {
        setMessages(prev => [...prev, { role: 'assistant', content: text.trim() }])
        setPendingMessage(null)
      }
    })
  }, [])

  return (
    <div className="space-y-4">
      {/* Strategy header */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-[var(--color-text-bold)] mb-1">{config.name}</h3>
            <p className="text-xs text-[var(--color-text-secondary)]">{config.description}</p>
          </div>
          {apiDisabled && (
            <span className="text-[9px] font-medium uppercase tracking-wider px-2 py-0.5 rounded bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]">
              Copy-paste mode
            </span>
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
        <div className="min-h-[300px] max-h-[500px] overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && !loading && (
            <div className="text-center py-12">
              <div className="text-xs text-[var(--color-text-muted)] uppercase tracking-wide mb-4">
                Ask the {config.name} coach anything
              </div>
              <div className="flex flex-wrap gap-2 justify-center">
                {config.samplePrompts?.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(prompt)}
                    className="px-3 py-1.5 text-[11px] text-[var(--color-text-secondary)] bg-[var(--color-bg)] border border-[var(--color-border)] rounded-full hover:bg-[var(--color-hover-bg)] cursor-pointer transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] px-3 py-2 rounded-lg text-sm ${
                msg.role === 'user'
                  ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                  : 'bg-[var(--color-bg)] text-[var(--color-text)] border border-[var(--color-border)]'
              }`}>
                <div className="whitespace-pre-wrap">{msg.content}</div>
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {loading && (
            <div className="flex justify-start">
              <div className="px-3 py-2 rounded-lg text-sm bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text-muted)]">
                Thinking...
              </div>
            </div>
          )}

          {/* Copy-paste fallback prompt */}
          {pendingMessage && !loading && (
            <div className="flex justify-start">
              <div className="max-w-[80%] px-4 py-3 rounded-lg bg-[var(--color-bg)] border border-dashed border-[var(--color-border)] space-y-2">
                <p className="text-xs text-[var(--color-text-secondary)]">
                  Copy the prompt to claude.ai, then paste the response back.
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={handleCopyPrompt}
                    className="px-3 py-1 text-[11px] font-medium rounded cursor-pointer bg-[var(--color-accent)] text-white hover:opacity-90 transition-opacity"
                  >
                    {copied ? 'Copied!' : 'Copy Prompt'}
                  </button>
                  <button
                    onClick={handlePasteResponse}
                    className="px-3 py-1 text-[11px] font-medium rounded cursor-pointer bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)] hover:opacity-90 transition-opacity"
                  >
                    Paste Response
                  </button>
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="border-t border-[var(--color-border)] p-3 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !loading && handleSend()}
            placeholder={`Ask about ${config.name?.toLowerCase() || 'trading'}...`}
            disabled={loading}
            className="flex-1 px-3 py-2 border border-[var(--color-border)] rounded text-sm bg-[var(--color-surface)] outline-none focus:border-[var(--color-text-muted)] font-sans disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="px-4 py-2 bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)] rounded text-xs font-semibold cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[var(--color-hover-bg)] transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
