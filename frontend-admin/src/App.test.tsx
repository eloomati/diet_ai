import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '@/lib/auth'
import { clearTokens } from '@/lib/auth/tokenStore'

import App from './App'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function renderApp() {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </QueryClientProvider>,
  )
}

describe('App', () => {
  afterEach(() => {
    clearTokens()
    vi.unstubAllGlobals()
  })

  it('shows the login page when not authenticated', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(200, {})))

    renderApp()

    expect(await screen.findByRole('button', { name: 'Zaloguj się' })).toBeInTheDocument()
  })

  it('shows the admin shell with all 4 tabs after a successful ADMIN login', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, {
            user_id: 'u-1',
            email: 'admin@example.com',
            status: 'ACTIVE',
            email_verified: true,
            role: 'ADMIN',
          }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderApp()

    await user.type(await screen.findByLabelText('E-mail'), 'admin@example.com')
    await user.type(screen.getByLabelText('Hasło'), 'StrongPass123')
    await user.click(screen.getByRole('button', { name: 'Zaloguj się' }))

    expect(await screen.findByText('Diet AI — Panel administracyjny')).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Raporty' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Użytkownicy' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Dietetycy' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Transakcje' })).toBeInTheDocument()
    expect(screen.getByText('Lista użytkowników pojawi się tutaj w kolejnym etapie.')).toBeInTheDocument()
  })

  it('shows an error and stays on the login page for a non-admin user', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, {
            user_id: 'u-2',
            email: 'user@example.com',
            status: 'ACTIVE',
            email_verified: true,
            role: 'USER',
          }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderApp()

    await user.type(await screen.findByLabelText('E-mail'), 'user@example.com')
    await user.type(screen.getByLabelText('Hasło'), 'StrongPass123')
    await user.click(screen.getByRole('button', { name: 'Zaloguj się' }))

    expect(await screen.findByText(/nie ma uprawnień administratora/)).toBeInTheDocument()
    expect(screen.queryByText('Diet AI — Panel administracyjny')).not.toBeInTheDocument()
  })

  it('logs out back to the login page', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, {
            user_id: 'u-1',
            email: 'admin@example.com',
            status: 'ACTIVE',
            email_verified: true,
            role: 'ADMIN',
          }),
        )
      }
      return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderApp()
    await user.type(await screen.findByLabelText('E-mail'), 'admin@example.com')
    await user.type(screen.getByLabelText('Hasło'), 'StrongPass123')
    await user.click(screen.getByRole('button', { name: 'Zaloguj się' }))
    await screen.findByText('Diet AI — Panel administracyjny')

    await user.click(screen.getByRole('button', { name: 'Wyloguj się' }))

    expect(await screen.findByRole('button', { name: 'Zaloguj się' })).toBeInTheDocument()
  })
})
