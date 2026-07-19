import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { DietitianProfileTab } from './DietitianProfileTab'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const BASE_PROFILE = {
  id: 'profile-1',
  user_id: 'u1',
  experience: '5 lat doświadczenia',
  diplomas: ['MSc Dietetics'],
  description: 'Specjalizuję się w redukcji wagi.',
  photos: ['/static/dietitian-photos/a.jpg'],
  created_at: '2026-07-19T00:00:00Z',
}

function renderTab() {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <DietitianProfileTab />
    </QueryClientProvider>,
  )
}

describe('DietitianProfileTab', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads the profile into the form and shows existing photos', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(jsonResponse(200, BASE_PROFILE)),
    )

    renderTab()

    expect(await screen.findByDisplayValue('5 lat doświadczenia')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Specjalizuję się w redukcji wagi.')).toBeInTheDocument()
    expect(screen.getByText('Zdjęcia (1/3)')).toBeInTheDocument()
  })

  it('saves changes to experience/diplomas/description', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((_url: string, options?: RequestInit) => {
      if (options?.method === 'PUT') {
        return Promise.resolve(
          jsonResponse(200, { ...BASE_PROFILE, description: 'Nowy opis.' }),
        )
      }
      return Promise.resolve(jsonResponse(200, BASE_PROFILE))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderTab()
    await screen.findByDisplayValue('5 lat doświadczenia')

    const descriptionField = screen.getByLabelText('Opis')
    await user.clear(descriptionField)
    await user.type(descriptionField, 'Nowy opis.')
    await user.click(screen.getByRole('button', { name: 'Zapisz zmiany' }))

    expect(await screen.findByText('Zapisano ✓')).toBeInTheDocument()
  })

  it('uploads a new photo and disables the button at the 3-photo cap', async () => {
    const user = userEvent.setup()
    const threePhotos = {
      ...BASE_PROFILE,
      photos: ['/static/dietitian-photos/a.jpg', '/static/dietitian-photos/b.jpg', '/static/dietitian-photos/c.jpg'],
    }
    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url.includes('/photos') && options?.method === 'POST') {
        return Promise.resolve(jsonResponse(201, threePhotos))
      }
      return Promise.resolve(jsonResponse(200, BASE_PROFILE))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderTab()
    await screen.findByText('Zdjęcia (1/3)')

    const file = new File(['fake-bytes'], 'photo.jpg', { type: 'image/jpeg' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    await user.upload(input, file)

    expect(await screen.findByText('Zdjęcia (3/3)')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Dodaj zdjęcie' })).toBeDisabled()
  })

  it('removes a photo', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url.includes('/photos/0') && options?.method === 'DELETE') {
        return Promise.resolve(jsonResponse(200, { ...BASE_PROFILE, photos: [] }))
      }
      return Promise.resolve(jsonResponse(200, BASE_PROFILE))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderTab()
    await screen.findByText('Zdjęcia (1/3)')

    await user.click(screen.getByRole('button', { name: 'Usuń zdjęcie' }))

    expect(await screen.findByText('Zdjęcia (0/3)')).toBeInTheDocument()
  })
})
