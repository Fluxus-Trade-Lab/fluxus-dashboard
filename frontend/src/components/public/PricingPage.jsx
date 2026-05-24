import { useState } from 'react'

const FREE_FEATURES = [
  'Daily market brief (preview)',
  'Weekly trade idea recap',
  'Public YouTube content',
  'Community Discord (general channels)',
]

const MEMBER_FEATURES = [
  'Full daily brief + watchlist',
  'Real-time trade alerts',
  'Live morning voice chat',
  'Options flow interpretation',
  'Position sizing tools',
  'Full Discord access (all channels)',
  'Weekly AMA sessions',
  'Institutional-grade research',
  'Mentorship sessions',
]

function CheckIcon() {
  return (
    <span className="text-[var(--color-profit)] mr-2 font-mono text-sm">✓</span>
  )
}

export default function PricingPage() {
  const [billing, setBilling] = useState('monthly')

  const price = billing === 'monthly' ? 99 : 79
  const period = billing === 'monthly' ? '/month' : '/month'
  const billedNote = billing === 'yearly' ? 'Billed annually ($948/year)' : null

  return (
    <div>
      {/* Header */}
      <section className="public-section public-section-prose pt-16 sm:pt-24 pb-8">
        <h1 className="public-h1">Simple pricing</h1>
        <p className="public-body mt-4 text-[var(--color-text-secondary)]">
          Free to follow. One membership to join.
        </p>
      </section>

      {/* Billing toggle */}
      <section className="public-section public-section-prose pb-8">
        <div className="inline-flex items-center gap-2 bg-[var(--color-surface-raised)] rounded p-1 text-sm">
          <button
            onClick={() => setBilling('monthly')}
            className={`px-3 py-1.5 rounded border-none cursor-pointer transition-colors ${
              billing === 'monthly'
                ? 'bg-[var(--color-surface)] text-[var(--color-text)] font-medium'
                : 'bg-transparent text-[var(--color-text-secondary)]'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBilling('yearly')}
            className={`px-3 py-1.5 rounded border-none cursor-pointer transition-colors ${
              billing === 'yearly'
                ? 'bg-[var(--color-surface)] text-[var(--color-text)] font-medium'
                : 'bg-transparent text-[var(--color-text-secondary)]'
            }`}
          >
            Yearly
            <span className="ml-1 text-xs text-[var(--color-profit)]">save 20%</span>
          </button>
        </div>
      </section>

      {/* Two-column pricing */}
      <section className="public-section public-section-wide pb-16">
        <div className="grid sm:grid-cols-2 gap-6 max-w-[700px]">
          {/* Free */}
          <div className="border border-[var(--color-border)] rounded p-6">
            <p className="public-label">Free</p>
            <div className="mt-2 font-mono text-3xl font-medium text-[var(--color-text)]">$0</div>
            <p className="text-sm text-[var(--color-text-muted)] mt-1">Forever</p>
            <ul className="mt-6 space-y-3">
              {FREE_FEATURES.map(f => (
                <li key={f} className="text-sm text-[var(--color-text-secondary)] flex items-start">
                  <CheckIcon />{f}
                </li>
              ))}
            </ul>
            <div className="mt-6">
              <a
                href="https://whop.com/fluxus-trade-lab/"
                target="_blank"
                rel="noopener noreferrer"
                className="public-cta-secondary block text-center no-underline"
              >
                Join free
              </a>
            </div>
          </div>

          {/* Member */}
          <div className="border-2 border-[var(--color-accent)] rounded p-6 relative">
            <p className="public-label text-[var(--color-accent)]">Member</p>
            <div className="mt-2 font-mono text-3xl font-medium text-[var(--color-text)]">
              ${price}<span className="text-lg font-normal text-[var(--color-text-muted)]">{period}</span>
            </div>
            {billedNote && (
              <p className="text-xs text-[var(--color-text-muted)] mt-1">{billedNote}</p>
            )}
            {!billedNote && (
              <p className="text-sm text-[var(--color-text-muted)] mt-1">Cancel anytime</p>
            )}
            <ul className="mt-6 space-y-3">
              {MEMBER_FEATURES.map(f => (
                <li key={f} className="text-sm text-[var(--color-text-secondary)] flex items-start">
                  <CheckIcon />{f}
                </li>
              ))}
            </ul>
            <div className="mt-6">
              <a
                href="https://whop.com/fluxus-trade-lab/"
                target="_blank"
                rel="noopener noreferrer"
                className="public-cta block text-center no-underline"
              >
                Join now
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="public-section public-section-prose py-16">
          <h2 className="public-h2">Questions</h2>
          <div className="mt-8 space-y-8">
            <div>
              <h3 className="text-sm font-semibold text-[var(--color-text)]">Who is this for?</h3>
              <p className="text-sm text-[var(--color-text-secondary)] mt-2 leading-relaxed">
                Performance-oriented traders with at least some market experience
                who want a systematic approach. If you're looking for hot tips or
                overnight returns, this isn't for you.
              </p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[var(--color-text)]">What happens after the course?</h3>
              <p className="text-sm text-[var(--color-text-secondary)] mt-2 leading-relaxed">
                You keep full access to recorded sessions for 2 months, plus
                ongoing Premium Discord membership. Show us 3 months of consistent
                results and we'll refund your course fee and issue a certificate.
              </p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[var(--color-text)]">What languages?</h3>
              <p className="text-sm text-[var(--color-text-secondary)] mt-2 leading-relaxed">
                English and Mandarin Chinese. Both versions cover the same material.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
