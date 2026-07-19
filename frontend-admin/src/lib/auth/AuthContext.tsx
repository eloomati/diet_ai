import { createContext, useEffect, useState, useSyncExternalStore, type ReactNode } from 'react'

import { login as loginRequest, logout as logoutRequest, me as meRequest } from '@/api/auth'
import type { MeResponse } from '@/api/auth'
import { attemptTokenRefresh } from '@/lib/apiFetch'

import { clearTokens, getRefreshToken, setTokens, subscribe } from './tokenStore'

const ADMIN_ROLES: ReadonlySet<MeResponse['role']> = new Set(['ADMIN', 'SUPER_ADMIN'])

export class InsufficientRoleError extends Error {
  constructor() {
    super('To konto nie ma uprawnień administratora.')
    this.name = 'InsufficientRoleError'
  }
}

export interface AuthContextValue {
  /** Backed by a confirmed GET /auth/me with an ADMIN/SUPER_ADMIN role —
   * never just "some token is in memory". */
  isAuthenticated: boolean
  /** True until the initial silent session restore (or its absence) is resolved. */
  isBootstrapping: boolean
  user: MeResponse | null
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  useSyncExternalStore(subscribe, () => null) // re-render on token changes
  const [user, setUser] = useState<MeResponse | null>(null)
  const [isBootstrapping, setIsBootstrapping] = useState(true)

  useEffect(() => {
    // A page load starts with no access token in memory even if the admin
    // was logged in before — silently redeem a stored refresh token (if
    // any) so a reload doesn't force them back through the login page.
    async function bootstrap() {
      if (getRefreshToken()) {
        const refreshed = await attemptTokenRefresh()
        if (refreshed) {
          try {
            const fetchedUser = await meRequest()
            if (ADMIN_ROLES.has(fetchedUser.role)) setUser(fetchedUser)
            else clearTokens()
          } catch {
            clearTokens()
          }
        }
      }
      setIsBootstrapping(false)
    }
    bootstrap()
  }, [])

  async function login(email: string, password: string): Promise<void> {
    const result = await loginRequest({ email, password })
    setTokens(result.access_token, result.refresh_token)

    const fetchedUser = await meRequest()
    if (!ADMIN_ROLES.has(fetchedUser.role)) {
      clearTokens()
      throw new InsufficientRoleError()
    }
    setUser(fetchedUser)
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
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
