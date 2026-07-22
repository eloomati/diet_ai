import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from './AuthContext'
import { clearTokens, getAccessToken, getRefreshToken, setRefreshToken } from './tokenStore'
import { useAuth } from './useAuth'

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient()
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  )
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const ME_RESPONSE = {
  user_id: 'u-1',
  email: 'user@example.com',
  status: 'ACTIVE',
  email_verified: false,
}

/** Routes /auth/login, /auth/refresh and /auth/me to distinct canned responses. */
function stubAuthEndpoints() {
  const fetchMock = vi.fn().mockImplementation((url: string) => {
    if (url.includes('/auth/me')) return Promise.resolve(jsonResponse(200, ME_RESPONSE))
    if (url.includes('/auth/refresh')) {
      return Promise.resolve(jsonResponse(200, { access_token: 'new-a', refresh_token: 'new-r' }))
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

  it('starts unauthenticated, and login stores tokens then confirms via /auth/me', async () => {
    const fetchMock = stubAuthEndpoints()

    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.isAuthenticated).toBe(false)

    await act(async () => {
      await result.current.login('user@example.com', 'password123')
    })

    await waitFor(() => expect(result.current.isAuthenticated).toBe(true))
    expect(getAccessToken()).toBe('a')
    expect(getRefreshToken()).toBe('r')
    expect(result.current.user).toEqual(ME_RESPONSE)
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/auth/me'))).toBe(true)
  })

  it('does not confirm the session if /auth/me rejects the fresh token', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(jsonResponse(401, { code: 'INVALID_ACCESS_TOKEN', message: 'x' }))
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      return Promise.resolve(jsonResponse(200, { message: 'ok' }))
    })
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() => useAuth(), { wrapper })
    await act(async () => {
      await result.current.login('user@example.com', 'password123')
    })

    await waitFor(() => expect(result.current.isAuthenticated).toBe(false))
    expect(result.current.user).toBeNull()
    expect(getAccessToken()).toBeNull()
  })

  it('logout clears tokens and the confirmed user even if the API call fails', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) return Promise.resolve(jsonResponse(200, ME_RESPONSE))
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      if (url.includes('/auth/logout')) {
        return Promise.resolve(jsonResponse(500, { code: 'INTERNAL_ERROR', message: 'boom' }))
      }
      return Promise.resolve(jsonResponse(200, { message: 'ok' }))
    })
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() => useAuth(), { wrapper })
    await act(async () => {
      await result.current.login('user@example.com', 'password123')
    })
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true))

    await act(async () => {
      await result.current.logout()
    })

    await waitFor(() => expect(result.current.isAuthenticated).toBe(false))
    expect(result.current.user).toBeNull()
    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
  })

  it('silently restores a session on mount when a refresh token is already stored', async () => {
    setRefreshToken('stored-refresh-token')
    const fetchMock = stubAuthEndpoints()

    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.isBootstrapping).toBe(true)

    await waitFor(() => expect(result.current.isBootstrapping).toBe(false))
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.user).toEqual(ME_RESPONSE)
    expect(getAccessToken()).toBe('new-a')
    // Never called login() directly — restored purely from the stored refresh token.
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/auth/refresh'))).toBe(true)
  })

  it('finishes bootstrapping as a guest when no refresh token is stored', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => expect(result.current.isBootstrapping).toBe(false))
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('clears a stale/expired stored refresh token instead of restoring a session', async () => {
    setRefreshToken('expired-refresh-token')
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(401, { code: 'INVALID_REFRESH_TOKEN', message: 'expired' }))
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isBootstrapping).toBe(false))

    expect(result.current.isAuthenticated).toBe(false)
    expect(getRefreshToken()).toBeNull()
  })

  it('refreshUser re-fetches /auth/me so callers can pick up a just-confirmed flag', async () => {
    let emailVerified = false
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(jsonResponse(200, { ...ME_RESPONSE, email_verified: emailVerified }))
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      return Promise.resolve(jsonResponse(200, { message: 'ok' }))
    })
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() => useAuth(), { wrapper })
    await act(async () => {
      await result.current.login('user@example.com', 'password123')
    })
    await waitFor(() => expect(result.current.user?.email_verified).toBe(false))

    emailVerified = true
    await act(async () => {
      await result.current.refreshUser()
    })

    expect(result.current.user?.email_verified).toBe(true)
  })

  it('login clears any cached data left over from a previous session', async () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(['profile'], { stale: 'from-previous-account' })
    function scopedWrapper({ children }: { children: ReactNode }) {
      return (
        <QueryClientProvider client={queryClient}>
          <AuthProvider>{children}</AuthProvider>
        </QueryClientProvider>
      )
    }
    stubAuthEndpoints()

    const { result } = renderHook(() => useAuth(), { wrapper: scopedWrapper })
    await act(async () => {
      await result.current.login('user@example.com', 'password123')
    })

    expect(queryClient.getQueryData(['profile'])).toBeUndefined()
  })

  it('logout clears any cached data so a next login never sees it', async () => {
    const queryClient = new QueryClient()
    function scopedWrapper({ children }: { children: ReactNode }) {
      return (
        <QueryClientProvider client={queryClient}>
          <AuthProvider>{children}</AuthProvider>
        </QueryClientProvider>
      )
    }
    stubAuthEndpoints()

    const { result } = renderHook(() => useAuth(), { wrapper: scopedWrapper })
    await act(async () => {
      await result.current.login('user@example.com', 'password123')
    })
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true))
    queryClient.setQueryData(['profile'], { belongs: 'to-this-account' })

    await act(async () => {
      await result.current.logout()
    })

    expect(queryClient.getQueryData(['profile'])).toBeUndefined()
  })

  it('register clears any cached data left over from browsing as a guest', async () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(['dietitian-listing'], [{ user_id: 'guest-cached' }])
    function scopedWrapper({ children }: { children: ReactNode }) {
      return (
        <QueryClientProvider client={queryClient}>
          <AuthProvider>{children}</AuthProvider>
        </QueryClientProvider>
      )
    }
    stubAuthEndpoints()

    const { result } = renderHook(() => useAuth(), { wrapper: scopedWrapper })
    await act(async () => {
      await result.current.register('new@example.com', 'password123', 'captcha-token')
    })

    expect(queryClient.getQueryData(['dietitian-listing'])).toBeUndefined()
  })

  it('drops the confirmed user if the token store loses its access token in the background', async () => {
    const fetchMock = stubAuthEndpoints()

    const { result } = renderHook(() => useAuth(), { wrapper })
    await act(async () => {
      await result.current.login('user@example.com', 'password123')
    })
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true))

    // Simulate apiFetch's own 401-retry-then-clear happening during some
    // unrelated call elsewhere in the app — AuthContext never sees this
    // directly, only the shared tokenStore.
    act(() => {
      clearTokens()
    })

    await waitFor(() => expect(result.current.isAuthenticated).toBe(false))
    expect(result.current.user).toBeNull()
    void fetchMock
  })
})
