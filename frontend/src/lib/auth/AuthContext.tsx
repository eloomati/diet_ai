import { createContext, useEffect, useState, useSyncExternalStore, type ReactNode } from 'react'

import { login as loginRequest, logout as logoutRequest, me as meRequest, register as registerRequest } from '@/api/auth'
import type { MeResponse } from '@/api/auth'
import { attemptTokenRefresh } from '@/lib/apiFetch'

import { clearTokens, getIsAuthenticatedSnapshot, getRefreshToken, setTokens, subscribe } from './tokenStore'

export interface AuthContextValue {
  /** Backed by a confirmed GET /auth/me, not just "some token is in memory". */
  isAuthenticated: boolean
  /** True until the initial silent session restore (or its absence) is resolved. */
  isBootstrapping: boolean
  user: MeResponse | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, captchaToken: string) => Promise<void>
  logout: () => Promise<void>
  /** Re-fetches /auth/me — e.g. after confirming email verification, to flip the flag without a full re-login. */
  refreshUser: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const hasToken = useSyncExternalStore(subscribe, getIsAuthenticatedSnapshot)
  const [user, setUser] = useState<MeResponse | null>(null)
  const [isBootstrapping, setIsBootstrapping] = useState(true)

  async function loadUser(): Promise<void> {
    try {
      setUser(await meRequest())
    } catch {
      // Token references a deleted/inactive user, or is otherwise invalid —
      // GET /auth/me is the source of truth, not just "a token exists".
      clearTokens()
      setUser(null)
    }
  }

  useEffect(() => {
    // A page load starts with no access token in memory even if the user was
    // logged in before — silently redeem a stored refresh token (if any) so
    // a reload doesn't force them back through the login popup.
    async function bootstrap() {
      if (getRefreshToken()) {
        const refreshed = await attemptTokenRefresh()
        if (refreshed) await loadUser()
      }
      setIsBootstrapping(false)
    }
    bootstrap()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    // Whenever the token store loses its access token — explicit logout, or
    // a background refresh failing during some later API call — the
    // confirmed user should be dropped too, everywhere `useAuth()` is read.
    if (!hasToken) setUser(null)
  }, [hasToken])

  async function login(email: string, password: string): Promise<void> {
    const result = await loginRequest({ email, password })
    setTokens(result.access_token, result.refresh_token)
    await loadUser()
  }

  async function register(email: string, password: string, captchaToken: string): Promise<void> {
    await registerRequest({ email, password, captcha_token: captchaToken })
  }

  async function logout(): Promise<void> {
    const refreshToken = getRefreshToken()
    clearTokens()
    setUser(null)
    if (refreshToken) {
      // Best-effort — an already-expired/garbage token still means "logged
      // out" locally, matching the backend's own idempotent /auth/logout.
      await logoutRequest(refreshToken).catch(() => {})
    }
  }

  const value: AuthContextValue = {
    isAuthenticated: user !== null,
    isBootstrapping,
    user,
    login,
    register,
    logout,
    refreshUser: loadUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
