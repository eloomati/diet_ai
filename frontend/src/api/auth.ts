import { apiFetch } from '@/lib/apiFetch'

export interface RegisterRequest {
  email: string
  password: string
}

export interface RegisterResponse {
  user_id: string
  email: string
}

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
}

export interface MessageResponse {
  message: string
}

export function register(payload: RegisterRequest): Promise<RegisterResponse> {
  return apiFetch('/auth/register', { method: 'POST', body: payload, skipAuth: true })
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

export function requestPasswordReset(email: string): Promise<MessageResponse> {
  return apiFetch('/auth/password-reset/request', { method: 'POST', body: { email }, skipAuth: true })
}

export function confirmPasswordReset(token: string, newPassword: string): Promise<MessageResponse> {
  return apiFetch('/auth/password-reset/confirm', {
    method: 'POST',
    body: { token, new_password: newPassword },
    skipAuth: true,
  })
}

export function confirmEmailVerification(token: string): Promise<MessageResponse> {
  return apiFetch('/auth/verify-email/confirm', { method: 'POST', body: { token }, skipAuth: true })
}
