import { patternTag, formatPattern } from './patternTag'

/* The notes rail — Andy, 2026-09-25: "注释是很有用的教学，可以有一个侧栏是
   notes栏目."

   Two kinds of note sit here and they are not the same thing:

   · a MODEL BOOK CARD, a paragraph someone wrote about this stock that year.
     Ross Haber's TraderLion write-ups and Richard Moglen's chart captions.
     These are other people's work, reproduced with Andy's decision on
     2026-09-25 ("Haber's paragraphs可以放入。给credit"), so every one of them
     carries its book, its author and its page. A note with no credit is not
     rendered — see `Credit` below; that is the enforcement, not a convention.

   · CHART LABELS, the short phrases drawn on the original chart ("Base Pivot",
     "Holds 21ema during market correction"). They are the vocabulary the
     annotations teach, and they read better as chips than as a paragraph. */

function Credit({ source }) {
  // Refusing to render is the point: an uncredited quotation must not reach the
  // page just because a parser lost a field.
  if (!source?.book || !source?.author) return null
  /* The vault's front matter writes the author into the book title, so the
     line came out "Richard Moglen · 10 Years of Market Leaders（Richard
     Moglen）". Drop the parenthetical when it is only repeating the name we
     are already printing — never drop the name itself. */
  const book = source.book.replace(/[（(][^）)]*[）)]\s*$/, m =>
    m.includes(source.author) ? '' : m).trim()
  return (
    <p className="text-[11px] text-[var(--color-text-muted)] m-0">
      {source.author} · {book || source.book}
      {source.page ? ` · p${source.page}` : ''}
    </p>
  )
}

function Labels({ labels }) {
  if (!labels?.length) return null
  return (
    <div className="flex flex-wrap gap-1 mt-1.5">
      {labels.map((l, i) => (
        <span key={i}
              className="text-[11px] px-1.5 py-0.5 rounded bg-[var(--color-surface-alt)]
                         text-[var(--color-text-secondary)] leading-tight">
          {l}
        </span>
      ))}
    </div>
  )
}

function SourceCard({ source }) {
  if (!source?.book || !source?.author) return null
  const prose = source.prose
    ? source.prose.replace(/^[^\n]*\n/, '').replace(/```text|```/g, '').trim()
    : null
  const caption = (source.caption || []).filter(Boolean)
  return (
    <div className="py-3 border-b border-[var(--color-border-light)] last:border-b-0">
      <Credit source={source} />
      {source.chart && (
        <p className="text-[13px] text-[var(--color-text)] font-medium mt-1 mb-0">{source.chart}</p>
      )}
      {caption.map((c, i) => (
        <blockquote key={i}
                    className="border-l-2 border-[var(--color-border)] pl-2.5 my-1.5
                               text-[13px] italic text-[var(--color-text-secondary)] leading-relaxed">
          {c}
        </blockquote>
      ))}
      <Labels labels={source.labels} />
      {prose && (
        <details className="mt-1.5">
          <summary className="text-[11px] text-[var(--color-text-muted)] cursor-pointer">
            原文（{source.author}）
          </summary>
          <pre className="mt-1.5 whitespace-pre-wrap text-[11px] leading-relaxed
                          text-[var(--color-text-secondary)] font-sans m-0">{prose}</pre>
        </details>
      )}
    </div>
  )
}

export default function NotesRail({ entry }) {
  if (!entry) return null
  const note = entry.note
  const sources = (note?.sources || []).filter(s => s?.book && s?.author)
  const lessons = entry.key_lessons || []

  if (!sources.length && !lessons.length && !entry.patterns?.length) {
    return (
      <p className="text-[13px] italic text-[var(--color-text-muted)] p-3 m-0">
        这条没有注释。库里 {entry.libraryNoteCount ?? ''} 条有，其余只有 K 线。
      </p>
    )
  }

  return (
    <div className="p-3">
      {entry.patterns?.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {entry.patterns.map(p => (
            <span key={p}
                  className={`inline-block px-1.5 py-0.5 text-[11px] font-medium rounded-full leading-tight ${patternTag(p)}`}>
              {formatPattern(p)}
            </span>
          ))}
        </div>
      )}

      {(note?.sector || note?.industry) && (
        <p className="text-[11px] text-[var(--color-text-muted)] mt-0 mb-3">
          {[note.sector, note.industry].filter(Boolean).join(' · ')}
        </p>
      )}

      {note?.breakout && (
        <div className="mb-3 text-[13px]">
          <span className="text-[var(--color-text-muted)]">模型册写明的突破 </span>
          <span className="font-mono text-[var(--color-text-bold)]">
            {note.breakout.date}{note.breakout.price ? ` @ $${note.breakout.price}` : ''}
          </span>
          {note.peak?.date && (
            <>
              <span className="text-[var(--color-text-muted)]"> → 高点 </span>
              <span className="font-mono text-[var(--color-text-bold)]">
                {note.peak.date}{note.peak.price ? ` @ $${note.peak.price}` : ''}
              </span>
            </>
          )}
          {note.gain_pct != null && (
            <span className="text-[var(--color-text-muted)]">
              {' '}· 作者记的是 {note.gain_pct}%{note.weeks ? ` / ${note.weeks} 周` : ''}
            </span>
          )}
        </div>
      )}

      {lessons.length > 0 && (
        <div className="mb-3">
          <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1">
            Key lessons
          </span>
          {lessons.map((l, i) => (
            <blockquote key={i}
                        className="border-l-2 border-[var(--color-border)] pl-2.5 my-1.5
                                   text-[13px] italic text-[var(--color-text-secondary)] leading-relaxed">
              {l}
            </blockquote>
          ))}
        </div>
      )}

      {sources.map((s, i) => <SourceCard key={i} source={s} />)}
    </div>
  )
}

export { Credit, SourceCard }
