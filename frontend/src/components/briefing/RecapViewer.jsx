import { useState, useEffect } from 'react'

export default function RecapViewer({ date }) {
  const [content, setContent] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setContent(null)

    fetch(`/data/briefings/${date}.md`)
      .then(res => {
        if (!res.ok) throw new Error('Not found')
        return res.text()
      })
      .then(text => {
        if (!cancelled) setContent(text)
      })
      .catch(() => {
        if (!cancelled) setContent(null)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [date])

  if (loading) {
    return (
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6">
        <div className="text-xs text-[var(--color-text-muted)] animate-pulse">Loading briefing...</div>
      </div>
    )
  }

  if (!content) {
    return (
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6 flex items-center justify-center h-32">
        <span className="text-xs text-[var(--color-text-muted)] uppercase tracking-wide">No briefing for this date</span>
      </div>
    )
  }

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6">
      <div
        className="prose prose-stone prose-sm max-w-none
          prose-headings:text-[var(--color-text-bold)] prose-headings:tracking-tight
          prose-p:text-[var(--color-text-secondary)] prose-p:text-sm prose-p:leading-relaxed
          prose-li:text-[var(--color-text-secondary)] prose-li:text-sm
          prose-strong:text-[var(--color-text-bold)]
          prose-code:text-[var(--color-text)] prose-code:bg-[var(--color-surface-raised)] prose-code:px-1 prose-code:rounded
          prose-a:text-blue-600"
        dangerouslySetInnerHTML={{ __html: simpleMarkdown(content) }}
      />
    </div>
  )
}

// Simple markdown parser - handles common cases
function simpleMarkdown(md) {
  let html = md
    // Code blocks
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="bg-[var(--color-bg)] border border-[var(--color-border)] rounded p-3 overflow-x-auto text-xs font-mono"><code>$2</code></pre>')
    // Headings
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // Horizontal rules
    .replace(/^---$/gm, '<hr class="border-[var(--color-border)] my-4" />')
    // Bold and italic
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    // Unordered lists
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    // Paragraphs (lines not already wrapped)
    .split('\n\n')
    .map(block => {
      block = block.trim()
      if (!block) return ''
      if (block.startsWith('<')) return block
      // Wrap consecutive <li> in <ul>
      if (block.includes('<li>')) return `<ul class="list-disc pl-5 space-y-1">${block}</ul>`
      return `<p>${block.replace(/\n/g, '<br/>')}</p>`
    })
    .join('\n')

  return html
}
