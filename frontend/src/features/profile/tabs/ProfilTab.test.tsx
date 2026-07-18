import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRef } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from '@/lib/auth'
import { clearTokens } from '@/lib/auth/tokenStore'

import { ProfilTab } from './ProfilTab'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

/** Logs in via the real AuthContext before rendering ProfilTab, so `user` is populated. */
function LoggedInProfilTab() {
  const { login } = useAuth()
  const didLogin = useRef(false)

  if (!didLogin.current) {
    didLogin.current = true
    void login('user@example.com', 'StrongPass123')
  }

  return <ProfilTab />
}

function renderLoggedIn() {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <LoggedInProfilTab />
      </AuthProvider>
    </QueryClientProvider>,
  )
}

describe('ProfilTab', () => {
  beforeEach(() => {
    clearTokens()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows the verification form for an unverified user, then the badge after confirming', async () => {
    const user = userEvent.setup()
    let emailVerified = false
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, {
            user_id: 'u1',
            email: 'user@example.com',
            status: 'ACTIVE',
            email_verified: emailVerified,
          }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      if (url.includes('/verify-email/confirm')) {
        emailVerified = true
        return Promise.resolve(jsonResponse(200, { message: 'Email verified successfully.' }))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderLoggedIn()

    expect(await screen.findByLabelText('Kod z e-maila powitalnego')).toBeInTheDocument()

    await user.type(screen.getByLabelText('Kod z e-maila powitalnego'), 'welcome-token')
    await user.click(screen.getByRole('button', { name: 'Zweryfikuj' }))

    expect(await screen.findByText('Adres e-mail zweryfikowany ✓')).toBeInTheDocument()
  })

  it('shows the verified badge directly for an already-verified user', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, { user_id: 'u1', email: 'user@example.com', status: 'ACTIVE', email_verified: true }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderLoggedIn()

    expect(await screen.findByText('Adres e-mail zweryfikowany ✓')).toBeInTheDocument()
    expect(screen.queryByLabelText('Kod z e-maila powitalnego')).not.toBeInTheDocument()
  })

  it('shows an inline error for an invalid verification token', async () => {
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
      if (url.includes('/verify-email/confirm')) {
        return Promise.resolve(jsonResponse(400, { code: 'BAD_REQUEST', message: 'invalid' }))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderLoggedIn()

    await user.type(await screen.findByLabelText('Kod z e-maila powitalnego'), 'garbage')
    await user.click(screen.getByRole('button', { name: 'Zweryfikuj' }))

    expect(
      await screen.findByText('Kod jest nieprawidłowy, wygasł lub został już użyty.'),
    ).toBeInTheDocument()
  })

  it('calls logout when "Wyloguj się" is clicked', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, { user_id: 'u1', email: 'user@example.com', status: 'ACTIVE', email_verified: true }),
        )
      }
      return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderLoggedIn()
    await screen.findByText('Adres e-mail zweryfikowany ✓')

    await act(async () => {
      await user.click(screen.getByRole('button', { name: 'Wyloguj się' }))
    })

    await waitFor(() => expect(screen.queryByText(/Zalogowano jako/)).not.toBeInTheDocument())
  })
})
