import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRef } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from '@/lib/auth'
import { notifyError, notifyInfo } from '@/lib/toast'

import { ChatCanvas } from './ChatCanvas'

vi.mock('@/lib/toast', () => ({ notifyError: vi.fn(), notifyInfo: vi.fn() }))

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const noop = () => {}

function LoggedInChatCanvas(props: { conversationId?: string; rightCollapsed: boolean }) {
  const { login } = useAuth()
  const didLogin = useRef(false)
  if (!didLogin.current) {
    didLogin.current = true
    void login('user@example.com', 'StrongPass123')
  }
  return (
    <ChatCanvas
      leftCollapsed={false}
      rightCollapsed={props.rightCollapsed}
      onExpandLeft={noop}
      onExpandRight={noop}
      conversationId={props.conversationId}
    />
  )
}

function renderCanvas(
  conversationId?: string,
  options?: { rightCollapsed?: boolean; loggedIn?: boolean },
) {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AuthProvider>
          {options?.loggedIn ? (
            <LoggedInChatCanvas
              conversationId={conversationId}
              rightCollapsed={options?.rightCollapsed ?? false}
            />
          ) : (
            <ChatCanvas
              leftCollapsed={false}
              rightCollapsed={options?.rightCollapsed ?? false}
              onExpandLeft={noop}
              onExpandRight={noop}
              conversationId={conversationId}
            />
          )}
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ChatCanvas', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.mocked(notifyError).mockClear()
    vi.mocked(notifyInfo).mockClear()
  })

  it('shows the hero when there is no active conversation', () => {
    renderCanvas(undefined)

    expect(screen.getByText('Cześć! W czym mogę Ci dziś pomóc?')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Wyślij' })).toBeDisabled()
  })

  it('keeps the Mycelo notification badge visible next to the collapsed right rail for a logged-in user, even with zero unread notifications', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, { user_id: 'u1', email: 'user@example.com', status: 'ACTIVE', email_verified: true }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      if (url.includes('/notifications')) {
        return Promise.resolve(jsonResponse(200, []))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas(undefined, { rightCollapsed: true, loggedIn: true })

    expect(await screen.findByRole('button', { name: 'Powiadomienia' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Rozwiń panel' })).toBeInTheDocument()
  })

  it('hides the Mycelo notification badge next to the collapsed right rail for a guest', () => {
    renderCanvas(undefined, { rightCollapsed: true })

    expect(screen.queryByRole('button', { name: 'Powiadomienia' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Rozwiń panel' })).toBeInTheDocument()
  })

  it('shows the hero for a freshly created conversation with no messages yet', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        jsonResponse(200, { conversation_id: 'c1', title: 'Dieta', categories: ['DIET'], status: 'ACTIVE', messages: [] }),
      )
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas('c1')

    expect(await screen.findByText('Cześć! W czym mogę Ci dziś pomóc?')).toBeInTheDocument()
    expect(await screen.findByText('🥗 DIET')).toBeInTheDocument()
  })

  it('renders message history and sends a new message', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/messages')) {
        return Promise.resolve(
          jsonResponse(201, {
            conversation_id: 'c1',
            user_message_id: 'm-user-2',
            assistant_message_id: 'm-assistant-2',
            assistant_content: 'Oto Twój plan.',
          }),
        )
      }
      if (init?.method === undefined) {
        return Promise.resolve(
          jsonResponse(200, {
            conversation_id: 'c1',
            title: 'Dieta',
            categories: ['DIET'],
            status: 'ACTIVE',
            messages: [{ id: 'm1', role: 'USER', content: 'Cześć', created_at: '2026-01-01T10:00:00Z' }],
          }),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas('c1')

    expect(await screen.findByText('Cześć')).toBeInTheDocument()

    await user.type(screen.getByPlaceholderText('Napisz wiadomość…'), 'Zaproponuj plan')
    await user.click(screen.getByRole('button', { name: 'Wyślij' }))

    expect(await screen.findByText('Oto Twój plan.')).toBeInTheDocument()
    expect(screen.getByText('Zaproponuj plan')).toBeInTheDocument()

    const messagesCall = fetchMock.mock.calls.find(([url]) => (url as string).includes('/messages'))
    expect(messagesCall).toBeDefined()
    const body = JSON.parse(messagesCall![1].body as string)
    expect(body).toEqual({ content: 'Zaproponuj plan' })
  })

  it('shows a friendly error when sending to an archived conversation', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/messages')) {
        return Promise.resolve(jsonResponse(409, { code: 'CONFLICT', message: 'conversation is archived' }))
      }
      if (init?.method === undefined) {
        return Promise.resolve(
          jsonResponse(200, {
            conversation_id: 'c1',
            title: 'Dieta',
            categories: ['DIET'],
            status: 'ARCHIVED',
            messages: [{ id: 'm1', role: 'USER', content: 'Cześć', created_at: '2026-01-01T10:00:00Z' }],
          }),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas('c1')

    await screen.findByText('Cześć')
    await user.type(screen.getByPlaceholderText('Napisz wiadomość…'), 'Jeszcze coś')
    await user.click(screen.getByRole('button', { name: 'Wyślij' }))

    expect(
      await screen.findByText('Ta rozmowa jest zarchiwizowana — nie można już do niej pisać.'),
    ).toBeInTheDocument()
  })

  it('shows an error state when the conversation fails to load', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(404, { code: 'NOT_FOUND', message: 'not found' }))
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas('missing-id')

    expect(await screen.findByText('Nie znaleziono rozmowy')).toBeInTheDocument()
    expect(
      await screen.findByText('Nie udało się wczytać tej rozmowy — mogła zostać usunięta.'),
    ).toBeInTheDocument()
  })

  it('disables the composer while a message is in flight', async () => {
    const user = userEvent.setup()
    let resolveSend!: (value: Response) => void
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/messages')) {
        return new Promise<Response>((resolve) => {
          resolveSend = resolve
        })
      }
      if (init?.method === undefined) {
        return Promise.resolve(
          jsonResponse(200, { conversation_id: 'c1', title: 'Dieta', categories: ['DIET'], status: 'ACTIVE', messages: [] }),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas('c1')

    await screen.findByText('🥗 DIET')
    await user.type(screen.getByPlaceholderText('Napisz wiadomość…'), 'Cześć')
    await user.click(screen.getByRole('button', { name: 'Wyślij' }))

    // The user's own bubble appears immediately, before the AI response
    // resolves — not only once the round trip completes.
    expect(await screen.findByText('Cześć')).toBeInTheDocument()
    expect(await screen.findByText('Mycelo pisze odpowiedź…')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Napisz wiadomość…')).toBeDisabled()

    resolveSend(
      jsonResponse(201, {
        conversation_id: 'c1',
        user_message_id: 'u1',
        assistant_message_id: 'a1',
        assistant_content: 'Odpowiedź',
      }),
    )
    await waitFor(() => expect(screen.queryByText('Mycelo pisze odpowiedź…')).not.toBeInTheDocument())
  })

  it('archives the conversation and disables the composer', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/archive')) {
        return Promise.resolve(
          jsonResponse(200, {
            conversation_id: 'c1',
            title: 'Dieta',
            categories: ['DIET'],
            status: 'ARCHIVED',
            messages: [{ id: 'm1', role: 'USER', content: 'Cześć', created_at: '2026-01-01T10:00:00Z' }],
          }),
        )
      }
      if (init?.method === undefined) {
        return Promise.resolve(
          jsonResponse(200, {
            conversation_id: 'c1',
            title: 'Dieta',
            categories: ['DIET'],
            status: 'ACTIVE',
            messages: [{ id: 'm1', role: 'USER', content: 'Cześć', created_at: '2026-01-01T10:00:00Z' }],
          }),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas('c1')

    await user.click(await screen.findByRole('button', { name: 'Archiwizuj rozmowę' }))

    expect(await screen.findByText('Zarchiwizowana')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Archiwizuj rozmowę' })).not.toBeInTheDocument()
    expect(screen.getByPlaceholderText('Napisz wiadomość…')).toBeDisabled()
    expect(
      screen.getByText('Ta rozmowa jest zarchiwizowana — nie można już do niej pisać.'),
    ).toBeInTheDocument()

    const archiveCall = fetchMock.mock.calls.find(([url]) => (url as string).includes('/archive'))
    expect(archiveCall).toBeDefined()
  })

  it('shows a toast when archiving fails (previously a silent failure)', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/archive')) {
        return Promise.resolve(jsonResponse(404, { code: 'NOT_FOUND', message: 'not found' }))
      }
      if (init?.method === undefined) {
        return Promise.resolve(
          jsonResponse(200, { conversation_id: 'c1', title: 'Dieta', categories: ['DIET'], status: 'ACTIVE', messages: [] }),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas('c1')

    await user.click(await screen.findByRole('button', { name: 'Archiwizuj rozmowę' }))

    await waitFor(() =>
      expect(notifyError).toHaveBeenCalledWith('Nie udało się zarchiwizować rozmowy. Spróbuj ponownie.'),
    )
  })

  it('shows a toast when deleting fails (previously a silent failure)', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const fetchMock = vi.fn().mockImplementation((_url: string, init?: RequestInit) => {
      if (init?.method === 'DELETE') {
        return Promise.resolve(jsonResponse(404, { code: 'NOT_FOUND', message: 'not found' }))
      }
      if (init?.method === undefined) {
        return Promise.resolve(
          jsonResponse(200, { conversation_id: 'c1', title: 'Dieta', categories: ['DIET'], status: 'ACTIVE', messages: [] }),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas('c1')

    await user.click(await screen.findByRole('button', { name: 'Usuń rozmowę' }))

    await waitFor(() =>
      expect(notifyError).toHaveBeenCalledWith('Nie udało się usunąć rozmowy. Spróbuj ponownie.'),
    )
  })

  it('shows a disabled composer immediately for an already-archived conversation', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        conversation_id: 'c1',
        title: 'Dieta',
        categories: ['DIET'],
        status: 'ARCHIVED',
        messages: [{ id: 'm1', role: 'USER', content: 'Cześć', created_at: '2026-01-01T10:00:00Z' }],
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas('c1')

    expect(await screen.findByText('Zarchiwizowana')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Archiwizuj rozmowę' })).not.toBeInTheDocument()
    expect(screen.getByPlaceholderText('Napisz wiadomość…')).toBeDisabled()
  })

  it('deletes the conversation after confirmation', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const fetchMock = vi.fn().mockImplementation((_url: string, init?: RequestInit) => {
      if (init?.method === 'DELETE') {
        return Promise.resolve(new Response(null, { status: 204 }))
      }
      if (init?.method === undefined) {
        return Promise.resolve(
          jsonResponse(200, { conversation_id: 'c1', title: 'Dieta', categories: ['DIET'], status: 'ACTIVE', messages: [] }),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas('c1')

    await user.click(await screen.findByRole('button', { name: 'Usuń rozmowę' }))

    await waitFor(() => {
      const deleteCall = fetchMock.mock.calls.find(([, i]) => i?.method === 'DELETE')
      expect(deleteCall).toBeDefined()
    })
  })

  it('does not delete the conversation when the confirmation is dismissed', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    const fetchMock = vi.fn().mockImplementation((_url: string, init?: RequestInit) => {
      if (init?.method === undefined) {
        return Promise.resolve(
          jsonResponse(200, { conversation_id: 'c1', title: 'Dieta', categories: ['DIET'], status: 'ACTIVE', messages: [] }),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas('c1')

    await user.click(await screen.findByRole('button', { name: 'Usuń rozmowę' }))

    const deleteCall = fetchMock.mock.calls.find(([, init]) => init?.method === 'DELETE')
    expect(deleteCall).toBeUndefined()
  })

  it('generates a diet plan and renders it, even with no active conversation', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/generate')) {
        return Promise.resolve(
          jsonResponse(201, {
            plan_id: 'p1',
            user_id: 'u1',
            goal: 'MUSCLE_GAIN',
            diet_type: 'VEGETARIAN',
            duration_days: 3,
            requirements: [],
            days: [
              {
                day_number: 1,
                meals: [
                  { name: 'Owsianka białkowa', calories: 600, protein: 45, carbohydrates: 70, fat: 15, time: '08:00' },
                ],
              },
            ],
            created_at: '2026-01-01T10:00:00Z',
            updated_at: '2026-01-01T10:00:00Z',
          }),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas(undefined)

    await user.click(screen.getByRole('button', { name: 'Generuj plan' }))

    expect(await screen.findByText('Wygenerowany plan')).toBeInTheDocument()
    expect(screen.getByText(/Budowa masy mięśniowej · Wegetariańska · 3 dni/)).toBeInTheDocument()
    expect(screen.getByText(/08:00 · Owsianka białkowa/)).toBeInTheDocument()
    expect(notifyInfo).toHaveBeenCalledWith('Plan wygenerowany! Zobacz go poniżej.')

    const generateCall = fetchMock.mock.calls.find(([url]) => (url as string).includes('/diet-plans/generate'))
    expect(generateCall).toBeDefined()
    const body = JSON.parse(generateCall![1].body as string)
    expect(body).toEqual({ duration_days: 3 })
  })

  it('includes the typed composer text as a requirement hint', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/diet-plans/generate')) {
        return Promise.resolve(
          jsonResponse(201, {
            plan_id: 'p1',
            user_id: 'u1',
            goal: 'WEIGHT_LOSS',
            diet_type: 'STANDARD',
            duration_days: 3,
            requirements: ['wysokobiałkowe śniadania'],
            days: [],
            created_at: '2026-01-01T10:00:00Z',
            updated_at: '2026-01-01T10:00:00Z',
          }),
        )
      }
      if (init?.method === undefined) {
        return Promise.resolve(
          jsonResponse(200, { conversation_id: 'c1', title: 'Dieta', categories: ['DIET'], status: 'ACTIVE', messages: [] }),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas('c1')
    await screen.findByText('🥗 DIET')

    await user.type(screen.getByPlaceholderText('Napisz wiadomość…'), 'wysokobiałkowe śniadania')
    await user.click(screen.getByRole('button', { name: 'Generuj plan' }))

    await screen.findByText('Wygenerowany plan')

    const generateCall = fetchMock.mock.calls.find(([url]) => (url as string).includes('/diet-plans/generate'))
    const body = JSON.parse(generateCall![1].body as string)
    expect(body).toEqual({ duration_days: 3, requirements: ['wysokobiałkowe śniadania'] })
  })

  it('prompts to complete the profile first when generating without one', async () => {
    const user = userEvent.setup()
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(404, { code: 'NOT_FOUND', message: 'no nutrition profile' }))
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas(undefined)

    await user.click(screen.getByRole('button', { name: 'Generuj plan' }))

    await waitFor(() =>
      expect(notifyError).toHaveBeenCalledWith(
        'Uzupełnij najpierw profil żywieniowy (zakładka Profil), żeby wygenerować plan.',
      ),
    )
  })

  it('shows a pending state while a plan is being generated', async () => {
    const user = userEvent.setup()
    let resolveGenerate!: (response: Response) => void
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/generate')) {
        return new Promise<Response>((resolve) => {
          resolveGenerate = resolve
        })
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas(undefined)

    await user.click(screen.getByRole('button', { name: 'Generuj plan' }))

    expect(await screen.findByText('Generowanie planu…')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Generowanie…' })).toBeDisabled()

    resolveGenerate(
      jsonResponse(201, {
        plan_id: 'p1',
        user_id: 'u1',
        goal: 'MUSCLE_GAIN',
        diet_type: 'VEGETARIAN',
        duration_days: 3,
        requirements: [],
        days: [],
        created_at: '2026-01-01T10:00:00Z',
        updated_at: '2026-01-01T10:00:00Z',
      }),
    )

    expect(await screen.findByText('Wygenerowany plan')).toBeInTheDocument()
  })

  it('shows a generic retry message for an unexpected plan-generation failure', async () => {
    const user = userEvent.setup()
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(500, { code: 'INTERNAL_ERROR', message: 'boom' }))
    vi.stubGlobal('fetch', fetchMock)

    renderCanvas(undefined)

    await user.click(screen.getByRole('button', { name: 'Generuj plan' }))

    await waitFor(() =>
      expect(notifyError).toHaveBeenCalledWith('Nie udało się wygenerować planu. Spróbuj ponownie.'),
    )
  })
})
