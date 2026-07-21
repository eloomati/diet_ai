import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRef } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from '@/lib/auth'
import { clearTokens } from '@/lib/auth/tokenStore'
import { notifyError, notifyInfo } from '@/lib/toast'

import { DietitianProfileModal } from './DietitianProfileModal'

vi.mock('@/lib/toast', () => ({ notifyError: vi.fn(), notifyInfo: vi.fn() }))

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const noop = () => {}

function LoggedInModal({ dietitianId }: { dietitianId: string | null }) {
  const { login } = useAuth()
  const didLogin = useRef(false)
  if (!didLogin.current) {
    didLogin.current = true
    void login('user@example.com', 'StrongPass123')
  }
  return <DietitianProfileModal dietitianId={dietitianId} onOpenChange={noop} />
}

function renderModal(
  dietitianId: string | null,
  { loggedIn = false }: { loggedIn?: boolean } = {},
) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        {loggedIn ? (
          <LoggedInModal dietitianId={dietitianId} />
        ) : (
          <DietitianProfileModal dietitianId={dietitianId} onOpenChange={noop} />
        )}
      </AuthProvider>
    </QueryClientProvider>,
  )
}

const FULL_PROFILE = {
  user_id: 'd1',
  email: 'dietitian@example.com',
  experience: '10 lat doświadczenia klinicznego',
  diplomas: ['MSc Dietetics', 'PhD Nutrition'],
  description: 'Pomagam bezpiecznie zmienić nawyki żywieniowe.',
  photos: ['/static/dietitian-photos/a.jpg'],
  created_at: '2026-07-19T00:00:00Z',
  average_rating: 8.5,
  review_count: 2,
  reviews: [
    { rating: 9, comment: 'Świetne podejście.', created_at: '2026-07-19T00:00:00Z' },
    { rating: 8, comment: 'Bardzo pomocne.', created_at: '2026-07-18T00:00:00Z' },
  ],
}

function stubGuestFetch(profile: unknown = FULL_PROFILE) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockImplementation((url: string) => {
      if (url.endsWith('/dietitian/d1')) return Promise.resolve(jsonResponse(200, profile))
      return Promise.resolve(jsonResponse(200, {}))
    }),
  )
}

