import { useCallback, useEffect, useState } from 'react'
import * as whopAuth from '../lib/whopAuth'

/**
 * "已验证会员" state for the login button (CLAUDE.md 2026-09-25 定案:
 * 最小化阶段登录只标状态，不挡任何页面). Runs the callback exchange once on
 * whichever public page the app happens to mount on.
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
      .then(({ token, user }) => {
        const next = {
          accessToken: token.access_token,
          refreshToken: token.refresh_token ?? null,
          user,
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
