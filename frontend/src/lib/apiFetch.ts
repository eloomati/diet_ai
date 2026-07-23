import { clearTokens, getAccessToken, getRefreshToken, setTokens } from './auth/tokenStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

/** Resolves a root-absolute path (e.g. a stored dietitian photo URL like
 * `/static/dietitian-photos/x.jpg`) against the API's own origin — those
 * files are served outside the `/api/v1` prefix, so a plain relative `<img
 * src>` would resolve against the frontend's own origin instead. */
export function resolveStaticUrl(path: string): string {
  const apiUrl = new URL(API_BASE_URL, window.location.origin)
  return new URL(path, apiUrl).toString()
}

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

/**
 * Redeems the stored refresh token for a new token pair. Used both
 * reactively (apiFetch's 401 retry, below) and proactively (AuthContext's
 * session-bootstrap-on-load) — clearing tokens on failure lives here so
 * neither call site can forget it.
 */
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
  /** Skip attaching the Authorization header and the 401-refresh dance (login/register/etc). */
  skipAuth?: boolean
}

/**
 * Attaches the bearer token and retries once through a refresh-token
 * exchange on a 401 — the shared auth dance behind both `apiFetch` (JSON)
 * and `apiFetchBlob` (file downloads), which only differ in how they read
 * a successful response body.
 */
async function authedFetch(path: string, options: ApiFetchOptions): Promise<Response> {
  const { skipAuth, body, headers, ...rest } = options
  // A FormData body (file uploads) must go through untouched — the browser
  // sets its own multipart Content-Type with the correct boundary, which a
  // hardcoded 'application/json' header would otherwise clobber.
  const isFormData = body instanceof FormData

  const doFetch = (): Promise<Response> => {
    const token = getAccessToken()
    const finalHeaders: HeadersInit = {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...headers,
      ...(token && !skipAuth ? { Authorization: `Bearer ${token}` } : {}),
    }
    return fetch(`${API_BASE_URL}${path}`, {
      ...rest,
      headers: finalHeaders,
      body: isFormData ? (body as FormData) : body !== undefined ? JSON.stringify(body) : undefined,
    })
  }

  let response = await doFetch()

  if (response.status === 401 && !skipAuth) {
    const refreshed = await attemptTokenRefresh()
    if (refreshed) {
      response = await doFetch()
    }
  }

  return response
}

/**
 * Thin fetch wrapper: attaches the bearer token, retries once through a
 * refresh-token exchange on a 401, and falls back to "guest" (cleared
 * tokens) if the refresh itself fails — mirrors the approved mockup's
 * "dismiss the login popup and keep browsing as a guest" behavior.
 */
export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const response = await authedFetch(path, options)

  if (!response.ok) {
    const errorBody = await parseErrorBody(response)
    throw new ApiError(response.status, errorBody.code, errorBody.message)
  }

  if (response.status === 204) return undefined as T

  return (await response.json()) as T
}

/** Same auth dance as `apiFetch`, but for endpoints that stream a file
 * (e.g. a CSV export) instead of returning JSON. */
export async function apiFetchBlob(path: string, options: ApiFetchOptions = {}): Promise<Blob> {
  const response = await authedFetch(path, options)

  if (!response.ok) {
    const errorBody = await parseErrorBody(response)
    throw new ApiError(response.status, errorBody.code, errorBody.message)
  }

  return response.blob()
}
