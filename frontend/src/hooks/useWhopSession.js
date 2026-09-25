import { useCallback, useEffect, useState } from 'react'
import * as whopAuth from '../lib/whopAuth'

/**
 * "已验证会员" state for the login button (CLAUDE.md 2026-09-25 定案:
 * 最小化阶段登录只标状态，不挡任何页面). Runs the callback exchange once on
 * whichever public page the app happens to mount on.
 *
 * `session.access` is the optional has_access result (T-0925-75/T-0925-77) —
 * display-only, never consulted by anything that gates content. It's `null`
 * whenever VITE_WHOP_ACCESS_PASS_ID is unset or the lookup fails; the button
 * just falls back to the plain "已验证会员" label in that case.
 */
export function useWhopSession() {
  const [session, setSession] = useState(() => whopAuth.loadSession())
  const [status, setStatus] = useState('idle') // idle | exchanging | error
  const [error, setError] = useState(null)

  useEffect(() => {
    const callback = whopAuth.consumePendingCallback()
    if (!callback) return
    if (callback.error) {
      setStatus('error')
      setError(callback.error)
      return
    }
    setStatus('exchanging')
    whopAuth
      .exchangeCodeForToken(callback.code)
      .then((token) =>
        whopAuth.fetchUserinfo(token.access_token).then((user) => ({ token, user }))
      )
      .then(({ token, user }) =>
        // Display-only (T-0925-75/T-0925-77): failure here must not block
        // login — a Whop account with no access pass, or the endpoint being
        // unreachable, still gets the plain "已验证会员" state, not an error.
        (whopAuth.hasAccessPassConfigured()
          ? whopAuth
              .fetchHasAccess(token.access_token, whopAuth.getAccessPassId())
              .catch(() => null)
          : Promise.resolve(null)
        ).then((access) => ({ token, user, access }))
      )
      .then(({ token, user, access }) => {
        const next = {
          accessToken: token.access_token,
          refreshToken: token.refresh_token ?? null,
          user,
          access,
        }
        whopAuth.saveSession(next)
        setSession(next)
        setStatus('idle')
      })
      .catch((err) => {
        setStatus('error')
        setError(err.message)
      })
  }, [])

  const login = useCallback(() => {
    whopAuth.startLogin().catch((err) => {
      setStatus('error')
      setError(err.message)
    })
  }, [])

  const logout = useCallback(() => {
    whopAuth.clearSession()
    setSession(null)
  }, [])

  return {
    session,
    isAuthenticated: !!session,
    isConfigured: whopAuth.isConfigured(),
    status,
    error,
    login,
    logout,
  }
}
