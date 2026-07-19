import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
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
})
