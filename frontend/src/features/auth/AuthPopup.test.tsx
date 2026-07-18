import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '@/lib/auth'
import { clearTokens } from '@/lib/auth/tokenStore'

import { AuthPopup } from './AuthPopup'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function renderPopup(onOpenChange = vi.fn()) {
  const queryClient = new QueryClient()
  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <AuthProvider>{children}</AuthProvider>
      </QueryClientProvider>
    )
  }
  render(<AuthPopup open onOpenChange={onOpenChange} />, { wrapper: Wrapper })
  return { onOpenChange }
}

describe('AuthPopup', () => {
  beforeEach(() => {
    clearTokens()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('logs in successfully and closes the popup', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, { user_id: 'u1', email: 'user@example.com', status: 'ACTIVE', email_verified: false }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    const { onOpenChange } = renderPopup()

    await user.type(screen.getByPlaceholderText('ty@przyklad.pl'), 'user@example.com')
    await user.type(screen.getByPlaceholderText('••••••••'), 'StrongPass123')
    await user.click(screen.getByRole('button', { name: 'Zaloguj się' }))

    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
  })

  it('shows an inline error on invalid credentials without closing the popup', async () => {
    const user = userEvent.setup()
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(401, { code: 'INVALID_CREDENTIALS', message: 'nope' }))
    vi.stubGlobal('fetch', fetchMock)

    const { onOpenChange } = renderPopup()

    await user.type(screen.getByPlaceholderText('ty@przyklad.pl'), 'user@example.com')
    await user.type(screen.getByPlaceholderText('••••••••'), 'WrongPass123')
    await user.click(screen.getByRole('button', { name: 'Zaloguj się' }))

    expect(await screen.findByText('Nieprawidłowy e-mail lub hasło.')).toBeInTheDocument()
    expect(onOpenChange).not.toHaveBeenCalledWith(false)
  })

  it('registers, logs in with the same credentials, and closes the popup', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, { user_id: 'u1', email: 'new@example.com', status: 'ACTIVE', email_verified: false }),
        )
      }
      if (url.includes('/auth/register')) {
        return Promise.resolve(jsonResponse(201, { user_id: 'u1', email: 'new@example.com' }))
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    const { onOpenChange } = renderPopup()

    await user.click(screen.getByRole('tab', { name: 'Zarejestruj się' }))
    await user.type(screen.getByPlaceholderText('ty@przyklad.pl'), 'new@example.com')
    await user.type(screen.getByPlaceholderText('••••••••'), 'StrongPass123')

    // The Captcha widget resolves to a dev placeholder token when no site
    // key is configured (the test environment), enabling the submit button.
    await waitFor(() => expect(screen.getByRole('button', { name: 'Utwórz konto' })).toBeEnabled())
    await user.click(screen.getByRole('button', { name: 'Utwórz konto' }))

    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/auth/register'))).toBe(true)
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/auth/login'))).toBe(true)
  })

  it('shows an inline error when registering with an email already in use', async () => {
    const user = userEvent.setup()
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(409, { code: 'USER_ALREADY_EXISTS', message: 'taken' }))
    vi.stubGlobal('fetch', fetchMock)

    renderPopup()

    await user.click(screen.getByRole('tab', { name: 'Zarejestruj się' }))
    await user.type(screen.getByPlaceholderText('ty@przyklad.pl'), 'dup@example.com')
    await user.type(screen.getByPlaceholderText('••••••••'), 'StrongPass123')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Utwórz konto' })).toBeEnabled())
    await user.click(screen.getByRole('button', { name: 'Utwórz konto' }))

    expect(await screen.findByText('Konto z tym adresem e-mail już istnieje.')).toBeInTheDocument()
  })

  it('closes the popup when continuing as a guest', async () => {
    const user = userEvent.setup()
    const { onOpenChange } = renderPopup()

    await user.click(screen.getByRole('button', { name: 'Kontynuuj jako gość →' }))

    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it('navigates to the forgot-password flow and back', async () => {
    const user = userEvent.setup()
    renderPopup()

    await user.click(screen.getByRole('button', { name: 'Zapomniałeś hasła?' }))
    expect(screen.getByText('Podaj adres e-mail konta — wyślemy kod do zresetowania hasła.')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '← Wróć do logowania' }))
    expect(screen.getByRole('tab', { name: 'Zaloguj się' })).toBeInTheDocument()
  })
})
