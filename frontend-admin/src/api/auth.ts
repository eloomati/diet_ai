import { apiFetch } from '@/lib/apiFetch'

export type UserRole = 'USER' | 'DIET_USER' | 'ADMIN' | 'SUPER_ADMIN'

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface MeResponse {
  user_id: string
  email: string
  status: string
  email_verified: boolean
  role: UserRole
}

export interface MessageResponse {
  message: string
}

export function login(payload: LoginRequest): Promise<TokenPair> {
  return apiFetch('/auth/login', { method: 'POST', body: payload, skipAuth: true })
}

export function logout(refreshToken: string): Promise<MessageResponse> {
  return apiFetch('/auth/logout', {
    method: 'POST',
    body: { refresh_token: refreshToken },
    skipAuth: true,
  })
}

export function me(): Promise<MeResponse> {
  return apiFetch('/auth/me')
}
