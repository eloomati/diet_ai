import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { PlanyTab } from './PlanyTab'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const PLAN_SUMMARY = {
  plan_id: 'p1',
  goal: 'MUSCLE_GAIN',
  diet_type: 'VEGETARIAN',
  duration_days: 3,
  created_at: '2026-01-15T10:00:00Z',
}

const PLAN_DETAIL = {
  ...PLAN_SUMMARY,
  user_id: 'u1',
  requirements: [],
  days: [
    {
      day_number: 1,
      meals: [{ name: 'Owsianka', calories: 500, protein: 30, carbohydrates: 60, fat: 12, time: '08:00' }],
    },
  ],
  updated_at: '2026-01-15T10:00:00Z',
}

function renderPlanyTab() {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <PlanyTab />
    </QueryClientProvider>,
  )
}

describe('PlanyTab', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('lists diet plans with goal, diet type, duration, and date', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, [PLAN_SUMMARY]))
    vi.stubGlobal('fetch', fetchMock)

    renderPlanyTab()

    expect(
      await screen.findByText('Budowa masy mięśniowej · Wegetariańska · 3 dni'),
    ).toBeInTheDocument()
    expect(screen.getByText(/15 stycznia 2026/)).toBeInTheDocument()
  })

  it('shows a loading state while the plan list is in flight', async () => {
    let resolveList!: (response: Response) => void
    const fetchMock = vi.fn().mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveList = resolve
        }),
    )
    vi.stubGlobal('fetch', fetchMock)

    renderPlanyTab()

    expect(await screen.findByRole('status', { name: 'Ładowanie planów…' })).toBeInTheDocument()

    resolveList(jsonResponse(200, [PLAN_SUMMARY]))

    expect(await screen.findByText('Budowa masy mięśniowej · Wegetariańska · 3 dni')).toBeInTheDocument()
  })

  it('shows an empty state when there are no plans', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, []))
    vi.stubGlobal('fetch', fetchMock)

    renderPlanyTab()

    expect(await screen.findByText('Brak wygenerowanych planów w tym zakresie dat.')).toBeInTheDocument()
  })

  it('shows a friendly error when the date range is invalid', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(400, { code: 'BAD_REQUEST', message: 'from is after to' }))
    vi.stubGlobal('fetch', fetchMock)

    renderPlanyTab()

    expect(
      await screen.findByText('Data początkowa musi być wcześniejsza niż data końcowa.'),
    ).toBeInTheDocument()
  })

  it('refetches with from/to query params when the filter is applied', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, [PLAN_SUMMARY]))
    vi.stubGlobal('fetch', fetchMock)

    renderPlanyTab()
    await screen.findByText('Budowa masy mięśniowej · Wegetariańska · 3 dni')

    fireEvent.change(screen.getByLabelText('Od'), { target: { value: '2026-01-01' } })
    fireEvent.change(screen.getByLabelText('Do'), { target: { value: '2026-01-31' } })
    await user.click(screen.getByRole('button', { name: 'Filtruj' }))

    const filteredCall = fetchMock.mock.calls.find(([url]) =>
      (url as string).includes('from=2026-01-01') && (url as string).includes('to=2026-01-31'),
    )
    expect(filteredCall).toBeDefined()
  })

  it('expands a plan row to show its full detail', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/p1')) {
        return Promise.resolve(jsonResponse(200, PLAN_DETAIL))
      }
      return Promise.resolve(jsonResponse(200, [PLAN_SUMMARY]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderPlanyTab()

    await user.click(await screen.findByText('Budowa masy mięśniowej · Wegetariańska · 3 dni'))

    expect(await screen.findByText('Wygenerowany plan')).toBeInTheDocument()
    expect(screen.getByText(/08:00 · Owsianka/)).toBeInTheDocument()
  })

  it('shows a loading state for plan details while they are in flight', async () => {
    const user = userEvent.setup()
    let resolveDetail!: (response: Response) => void
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/p1')) {
        return new Promise<Response>((resolve) => {
          resolveDetail = resolve
        })
      }
      return Promise.resolve(jsonResponse(200, [PLAN_SUMMARY]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderPlanyTab()
    await user.click(await screen.findByText('Budowa masy mięśniowej · Wegetariańska · 3 dni'))

    expect(await screen.findByRole('status', { name: 'Ładowanie szczegółów…' })).toBeInTheDocument()

    resolveDetail(jsonResponse(200, PLAN_DETAIL))

    expect(await screen.findByText('Wygenerowany plan')).toBeInTheDocument()
  })

  it('exports and downloads a plan when "Pobierz" is clicked', async () => {
    const user = userEvent.setup()
    const createObjectURL = vi.fn(() => 'blob:mock-url')
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('URL', { ...URL, createObjectURL, revokeObjectURL })
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (init?.method === 'POST' && url.includes('/diet-plans/p1/export')) {
        return Promise.resolve(
          jsonResponse(201, {
            export_id: 'e1',
            diet_plan_id: 'p1',
            filename: 'p1-export.csv',
            created_at: '2026-01-15T10:05:00Z',
          }),
        )
      }
      if (url.includes('/diet-plans/p1/exports/e1/download')) {
        return Promise.resolve(new Response(new Blob(['day,meal\n1,Owsianka'], { type: 'text/csv' }), { status: 200 }))
      }
      return Promise.resolve(jsonResponse(200, [PLAN_SUMMARY]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderPlanyTab()
    await user.click(await screen.findByRole('button', { name: 'Pobierz' }))

    await waitFor(() => expect(clickSpy).toHaveBeenCalled())

    expect(fetchMock.mock.calls.some(([u, i]) => i?.method === 'POST' && u.includes('/diet-plans/p1/export'))).toBe(
      true,
    )
    expect(fetchMock.mock.calls.some(([u]) => u.includes('/diet-plans/p1/exports/e1/download'))).toBe(true)
    expect(createObjectURL).toHaveBeenCalled()
    const savedLink = clickSpy.mock.instances[0] as unknown as HTMLAnchorElement
    expect(savedLink.download).toBe('p1-export.csv')
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')

    clickSpy.mockRestore()
  })

  it('shows a friendly error when the export request fails', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (init?.method === 'POST' && url.includes('/diet-plans/p1/export')) {
        return Promise.resolve(jsonResponse(404, { code: 'NOT_FOUND', message: 'plan not found' }))
      }
      return Promise.resolve(jsonResponse(200, [PLAN_SUMMARY]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderPlanyTab()
    await user.click(await screen.findByRole('button', { name: 'Pobierz' }))

    expect(
      await screen.findByText('Nie udało się wyeksportować planu. Spróbuj ponownie.'),
    ).toBeInTheDocument()
  })
})
