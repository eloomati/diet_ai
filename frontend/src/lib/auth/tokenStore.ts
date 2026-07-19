const REFRESH_TOKEN_KEY = 'diet-ai:refresh-token'

type Listener = () => void

// Access token lives in memory only (not localStorage) to limit exposure to
// XSS — it's gone on a full page reload, which is fine: the refresh token
// (below) is what survives a reload and silently re-establishes a session.
let accessToken: string | null = null
const listeners = new Set<Listener>()

function notify(): void {
  for (const listener of listeners) listener()
}

export function getAccessToken(): string | null {
  return accessToken
}

export function setAccessToken(token: string | null): void {
  accessToken = token
  notify()
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setRefreshToken(token: string | null): void {
  if (token) localStorage.setItem(REFRESH_TOKEN_KEY, token)
  else localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function setTokens(access: string, refresh: string): void {
  setAccessToken(access)
  setRefreshToken(refresh)
}

export function clearTokens(): void {
  setAccessToken(null)
  setRefreshToken(null)
}

/** For useSyncExternalStore — re-renders subscribers when the access token changes. */
export function subscribe(listener: Listener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function getIsAuthenticatedSnapshot(): boolean {
  return accessToken !== null
}
