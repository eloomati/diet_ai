import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { DietetycyTab } from './DietetycyTab'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const APPLICANT_USER = {
  id: 'user-1',
  email: 'applicant@example.com',
  status: 'ACTIVE',
  role: 'USER',
  email_verified: false,
  created_at: '2026-07-19T00:00:00Z',
}

const PENDING_APPLICATION = {
  id: 'app-1',
  user_id: 'user-1',
  experience: '5 lat doświadczenia',
  diplomas: ['MSc Dietetics'],
  description: 'Specjalizuję się w redukcji wagi.',
  status: 'PENDING',
  created_at: '2026-07-19T00:00:00Z',
}

function renderTab() {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <DietetycyTab />
    </QueryClientProvider>,
  )
}

function stubFetch(applications: unknown[], overrides: (url: string, options?: RequestInit) => Response | undefined = () => undefined) {
  const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
    const override = overrides(url, options)
    if (override) return Promise.resolve(override)
    if (url.includes('/admin/dietitian-applications')) return Promise.resolve(jsonResponse(200, applications))
    if (url.includes('/admin/users')) return Promise.resolve(jsonResponse(200, [APPLICANT_USER]))
    return Promise.resolve(jsonResponse(200, {}))
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('DietetycyTab', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows the applicant email (resolved from the user list) and application details', async () => {
    stubFetch([PENDING_APPLICATION])

    renderTab()

    expect(await screen.findByText('applicant@example.com')).toBeInTheDocument()
    expect(screen.getByText(/5 lat doświadczenia/)).toBeInTheDocument()
    expect(screen.getByText(/MSc Dietetics/)).toBeInTheDocument()
    // "Oczekujące" appears twice: the status filter's current value and the
    // application's own status badge.
    expect(screen.getAllByText('Oczekujące')).toHaveLength(2)
  })

  it('shows an empty state when there are no applications in the filtered status', async () => {
    stubFetch([])

    renderTab()

    expect(await screen.findByText('Brak zgłoszeń w tej kategorii.')).toBeInTheDocument()
  })

  it('shows no approve/reject actions for a non-pending application', async () => {
    stubFetch([{ ...PENDING_APPLICATION, status: 'APPROVED' }])

    renderTab()
    await screen.findByText('applicant@example.com')

    expect(screen.queryByRole('button', { name: 'Zaakceptuj' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Odrzuć' })).not.toBeInTheDocument()
  })

  it('approves a pending application', async () => {
    const user = userEvent.setup()
    const fetchMock = stubFetch([PENDING_APPLICATION], (url, options) => {
      if (url.includes('/approve') && options?.method === 'POST') {
        return jsonResponse(200, { ...PENDING_APPLICATION, status: 'APPROVED' })
      }
      return undefined
    })

    renderTab()
    await screen.findByText('applicant@example.com')

    await user.click(screen.getByRole('button', { name: 'Zaakceptuj' }))

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/admin/dietitian-applications/app-1/approve'),
        expect.objectContaining({ method: 'POST' }),
      ),
    )
  })

  it('rejects a pending application', async () => {
    const user = userEvent.setup()
    const fetchMock = stubFetch([PENDING_APPLICATION], (url, options) => {
      if (url.includes('/reject') && options?.method === 'POST') {
        return jsonResponse(200, { ...PENDING_APPLICATION, status: 'REJECTED' })
      }
      return undefined
    })

    renderTab()
    await screen.findByText('applicant@example.com')

    await user.click(screen.getByRole('button', { name: 'Odrzuć' }))

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/admin/dietitian-applications/app-1/reject'),
        expect.objectContaining({ method: 'POST' }),
      ),
    )
  })

  it('falls back to the raw user_id when the user list has no matching entry', async () => {
    stubFetch([{ ...PENDING_APPLICATION, user_id: 'unknown-user' }], (url) => {
      if (url.includes('/admin/users')) return jsonResponse(200, [])
      return undefined
    })

    renderTab()

    expect(await screen.findByText('unknown-user')).toBeInTheDocument()
  })
})
