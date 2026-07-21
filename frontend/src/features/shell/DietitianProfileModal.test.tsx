import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { DietitianProfileModal } from './DietitianProfileModal'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const noop = () => {}

function renderModal(dietitianId: string | null) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <DietitianProfileModal dietitianId={dietitianId} onOpenChange={noop} />
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

describe('DietitianProfileModal (Etap 4 Stage 3)', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('is closed and fetches nothing when no dietitian is selected', () => {
    vi.stubGlobal('fetch', vi.fn())

    renderModal(null)

    expect(screen.queryByText('Doświadczenie')).not.toBeInTheDocument()
  })

  it('renders experience, diplomas, description, photos, offers, and reviews', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(200, FULL_PROFILE)))

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
    const applyButtons = screen.getAllByRole('button', { name: 'Zgłoś się' })
    expect(applyButtons).toHaveLength(2)
    applyButtons.forEach((button) => expect(button).toBeDisabled())

    expect(screen.getByText('Świetne podejście.')).toBeInTheDocument()
    expect(screen.getByText('Bardzo pomocne.')).toBeInTheDocument()
  })

  it('shows "Brak ocen" and "Brak opinii." when there are no reviews yet', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(200, { ...FULL_PROFILE, average_rating: null, review_count: 0, reviews: [] }),
      ),
    )

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
})
