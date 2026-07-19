import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from './AuthContext'
import { clearTokens, getAccessToken, getRefreshToken } from './tokenStore'
import { useAuth } from './useAuth'

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function stubAuthEndpoints(role: string) {
  const fetchMock = vi.fn().mockImplementation((url: string) => {
    if (url.includes('/auth/me')) {
      return Promise.resolve(
        jsonResponse(200, {
          user_id: 'u-1',
          email: 'admin@example.com',
          status: 'ACTIVE',
          email_verified: true,
          role,
        }),
      )
    }
    if (url.includes('/auth/login')) {
      return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
    }
    return Promise.resolve(jsonResponse(200, { message: 'ok' }))
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('AuthContext', () => {
  beforeEach(() => {
    clearTokens()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('throws when useAuth is called outside an AuthProvider', () => {
    expect(() => renderHook(() => useAuth())).toThrow(/AuthProvider/)
  })

  it('logs in an ADMIN user successfully', async () => {
    stubAuthEndpoints('ADMIN')
    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isBootstrapping).toBe(false))

    await act(async () => {
      await result.current.login('admin@example.com', 'StrongPass123')
    })

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.user?.role).toBe('ADMIN')
    expect(getAccessToken()).toBe('a')
  })

  it('logs in a SUPER_ADMIN user successfully', async () => {
    stubAuthEndpoints('SUPER_ADMIN')
    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isBootstrapping).toBe(false))

    await act(async () => {
      await result.current.login('admin@example.com', 'StrongPass123')
    })

    expect(result.current.isAuthenticated).toBe(true)
  })

  it('rejects a USER login and clears any stored tokens', async () => {
    stubAuthEndpoints('USER')
    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isBootstrapping).toBe(false))

    await expect(
      act(async () => {
        await result.current.login('user@example.com', 'StrongPass123')
      }),
    ).rejects.toThrow(/uprawnień administratora/)

    expect(result.current.isAuthenticated).toBe(false)
    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
  })

  it('rejects a DIET_USER login the same way', async () => {
    stubAuthEndpoints('DIET_USER')
    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isBootstrapping).toBe(false))

    await expect(
      act(async () => {
        await result.current.login('dietuser@example.com', 'StrongPass123')
      }),
    ).rejects.toThrow(/uprawnień administratora/)

    expect(result.current.isAuthenticated).toBe(false)
  })

  it('logout clears tokens and user', async () => {
    stubAuthEndpoints('ADMIN')
    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isBootstrapping).toBe(false))
    await act(async () => {
      await result.current.login('admin@example.com', 'StrongPass123')
    })

    await act(async () => {
      await result.current.logout()
    })

    expect(result.current.isAuthenticated).toBe(false)
    expect(getAccessToken()).toBeNull()
  })
})
