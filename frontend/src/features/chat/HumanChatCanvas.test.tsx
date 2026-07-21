import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRef } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from '@/lib/auth'
import { clearTokens } from '@/lib/auth/tokenStore'

import { HumanChatCanvas } from './HumanChatCanvas'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const noop = () => {}

const THREAD = {
  id: 'thread-1',
  user_id: 'u1',
  dietitian_id: 'd1',
  created_at: '2026-07-22T00:00:00Z',
  other_participant_email: 'dietitian@example.com',
}

function LoggedInCanvas({ email = 'user@example.com' }: { email?: string }) {
  const { login } = useAuth()
  const didLogin = useRef(false)
  if (!didLogin.current) {
    didLogin.current = true
    void login(email, 'StrongPass123')
  }
  return (
    <HumanChatCanvas
      leftCollapsed={false}
      rightCollapsed={false}
      onExpandLeft={noop}
      onExpandRight={noop}
      threadId="thread-1"
    />
  )
}

function renderCanvas() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AuthProvider>
          <LoggedInCanvas />
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function stubAuthAndThread(extra: (url: string, init?: RequestInit) => Response | undefined) {
  const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
    if (url.includes('/auth/me')) {
      return Promise.resolve(
        jsonResponse(200, { user_id: 'u1', email: 'user@example.com', status: 'ACTIVE', email_verified: true }),
      )
    }
    if (url.includes('/auth/login')) {
      return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
    }
    if (url.endsWith('/messaging/threads')) {
      return Promise.resolve(jsonResponse(200, [THREAD]))
    }
    if (url.endsWith('/diet-plans')) {
      return Promise.resolve(jsonResponse(200, []))
    }
    const override = extra(url, init)
    if (override) return Promise.resolve(override)
    return Promise.resolve(jsonResponse(200, {}))
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('HumanChatCanvas (Etap 5 Stage 3)', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    clearTokens()
  })

  it('shows the other participants email in the header', async () => {
    stubAuthAndThread((url) => {
      if (url.endsWith('/messaging/threads/thread-1/messages')) return jsonResponse(200, [])
      return undefined
    })

    renderCanvas()

    expect(await screen.findByText('dietitian@example.com')).toBeInTheDocument()
  })

  it('shows an empty state with no messages yet', async () => {
    stubAuthAndThread((url) => {
      if (url.endsWith('/messaging/threads/thread-1/messages')) return jsonResponse(200, [])
      return undefined
    })

    renderCanvas()

    expect(await screen.findByText('Brak jeszcze żadnych wiadomości. Napisz pierwszy!')).toBeInTheDocument()
  })

  it('aligns the callers own messages differently from the other sides', async () => {
    stubAuthAndThread((url) => {
      if (url.endsWith('/messaging/threads/thread-1/messages')) {
        return jsonResponse(200, [
          {
            id: 'm1',
            thread_id: 'thread-1',
            sender: 'USER',
            content: 'Hi, question about my plan.',
            diet_plan_id: null,
            created_at: '2026-07-22T00:00:00Z',
          },
          {
            id: 'm2',
            thread_id: 'thread-1',
            sender: 'DIETITIAN',
            content: 'Sure, go ahead.',
            diet_plan_id: null,
            created_at: '2026-07-22T00:01:00Z',
          },
        ])
      }
      return undefined
    })

    renderCanvas()

    const mine = await screen.findByText('Hi, question about my plan.')
    const theirs = await screen.findByText('Sure, go ahead.')
    expect(mine.className).toContain('bg-primary')
    expect(theirs.className).toContain('bg-card')
  })

  it('sends a text message and appends it to the thread', async () => {
    const user = userEvent.setup()
    const fetchMock = stubAuthAndThread((url, init) => {
      if (url.endsWith('/messaging/threads/thread-1/messages') && init?.method === 'POST') {
        return jsonResponse(201, {
          id: 'm3',
          thread_id: 'thread-1',
          sender: 'USER',
          content: 'New message',
          diet_plan_id: null,
          created_at: '2026-07-22T00:02:00Z',
        })
      }
      if (url.endsWith('/messaging/threads/thread-1/messages')) return jsonResponse(200, [])
      return undefined
    })

    renderCanvas()
    await screen.findByText('Brak jeszcze żadnych wiadomości. Napisz pierwszy!')

    await user.type(screen.getByPlaceholderText('Napisz wiadomość…'), 'New message')
    await user.click(screen.getByRole('button', { name: 'Wyślij' }))

    expect(await screen.findByText('New message')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/messaging/threads/thread-1/messages'),
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('renders a plan-attached message as a DietPlanCard instead of a text bubble', async () => {
    stubAuthAndThread((url) => {
      if (url.endsWith('/messaging/threads/thread-1/messages')) {
        return jsonResponse(200, [
          {
            id: 'm1',
            thread_id: 'thread-1',
            sender: 'USER',
            content: 'Przesyłam mój wygenerowany plan.',
            diet_plan_id: 'plan-1',
            created_at: '2026-07-22T00:00:00Z',
          },
        ])
      }
      if (url.endsWith('/diet-plans/plan-1')) {
        return jsonResponse(200, {
          plan_id: 'plan-1',
          user_id: 'u1',
          goal: 'WEIGHT_LOSS',
          diet_type: 'STANDARD',
          duration_days: 3,
          requirements: [],
          days: [],
          created_at: '2026-07-22T00:00:00Z',
          updated_at: '2026-07-22T00:00:00Z',
        })
      }
      return undefined
    })

    renderCanvas()

    expect(await screen.findByText('Wygenerowany plan')).toBeInTheDocument()
    expect(screen.queryByText('Przesyłam mój wygenerowany plan.')).not.toBeInTheDocument()
  })

  it('shows a message when the caller has no diet plans to send', async () => {
    const user = userEvent.setup()
    stubAuthAndThread((url) => {
      if (url.endsWith('/messaging/threads/thread-1/messages')) return jsonResponse(200, [])
      return undefined
    })

    renderCanvas()
    await screen.findByText('Brak jeszcze żadnych wiadomości. Napisz pierwszy!')

    await user.click(screen.getByRole('button', { name: /Wyślij mój plan/ }))

    expect(await screen.findByText('Nie masz jeszcze żadnych wygenerowanych planów.')).toBeInTheDocument()
  })
})
