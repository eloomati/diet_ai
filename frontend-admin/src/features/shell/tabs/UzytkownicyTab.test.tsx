import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRef } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from '@/lib/auth'
import { clearTokens } from '@/lib/auth/tokenStore'

import { UzytkownicyTab } from './UzytkownicyTab'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const CALLER = {
  user_id: 'caller-1',
  email: 'caller@example.com',
  status: 'ACTIVE',
  email_verified: true,
}

const TARGET_USER = {
  id: 'target-1',
  email: 'target@example.com',
  status: 'ACTIVE',
  role: 'USER',
  email_verified: false,
  created_at: '2026-07-19T00:00:00Z',
}

/** Logs in via the real AuthContext before rendering, so `useAuth()`'s
 * `user` (needed for the SUPER_ADMIN gate and the self-action guard) is
 * populated — same pattern as the main app's ProfilTab.test.tsx. */
function LoggedInTab() {
  const { login } = useAuth()
  const didLogin = useRef(false)

  if (!didLogin.current) {
    didLogin.current = true
    void login('caller@example.com', 'StrongPass123')
  }

  return <UzytkownicyTab />
}

function renderTab() {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <LoggedInTab />
      </AuthProvider>
    </QueryClientProvider>,
  )
}

function stubFetch(callerRole: string, users: unknown[], overrides: (url: string, options?: RequestInit) => Response | undefined = () => undefined) {
  const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
    const override = overrides(url, options)
    if (override) return Promise.resolve(override)
    if (url.includes('/auth/me')) return Promise.resolve(jsonResponse(200, { ...CALLER, role: callerRole }))
    if (url.includes('/auth/login')) {
      return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
    }
    if (url.includes('/admin/users')) return Promise.resolve(jsonResponse(200, users))
    return Promise.resolve(jsonResponse(200, {}))
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('UzytkownicyTab', () => {
  afterEach(() => {
    clearTokens()
    vi.unstubAllGlobals()
  })

  it('renders the user list with status and role', async () => {
    stubFetch('ADMIN', [TARGET_USER])

    renderTab()

    expect(await screen.findByText('target@example.com')).toBeInTheDocument()
    expect(screen.getByText('ACTIVE')).toBeInTheDocument()
    expect(screen.getByText('Użytkownik')).toBeInTheDocument()
  })

  it('does not show the role selector for a plain ADMIN', async () => {
    stubFetch('ADMIN', [TARGET_USER])

    renderTab()
    await screen.findByText('target@example.com')

    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
  })

  it('shows the role selector for a SUPER_ADMIN, but not for their own row', async () => {
    stubFetch('SUPER_ADMIN', [TARGET_USER, { ...CALLER, id: 'caller-1', role: 'SUPER_ADMIN', created_at: '2026-07-19T00:00:00Z' }])

    renderTab()
    await screen.findByText('target@example.com')

    expect(screen.getAllByRole('combobox')).toHaveLength(1)
  })

  it('bans an active user', async () => {
    const user = userEvent.setup()
    const fetchMock = stubFetch('ADMIN', [TARGET_USER], (url, options) => {
      if (url.includes('/ban') && options?.method === 'POST') {
        return jsonResponse(200, { ...TARGET_USER, status: 'BLOCKED' })
      }
      return undefined
    })
    renderTab()
    await screen.findByText('target@example.com')

    await user.click(screen.getByRole('button', { name: 'Zablokuj' }))

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/admin/users/target-1/ban'),
        expect.objectContaining({ method: 'POST' }),
      ),
    )
  })

  it('disables ban/delete for the caller’s own row', async () => {
    stubFetch('ADMIN', [{ ...TARGET_USER, id: 'caller-1', email: 'caller@example.com' }])

    renderTab()
    await screen.findByText('caller@example.com')

    expect(screen.getByRole('button', { name: 'Zablokuj' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Usuń' })).toBeDisabled()
  })

  it('deletes a user after confirming in the dialog', async () => {
    const user = userEvent.setup()
    let deleted = false
    const fetchMock = stubFetch('ADMIN', [TARGET_USER], (url, options) => {
      if (url.includes('/admin/users/target-1') && options?.method === 'DELETE') {
        deleted = true
        return new Response(null, { status: 204 })
      }
      if (deleted && url.endsWith('/admin/users')) return jsonResponse(200, [])
      return undefined
    })
    renderTab()
    await screen.findByText('target@example.com')

    await user.click(screen.getByRole('button', { name: 'Usuń' }))
    expect(await screen.findByText('Usunąć konto?')).toBeInTheDocument()

    const confirmButtons = screen.getAllByRole('button', { name: 'Usuń' })
    await user.click(confirmButtons[confirmButtons.length - 1])

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/admin/users/target-1'),
        expect.objectContaining({ method: 'DELETE' }),
      ),
    )
  })
})
