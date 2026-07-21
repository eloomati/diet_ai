import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRef } from 'react'
import { MemoryRouter, Route, Routes, useParams } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from '@/lib/auth'
import { clearTokens } from '@/lib/auth/tokenStore'

import { RightRail } from './RightRail'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const noop = () => {}

function LoggedInRightRail() {
  const { login } = useAuth()
  const didLogin = useRef(false)
  if (!didLogin.current) {
    didLogin.current = true
    void login('user@example.com', 'StrongPass123')
  }
  return <RightRail onCollapse={noop} />
}

function ThreadIdMarker() {
  const { threadId } = useParams<{ threadId: string }>()
  return <p>Czat z wątkiem {threadId}</p>
}

function renderRightRail({ loggedIn = false }: { loggedIn?: boolean } = {}) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/"
              element={loggedIn ? <LoggedInRightRail /> : <RightRail onCollapse={noop} />}
            />
            <Route path="/dietitian-chat/:threadId" element={<ThreadIdMarker />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const DIETITIAN_A = {
  user_id: 'd1',
  email: 'dietitian.a@example.com',
  experience: '5 lat doświadczenia jako dietetyk kliniczny',
  description: 'Opis.',
  photos: [],
  average_rating: 8.5,
  review_count: 4,
}

const DIETITIAN_B = {
  user_id: 'd2',
  email: 'dietitian.b@example.com',
  experience: '2 lata',
  description: 'Opis.',
  photos: [],
  average_rating: null,
  review_count: 0,
}

describe('RightRail marketplace listing (Etap 4 Stage 2)', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    clearTokens()
  })

  it('shows an empty state when there are no dietitians, without requiring login', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(200, [])))

    renderRightRail()

    expect(await screen.findByText('Brak dostępnych dietetyków.')).toBeInTheDocument()
  })

  it('renders dietitian cards with email, experience, and average rating', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((url: string) => {
        if (url.endsWith('/dietitian')) {
          return Promise.resolve(jsonResponse(200, [DIETITIAN_A, DIETITIAN_B]))
        }
        return Promise.resolve(jsonResponse(200, {}))
      }),
    )

    renderRightRail()

    expect(await screen.findByText('dietitian.a@example.com')).toBeInTheDocument()
    expect(screen.getByText('dietitian.b@example.com')).toBeInTheDocument()
    expect(screen.getByText('8.5')).toBeInTheDocument()
    expect(screen.getByText('(4)')).toBeInTheDocument()
    expect(screen.getByText('Brak ocen')).toBeInTheDocument()
  })

  it('shows an error message when the listing fails to load', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(500, { code: 'INTERNAL_ERROR', message: 'boom' })))

    renderRightRail()

    expect(await screen.findByText('Nie udało się wczytać listy dietetyków.')).toBeInTheDocument()
  })

  it('pins a dietitian the logged-in user already has a transaction with', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, { user_id: 'u1', email: 'user@example.com', status: 'ACTIVE', email_verified: true }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      if (url.endsWith('/dietitian')) {
        return Promise.resolve(jsonResponse(200, [DIETITIAN_A, DIETITIAN_B]))
      }
      if (url.endsWith('/transactions/me/purchases')) {
        return Promise.resolve(
          jsonResponse(200, [
            {
              id: 't1',
              user_id: 'u1',
              dietitian_id: 'd2',
              offer_type: 'PLAN_REVIEW',
              amount: '49.00',
              status: 'UNPAID',
              created_at: '2026-07-19T00:00:00Z',
              paid_at: null,
            },
          ]),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderRightRail({ loggedIn: true })

    expect(await screen.findByText('Twoi dietetycy')).toBeInTheDocument()
    const pinnedHeading = screen.getByText('Twoi dietetycy')
    const pinnedSection = pinnedHeading.parentElement!
    expect(pinnedSection).toHaveTextContent('dietitian.b@example.com')
    expect(pinnedSection).not.toHaveTextContent('dietitian.a@example.com')
    expect(screen.getByText('Wszyscy dietetycy')).toBeInTheDocument()
  })

  it('opens the public profile modal for the clicked dietitian', async () => {
    const user = userEvent.setup()
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((url: string) => {
        if (url.endsWith('/dietitian')) {
          return Promise.resolve(jsonResponse(200, [DIETITIAN_A, DIETITIAN_B]))
        }
        if (url.endsWith('/dietitian/d1')) {
          return Promise.resolve(
            jsonResponse(200, {
              user_id: 'd1',
              email: 'dietitian.a@example.com',
              experience: DIETITIAN_A.experience,
              diplomas: ['MSc Dietetics'],
              description: 'Pełny opis dietetyka A.',
              photos: [],
              created_at: '2026-07-19T00:00:00Z',
              average_rating: 8.5,
              review_count: 4,
              reviews: [],
            }),
          )
        }
        return Promise.resolve(jsonResponse(200, {}))
      }),
    )

    renderRightRail()
    await user.click(await screen.findByText('dietitian.a@example.com'))

    expect(await screen.findByText('Pełny opis dietetyka A.')).toBeInTheDocument()
    expect(screen.getByText('MSc Dietetics')).toBeInTheDocument()
  })

  it('shows a "Wiadomości" section with contact cards and navigates to the chat on click (Etap 5 Stage 3)', async () => {
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
      if (url.endsWith('/dietitian')) {
        return Promise.resolve(jsonResponse(200, []))
      }
      if (url.endsWith('/transactions/me/purchases')) {
        return Promise.resolve(jsonResponse(200, []))
      }
      if (url.endsWith('/messaging/threads')) {
        return Promise.resolve(
          jsonResponse(200, [
            {
              id: 'thread-1',
              user_id: 'u1',
              dietitian_id: 'd1',
              created_at: '2026-07-22T00:00:00Z',
              other_participant_email: 'dietitian.contact@example.com',
            },
          ]),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderRightRail({ loggedIn: true })

    expect(await screen.findByText('Wiadomości')).toBeInTheDocument()
    expect(screen.getByText('dietitian.contact@example.com')).toBeInTheDocument()

    await user.click(screen.getByText('dietitian.contact@example.com'))

    expect(await screen.findByText('Czat z wątkiem thread-1')).toBeInTheDocument()
  })

  it('does not show a "Wiadomości" section when there are no threads', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((url: string) => {
        if (url.endsWith('/dietitian')) return Promise.resolve(jsonResponse(200, []))
        return Promise.resolve(jsonResponse(200, {}))
      }),
    )

    renderRightRail()
    await screen.findByText('Brak dostępnych dietetyków.')

    expect(screen.queryByText('Wiadomości')).not.toBeInTheDocument()
  })
})
