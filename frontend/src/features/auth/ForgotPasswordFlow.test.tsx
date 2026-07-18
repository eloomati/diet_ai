import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ForgotPasswordFlow } from './ForgotPasswordFlow'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('ForgotPasswordFlow', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('requests a reset, then confirms it with a new password', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/password-reset/request')) {
        return Promise.resolve(jsonResponse(200, { message: 'ok' }))
      }
      if (url.includes('/password-reset/confirm')) {
        return Promise.resolve(jsonResponse(200, { message: 'Password has been reset successfully.' }))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    const onBackToLogin = vi.fn()
    render(<ForgotPasswordFlow onBackToLogin={onBackToLogin} />)

    await user.type(screen.getByPlaceholderText('ty@przyklad.pl'), 'user@example.com')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Wyślij kod resetujący' })).toBeEnabled())
    await user.click(screen.getByRole('button', { name: 'Wyślij kod resetujący' }))

    expect(await screen.findByLabelText('Kod z e-maila')).toBeInTheDocument()

    await user.type(screen.getByLabelText('Kod z e-maila'), 'raw-reset-token')
    await user.type(screen.getByLabelText('Nowe hasło'), 'NewStrongPass456')
    await user.click(screen.getByRole('button', { name: 'Ustaw nowe hasło' }))

    expect(await screen.findByText('Hasło zostało zmienione. Możesz się teraz zalogować.')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Wróć do logowania' }))
    expect(onBackToLogin).toHaveBeenCalled()
  })

  it('shows an inline error for an invalid/expired reset token', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/password-reset/request')) {
        return Promise.resolve(jsonResponse(200, { message: 'ok' }))
      }
      if (url.includes('/password-reset/confirm')) {
        return Promise.resolve(jsonResponse(400, { code: 'BAD_REQUEST', message: 'invalid token' }))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<ForgotPasswordFlow onBackToLogin={vi.fn()} />)

    await user.type(screen.getByPlaceholderText('ty@przyklad.pl'), 'user@example.com')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Wyślij kod resetujący' })).toBeEnabled())
    await user.click(screen.getByRole('button', { name: 'Wyślij kod resetujący' }))

    await user.type(await screen.findByLabelText('Kod z e-maila'), 'garbage-token')
    await user.type(screen.getByLabelText('Nowe hasło'), 'NewStrongPass456')
    await user.click(screen.getByRole('button', { name: 'Ustaw nowe hasło' }))

    expect(
      await screen.findByText('Kod jest nieprawidłowy, wygasł lub został już użyty.'),
    ).toBeInTheDocument()
  })

  it('jumps straight to the confirm step via "Mam już kod"', async () => {
    const user = userEvent.setup()
    render(<ForgotPasswordFlow onBackToLogin={vi.fn()} />)

    await user.click(screen.getByRole('button', { name: 'Mam już kod →' }))

    expect(screen.getByLabelText('Kod z e-maila')).toBeInTheDocument()
  })
})
