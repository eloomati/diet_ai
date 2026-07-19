import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { DietitianApplicationSection } from './DietitianApplicationSection'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function renderSection() {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <DietitianApplicationSection />
    </QueryClientProvider>,
  )
}

describe('DietitianApplicationSection', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows the apply button when no application exists yet, then submits it', async () => {
    const user = userEvent.setup()
    let submitted = false
    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url.includes('/dietitian/applications/me')) {
        if (submitted) {
          return Promise.resolve(
            jsonResponse(200, {
              id: 'app-1',
              user_id: 'u1',
              experience: '5 lat doświadczenia',
              diplomas: ['Dietetyk kliniczny'],
              description: 'Specjalizuję się w redukcji wagi.',
              status: 'PENDING',
              created_at: '2026-07-19T00:00:00Z',
            }),
          )
        }
        return Promise.resolve(jsonResponse(404, { code: 'NOT_FOUND', message: 'no application yet' }))
      }
      if (url.includes('/dietitian/applications') && options?.method === 'POST') {
        submitted = true
        return Promise.resolve(
          jsonResponse(201, {
            id: 'app-1',
            user_id: 'u1',
            experience: '5 lat doświadczenia',
            diplomas: ['Dietetyk kliniczny'],
            description: 'Specjalizuję się w redukcji wagi.',
            status: 'PENDING',
            created_at: '2026-07-19T00:00:00Z',
          }),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderSection()

    const applyButton = await screen.findByRole('button', { name: 'Zgłoszenie dietetyka' })
    await user.click(applyButton)

    await user.type(await screen.findByLabelText('Doświadczenie'), '5 lat doświadczenia')
    await user.type(screen.getByLabelText('Opis'), 'Specjalizuję się w redukcji wagi.')
    await user.click(screen.getByRole('button', { name: 'Wyślij zgłoszenie' }))

    expect(await screen.findByText('Zgłoszenie w trakcie rozpatrywania')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Zgłoszenie dietetyka' })).not.toBeInTheDocument()
  })

  it('shows the status badge directly when an application already exists', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/dietitian/applications/me')) {
        return Promise.resolve(
          jsonResponse(200, {
            id: 'app-1',
            user_id: 'u1',
            experience: 'exp',
            diplomas: [],
            description: 'desc',
            status: 'APPROVED',
            created_at: '2026-07-19T00:00:00Z',
          }),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderSection()

    expect(await screen.findByText('Zgłoszenie zaakceptowane')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Zgłoszenie dietetyka' })).not.toBeInTheDocument()
  })
})
