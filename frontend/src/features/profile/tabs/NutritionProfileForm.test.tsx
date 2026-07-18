import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { NutritionProfileForm } from './NutritionProfileForm'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const EXISTING_PROFILE = {
  profile_id: 'p1',
  user_id: 'u1',
  age: 29,
  height_cm: 187,
  weight_kg: 80,
  activity_level: 'HIGH',
  goal: 'MUSCLE_GAIN',
  diet_type: 'VEGETARIAN',
  weekly_obligations: [],
  created_at: '2026-01-01T10:00:00Z',
  updated_at: '2026-01-01T10:00:00Z',
}

function renderForm() {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <NutritionProfileForm />
    </QueryClientProvider>,
  )
}

describe('NutritionProfileForm', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows a create form when the user has no profile yet, then creates one', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/profile') && (!init || init.method === undefined)) {
        return Promise.resolve(jsonResponse(404, { code: 'NOT_FOUND', message: 'no profile' }))
      }
      if (url.includes('/profile') && init?.method === 'POST') {
        return Promise.resolve(jsonResponse(201, EXISTING_PROFILE))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderForm()

    expect(
      await screen.findByText('Nie masz jeszcze profilu żywieniowego — uzupełnij dane, żeby dostać plany skrojone pod siebie.'),
    ).toBeInTheDocument()

    await user.type(screen.getByLabelText('Wiek'), '29')
    await user.type(screen.getByLabelText('Wzrost (cm)'), '187')
    await user.type(screen.getByLabelText('Waga (kg)'), '80')
    await user.click(screen.getByRole('button', { name: 'Utwórz profil' }))

    expect(await screen.findByText('Zapisano ✓')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Zapisz zmiany' })).toBeInTheDocument()

    const postCall = fetchMock.mock.calls.find(([, init]) => init?.method === 'POST')
    expect(postCall).toBeDefined()
    const body = JSON.parse(postCall![1].body as string)
    expect(body).toMatchObject({ age: 29, height_cm: 187, weight_kg: 80 })
  })

  it('pre-fills the form for an existing profile and saves edits via PUT', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/profile') && init?.method === 'PUT') {
        return Promise.resolve(jsonResponse(200, { ...EXISTING_PROFILE, weight_kg: 82 }))
      }
      if (url.includes('/profile')) {
        return Promise.resolve(jsonResponse(200, EXISTING_PROFILE))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderForm()

    expect(await screen.findByDisplayValue('29')).toBeInTheDocument()
    expect(screen.getByDisplayValue('187')).toBeInTheDocument()
    expect(screen.getByDisplayValue('80')).toBeInTheDocument()

    const weightInput = screen.getByLabelText('Waga (kg)')
    await user.clear(weightInput)
    await user.type(weightInput, '82')
    await user.click(screen.getByRole('button', { name: 'Zapisz zmiany' }))

    await waitFor(() => expect(screen.getByText('Zapisano ✓')).toBeInTheDocument())

    const putCall = fetchMock.mock.calls.find(([, init]) => init?.method === 'PUT')
    expect(putCall).toBeDefined()
    const body = JSON.parse(putCall![1].body as string)
    expect(body).toMatchObject({ weight_kg: 82 })
  })

  it('shows an inline error for an unexpected failure fetching the profile', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(500, { code: 'INTERNAL_ERROR', message: 'Internal server error' }))
    vi.stubGlobal('fetch', fetchMock)

    renderForm()

    expect(await screen.findByText('Internal server error')).toBeInTheDocument()
  })

  it('shows a friendly message for a 422 range-validation failure on save', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/profile') && init?.method === 'POST') {
        return Promise.resolve(jsonResponse(422, { code: 'VALIDATION_ERROR', message: 'age: ensure this value is <= 120' }))
      }
      if (url.includes('/profile')) {
        return Promise.resolve(jsonResponse(404, { code: 'NOT_FOUND', message: 'no profile' }))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderForm()

    await user.type(await screen.findByLabelText('Wiek'), '29')
    await user.type(screen.getByLabelText('Wzrost (cm)'), '187')
    await user.type(screen.getByLabelText('Waga (kg)'), '80')
    await user.click(screen.getByRole('button', { name: 'Utwórz profil' }))

    expect(
      await screen.findByText('Sprawdź poprawność danych: wiek 1-120, wzrost 50-250 cm, waga 20-400 kg.'),
    ).toBeInTheDocument()
  })

  it('resyncs with the server on a 409 conflict (profile already exists)', async () => {
    const user = userEvent.setup()
    let getCount = 0
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/profile') && init?.method === 'POST') {
        return Promise.resolve(jsonResponse(409, { code: 'CONFLICT', message: 'profile already exists' }))
      }
      if (url.includes('/profile')) {
        getCount += 1
        if (getCount === 1) return Promise.resolve(jsonResponse(404, { code: 'NOT_FOUND', message: 'no profile' }))
        return Promise.resolve(jsonResponse(200, EXISTING_PROFILE))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderForm()

    await user.type(await screen.findByLabelText('Wiek'), '29')
    await user.type(screen.getByLabelText('Wzrost (cm)'), '187')
    await user.type(screen.getByLabelText('Waga (kg)'), '80')
    await user.click(screen.getByRole('button', { name: 'Utwórz profil' }))

    expect(
      await screen.findByText('Ten profil już istnieje — dane zostały odświeżone, spróbuj zapisać ponownie.'),
    ).toBeInTheDocument()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Zapisz zmiany' })).toBeInTheDocument())
  })

  it('resyncs with the server on a 404 (profile deleted concurrently) during save', async () => {
    const user = userEvent.setup()
    let getCount = 0
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/profile') && init?.method === 'PUT') {
        return Promise.resolve(jsonResponse(404, { code: 'NOT_FOUND', message: 'profile not found' }))
      }
      if (url.includes('/profile')) {
        getCount += 1
        if (getCount === 1) return Promise.resolve(jsonResponse(200, EXISTING_PROFILE))
        return Promise.resolve(jsonResponse(404, { code: 'NOT_FOUND', message: 'no profile' }))
      }
      return Promise.resolve(jsonResponse(200, {}))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderForm()

    await screen.findByDisplayValue('29')
    await user.click(screen.getByRole('button', { name: 'Zapisz zmiany' }))

    expect(
      await screen.findByText('Ten profil już nie istnieje — uzupełnij dane, żeby utworzyć go od nowa.'),
    ).toBeInTheDocument()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Utwórz profil' })).toBeInTheDocument())
  })
})
