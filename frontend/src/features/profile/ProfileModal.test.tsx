import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRef, useState } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from '@/lib/auth'
import { clearTokens } from '@/lib/auth/tokenStore'

import { ProfileModal } from './ProfileModal'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function stubLoggedInFetch(role: string = 'USER') {
  const fetchMock = vi.fn().mockImplementation((url: string) => {
    if (url.includes('/auth/me')) {
      return Promise.resolve(
        jsonResponse(200, {
          user_id: 'u1',
          email: 'user@example.com',
          status: 'ACTIVE',
          email_verified: true,
          role,
        }),
      )
    }
    if (url.includes('/auth/login')) {
      return Promise.resolve(jsonResponse(200, { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
    }
    if (url.includes('/auth/logout')) {
      return Promise.resolve(jsonResponse(200, { message: 'Logged out successfully.' }))
    }
    if (url.includes('/dietitian/applications')) {
      return Promise.resolve(jsonResponse(404, { code: 'NOT_FOUND', message: 'no application yet' }))
    }
    if (url.includes('/transactions/me')) {
      return Promise.resolve(jsonResponse(200, []))
    }
    if (url.includes('/dietitian/profile')) {
      return Promise.resolve(
        jsonResponse(200, {
          id: 'profile-1',
          user_id: 'u1',
          experience: 'exp',
          diplomas: [],
          description: 'desc',
          photos: [],
          created_at: '2026-07-19T00:00:00Z',
        }),
      )
    }
    if (url.includes('/profile')) {
      return Promise.resolve(jsonResponse(404, { code: 'NOT_FOUND', message: 'no profile yet' }))
    }
    if (url.endsWith('/diet-plans')) {
      return Promise.resolve(jsonResponse(200, []))
    }
    return Promise.resolve(jsonResponse(200, {}))
  })
  vi.stubGlobal('fetch', fetchMock)
}

/** Logs in via the real AuthContext before rendering, so the modal opens
 * already-authenticated — same pattern as ProfilTab.test.tsx. `onClose`
 * lets tests observe the auto-close-on-logout behavior deterministically,
 * without depending on Base UI's animated-close unmount timing in jsdom. */
function LoggedInProfileModal({ onClose }: { onClose?: () => void }) {
  const { login } = useAuth()
  const didLogin = useRef(false)
  const [open, setOpen] = useState(true)

  if (!didLogin.current) {
    didLogin.current = true
    void login('user@example.com', 'StrongPass123')
  }

  function handleOpenChange(next: boolean) {
    setOpen(next)
    if (!next) onClose?.()
  }

  return <ProfileModal open={open} onOpenChange={handleOpenChange} />
}

function renderOpenModal(onClose?: () => void) {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <LoggedInProfileModal onClose={onClose} />
      </AuthProvider>
    </QueryClientProvider>,
  )
}

describe('ProfileModal', () => {
  beforeEach(() => {
    clearTokens()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows the Profil tab by default', async () => {
    stubLoggedInFetch()

    renderOpenModal()

    expect(await screen.findByText('Profil żywieniowy')).toBeInTheDocument()
  })

  it('switches to the Plany tab content when clicked', async () => {
    const user = userEvent.setup()
    stubLoggedInFetch()

    renderOpenModal()
    await screen.findByText('Profil żywieniowy')

    await user.click(screen.getByRole('tab', { name: 'Plany' }))

    expect(await screen.findByLabelText('Od')).toBeInTheDocument()
    expect(await screen.findByText('Brak wygenerowanych planów w tym zakresie dat.')).toBeInTheDocument()
  })

  it('switches to the Kalendarz tab content when clicked', async () => {
    const user = userEvent.setup()
    stubLoggedInFetch()

    renderOpenModal()
    await screen.findByText('Profil żywieniowy')

    await user.click(screen.getByRole('tab', { name: 'Kalendarz' }))

    expect(
      await screen.findByText('Brak wygenerowanych planów — wygeneruj plan w czacie, żeby zobaczyć go w kalendarzu.'),
    ).toBeInTheDocument()
  })

  it('closes automatically when the user logs out from inside', async () => {
    const user = userEvent.setup()
    stubLoggedInFetch()
    const onClose = vi.fn()

    renderOpenModal(onClose)
    await screen.findByText('Profil żywieniowy')

    await user.click(screen.getByRole('button', { name: 'Wyloguj się' }))

    await waitFor(() => expect(onClose).toHaveBeenCalled())
  })

  it('hides the Profil dietetyka and Transakcje tabs for a regular USER', async () => {
    stubLoggedInFetch('USER')

    renderOpenModal()
    await screen.findByText('Profil żywieniowy')

    expect(screen.queryByRole('tab', { name: 'Profil dietetyka' })).not.toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: 'Transakcje' })).not.toBeInTheDocument()
  })

  it('shows the Profil dietetyka and Transakcje tabs for a DIET_USER', async () => {
    const user = userEvent.setup()
    stubLoggedInFetch('DIET_USER')

    renderOpenModal()
    await screen.findByText('Profil żywieniowy')

    expect(screen.getByRole('tab', { name: 'Profil dietetyka' })).toBeInTheDocument()

    await user.click(screen.getByRole('tab', { name: 'Transakcje' }))
    expect(
      await screen.findByText('Nie masz jeszcze żadnych transakcji.'),
    ).toBeInTheDocument()
  })
})
