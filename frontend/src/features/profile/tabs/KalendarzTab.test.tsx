import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
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

function twoMealPlan() {
  return {
    ...PLAN_SUMMARY,
    plan_id: 'p1',
    duration_days: 2,
    user_id: 'u1',
    requirements: [],
    days: [
      { day_number: 1, meals: [{ name: 'Owsianka', calories: 500, protein: 30, carbohydrates: 60, fat: 12, time: '08:00' }] },
      { day_number: 2, meals: [{ name: 'Obiad', calories: 700, protein: 40, carbohydrates: 80, fat: 20, time: '12:00' }] },
    ],
    updated_at: '2026-01-15T10:00:00Z',
  }
}

function duplicateMealNamePlan() {
  return {
    ...PLAN_SUMMARY,
    plan_id: 'p1',
    duration_days: 1,
    user_id: 'u1',
    requirements: [],
    days: [
      {
        day_number: 1,
        meals: [
          { name: 'Snack', calories: 200, protein: 10, carbohydrates: 15, fat: 8, time: '07:00' },
          { name: 'Snack', calories: 250, protein: 15, carbohydrates: 20, fat: 10, time: '09:00' },
        ],
      },
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

  it('shows a loading state while the plan list is in flight', async () => {
    let resolveList!: (response: Response) => void
    const fetchMock = vi.fn().mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveList = resolve
        }),
    )
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()

    expect(await screen.findByRole('status', { name: 'Ładowanie planów…' })).toBeInTheDocument()

    resolveList(jsonResponse(200, []))

    expect(
      await screen.findByText('Brak wygenerowanych planów — wygeneruj plan w czacie, żeby zobaczyć go w kalendarzu.'),
    ).toBeInTheDocument()
  })

  it('shows a loading state for the selected plan while it is in flight', async () => {
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

    renderKalendarzTab()

    expect(await screen.findByRole('status', { name: 'Ładowanie kalendarza…' })).toBeInTheDocument()

    resolveDetail(jsonResponse(200, threeDayPlan()))

    expect(await screen.findByTestId('meal-day1-Owsianka')).toBeInTheDocument()
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

    // 2026-01-15 (day 1) is a Thursday, so the 3-day plan (Thu/Fri/Sat)
    // lands entirely within one real week — Pon-Śr and Ndz stay empty.
    expect(await screen.findByText('Czw')).toBeInTheDocument()
    expect(screen.getByText('Pt')).toBeInTheDocument()
    expect(screen.getByText('Sob')).toBeInTheDocument()
    expect(screen.getByText('08:00')).toBeInTheDocument()
    expect(screen.getByText('Bez pory')).toBeInTheDocument()
    expect(screen.getByTestId('meal-day1-Owsianka')).toBeInTheDocument()
    expect(screen.getByTestId('meal-day2-Jajecznica')).toBeInTheDocument()
    expect(screen.getByTestId('meal-day3-Placki')).toBeInTheDocument()
  })

  it('paginates a 10-day plan across real calendar weeks', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/p10')) {
        return Promise.resolve(jsonResponse(200, tenDayPlan()))
      }
      return Promise.resolve(jsonResponse(200, [{ ...PLAN_SUMMARY, plan_id: 'p10', duration_days: 10 }]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()

    // Day 1 (2026-01-15, Thu) through day 4 (2026-01-18, Sun) fall in the
    // first real week (12-18 stycznia); days 5-10 (Mon-Sat) fall entirely
    // in the second (19-25 stycznia) — so this 10-day plan spans exactly
    // two real weeks, not three chunks of 7.
    await screen.findByTestId('meal-day1-Posiłek 1')
    expect(screen.getByText(/12–18 stycznia 2026/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '← Poprzedni tydzień' })).toBeDisabled()
    expect(screen.getByTestId('meal-day4-Posiłek 4')).toBeInTheDocument()
    expect(screen.queryByTestId('meal-day5-Posiłek 5')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Następny tydzień →' }))

    expect(await screen.findByTestId('meal-day5-Posiłek 5')).toBeInTheDocument()
    expect(screen.getByTestId('meal-day10-Posiłek 10')).toBeInTheDocument()
    expect(screen.getByText(/19–25 stycznia 2026/)).toBeInTheDocument()
    expect(screen.queryByTestId('meal-day1-Posiłek 1')).not.toBeInTheDocument()

    // The plan's own data ends here, but the calendar keeps scrolling
    // through a full year regardless — "Next" stays enabled, and the
    // following week simply renders empty rather than being disabled or
    // fabricating meals to fill it.
    expect(screen.getByRole('button', { name: 'Następny tydzień →' })).toBeEnabled()
    await user.click(screen.getByRole('button', { name: 'Następny tydzień →' }))
    expect(await screen.findByText(/26 stycznia – 1 lutego 2026/)).toBeInTheDocument()
    expect(screen.queryByTestId('meal-day10-Posiłek 10')).not.toBeInTheDocument()
  })

  it('allows scrolling forward through empty weeks for a full year past the plan', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/p1')) return Promise.resolve(jsonResponse(200, threeDayPlan()))
      return Promise.resolve(jsonResponse(200, [PLAN_SUMMARY]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()
    await screen.findByTestId('meal-day1-Owsianka')

    // threeDayPlan starts 2026-01-15 (Thu) — first Monday is 2026-01-12.
    // 51 more clicks reaches the 52nd (last) week of the full year, where
    // "Next" finally disables.
    for (let i = 0; i < 51; i++) {
      await user.click(screen.getByRole('button', { name: 'Następny tydzień →' }))
    }
    expect(screen.getByRole('button', { name: 'Następny tydzień →' })).toBeDisabled()
  })

  it('always shows all 7 days of the week, including ones the plan does not cover', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/p1')) {
        return Promise.resolve(jsonResponse(200, twoMealPlan()))
      }
      return Promise.resolve(jsonResponse(200, [{ ...PLAN_SUMMARY, duration_days: 2 }]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()

    // twoMealPlan only has day 1 (Thu) and day 2 (Fri) — Pon/Wt/Śr/Sob/Ndz
    // have no plan data at all, but the week grid still shows all 7.
    await screen.findByTestId('meal-day1-Owsianka')
    expect(screen.getByText('Pon')).toBeInTheDocument()
    expect(screen.getByText('Wt')).toBeInTheDocument()
    expect(screen.getByText('Śr')).toBeInTheDocument()
    expect(screen.getByText('Czw')).toBeInTheDocument()
    expect(screen.getByText('Pt')).toBeInTheDocument()
    expect(screen.getByText('Sob')).toBeInTheDocument()
    expect(screen.getByText('Ndz')).toBeInTheDocument()
  })

  it('always shows the full 07:00-21:00 hour grid, even for hours with no meals', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/p1')) {
        return Promise.resolve(jsonResponse(200, twoMealPlan()))
      }
      return Promise.resolve(jsonResponse(200, [{ ...PLAN_SUMMARY, duration_days: 2 }]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()

    // twoMealPlan only has meals at 08:00 and 12:00 — every other half-hour
    // row in the 07:00-21:00 baseline should still render.
    await screen.findByTestId('meal-day1-Owsianka')
    expect(screen.getByText('07:00')).toBeInTheDocument()
    expect(screen.getByText('07:30')).toBeInTheDocument()
    expect(screen.getByText('09:00')).toBeInTheDocument()
    expect(screen.getByText('15:00')).toBeInTheDocument()
    expect(screen.getByText('20:30')).toBeInTheDocument()
  })

  it("shows the plan's full date span in the picker, not just its start date", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/p1')) {
        return Promise.resolve(jsonResponse(200, threeDayPlan()))
      }
      return Promise.resolve(jsonResponse(200, [PLAN_SUMMARY]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()

    // threeDayPlan starts 2026-01-15 (Thu) and runs 3 days — the picker
    // should read "15-17 stycznia 2026", not just the creation date.
    expect(await screen.findByText(/15–17 stycznia 2026/)).toBeInTheDocument()
  })

  it('shows a compact overview without an hour grid in "Ogólny" view, and back again in "Szczegółowy"', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/p1')) {
        return Promise.resolve(jsonResponse(200, twoMealPlan()))
      }
      return Promise.resolve(jsonResponse(200, [{ ...PLAN_SUMMARY, duration_days: 2 }]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()
    await screen.findByTestId('meal-day1-Owsianka')
    expect(screen.getByText('07:00')).toBeInTheDocument()

    const viewSwitch = screen.getByRole('switch')
    await user.click(viewSwitch)

    expect(screen.getByTestId('meal-day1-Owsianka')).toBeInTheDocument()
    expect(screen.getByTestId('meal-day2-Obiad')).toBeInTheDocument()
    expect(screen.queryByText('07:00')).not.toBeInTheDocument()
    expect(screen.queryByText('Bez pory')).not.toBeInTheDocument()

    await user.click(viewSwitch)
    expect(screen.getByText('07:00')).toBeInTheDocument()
  })

  it('does not allow dragging meals in the "Ogólny" overview', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/p1')) {
        return Promise.resolve(jsonResponse(200, twoMealPlan()))
      }
      return Promise.resolve(jsonResponse(200, [{ ...PLAN_SUMMARY, duration_days: 2 }]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()
    await screen.findByTestId('meal-day1-Owsianka')
    await user.click(screen.getByRole('switch'))

    fireEvent.pointerDown(screen.getByTestId('meal-day1-Owsianka'))
    fireEvent.pointerEnter(screen.getByTestId('overview-day2'))
    fireEvent.pointerUp(window)

    const patchCall = fetchMock.mock.calls.find(([, init]) => (init as RequestInit | undefined)?.method === 'PATCH')
    expect(patchCall).toBeUndefined()
  })

  it('shows an error state when the selected plan fails to load', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/p1')) {
        return Promise.resolve(jsonResponse(500, { code: 'INTERNAL_ERROR', message: 'boom' }))
      }
      return Promise.resolve(jsonResponse(200, [PLAN_SUMMARY]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()

    expect(await screen.findByText('Nie udało się wczytać tego planu.')).toBeInTheDocument()
  })

  it('shows an error state when the plan list fails to load', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(500, { code: 'INTERNAL_ERROR', message: 'boom' }))
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()

    expect(await screen.findByText('Nie udało się wczytać planów. Spróbuj ponownie.')).toBeInTheDocument()
  })

  it('drags a meal to a different time within the same day and persists it', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/diet-plans/p1/meals') && init?.method === 'PATCH') {
        const plan = twoMealPlan()
        plan.days[0].meals[0].time = '12:00'
        return Promise.resolve(jsonResponse(200, plan))
      }
      if (url.includes('/diet-plans/p1')) {
        return Promise.resolve(jsonResponse(200, twoMealPlan()))
      }
      return Promise.resolve(jsonResponse(200, [{ ...PLAN_SUMMARY, duration_days: 2 }]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()
    await screen.findByTestId('meal-day1-Owsianka')

    fireEvent.pointerDown(screen.getByTestId('meal-day1-Owsianka'))
    fireEvent.pointerEnter(screen.getByTestId('cell-day1-12:00'))
    fireEvent.pointerUp(window)

    await waitFor(() => {
      const patchCall = fetchMock.mock.calls.find(([, init]) => init?.method === 'PATCH')
      expect(patchCall).toBeDefined()
    })
    const patchCall = fetchMock.mock.calls.find(([, init]) => init?.method === 'PATCH')
    const body = JSON.parse(patchCall![1].body as string)
    expect(body).toEqual({ day_number: 1, meal_index: 0, new_time: '12:00:00' })

    expect(await screen.findByText(/Przeniesiono „Owsianka” na 12:00/)).toBeInTheDocument()
  })

  it('moves a meal to a different day and time on a cross-day drop', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/diet-plans/p1/meals') && init?.method === 'PATCH') {
        const plan = twoMealPlan()
        plan.days[0].meals = []
        plan.days[1].meals.push({
          name: 'Owsianka',
          calories: 500,
          protein: 30,
          carbohydrates: 60,
          fat: 12,
          time: '13:00',
        })
        return Promise.resolve(jsonResponse(200, plan))
      }
      if (url.includes('/diet-plans/p1')) {
        return Promise.resolve(jsonResponse(200, twoMealPlan()))
      }
      return Promise.resolve(jsonResponse(200, [{ ...PLAN_SUMMARY, duration_days: 2 }]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()
    await screen.findByTestId('meal-day1-Owsianka')

    // Day 2's cell at a *different* time than Owsianka's origin (08:00) —
    // a real cross-day, cross-time drop.
    fireEvent.pointerDown(screen.getByTestId('meal-day1-Owsianka'))
    fireEvent.pointerEnter(screen.getByTestId('cell-day2-13:00'))
    fireEvent.pointerUp(window)

    await waitFor(() => {
      const patchCall = fetchMock.mock.calls.find(([, init]) => init?.method === 'PATCH')
      expect(patchCall).toBeDefined()
    })
    const patchCall = fetchMock.mock.calls.find(([, init]) => init?.method === 'PATCH')
    const body = JSON.parse(patchCall![1].body as string)
    expect(body).toEqual({
      day_number: 1,
      meal_index: 0,
      new_time: '13:00:00',
      new_day_number: 2,
    })

    expect(
      await screen.findByText(/Przeniesiono „Owsianka” na inny dzień, godzina 13:00\./),
    ).toBeInTheDocument()
    expect(await screen.findByTestId('meal-day2-Owsianka')).toBeInTheDocument()
  })

  it('drags the correct meal when two meals on the same day share a name', async () => {
    // AI-generated plans routinely produce two meals named "Snack" on the
    // same day — the drag must identify the target by its position in
    // `day.meals`, not by name, or dragging the second chip would silently
    // reschedule the first one instead.
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/diet-plans/p1/meals') && init?.method === 'PATCH') {
        const plan = duplicateMealNamePlan()
        plan.days[0].meals[1].time = '10:00'
        return Promise.resolve(jsonResponse(200, plan))
      }
      if (url.includes('/diet-plans/p1')) {
        return Promise.resolve(jsonResponse(200, duplicateMealNamePlan()))
      }
      return Promise.resolve(jsonResponse(200, [{ ...PLAN_SUMMARY, duration_days: 1 }]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()
    await screen.findByTestId('cell-day1-09:00')

    const snackChips = screen.getAllByTestId('meal-day1-Snack')
    expect(snackChips).toHaveLength(2)

    fireEvent.pointerDown(snackChips[1])
    fireEvent.pointerEnter(screen.getByTestId('cell-day1-10:00'))
    fireEvent.pointerUp(window)

    await waitFor(() => {
      const patchCall = fetchMock.mock.calls.find(([, reqInit]) => reqInit?.method === 'PATCH')
      expect(patchCall).toBeDefined()
    })
    const patchCall = fetchMock.mock.calls.find(([, reqInit]) => reqInit?.method === 'PATCH')
    const body = JSON.parse(patchCall![1].body as string)
    expect(body).toEqual({ day_number: 1, meal_index: 1, new_time: '10:00:00' })
  })

  it('rejects a drop onto a date the plan does not cover', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/p1')) {
        return Promise.resolve(jsonResponse(200, twoMealPlan()))
      }
      return Promise.resolve(jsonResponse(200, [{ ...PLAN_SUMMARY, duration_days: 2 }]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()
    await screen.findByTestId('meal-day1-Owsianka')

    fireEvent.pointerDown(screen.getByTestId('meal-day1-Owsianka'))
    fireEvent.pointerEnter(screen.getByTestId('cell-empty2-13:00'))
    fireEvent.pointerUp(window)

    const patchCall = fetchMock.mock.calls.find(([, init]) => (init as RequestInit | undefined)?.method === 'PATCH')
    expect(patchCall).toBeUndefined()
    expect(
      await screen.findByText('Posiłek można przenieść tylko na dzień i godzinę w obrębie planu, z którego pochodzi.'),
    ).toBeInTheDocument()
  })

  it('does not persist a drop back onto the same cell', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/diet-plans/p1')) {
        return Promise.resolve(jsonResponse(200, twoMealPlan()))
      }
      return Promise.resolve(jsonResponse(200, [{ ...PLAN_SUMMARY, duration_days: 2 }]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()
    await screen.findByTestId('meal-day1-Owsianka')

    fireEvent.pointerDown(screen.getByTestId('meal-day1-Owsianka'))
    fireEvent.pointerEnter(screen.getByTestId('cell-day1-08:00'))
    fireEvent.pointerUp(window)

    const patchCall = fetchMock.mock.calls.find(([, init]) => (init as RequestInit | undefined)?.method === 'PATCH')
    expect(patchCall).toBeUndefined()
  })

  it('shows a friendly error when the reschedule request fails', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/diet-plans/p1/meals') && init?.method === 'PATCH') {
        return Promise.resolve(jsonResponse(400, { code: 'BAD_REQUEST', message: 'meal not found' }))
      }
      if (url.includes('/diet-plans/p1')) {
        return Promise.resolve(jsonResponse(200, twoMealPlan()))
      }
      return Promise.resolve(jsonResponse(200, [{ ...PLAN_SUMMARY, duration_days: 2 }]))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderKalendarzTab()
    await screen.findByTestId('meal-day1-Owsianka')

    fireEvent.pointerDown(screen.getByTestId('meal-day1-Owsianka'))
    fireEvent.pointerEnter(screen.getByTestId('cell-day1-12:00'))
    fireEvent.pointerUp(window)

    expect(
      await screen.findByText('Nie udało się przenieść posiłku — plan mógł się zmienić w międzyczasie.'),
    ).toBeInTheDocument()
  })

  describe('multi-select plan picker (Etap 3 Stage 2)', () => {
    // p1: 15-17 stycznia (3 days). p2: 20-21 stycznia (2 days) — no overlap
    // with p1. p3: 16 stycznia (1 day) — overlaps p1's 15-17 span.
    const PLAN_A = { ...PLAN_SUMMARY, plan_id: 'p1', created_at: '2026-01-15T10:00:00Z', duration_days: 3 }
    const PLAN_B = { ...PLAN_SUMMARY, plan_id: 'p2', created_at: '2026-01-20T10:00:00Z', duration_days: 2 }
    const PLAN_C = { ...PLAN_SUMMARY, plan_id: 'p3', created_at: '2026-01-16T10:00:00Z', duration_days: 1 }

    function multiPlanFetchMock() {
      return vi.fn().mockImplementation((url: string) => {
        if (url.includes('/diet-plans/p1')) return Promise.resolve(jsonResponse(200, threeDayPlan()))
        if (url.includes('/diet-plans/')) return Promise.resolve(jsonResponse(200, threeDayPlan()))
        return Promise.resolve(jsonResponse(200, [PLAN_A, PLAN_B, PLAN_C]))
      })
    }

    it('selects a second, non-overlapping plan alongside the first', async () => {
      const user = userEvent.setup()
      vi.stubGlobal('fetch', multiPlanFetchMock())

      renderKalendarzTab()
      await screen.findByTestId('meal-day1-Owsianka')

      await user.click(screen.getByTestId('plan-picker-trigger'))
      await user.click(screen.getByTestId('plan-option-p2'))

      expect(screen.queryByText(/Nie można wybrać/)).not.toBeInTheDocument()
      expect(screen.getByTestId('plan-option-p1')).toHaveClass('bg-accent')
      expect(screen.getByTestId('plan-option-p2')).toHaveClass('bg-accent')
      expect(screen.getByTestId('plan-picker-trigger')).toHaveTextContent(/15–17 stycznia 2026.*20–21 stycznia 2026/)
    })

    it('blocks selecting a plan that overlaps an already-selected one', async () => {
      const user = userEvent.setup()
      vi.stubGlobal('fetch', multiPlanFetchMock())

      renderKalendarzTab()
      await screen.findByTestId('meal-day1-Owsianka')

      await user.click(screen.getByTestId('plan-picker-trigger'))
      await user.click(screen.getByTestId('plan-option-p3'))

      expect(await screen.findByText(/Nie można wybrać nakładających się planów/)).toBeInTheDocument()
      expect(screen.getByTestId('plan-option-p3')).not.toHaveClass('bg-accent')
      expect(screen.getByTestId('plan-picker-trigger')).not.toHaveTextContent(/16 stycznia 2026/)
    })

    it('does not allow deselecting the last remaining plan', async () => {
      const user = userEvent.setup()
      vi.stubGlobal('fetch', multiPlanFetchMock())

      renderKalendarzTab()
      await screen.findByTestId('meal-day1-Owsianka')

      await user.click(screen.getByTestId('plan-picker-trigger'))
      // p1 is selected by default — clicking its own checked row again must
      // not clear the selection down to zero.
      await user.click(screen.getByTestId('plan-option-p1'))

      expect(screen.getByTestId('plan-option-p1')).toHaveClass('bg-accent')
      expect(screen.getByTestId('plan-picker-trigger')).toHaveTextContent(/15–17 stycznia 2026/)
    })
  })

  describe('combined week-by-week navigation (Etap 3 Stage 3)', () => {
    // p1: 15-17 stycznia (Thu-Sat), first real week (12-18). p2: 20-21
    // stycznia (Tue-Wed), second real week (19-25) — non-overlapping,
    // adjacent-but-different weeks, so navigating forward one week should
    // swap from p1's meals to p2's with no gap or leftover overlap.
    const PLAN_A_SUMMARY = { ...PLAN_SUMMARY, plan_id: 'p1', created_at: '2026-01-15T10:00:00Z', duration_days: 3 }
    const PLAN_B_SUMMARY = { ...PLAN_SUMMARY, plan_id: 'p2', created_at: '2026-01-20T10:00:00Z', duration_days: 2 }

    function planADetail() {
      return threeDayPlan()
    }
    function planBDetail() {
      return {
        ...PLAN_B_SUMMARY,
        user_id: 'u1',
        requirements: ['wysokobiałkowe'],
        days: [
          { day_number: 1, meals: [{ name: 'Kurczak', calories: 600, protein: 50, carbohydrates: 40, fat: 15, time: '13:00' }] },
          { day_number: 2, meals: [{ name: 'Ryba', calories: 550, protein: 45, carbohydrates: 30, fat: 20, time: '13:00' }] },
        ],
        updated_at: '2026-01-20T10:00:00Z',
      }
    }

    function twoPlanFetchMock() {
      return vi.fn().mockImplementation((url: string) => {
        if (url.includes('/diet-plans/p1')) return Promise.resolve(jsonResponse(200, planADetail()))
        if (url.includes('/diet-plans/p2')) return Promise.resolve(jsonResponse(200, planBDetail()))
        return Promise.resolve(jsonResponse(200, [PLAN_A_SUMMARY, PLAN_B_SUMMARY]))
      })
    }

    it("shows each selected plan's meals in its own week, with no gaps or overlaps", async () => {
      const user = userEvent.setup()
      vi.stubGlobal('fetch', twoPlanFetchMock())

      renderKalendarzTab()
      await screen.findByTestId('meal-day1-Owsianka')

      await user.click(screen.getByTestId('plan-picker-trigger'))
      await user.click(screen.getByTestId('plan-option-p2'))
      await user.click(screen.getByTestId('plan-picker-trigger')) // close the popover

      // Two plans are now active, so testids disambiguate by plan id.
      // Week 1 (12-18 stycznia): only p1's meals.
      expect(screen.getByText(/12–18 stycznia 2026/)).toBeInTheDocument()
      expect(screen.getByTestId('meal-p1-day1-Owsianka')).toBeInTheDocument()
      expect(screen.queryByTestId('meal-p2-day1-Kurczak')).not.toBeInTheDocument()

      await user.click(screen.getByRole('button', { name: 'Następny tydzień →' }))

      // Week 2 (19-25 stycznia): only p2's meals — p1's are gone, not
      // duplicated, and nothing from either plan is missing.
      expect(await screen.findByText(/19–25 stycznia 2026/)).toBeInTheDocument()
      expect(screen.getByTestId('meal-p2-day1-Kurczak')).toBeInTheDocument()
      expect(screen.getByTestId('meal-p2-day2-Ryba')).toBeInTheDocument()
      expect(screen.queryByTestId('meal-p1-day1-Owsianka')).not.toBeInTheDocument()
      expect(screen.queryByTestId('meal-p1-day2-Jajecznica')).not.toBeInTheDocument()
    })

    it('rejects dragging a meal onto a cell that belongs to a different plan', async () => {
      const user = userEvent.setup()
      // p1: 15 stycznia (Thu) only. p2: 16 stycznia (Fri) only — adjacent
      // day, same real week (12-18), non-overlapping. Both plans' cells are
      // visible together in this one week, so a cross-plan drop is
      // actually reachable.
      const adjacentPlanA = { ...PLAN_A_SUMMARY, duration_days: 1 }
      const adjacentPlanB = { ...PLAN_B_SUMMARY, created_at: '2026-01-16T10:00:00Z', duration_days: 1 }
      const fetchMock = vi.fn().mockImplementation((url: string) => {
        if (url.includes('/diet-plans/p1')) {
          return Promise.resolve(
            jsonResponse(200, {
              ...adjacentPlanA,
              user_id: 'u1',
              requirements: [],
              days: [{ day_number: 1, meals: [{ name: 'Owsianka', calories: 500, protein: 30, carbohydrates: 60, fat: 12, time: '08:00' }] }],
              updated_at: '2026-01-15T10:00:00Z',
            }),
          )
        }
        if (url.includes('/diet-plans/p2')) {
          return Promise.resolve(
            jsonResponse(200, {
              ...adjacentPlanB,
              user_id: 'u1',
              requirements: [],
              days: [{ day_number: 1, meals: [{ name: 'Kurczak', calories: 600, protein: 50, carbohydrates: 40, fat: 15, time: '13:00' }] }],
              updated_at: '2026-01-16T10:00:00Z',
            }),
          )
        }
        return Promise.resolve(jsonResponse(200, [adjacentPlanA, adjacentPlanB]))
      })
      vi.stubGlobal('fetch', fetchMock)

      renderKalendarzTab()
      await screen.findByTestId('meal-day1-Owsianka')

      await user.click(screen.getByTestId('plan-picker-trigger'))
      await user.click(screen.getByTestId('plan-option-p2'))
      await screen.findByTestId('meal-p2-day1-Kurczak')

      fireEvent.pointerDown(screen.getByTestId('meal-p1-day1-Owsianka'))
      fireEvent.pointerEnter(screen.getByTestId('cell-p2-day1-13:00'))
      fireEvent.pointerUp(window)

      const patchCall = fetchMock.mock.calls.find(([, init]) => (init as RequestInit | undefined)?.method === 'PATCH')
      expect(patchCall).toBeUndefined()
      // Both meals stay exactly where they started.
      expect(screen.getByTestId('meal-p1-day1-Owsianka')).toBeInTheDocument()
      expect(screen.getByTestId('meal-p2-day1-Kurczak')).toBeInTheDocument()
      expect(
        await screen.findByText('Posiłek można przenieść tylko na dzień i godzinę w obrębie planu, z którego pochodzi.'),
      ).toBeInTheDocument()
    })
  })

  describe('combined export — save then download (Etap 3 Stage 4)', () => {
    function combinedExportFetchMock(saveResponse: () => Promise<Response>) {
      return vi.fn().mockImplementation((url: string, init?: RequestInit) => {
        if (url.includes('/diet-plans/export-combined') && init?.method === 'POST') {
          return saveResponse()
        }
        if (url.includes('/diet-plans/exports-combined/exp-1/download')) {
          return Promise.resolve(new Response(new Blob(['plan_id,day_number\np1,1'], { type: 'text/csv' }), { status: 200 }))
        }
        if (url.includes('/diet-plans/p1')) return Promise.resolve(jsonResponse(200, twoMealPlan()))
        return Promise.resolve(jsonResponse(200, [{ ...PLAN_SUMMARY, duration_days: 2 }]))
      })
    }

    it('"Zapisz" archives the selection without downloading, then "Pobierz" downloads it', async () => {
      const user = userEvent.setup()
      const createObjectURL = vi.fn(() => 'blob:mock-url')
      const revokeObjectURL = vi.fn()
      vi.stubGlobal('URL', { ...URL, createObjectURL, revokeObjectURL })
      const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

      const fetchMock = combinedExportFetchMock(() =>
        Promise.resolve(
          jsonResponse(201, {
            export_id: 'exp-1',
            diet_plan_ids: ['p1'],
            filename: 'combined.csv',
            created_at: '2026-01-15T10:00:00Z',
          }),
        ),
      )
      vi.stubGlobal('fetch', fetchMock)

      renderKalendarzTab()
      await screen.findByTestId('meal-day1-Owsianka')

      expect(screen.queryByRole('button', { name: 'Pobierz' })).not.toBeInTheDocument()
      await user.click(screen.getByRole('button', { name: 'Zapisz' }))

      // Saving alone must not trigger a download.
      expect(await screen.findByText(/Zapisano ✓/)).toBeInTheDocument()
      expect(createObjectURL).not.toHaveBeenCalled()
      const saveCall = fetchMock.mock.calls.find(
        ([url, init]) => (url as string).includes('/diet-plans/export-combined') && (init as RequestInit)?.method === 'POST',
      )
      expect(JSON.parse(saveCall![1].body as string)).toEqual({ plan_ids: ['p1'] })

      await user.click(screen.getByRole('button', { name: 'Pobierz' }))

      await waitFor(() => expect(clickSpy).toHaveBeenCalled())
      expect(createObjectURL).toHaveBeenCalled()
      expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')

      clickSpy.mockRestore()
    })

    it('shows a friendly error when saving the combined export fails', async () => {
      const user = userEvent.setup()
      const fetchMock = combinedExportFetchMock(() =>
        Promise.resolve(jsonResponse(404, { code: 'NOT_FOUND', message: 'plan not found' })),
      )
      vi.stubGlobal('fetch', fetchMock)

      renderKalendarzTab()
      await screen.findByTestId('meal-day1-Owsianka')

      await user.click(screen.getByRole('button', { name: 'Zapisz' }))

      expect(
        await screen.findByText('Nie udało się zapisać — jeden z wybranych planów mógł zostać usunięty.'),
      ).toBeInTheDocument()
      expect(screen.queryByRole('button', { name: 'Pobierz' })).not.toBeInTheDocument()
    })

    it('hides "Pobierz" again once the plan selection changes after saving', async () => {
      const user = userEvent.setup()
      const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
        if (url.includes('/diet-plans/export-combined') && init?.method === 'POST') {
          return Promise.resolve(
            jsonResponse(201, {
              export_id: 'exp-1',
              diet_plan_ids: ['p1'],
              filename: 'combined.csv',
              created_at: '2026-01-15T10:00:00Z',
            }),
          )
        }
        if (url.includes('/diet-plans/p1')) return Promise.resolve(jsonResponse(200, twoMealPlan()))
        if (url.includes('/diet-plans/p2')) {
          return Promise.resolve(
            jsonResponse(200, {
              ...twoMealPlan(),
              plan_id: 'p2',
              created_at: '2026-02-01T10:00:00Z',
              duration_days: 1,
              days: [twoMealPlan().days[0]],
            }),
          )
        }
        return Promise.resolve(
          jsonResponse(200, [
            { ...PLAN_SUMMARY, plan_id: 'p1', duration_days: 2 },
            { ...PLAN_SUMMARY, plan_id: 'p2', created_at: '2026-02-01T10:00:00Z', duration_days: 1 },
          ]),
        )
      })
      vi.stubGlobal('fetch', fetchMock)

      renderKalendarzTab()
      await screen.findByTestId('meal-day1-Owsianka')

      await user.click(screen.getByRole('button', { name: 'Zapisz' }))
      await screen.findByRole('button', { name: 'Pobierz' })

      await user.click(screen.getByTestId('plan-picker-trigger'))
      await user.click(screen.getByTestId('plan-option-p2'))

      expect(screen.queryByRole('button', { name: 'Pobierz' })).not.toBeInTheDocument()
    })
  })
})
