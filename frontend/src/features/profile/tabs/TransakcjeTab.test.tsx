import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { TransakcjeTab } from './TransakcjeTab'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function renderTab() {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <TransakcjeTab />
    </QueryClientProvider>,
  )
}

describe('TransakcjeTab', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows an empty state when there are no transactions', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(200, [])))

    renderTab()

    expect(await screen.findByText('Nie masz jeszcze żadnych transakcji.')).toBeInTheDocument()
  })

  it('renders transactions with offer label, amount, and status', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
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
            user_id: 'u2',
            dietitian_id: 'd1',
            offer_type: 'INDIVIDUAL_PLAN',
            amount: '149.00',
            status: 'PAID',
            created_at: '2026-07-19T00:00:00Z',
            paid_at: '2026-07-19T01:00:00Z',
          },
        ]),
      ),
    )

    renderTab()

    expect(await screen.findByText('Ocena wygenerowanego planu')).toBeInTheDocument()
    expect(screen.getByText('Indywidualny plan')).toBeInTheDocument()
    expect(screen.getByText('Nieopłacone')).toBeInTheDocument()
    expect(screen.getByText('Opłacone')).toBeInTheDocument()
    // Word-boundary regex — "149.00" also contains the substring "49.00",
    // so a plain /49.00/ match would ambiguously match both rows.
    expect(screen.getByText(/\b49\.00 zł/)).toBeInTheDocument()
  })

  it('does not show the buyer identity — only offer/amount/status', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(200, [
          {
            id: 't1',
            user_id: 'buyer-uuid-should-not-appear',
            dietitian_id: 'd1',
            offer_type: 'PLAN_REVIEW',
            amount: '49.00',
            status: 'UNPAID',
            created_at: '2026-07-19T00:00:00Z',
            paid_at: null,
          },
        ]),
      ),
    )

    renderTab()
    await screen.findByText('Ocena wygenerowanego planu')

    expect(screen.queryByText('buyer-uuid-should-not-appear')).not.toBeInTheDocument()
  })

  it('reveals the buyer contact once a transaction is paid (Etap 5 Stage 1)', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(200, [
          {
            id: 't1',
            user_id: 'u1',
            dietitian_id: 'd1',
            offer_type: 'PLAN_REVIEW',
            amount: '49.00',
            status: 'PAID',
            created_at: '2026-07-19T00:00:00Z',
            paid_at: '2026-07-19T01:00:00Z',
            buyer_email: 'buyer@example.com',
          },
        ]),
      ),
    )

    renderTab()

    expect(await screen.findByText('Kontakt: buyer@example.com')).toBeInTheDocument()
  })

  it('does not show a contact line for an unpaid transaction', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
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
            buyer_email: null,
          },
        ]),
      ),
    )

    renderTab()
    await screen.findByText('Ocena wygenerowanego planu')

    expect(screen.queryByText(/Kontakt:/)).not.toBeInTheDocument()
  })
})
