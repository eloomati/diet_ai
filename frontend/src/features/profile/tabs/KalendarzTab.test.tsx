import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { KalendarzTab } from './KalendarzTab'

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

function threeDayPlan() {
  return {
    ...PLAN_SUMMARY,
    user_id: 'u1',
    requirements: [],
    days: [
      { day_number: 1, meals: [{ name: 'Owsianka', calories: 500, protein: 30, carbohydrates: 60, fat: 12, time: '08:00' }] },
      { day_number: 2, meals: [{ name: 'Jajecznica', calories: 450, protein: 28, carbohydrates: 20, fat: 30, time: '08:00' }] },
      { day_number: 3, meals: [{ name: 'Placki', calories: 480, protein: 20, carbohydrates: 70, fat: 14, time: null }] },
    ],
    updated_at: '2026-01-15T10:00:00Z',
  }
}

function tenDayPlan() {
  const days = Array.from({ length: 10 }, (_, i) => ({
    day_number: i + 1,
    meals: [{ name: `Posiłek ${i + 1}`, calories: 500, protein: 30, carbohydrates: 60, fat: 12, time: '08:00' }],
  }))
  return { ...PLAN_SUMMARY, plan_id: 'p10', duration_days: 10, user_id: 'u1', requirements: [], days, updated_at: '2026-01-15T10:00:00Z' }
}

function renderKalendarzTab() {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <KalendarzTab />
    </QueryClientProvider>,
  )
}

describe('KalendarzTab', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows an empty state when there are no plans yet', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, []))
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()

    expect(
      await screen.findByText('Brak wygenerowanych planów — wygeneruj plan w czacie, żeby zobaczyć go w kalendarzu.'),
    ).toBeInTheDocument()
  })

  it('auto-selects the most recent plan and renders its weekly grid', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/p1')) {
        return Promise.resolve(jsonResponse(200, threeDayPlan()))
      }
      return Promise.resolve(jsonResponse(200, [PLAN_SUMMARY]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()

    expect(await screen.findByText('Dzień 1')).toBeInTheDocument()
    expect(screen.getByText('Dzień 2')).toBeInTheDocument()
    expect(screen.getByText('Dzień 3')).toBeInTheDocument()
    expect(screen.getByText('08:00')).toBeInTheDocument()
    expect(screen.getByText('Bez pory')).toBeInTheDocument()
    expect(screen.getByText('Owsianka')).toBeInTheDocument()
    expect(screen.getByText('Placki')).toBeInTheDocument()
  })

  it('paginates a 10-day plan across two weeks', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/p10')) {
        return Promise.resolve(jsonResponse(200, tenDayPlan()))
      }
      return Promise.resolve(jsonResponse(200, [{ ...PLAN_SUMMARY, plan_id: 'p10', duration_days: 10 }]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()

    expect(await screen.findByText('Dzień 1')).toBeInTheDocument()
    expect(screen.getByText(/Dni 1-7/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '← Poprzedni tydzień' })).toBeDisabled()
    expect(screen.queryByText('Dzień 8')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Następny tydzień →' }))

    expect(await screen.findByText('Dzień 8')).toBeInTheDocument()
    expect(screen.getByText('Dzień 10')).toBeInTheDocument()
    expect(screen.getByText(/Dni 8-10/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Następny tydzień →' })).toBeDisabled()
    expect(screen.queryByText('Dzień 1')).not.toBeInTheDocument()
  })

  it('shows an error state when the plan list fails to load', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(500, { code: 'INTERNAL_ERROR', message: 'boom' }))
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()

    expect(await screen.findByText('Nie udało się wczytać planów. Spróbuj ponownie.')).toBeInTheDocument()
  })
})
