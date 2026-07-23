import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { TransakcjeTab } from './TransakcjeTab'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const BUYER = {
  id: 'buyer-1',
  email: 'buyer@example.com',
  status: 'ACTIVE',
  role: 'USER',
  email_verified: false,
  created_at: '2026-07-19T00:00:00Z',
}

const DIETITIAN = {
  id: 'dietitian-1',
  email: 'dietitian@example.com',
  status: 'ACTIVE',
  role: 'DIET_USER',
  email_verified: false,
  created_at: '2026-07-19T00:00:00Z',
}

const TRANSACTION = {
  id: 'txn-1',
  user_id: 'buyer-1',
  dietitian_id: 'dietitian-1',
  offer_type: 'PLAN_REVIEW',
  amount: '49.00',
  status: 'UNPAID',
  created_at: '2026-07-19T00:00:00Z',
  paid_at: null,
}

function renderTab() {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <TransakcjeTab />
    </QueryClientProvider>,
  )
}

function stubFetch(
  transactions: unknown[],
  overrides: (url: string, options?: RequestInit) => Response | undefined = () => undefined,
) {
  const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
    const override = overrides(url, options)
    if (override) return Promise.resolve(override)
    if (url.includes('/admin/transactions')) {
      return Promise.resolve(jsonResponse(200, { items: transactions, total: transactions.length }))
    }
    if (url.includes('/admin/users')) {
      return Promise.resolve(jsonResponse(200, { items: [BUYER, DIETITIAN], total: 2 }))
    }
    return Promise.resolve(jsonResponse(200, {}))
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('TransakcjeTab', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows an empty state when there are no transactions', async () => {
    stubFetch([])

    renderTab()

    expect(await screen.findByText('Brak transakcji.')).toBeInTheDocument()
  })

  it('renders a transaction with resolved buyer/dietitian emails', async () => {
    stubFetch([TRANSACTION])

    renderTab()

    expect(await screen.findByText('buyer@example.com')).toBeInTheDocument()
    expect(screen.getByText('dietitian@example.com')).toBeInTheDocument()
    expect(screen.getByText('Ocena wygenerowanego planu')).toBeInTheDocument()
    expect(screen.getByText('UNPAID')).toBeInTheDocument()
  })

  it('marks a transaction paid', async () => {
    const user = userEvent.setup()
    const fetchMock = stubFetch([TRANSACTION], (url, options) => {
      if (url.includes('/mark-paid') && options?.method === 'POST') {
        return jsonResponse(200, { ...TRANSACTION, status: 'PAID', paid_at: '2026-07-19T01:00:00Z' })
      }
      return undefined
    })
    renderTab()
    await screen.findByText('buyer@example.com')

    await user.click(screen.getByRole('button', { name: 'Oznacz jako opłacone' }))

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/admin/transactions/txn-1/mark-paid'),
        expect.objectContaining({ method: 'POST' }),
      ),
    )
  })

  it('marks a paid transaction unpaid', async () => {
    const user = userEvent.setup()
    const paidTransaction = { ...TRANSACTION, status: 'PAID', paid_at: '2026-07-19T01:00:00Z' }
    const fetchMock = stubFetch([paidTransaction], (url, options) => {
      if (url.includes('/mark-unpaid') && options?.method === 'POST') {
        return jsonResponse(200, TRANSACTION)
      }
      return undefined
    })
    renderTab()
    await screen.findByText('buyer@example.com')

    await user.click(screen.getByRole('button', { name: 'Oznacz jako nieopłacone' }))

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/admin/transactions/txn-1/mark-unpaid'),
        expect.objectContaining({ method: 'POST' }),
      ),
    )
  })

  it('falls back to the raw id when no matching user is found', async () => {
    stubFetch([TRANSACTION], (url) => {
      if (url.includes('/admin/users')) return jsonResponse(200, { items: [], total: 0 })
      return undefined
    })

    renderTab()

    expect(await screen.findByText('buyer-1')).toBeInTheDocument()
    expect(screen.getByText('dietitian-1')).toBeInTheDocument()
  })

  it('paginates through more than one page of transactions', async () => {
    const user = userEvent.setup()
    const allTransactions = Array.from({ length: 21 }, (_, i) => ({
      ...TRANSACTION,
      id: `txn-${i}`,
      amount: `${i}.00`,
    }))
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/admin/transactions')) {
        const params = new URL(url, 'http://localhost').searchParams
        const limit = Number(params.get('limit'))
        const offset = Number(params.get('offset'))
        return Promise.resolve(
          jsonResponse(200, {
            items: allTransactions.slice(offset, offset + limit),
            total: allTransactions.length,
          }),
        )
      }
      if (url.includes('/admin/users')) {
        return Promise.resolve(jsonResponse(200, { items: [BUYER, DIETITIAN], total: 2 }))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderTab()

    expect(await screen.findByText('0.00 zł')).toBeInTheDocument()
    expect(screen.getByText('1–20 z 21')).toBeInTheDocument()
    expect(screen.queryByText('20.00 zł')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Następna strona' }))

    expect(await screen.findByText('20.00 zł')).toBeInTheDocument()
    expect(screen.getByText('21–21 z 21')).toBeInTheDocument()
  })
})
