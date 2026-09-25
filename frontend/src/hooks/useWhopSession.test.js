import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useWhopSession } from './useWhopSession'
import * as whopAuth from '../lib/whopAuth'

// T-0925-75/T-0925-77: has_access is wired in for display only (button label),
// never as a content gate. These tests pin that the lookup only fires when an
// access pass id is configured, and that its failure can never block login.
vi.mock('../lib/whopAuth')

describe('useWhopSession — access pass display', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    whopAuth.loadSession.mockReturnValue(null)
    whopAuth.isConfigured.mockReturnValue(true)
  })

  it('fetches has_access and stores it on the session when an access pass id is configured', async () => {
    whopAuth.consumePendingCallback.mockReturnValue({ code: 'abc' })
    whopAuth.exchangeCodeForToken.mockResolvedValue({ access_token: 'tok', refresh_token: 'ref' })
    whopAuth.fetchUserinfo.mockResolvedValue({ email: 'a@b.com' })
    whopAuth.hasAccessPassConfigured.mockReturnValue(true)
    whopAuth.getAccessPassId.mockReturnValue('pass_123')
    whopAuth.fetchHasAccess.mockResolvedValue({ has_access: true, access_level: 'customer' })

    const { result } = renderHook(() => useWhopSession())

    await waitFor(() => expect(result.current.session).not.toBeNull())
    expect(whopAuth.fetchHasAccess).toHaveBeenCalledWith('tok', 'pass_123')
    expect(result.current.session.access).toEqual({ has_access: true, access_level: 'customer' })
  })

  it('never calls fetchHasAccess when no access pass id is configured (unset today)', async () => {
    whopAuth.consumePendingCallback.mockReturnValue({ code: 'abc' })
    whopAuth.exchangeCodeForToken.mockResolvedValue({ access_token: 'tok' })
    whopAuth.fetchUserinfo.mockResolvedValue({ email: 'a@b.com' })
    whopAuth.hasAccessPassConfigured.mockReturnValue(false)

    const { result } = renderHook(() => useWhopSession())

    await waitFor(() => expect(result.current.session).not.toBeNull())
    expect(whopAuth.fetchHasAccess).not.toHaveBeenCalled()
    expect(result.current.session.access).toBeNull()
  })

  it('a failed has_access lookup still lets login finish — display-only, never blocking', async () => {
    whopAuth.consumePendingCallback.mockReturnValue({ code: 'abc' })
    whopAuth.exchangeCodeForToken.mockResolvedValue({ access_token: 'tok' })
    whopAuth.fetchUserinfo.mockResolvedValue({ email: 'a@b.com' })
    whopAuth.hasAccessPassConfigured.mockReturnValue(true)
    whopAuth.getAccessPassId.mockReturnValue('pass_123')
    whopAuth.fetchHasAccess.mockRejectedValue(new Error('502'))

    const { result } = renderHook(() => useWhopSession())

    await waitFor(() => expect(result.current.session).not.toBeNull())
    expect(result.current.status).toBe('idle')
    expect(result.current.session.access).toBeNull()
  })
})
