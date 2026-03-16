import { useState, useRef, useEffect } from 'react'

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

export default function CoachTab({ strategy }) {
  const config = STRATEGY_DESCRIPTIONS[strategy] || {}
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Reset messages when strategy changes
  useEffect(() => {
    setMessages([])
    setInput('')
  }, [strategy])

  const handleSend = () => {
    if (!input.trim()) return

    const userMsg = { role: 'user', content: input.trim() }
    const stubReply = {
      role: 'assistant',
      content: `[Phase 2] This is where the ${config.name} coach will respond. The coach will be loaded with strategy-specific knowledge from \`data/coach/${strategy}.md\` and will use Claude API via a Vercel serverless function to provide personalized feedback on your setups and trades.\n\nFor now, try logging your trade observations here — they'll be available when coaching goes live.`
    }

    setMessages(prev => [...prev, userMsg, stubReply])
    setInput('')
  }

  return (
    <div className="space-y-4">
      {/* Strategy header */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
        <h3 className="text-sm font-semibold text-[var(--color-text-bold)] mb-1">{config.name}</h3>
        <p className="text-xs text-[var(--color-text-secondary)]">{config.description}</p>
      </div>

      {/* Chat area */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
        <div className="min-h-[300px] max-h-[500px] overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && (
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
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="border-t border-[var(--color-border)] p-3 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder={`Ask about ${config.name?.toLowerCase() || 'trading'}...`}
            className="flex-1 px-3 py-2 border border-[var(--color-border)] rounded text-sm bg-[var(--color-surface)] outline-none focus:border-[var(--color-text-muted)] font-sans"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="px-4 py-2 bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)] rounded text-xs font-semibold cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[var(--color-hover-bg)] transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
