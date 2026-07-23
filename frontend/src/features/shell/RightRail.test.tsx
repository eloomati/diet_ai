import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRef } from 'react'
import { MemoryRouter, Route, Routes, useParams } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from '@/lib/auth'
import { clearTokens } from '@/lib/auth/tokenStore'
import { notifyInfo } from '@/lib/toast'

import { RightRail } from './RightRail'

vi.mock('@/lib/toast', () => ({ notifyInfo: vi.fn() }))

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
  return queryClient
}

const DIETITIAN_A = {
  user_id: 'd1',
  name: 'Dietitian A',
  experience: '5 lat doświadczenia jako dietetyk kliniczny',
  description: 'Opis.',
  photos: [],
  average_rating: 8.5,
  review_count: 4,
}

const DIETITIAN_B = {
  user_id: 'd2',
  name: 'Dietitian B',
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

    expect(await screen.findByText('Dietitian A')).toBeInTheDocument()
    expect(screen.getByText('Dietitian B')).toBeInTheDocument()
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
      if (url.endsWith('/notifications')) {
        return Promise.resolve(jsonResponse(200, []))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderRightRail({ loggedIn: true })

    expect(await screen.findByText('Twoi dietetycy')).toBeInTheDocument()
    const pinnedHeading = screen.getByText('Twoi dietetycy')
    const pinnedSection = pinnedHeading.parentElement!
    expect(pinnedSection).toHaveTextContent('Dietitian B')
    expect(pinnedSection).not.toHaveTextContent('Dietitian A')
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
              name: 'Dietitian A',
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
    await user.click(await screen.findByText('Dietitian A'))

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
              other_participant_name: 'dietitian.contact@example.com',
            },
          ]),
        )
      }
      if (url.endsWith('/notifications')) {
        return Promise.resolve(jsonResponse(200, []))
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

const NEW_MESSAGE_NOTIFICATION = {
  id: 'n1',
  type: 'NEW_MESSAGE',
  reference_id: 'thread-1',
  created_at: '2026-07-22T00:00:00Z',
  read_at: null,
}

function loggedInFetchMock(notifications: unknown[]) {
  return vi.fn().mockImplementation((url: string) => {
    if (url.includes('/auth/me')) {
      return Promise.resolve(
        jsonResponse(200, { user_id: 'u1', email: 'user@example.com', status: 'ACTIVE', email_verified: true }),
      )
    }
    if (url.includes('/auth/login')) {
      return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
    }
    if (url.endsWith('/dietitian')) return Promise.resolve(jsonResponse(200, []))
    if (url.endsWith('/transactions/me/purchases')) return Promise.resolve(jsonResponse(200, []))
    if (url.endsWith('/messaging/threads')) return Promise.resolve(jsonResponse(200, []))
    if (url.endsWith('/notifications/mark-all-read')) {
      return Promise.resolve(
        jsonResponse(
          200,
          notifications.map((n) => ({ ...(n as object), read_at: '2026-07-22T00:05:00Z' })),
        ),
      )
    }
    if (url.endsWith('/notifications')) return Promise.resolve(jsonResponse(200, notifications))
    return Promise.resolve(jsonResponse(200, {}))
  })
}

describe('RightRail notification badge (Etap 5 Stage 4)', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    clearTokens()
    vi.mocked(notifyInfo).mockClear()
  })

  it('shows the unread notification count on the bell', async () => {
    vi.stubGlobal('fetch', loggedInFetchMock([NEW_MESSAGE_NOTIFICATION]))

    renderRightRail({ loggedIn: true })

    await waitFor(() => expect(screen.getByLabelText('Powiadomienia')).toHaveTextContent('1'))
  })

  it('does not show a badge when there are no unread notifications', async () => {
    vi.stubGlobal('fetch', loggedInFetchMock([]))

    renderRightRail({ loggedIn: true })

    await screen.findByLabelText('Powiadomienia')
    expect(screen.getByLabelText('Powiadomienia')).not.toHaveTextContent(/\d/)
  })

  it('hides the notification bell for a guest', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(200, [])))

    renderRightRail()
    await screen.findByText('Brak dostępnych dietetyków.')

    expect(screen.queryByLabelText('Powiadomienia')).not.toBeInTheDocument()
  })

  it('opens the popover, lists notifications, and marks them all read', async () => {
    const user = userEvent.setup()
    const fetchMock = loggedInFetchMock([NEW_MESSAGE_NOTIFICATION])
    vi.stubGlobal('fetch', fetchMock)

    renderRightRail({ loggedIn: true })
    await screen.findByLabelText('Powiadomienia')

    await user.click(screen.getByLabelText('Powiadomienia'))

    expect(await screen.findByText('Nowa wiadomość')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/notifications/mark-all-read'),
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('does not toast for a notification already present when the badge first loads', async () => {
    vi.stubGlobal(
      'fetch',
      loggedInFetchMock([{ ...NEW_MESSAGE_NOTIFICATION, type: 'TRANSACTION_PAID' }]),
    )

    renderRightRail({ loggedIn: true })

    await waitFor(() => expect(screen.getByLabelText('Powiadomienia')).toHaveTextContent('1'))
    expect(notifyInfo).not.toHaveBeenCalled()
  })

  it('toasts once when a new TRANSACTION_PAID notification arrives on a later poll', async () => {
    vi.stubGlobal('fetch', loggedInFetchMock([]))

    const queryClient = renderRightRail({ loggedIn: true })
    await waitFor(() =>
      expect(queryClient.getQueryData(['my-notifications'])).toEqual([]),
    )
    expect(notifyInfo).not.toHaveBeenCalled()

    queryClient.setQueryData(
      ['my-notifications'],
      [{ ...NEW_MESSAGE_NOTIFICATION, id: 'n2', type: 'TRANSACTION_PAID' }],
    )

    await waitFor(() => expect(screen.getByLabelText('Powiadomienia')).toHaveTextContent('1'))
    expect(notifyInfo).toHaveBeenCalledTimes(1)
    expect(notifyInfo).toHaveBeenCalledWith('Klient opłacił transakcję.')
  })
})
