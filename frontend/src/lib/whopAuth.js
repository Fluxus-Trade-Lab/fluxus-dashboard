/**
 * Whop OAuth 2.1 + PKCE, client-only (no client_secret — this dashboard is a
 * static SPA with no backend to hold one). Confirmed against docs.whop.com/
 * developer/guides/oauth (2026-09-25 检索): SPAs are public clients under
 * OAuth 2.1 and PKCE (S256) replaces the client_secret for the token
 * exchange, so this flow doesn't need a serverless proxy.
 *
 * Not wired to anything real yet: VITE_WHOP_CLIENT_ID is unset in this repo.
 * Activating it needs an OAuth app registered in Whop's Developer Dashboard
 * (redirect URI = this site's origin, exact match) — that's a Whop-account
 * action only Andy/ops can do, not something this code can supply.
 *
 * has_access endpoint's version prefix (search hits disagree: v1 vs v5)
 * isn't pinned here with confidence — confirm at docs.whop.com/api-reference
 * before relying on fetchHasAccess in production.
 */

const OAUTH_BASE = 'https://api.whop.com/oauth'
const API_BASE = 'https://api.whop.com/api/v1'

const VERIFIER_KEY = 'fluxus.whop.pkce_verifier'
const STATE_KEY = 'fluxus.whop.oauth_state'
const SESSION_KEY = 'fluxus.whop.session'

export function getClientId() {
  return import.meta.env.VITE_WHOP_CLIENT_ID || ''
}

export function isConfigured() {
  return getClientId().length > 0
}

function base64UrlEncode(bytes) {
  let binary = ''
  for (const b of bytes) binary += String.fromCharCode(b)
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

export function generateCodeVerifier() {
  const bytes = new Uint8Array(32)
  crypto.getRandomValues(bytes)
  return base64UrlEncode(bytes)
}

export async function deriveCodeChallenge(verifier) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier))
  return base64UrlEncode(new Uint8Array(digest))
}

/**
 * No hash (`#/page`) on purpose. Whop appends `?code=&state=` to this exact
 * string, and the app reads `location.search` once on boot regardless of
 * route — simpler than teaching the redirect about the SPA's hash router.
 * Net effect: logging in always lands back on `#/` (the landing page).
 */
export function getRedirectUri() {
  return `${window.location.origin}/`
}

export async function startLogin() {
  if (!isConfigured()) throw new Error('VITE_WHOP_CLIENT_ID 未配置，登录按钮还接不到真会员')
  const verifier = generateCodeVerifier()
  const challenge = await deriveCodeChallenge(verifier)
  const state = generateCodeVerifier()
  sessionStorage.setItem(VERIFIER_KEY, verifier)
  sessionStorage.setItem(STATE_KEY, state)

  const url = new URL(`${OAUTH_BASE}/authorize`)
  url.searchParams.set('response_type', 'code')
  url.searchParams.set('client_id', getClientId())
  url.searchParams.set('redirect_uri', getRedirectUri())
  url.searchParams.set('scope', 'openid profile email')
  url.searchParams.set('state', state)
  url.searchParams.set('code_challenge', challenge)
  url.searchParams.set('code_challenge_method', 'S256')
  window.location.assign(url.toString())
}

/**
 * Call once on app boot. Returns `{ code }` if this load is Whop redirecting
 * back with an authorization code, `{ error }` if a code arrived but the
 * state didn't match (CSRF guard), or `null` if this isn't a callback load.
 * Strips the query string either way so a page refresh never replays a used
 * code.
 */
export function consumePendingCallback() {
  const params = new URLSearchParams(window.location.search)
  const code = params.get('code')
  if (!code) return null

  const state = params.get('state')
  const expectedState = sessionStorage.getItem(STATE_KEY)
  window.history.replaceState({}, '', window.location.pathname + window.location.hash)

  if (!expectedState || state !== expectedState) {
    return { error: 'state 不匹配，已丢弃这次回调' }
  }
  return { code }
}

export async function exchangeCodeForToken(code) {
  const verifier = sessionStorage.getItem(VERIFIER_KEY)
  sessionStorage.removeItem(VERIFIER_KEY)
  sessionStorage.removeItem(STATE_KEY)
  if (!verifier) throw new Error('缺 code_verifier，登录会话已过期，请重新登录')

  const res = await fetch(`${OAUTH_BASE}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      code,
      redirect_uri: getRedirectUri(),
      client_id: getClientId(),
      code_verifier: verifier,
    }),
  })
  if (!res.ok) throw new Error(`token 交换失败：${res.status}`)
  return res.json()
}

export async function fetchUserinfo(accessToken) {
  const res = await fetch(`${OAUTH_BASE}/userinfo`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  if (!res.ok) throw new Error(`userinfo 拉取失败：${res.status}`)
  return res.json()
}

export async function fetchHasAccess(accessToken, resourceId) {
  const res = await fetch(`${API_BASE}/me/has_access/${resourceId}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  if (!res.ok) throw new Error(`has_access 查询失败：${res.status}`)
  return res.json()
}

export function saveSession(session) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

export function loadSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function clearSession() {
  localStorage.removeItem(SESSION_KEY)
}
