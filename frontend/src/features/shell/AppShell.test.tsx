import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from '@/App'
import { AuthProvider } from '@/lib/auth'
import { clearTokens } from '@/lib/auth/tokenStore'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const CONVERSATIONS = [
  {
    conversation_id: 'c1',
    title: 'Dieta, Śniadanie',
    categories: ['DIET', 'BREAKFAST'],
    status: 'ACTIVE',
    updated_at: '2026-01-01T10:00:00Z',
  },
]

function renderApp(initialEntries: string[] = ['/']) {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={initialEntries}>
          <App />
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  )
}

/** Logs in through the real AuthPopup UI — it closes itself on success. */
async function loginViaPopup(user: ReturnType<typeof userEvent.setup>) {
  await user.type(await screen.findByLabelText('E-mail'), 'user@example.com')
  await user.type(screen.getByLabelText('Hasło'), 'StrongPass123')
  await user.click(screen.getByRole('button', { name: 'Zaloguj się' }))
  await waitFor(() => expect(screen.queryByLabelText('E-mail')).not.toBeInTheDocument())
}

describe('AppShell conversations (Etap 3 Stage 1)', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    clearTokens()
  })

  it('lists conversations from GET /conversations for a logged-in user', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, { user_id: 'u1', email: 'user@example.com', status: 'ACTIVE', email_verified: true }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      if (url.endsWith('/conversations')) {
        return Promise.resolve(jsonResponse(200, CONVERSATIONS))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderApp()
    await loginViaPopup(user)

    expect((await screen.findAllByText('Dieta, Śniadanie')).length).toBeGreaterThan(0)
  })

  it('shows the empty state when the user has no conversations yet', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, { user_id: 'u1', email: 'user@example.com', status: 'ACTIVE', email_verified: true }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      if (url.endsWith('/conversations')) {
        return Promise.resolve(jsonResponse(200, []))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderApp()
    await loginViaPopup(user)

    expect(await screen.findByText('Brak jeszcze żadnych rozmów.')).toBeInTheDocument()
  })

  it('creates a conversation from the category picker and navigates to it', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, { user_id: 'u1', email: 'user@example.com', status: 'ACTIVE', email_verified: true }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      if (url.endsWith('/conversations') && init?.method === 'POST') {
        return Promise.resolve(
          jsonResponse(201, { conversation_id: 'new-1', title: 'Dieta', categories: ['DIET'], status: 'ACTIVE' }),
        )
      }
      if (url.includes('/conversations/new-1')) {
        return Promise.resolve(
          jsonResponse(200, {
            conversation_id: 'new-1',
            title: 'Dieta',
            categories: ['DIET'],
            status: 'ACTIVE',
            messages: [],
          }),
        )
      }
      if (url.endsWith('/conversations')) {
        return Promise.resolve(jsonResponse(200, []))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderApp()
    await loginViaPopup(user)

    await screen.findByText('Brak jeszcze żadnych rozmów.')
    await user.click(screen.getByRole('button', { name: 'Nowy czat' }))
    await user.click(screen.getByRole('button', { name: '🥗 Dieta' }))
    await user.click(screen.getByRole('button', { name: 'Rozpocznij czat' }))

    await waitFor(() => expect(screen.getByText('🥗 DIET')).toBeInTheDocument())

    const postCall = fetchMock.mock.calls.find(
      ([url, init]) => (url as string).endsWith('/conversations') && init?.method === 'POST',
    )
    expect(postCall).toBeDefined()
    const body = JSON.parse(postCall![1].body as string)
    expect(body).toMatchObject({ title: 'Dieta', categories: ['DIET'] })
  })

  it('shows an inline error banner when conversation creation fails', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, { user_id: 'u1', email: 'user@example.com', status: 'ACTIVE', email_verified: true }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      if (url.endsWith('/conversations') && init?.method === 'POST') {
        return Promise.resolve(jsonResponse(500, { code: 'INTERNAL_ERROR', message: 'boom' }))
      }
      if (url.endsWith('/conversations')) {
        return Promise.resolve(jsonResponse(200, []))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderApp()
    await loginViaPopup(user)

    await screen.findByText('Brak jeszcze żadnych rozmów.')
    await user.click(screen.getByRole('button', { name: 'Nowy czat' }))
    await user.click(screen.getByRole('button', { name: '🥗 Dieta' }))
    await user.click(screen.getByRole('button', { name: 'Rozpocznij czat' }))

    expect(await screen.findByText('Nie udało się utworzyć rozmowy. Spróbuj ponownie.')).toBeInTheDocument()
  })
})
