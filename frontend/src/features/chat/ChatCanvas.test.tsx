import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ChatCanvas } from './ChatCanvas'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const noop = () => {}

function renderCanvas(conversationId?: string) {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <ChatCanvas
        leftCollapsed={false}
        rightCollapsed={false}
        onExpandLeft={noop}
        onExpandRight={noop}
        conversationId={conversationId}
      />
    </QueryClientProvider>,
  )
}

describe('ChatCanvas', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows the hero when there is no active conversation', () => {
    renderCanvas(undefined)

    expect(screen.getByText('Cześć! W czym mogę Ci dziś pomóc?')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Wyślij' })).toBeDisabled()
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

    expect(await screen.findByText('Diet AI pisze odpowiedź…')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Napisz wiadomość…')).toBeDisabled()

    resolveSend(
      jsonResponse(201, {
        conversation_id: 'c1',
        user_message_id: 'u1',
        assistant_message_id: 'a1',
        assistant_content: 'Odpowiedź',
      }),
    )
    await waitFor(() => expect(screen.queryByText('Diet AI pisze odpowiedź…')).not.toBeInTheDocument())
  })
})
