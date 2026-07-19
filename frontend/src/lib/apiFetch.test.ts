import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { apiFetch, ApiError } from './apiFetch'
import { clearTokens, getAccessToken, setTokens } from './auth/tokenStore'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('apiFetch', () => {
  beforeEach(() => {
    clearTokens()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('returns parsed JSON on a successful request, without touching refresh', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { hello: 'world' }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await apiFetch<{ hello: string }>('/anything')

    expect(result).toEqual({ hello: 'world' })
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('refreshes once on a 401 and retries the original request', async () => {
    setTokens('expired-access-token', 'valid-refresh-token')

    const fetchMock = vi
      .fn()
      // 1) original request -> 401
      .mockResolvedValueOnce(jsonResponse(401, { code: 'INVALID_ACCESS_TOKEN', message: 'x' }))
      // 2) POST /auth/refresh -> new token pair
      .mockResolvedValueOnce(
        jsonResponse(200, { access_token: 'new-access-token', refresh_token: 'new-refresh-token' }),
      )
      // 3) retried original request -> success
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await apiFetch<{ ok: boolean }>('/protected')

    expect(result).toEqual({ ok: true })
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(getAccessToken()).toBe('new-access-token')
  })

  it('clears tokens and throws the original error when the refresh itself fails', async () => {
    setTokens('expired-access-token', 'stale-refresh-token')

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { code: 'INVALID_ACCESS_TOKEN', message: 'expired' }))
      .mockResolvedValueOnce(jsonResponse(401, { code: 'INVALID_REFRESH_TOKEN', message: 'stale' }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiFetch('/protected')).rejects.toMatchObject({
      code: 'INVALID_ACCESS_TOKEN',
      status: 401,
    } satisfies Partial<ApiError>)

    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(getAccessToken()).toBeNull()
  })

  it('does not attempt a refresh when there is no refresh token (guest)', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { code: 'INVALID_ACCESS_TOKEN', message: 'guest' }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiFetch('/protected')).rejects.toThrow(ApiError)

    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('coalesces concurrent 401s into a single refresh call', async () => {
    setTokens('expired-access-token', 'valid-refresh-token')

    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/refresh')) {
        return Promise.resolve(
          jsonResponse(200, { access_token: 'new-access-token', refresh_token: 'new-refresh-token' }),
        )
      }
      // Every non-refresh call 401s until the token has actually been swapped.
      if (getAccessToken() === 'new-access-token') {
        return Promise.resolve(jsonResponse(200, { ok: true }))
      }
      return Promise.resolve(jsonResponse(401, { code: 'INVALID_ACCESS_TOKEN', message: 'x' }))
    })
    vi.stubGlobal('fetch', fetchMock)

    const [a, b] = await Promise.all([apiFetch('/one'), apiFetch('/two')])

    expect(a).toEqual({ ok: true })
    expect(b).toEqual({ ok: true })
    const refreshCalls = fetchMock.mock.calls.filter(([url]) => String(url).includes('/auth/refresh'))
    expect(refreshCalls).toHaveLength(1)
  })
})
