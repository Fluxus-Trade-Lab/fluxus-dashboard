import { describe, it, expect } from 'vitest'
import { deriveCodeChallenge, generateCodeVerifier, isConfigured, hasAccessPassConfigured } from './whopAuth'

describe('whopAuth PKCE', () => {
  // RFC 7636 Appendix B test vector — the one place this SHA-256 + base64url
  // implementation gets checked against a known-correct answer instead of
  // just "runs without throwing".
  it('derives the RFC 7636 sample code_challenge from its sample verifier', async () => {
    const verifier = 'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk'
    const challenge = await deriveCodeChallenge(verifier)
    expect(challenge).toBe('E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM')
  })

  it('generates a verifier with no base64 padding or +/ characters (base64url)', () => {
    const verifier = generateCodeVerifier()
    expect(verifier).toMatch(/^[A-Za-z0-9_-]+$/)
    expect(verifier.length).toBeGreaterThanOrEqual(43)
  })

  it('two verifiers are not the same (drawn from crypto.getRandomValues)', () => {
    expect(generateCodeVerifier()).not.toBe(generateCodeVerifier())
  })

  it('reports unconfigured when VITE_WHOP_CLIENT_ID is unset (true today)', () => {
    // Documents the current repo state rather than asserting a fixed
    // client_id — the env var only becomes non-empty once ops wires a real
    // Whop OAuth app, which is outside this task's reach.
    expect(isConfigured()).toBe(!!import.meta.env.VITE_WHOP_CLIENT_ID)
  })

  it('reports the access-pass lookup unconfigured when VITE_WHOP_ACCESS_PASS_ID is unset (true today)', () => {
    // T-0925-75/T-0925-77: same shape as isConfigured() above — the display
    // -only has_access call only fires once ops fills in a real access pass id.
    expect(hasAccessPassConfigured()).toBe(!!import.meta.env.VITE_WHOP_ACCESS_PASS_ID)
  })
})
