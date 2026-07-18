import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { useRef } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from '@/lib/auth'
import { clearTokens } from '@/lib/auth/tokenStore'

import { LeftRail } from './LeftRail'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const noop = () => {}

function LoggedInLeftRail() {
  const { login } = useAuth()
  const didLogin = useRef(false)
  if (!didLogin.current) {
    didLogin.current = true
    void login('user@example.com', 'StrongPass123')
  }
  return (
    <LeftRail
      onProfileClick={noop}
      onCollapse={noop}
      onStartChat={noop}
      onSelectConversation={noop}
      createError={false}
    />
  )
}

function renderLeftRail() {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <LoggedInLeftRail />
      </AuthProvider>
    </QueryClientProvider>,
  )
}

describe('LeftRail conversation history (Etap 3 Stage 4)', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    clearTokens()
  })

  it('shows per-category tag chips and a "+N" overflow badge for 3+ categories', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, { user_id: 'u1', email: 'user@example.com', status: 'ACTIVE', email_verified: true }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      if (url.endsWith('/conversations')) {
        return Promise.resolve(
          jsonResponse(200, [
            {
              conversation_id: 'c1',
              title: 'Plan na tydzień',
              categories: ['DIET', 'BREAKFAST', 'FITNESS', 'RUNNING'],
              status: 'ACTIVE',
              updated_at: '2026-01-01T10:00:00Z',
            },
          ]),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderLeftRail()

    expect(await screen.findByText('🥗 Dieta')).toBeInTheDocument()
    expect(screen.getByText('🍳 Śniadanie')).toBeInTheDocument()
    expect(screen.getByText('+2')).toBeInTheDocument()
    expect(screen.queryByText(/Fitness/)).not.toBeInTheDocument()
  })

  it('sorts conversations by most recently updated first', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, { user_id: 'u1', email: 'user@example.com', status: 'ACTIVE', email_verified: true }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      if (url.endsWith('/conversations')) {
        return Promise.resolve(
          jsonResponse(200, [
            {
              conversation_id: 'old',
              title: 'Starsza rozmowa',
              categories: ['DIET'],
              status: 'ACTIVE',
              updated_at: '2026-01-01T10:00:00Z',
            },
            {
              conversation_id: 'new',
              title: 'Nowsza rozmowa',
              categories: ['DIET'],
              status: 'ACTIVE',
              updated_at: '2026-01-05T10:00:00Z',
            },
          ]),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderLeftRail()

    await screen.findByText('Nowsza rozmowa')
    const titles = screen.getAllByRole('button').map((el) => el.textContent ?? '')
    const conversationTitles = titles.filter((t) => t.includes('rozmowa'))
    expect(conversationTitles[0]).toContain('Nowsza rozmowa')
    expect(conversationTitles[1]).toContain('Starsza rozmowa')
  })

  it('visually mutes an archived conversation and shows an "Archiwum" chip', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve(
          jsonResponse(200, { user_id: 'u1', email: 'user@example.com', status: 'ACTIVE', email_verified: true }),
        )
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
      }
      if (url.endsWith('/conversations')) {
        return Promise.resolve(
          jsonResponse(200, [
            {
              conversation_id: 'c1',
              title: 'Stara dieta',
              categories: ['DIET'],
              status: 'ARCHIVED',
              updated_at: '2026-01-01T10:00:00Z',
            },
          ]),
        )
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderLeftRail()

    expect(await screen.findByText('Archiwum')).toBeInTheDocument()
    const row = screen.getByText('Stara dieta').closest('button')
    expect(row).toHaveClass('opacity-60')
  })
})