describe('DietitianProfileModal (Etap 4 Stage 3/4)', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    clearTokens()
    vi.mocked(notifyError).mockClear()
    vi.mocked(notifyInfo).mockClear()
  })

  it('is closed and fetches nothing when no dietitian is selected', () => {
    vi.stubGlobal('fetch', vi.fn())

    renderModal(null)

    expect(screen.queryByText('Doświadczenie')).not.toBeInTheDocument()
  })

  it('renders experience, diplomas, description, photos, offers, and reviews', async () => {
    stubGuestFetch()

    renderModal('d1')

    expect(await screen.findByText('dietitian@example.com')).toBeInTheDocument()
    expect(screen.getByText('10 lat doświadczenia klinicznego')).toBeInTheDocument()
    expect(screen.getByText('MSc Dietetics')).toBeInTheDocument()
    expect(screen.getByText('PhD Nutrition')).toBeInTheDocument()
    expect(screen.getByText('Pomagam bezpiecznie zmienić nawyki żywieniowe.')).toBeInTheDocument()
    expect(screen.getByAltText('')).toBeInTheDocument()
    expect(screen.getByText('8.5')).toBeInTheDocument()
    expect(screen.getByText('(2)')).toBeInTheDocument()

    expect(screen.getByText('Ocena wygenerowanego planu')).toBeInTheDocument()
    expect(screen.getByText('49.00 zł')).toBeInTheDocument()
    expect(screen.getByText('Indywidualny plan')).toBeInTheDocument()
    expect(screen.getByText('149.00 zł')).toBeInTheDocument()

    expect(screen.getByText('Świetne podejście.')).toBeInTheDocument()
    expect(screen.getByText('Bardzo pomocne.')).toBeInTheDocument()
  })

  it('shows "Brak ocen" and "Brak opinii." when there are no reviews yet', async () => {
    stubGuestFetch({ ...FULL_PROFILE, average_rating: null, review_count: 0, reviews: [] })

    renderModal('d1')

    expect(await screen.findByText('Brak ocen')).toBeInTheDocument()
    expect(screen.getByText('Brak opinii.')).toBeInTheDocument()
  })

  it('shows an error message when the profile fails to load', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(jsonResponse(404, { code: 'NOT_FOUND', message: 'No dietitian found for this id.' })),
    )

    renderModal('unknown')

    expect(await screen.findByText('No dietitian found for this id.')).toBeInTheDocument()
  })

  it('disables "Zgłoś się" for a guest with an explanatory tooltip', async () => {
    stubGuestFetch()

    renderModal('d1')

    const applyButtons = await screen.findAllByRole('button', { name: 'Zgłoś się' })
    expect(applyButtons).toHaveLength(2)
    applyButtons.forEach((button) => {
      expect(button).toBeDisabled()
      expect(button).toHaveAttribute('title', 'Zaloguj się, aby się zgłosić')
    })
  })

  it('disables "Zgłoś się" when viewing your own profile', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, { user_id: 'd1', email: 'user@example.com', status: 'ACTIVE', email_verified: true }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      if (url.endsWith('/dietitian/d1')) return Promise.resolve(jsonResponse(200, FULL_PROFILE))
      if (url.endsWith('/transactions/me/purchases')) return Promise.resolve(jsonResponse(200, []))
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderModal('d1', { loggedIn: true })

    const applyButtons = await screen.findAllByRole('button', { name: 'Zgłoś się' })
    applyButtons.forEach((button) => {
      expect(button).toBeDisabled()
      expect(button).toHaveAttribute('title', 'Nie możesz zgłosić się do własnej oferty')
    })
  })

  it('creates a transaction and shows the payment stub when a logged-in buyer applies', async () => {
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
      if (url.endsWith('/dietitian/d1')) return Promise.resolve(jsonResponse(200, FULL_PROFILE))
      if (url.endsWith('/transactions/me/purchases')) return Promise.resolve(jsonResponse(200, []))
      if (url.endsWith('/transactions') && init?.method === 'POST') {
        return Promise.resolve(
          jsonResponse(201, {
            id: 't1',
            user_id: 'u1',
            dietitian_id: 'd1',
            offer_type: 'PLAN_REVIEW',
            amount: '49.00',
            status: 'UNPAID',
            created_at: '2026-07-19T00:00:00Z',
            paid_at: null,
          }),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderModal('d1', { loggedIn: true })
    const applyButtons = await screen.findAllByRole('button', { name: 'Zgłoś się' })
    await user.click(applyButtons[0])

    expect(await screen.findByText('Płatność')).toBeInTheDocument()
    expect(screen.getByText('49.00 zł')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Zapłać' }))

    expect(notifyInfo).toHaveBeenCalledWith('Dziękujemy! Administrator potwierdzi płatność ręcznie.')
    expect(screen.getByText('Doświadczenie')).toBeInTheDocument()
  })

  it('shows "Przejdź do płatności" for an existing unpaid transaction, and "Opłacone ✓" for a paid one', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, { user_id: 'u1', email: 'user@example.com', status: 'ACTIVE', email_verified: true }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      if (url.endsWith('/dietitian/d1')) return Promise.resolve(jsonResponse(200, FULL_PROFILE))
      if (url.endsWith('/transactions/me/purchases')) {
        return Promise.resolve(
          jsonResponse(200, [
            {
              id: 't1',
              user_id: 'u1',
              dietitian_id: 'd1',
              offer_type: 'PLAN_REVIEW',
              amount: '49.00',
              status: 'UNPAID',
              created_at: '2026-07-19T00:00:00Z',
              paid_at: null,
            },
            {
              id: 't2',
              user_id: 'u1',
              dietitian_id: 'd1',
              offer_type: 'INDIVIDUAL_PLAN',
              amount: '149.00',
              status: 'PAID',
              created_at: '2026-07-19T00:00:00Z',
              paid_at: '2026-07-19T01:00:00Z',
            },
          ]),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderModal('d1', { loggedIn: true })

    expect(await screen.findByText('Przejdź do płatności')).toBeInTheDocument()
    expect(screen.getByText('Opłacone ✓')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Zgłoś się' })).not.toBeInTheDocument()
  })
})
