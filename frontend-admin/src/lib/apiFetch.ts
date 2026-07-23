import { clearTokens, getAccessToken, getRefreshToken, setTokens } from './auth/tokenStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

/** Matches the backend's common error format — see docs/api.md. */
interface ApiErrorBody {
  code: string
  message: string
  timestamp: string
}

export class ApiError extends Error {
  status: number
  code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

async function parseErrorBody(response: Response): Promise<ApiErrorBody> {
  try {
    return (await response.json()) as ApiErrorBody
  } catch {
    return { code: 'UNKNOWN', message: response.statusText, timestamp: new Date().toISOString() }
  }
}

// Concurrent requests that all 401 at once should share a single in-flight
// refresh call rather than each firing their own POST /auth/refresh.
let refreshPromise: Promise<boolean> | null = null

/** Redeems the stored refresh token for a new token pair — mirrors the main
 * app's apiFetch.ts exactly (same backend, same token shape). */
export async function attemptTokenRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return false

  refreshPromise ??= fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
    .then(async (response) => {
      if (!response.ok) {
        clearTokens()
        return false
      }
      const body = (await response.json()) as { access_token: string; refresh_token: string }
      setTokens(body.access_token, body.refresh_token)
      return true
    })
    .catch(() => {
      clearTokens()
      return false
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

export interface ApiFetchOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
  /** Skip attaching the Authorization header and the 401-refresh dance (login only). */
  skipAuth?: boolean
}

/** Thin fetch wrapper: attaches the bearer token, retries once through a
 * refresh-token exchange on a 401. No guest mode here — a failed refresh
 * just means the login page shows again. */
export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { skipAuth, body, headers, ...rest } = options

  const doFetch = (): Promise<Response> => {
    const token = getAccessToken()
    const finalHeaders: HeadersInit = {
      'Content-Type': 'application/json',
      ...headers,
      ...(token && !skipAuth ? { Authorization: `Bearer ${token}` } : {}),
    }
    return fetch(`${API_BASE_URL}${path}`, {
      ...rest,
      headers: finalHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  }

  let response = await doFetch()

  if (response.status === 401 && !skipAuth) {
    const refreshed = await attemptTokenRefresh()
    if (refreshed) {
      response = await doFetch()
    }
  }

  if (!response.ok) {
    const errorBody = await parseErrorBody(response)
    throw new ApiError(response.status, errorBody.code, errorBody.message)
  }

  if (response.status === 204) return undefined as T

  return (await response.json()) as T
}
