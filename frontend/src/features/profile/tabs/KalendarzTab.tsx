import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import { CalendarOff, Check } from 'lucide-react'
import { Fragment, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import { EmptyState } from '@/components/EmptyState'
import { FieldError } from '@/components/FieldError'
import { ApiError } from '@/lib/apiFetch'
import { dietTypeLabel, goalLabel } from '@/lib/profileOptions'
import { saveBlob } from '@/lib/saveBlob'
import { cn } from '@/lib/utils'
import {
  downloadCombinedDietPlanExport,
  getDietPlan,
  listDietPlans,
  rescheduleMeal,
  saveCombinedDietPlanExport,
} from '@/api/dietPlans'
import type { DietDay, DietPlan, DietPlanSummary, Meal } from '@/api/dietPlans'

const DAY_LABELS = ['Pon', 'Wt', 'Śr', 'Czw', 'Pt', 'Sob', 'Ndz']
const BASE_HOUR_START = 7
const BASE_HOUR_END = 21
const ROW_STEP_MINUTES = 30
const NO_TIME = ''

interface DraggedMeal {
  planId: string
  dayNumber: number
  mealIndex: number
  mealName: string
  originTime: string
}

/** `planId`/`dayNumber`: `null` means "no selected plan covers this date at
 * all" — still a trackable hover target (a drop there is rejected, styled
 * as invalid). A date covered by a *different* plan than the one being
 * dragged is equally invalid — moving a meal across plans isn't supported,
 * only within its own plan (day and/or time). */
interface HoverCell {
  planId: string | null
  dayNumber: number | null
  time: string
}

function rescheduleErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.code === 'BAD_REQUEST') {
    return 'Nie udało się przenieść posiłku — plan mógł się zmienić w międzyczasie.'
  }
  return 'Nie udało się zmienić godziny posiłku. Spróbuj ponownie.'
}

function combinedExportSaveErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.code === 'NOT_FOUND') {
    return 'Nie udało się zapisać — jeden z wybranych planów mógł zostać usunięty.'
  }
  return 'Nie udało się zapisać eksportu. Spróbuj ponownie.'
}

function combinedExportDownloadErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.code === 'NOT_FOUND') {
    return 'Nie udało się pobrać — zapisany eksport mógł zostać usunięty.'
  }
  return 'Nie udało się pobrać pliku. Spróbuj ponownie.'
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('pl-PL', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function planOptionLabel(plan: DietPlanSummary): string {
  return `${planDateRangeLabel(plan)} · ${goalLabel(plan.goal)} · ${plan.duration_days} ${
    plan.duration_days === 1 ? 'dzień' : 'dni'
  }`
}

/** Full span the plan covers ("19–21 lipca 2026"), not just its creation
 * date — a single date reads as ambiguous once a plan covers several days. */
function planDateRangeLabel(plan: DietPlanSummary): string {
  const start = startOfDay(new Date(plan.created_at))
  if (plan.duration_days <= 1) return formatDate(plan.created_at)
  return formatWeekRange(start, addDays(start, plan.duration_days - 1))
}

function startOfDay(date: Date): Date {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  return d
}

function addDays(date: Date, days: number): Date {
  const d = new Date(date)
  d.setDate(d.getDate() + days)
  return d
}

/** A plan's inclusive [start, end] date span, from `created_at` +
 * `duration_days` — the API has no per-plan date range of its own. */
function planDateRange(plan: DietPlanSummary): [Date, Date] {
  const start = startOfDay(new Date(plan.created_at))
  return [start, addDays(start, plan.duration_days - 1)]
}

function rangesOverlap(a: [Date, Date], b: [Date, Date]): boolean {
  return a[0] <= b[1] && b[0] <= a[1]
}

/** Monday of the week containing `date` — `getDay()` is 0=Sun..6=Sat. */
function startOfWeek(date: Date): Date {
  const d = startOfDay(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  return addDays(d, diff)
}

/** Local (not UTC) date key — avoids `toISOString`'s UTC shift near midnight. */
function dateKey(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function formatWeekRange(start: Date, end: Date): string {
  // "12 stycznia" (genitive, via a real day+month call), not "styczeń"
  // (nominative, what {month:'long'} alone would give) — Polish date
  // ranges read naturally in genitive: "12-18 stycznia", not "12-18 styczeń".
  const sameMonth = start.getMonth() === end.getMonth() && start.getFullYear() === end.getFullYear()
  const endFormatted = end.toLocaleDateString('pl-PL', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
  if (sameMonth) {
    return `${start.getDate()}–${endFormatted}`
  }
  const startFormatted = start.toLocaleDateString('pl-PL', { day: 'numeric', month: 'long' })
  return `${startFormatted} – ${endFormatted}`
}

/** Rounds a meal's time down to its 30-minute row. Display-only — never
 * mutates the underlying data. */
function rowTimeForMeal(time: string): string {
  const [h, m] = time.split(':').map(Number)
  const total = Math.floor((h * 60 + m) / ROW_STEP_MINUTES) * ROW_STEP_MINUTES
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
}

/** Always covers 07:00–21:00 (matching the approved mockup) and grows to
 * include any meal that falls outside that range, so nothing is hidden.
 * Takes the flattened days of every currently-selected plan, not a single
 * plan's own — the combined calendar has one shared hour axis. */
function buildHourRows(days: DietDay[]): string[] {
  let minMinutes = BASE_HOUR_START * 60
  let maxMinutes = BASE_HOUR_END * 60
  for (const day of days) {
    for (const meal of day.meals) {
      if (!meal.time) continue
      const [h, m] = meal.time.split(':').map(Number)
      const total = h * 60 + m
      minMinutes = Math.min(minMinutes, Math.floor(total / ROW_STEP_MINUTES) * ROW_STEP_MINUTES)
      maxMinutes = Math.max(
        maxMinutes,
        Math.ceil((total + 1) / ROW_STEP_MINUTES) * ROW_STEP_MINUTES,
      )
    }
  }
  const rows: string[] = []
  for (let t = minMinutes; t < maxMinutes; t += ROW_STEP_MINUTES) {
    rows.push(`${String(Math.floor(t / 60)).padStart(2, '0')}:${String(t % 60).padStart(2, '0')}`)
  }
  return rows
}

interface MealChipProps {
  meal: Meal
  testId: string
  time: string
  isDragging: boolean
  onDragStart: () => void
  draggable?: boolean
}

function MealChip({
  meal,
  testId,
  time,
  isDragging,
  onDragStart,
  draggable = true,
}: MealChipProps) {
  return (
    <div
      data-testid={testId}
      onPointerDown={draggable ? onDragStart : undefined}
      className={cn(
        'rounded-lg bg-card p-1.5 text-[11px] shadow-sm select-none',
        draggable && 'cursor-grab touch-none active:cursor-grabbing',
        isDragging && 'opacity-40',
      )}
    >
      <p className="font-bold">{meal.name}</p>
      <p className="text-muted-foreground">
        {time === NO_TIME ? '' : `${meal.time} · `}
        {meal.calories} kcal
      </p>
    </div>
  )
}

interface IndexedMeal {
  meal: Meal
  idx: number
}

/** Time-of-day order for the "Ogólny" overview column — meals without a
 * time (still "Bez pory") sort after every timed meal, not intermixed.
 * Carries each meal's original index in `day.meals` along through the
 * sort, since that index (not the name) is what identifies the meal to
 * the reschedule API — two meals can share a name (e.g. two "Snack"s). */
function sortMealsForOverview(meals: IndexedMeal[]): IndexedMeal[] {
  return [...meals].sort((a, b) => {
    if (a.meal.time && b.meal.time) return a.meal.time.localeCompare(b.meal.time)
    if (a.meal.time) return -1
    if (b.meal.time) return 1
    return 0
  })
}

export function KalendarzTab() {
  const queryClient = useQueryClient()
  const plansQuery = useQuery({
    queryKey: ['diet-plans', undefined, undefined],
    queryFn: () => listDietPlans(),
    retry: false,
  })

  // No separate "auto-select" effect: deriving the effective selection
  // directly during render (falling back to the newest plan) means the
  // picker never flips from uncontrolled (undefined) to controlled once
  // data arrives.
  const [selectedPlanIds, setSelectedPlanIds] = useState<string[]>([])
  const [pickerOpen, setPickerOpen] = useState(false)
  const [overlapError, setOverlapError] = useState<string | null>(null)
  const [weekIndex, setWeekIndex] = useState(0)
  const [viewMode, setViewMode] = useState<'szczegolowy' | 'ogolny'>('szczegolowy')
  const effectiveSelectedIds =
    selectedPlanIds.length > 0
      ? selectedPlanIds
      : plansQuery.data?.[0]
        ? [plansQuery.data[0].plan_id]
        : []
  // One query per selected plan — the combined calendar merges all of
  // their days into one continuous range (below), rather than showing
  // only the first selected plan as earlier stages did.
  const planQueries = useQueries({
    queries: effectiveSelectedIds.map((id) => ({
      queryKey: ['diet-plan', id],
      queryFn: () => getDietPlan(id),
      retry: false,
    })),
  })
  const plans = planQueries.map((q) => q.data).filter((d): d is DietPlan => !!d)
  const plansPending = planQueries.some((q) => q.isPending)
  const plansErrored = planQueries.some((q) => q.isError)

  // Dragging is pointer-events-based (not native HTML5 drag/drop), matching
  // the mechanic already proven in the approved mockup. A drop onto a cell
  // belonging to a different day *within the same plan* moves the meal
  // there and sets the dropped-on time. A drop onto a date no selected plan
  // covers, or one covered by a *different* plan than the dragged meal's
  // own, is rejected — moving a meal across plans isn't supported.
  const [dragging, setDragging] = useState<DraggedMeal | null>(null)
  const [hoverCell, setHoverCell] = useState<HoverCell | null>(null)
  const [confirmation, setConfirmation] = useState<string | null>(null)
  const [dropRejectedMessage, setDropRejectedMessage] = useState<string | null>(null)

  // Refs mirror the drag state so the window-level "pointerup anywhere"
  // safety net (added once on mount) always reads the latest values —
  // an effect re-run per state change would risk a stale closure since
  // hoverCell updates continuously while a drag is in progress.
  const draggingRef = useRef<DraggedMeal | null>(null)
  const hoverCellRef = useRef<HoverCell | null>(null)

  const rescheduleMutation = useMutation({
    mutationFn: (payload: {
      planId: string
      day_number: number
      meal_index: number
      new_time: string
      new_day_number?: number
    }) => {
      const { planId, ...body } = payload
      return rescheduleMeal(planId, body)
    },
    onSuccess: (updatedPlan, variables) => {
      queryClient.setQueryData(['diet-plan', variables.planId], updatedPlan)
    },
  })
  const rescheduleMutationRef = useRef(rescheduleMutation)
  rescheduleMutationRef.current = rescheduleMutation

  function finishDrag() {
    const activeDrag = draggingRef.current
    const target = hoverCellRef.current
    const validTarget =
      !!activeDrag && !!target && target.planId === activeDrag.planId && target.dayNumber !== null
    const somethingChanged =
      validTarget &&
      (target!.time !== activeDrag!.originTime || target!.dayNumber !== activeDrag!.dayNumber)

    if (activeDrag && target && !validTarget) {
      setDropRejectedMessage(
        'Posiłek można przenieść tylko na dzień i godzinę w obrębie planu, z którego pochodzi.',
      )
    }

    if (activeDrag && validTarget && somethingChanged) {
      const dayChanged = target!.dayNumber !== activeDrag.dayNumber
      rescheduleMutationRef.current.mutate(
        {
          planId: activeDrag.planId,
          day_number: activeDrag.dayNumber,
          meal_index: activeDrag.mealIndex,
          new_time: `${target!.time}:00`,
          ...(dayChanged ? { new_day_number: target!.dayNumber! } : {}),
        },
        {
          onSuccess: () => {
            setDropRejectedMessage(null)
            setConfirmation(
              dayChanged
                ? `Przeniesiono „${activeDrag.mealName}” na inny dzień, godzina ${target!.time}.`
                : `Przeniesiono „${activeDrag.mealName}” na ${target!.time}.`,
            )
          },
        },
      )
    }
    draggingRef.current = null
    hoverCellRef.current = null
    setDragging(null)
    setHoverCell(null)
  }

  useEffect(() => {
    window.addEventListener('pointerup', finishDrag)
    return () => window.removeEventListener('pointerup', finishDrag)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!confirmation) return
    const timeout = setTimeout(() => setConfirmation(null), 3500)
    return () => clearTimeout(timeout)
  }, [confirmation])

  function togglePlanSelection(plan: DietPlanSummary) {
    setOverlapError(null)
    // A previously saved export refers to the *old* selection — once that
    // changes, "Pobierz" would silently download stale data if left enabled.
    setSavedExport(null)
    saveExportMutation.reset()
    downloadExportMutation.reset()
    const isSelected = effectiveSelectedIds.includes(plan.plan_id)

    if (isSelected) {
      if (effectiveSelectedIds.length === 1) return // at least one plan must stay selected
      setSelectedPlanIds(effectiveSelectedIds.filter((id) => id !== plan.plan_id))
      return
    }

    const candidateRange = planDateRange(plan)
    const overlapping = (plansQuery.data ?? []).find(
      (other) =>
        effectiveSelectedIds.includes(other.plan_id) &&
        rangesOverlap(candidateRange, planDateRange(other)),
    )
    if (overlapping) {
      setOverlapError(
        `Nie można wybrać nakładających się planów — "${planOptionLabel(plan)}" nakłada się z "${planOptionLabel(overlapping)}".`,
      )
      return
    }

    setSelectedPlanIds([...effectiveSelectedIds, plan.plan_id])
    setWeekIndex(0)
  }

  // Two explicit steps, not one combined action: "Zapisz" archives the
  // current selection on the server (so it can be re-downloaded later,
  // same as a single plan's own export flow); "Pobierz" only becomes
  // available once something's actually been saved, and downloads that
  // specific saved export.
  const [savedExport, setSavedExport] = useState<{ exportId: string; filename: string } | null>(
    null,
  )

  const downloadExportMutation = useMutation({
    mutationFn: () => downloadCombinedDietPlanExport(savedExport!.exportId),
    onSuccess: (blob) => {
      saveBlob(blob, savedExport!.filename)
    },
  })

  const saveExportMutation = useMutation({
    mutationFn: () => saveCombinedDietPlanExport(effectiveSelectedIds),
    onSuccess: (result) => {
      setSavedExport({ exportId: result.export_id, filename: result.filename })
      downloadExportMutation.reset()
    },
  })

  function startDrag(meal: DraggedMeal) {
    draggingRef.current = meal
    setDragging(meal)
    setDropRejectedMessage(null)
    rescheduleMutationRef.current.reset()
  }

  function setHover(cell: HoverCell | null) {
    hoverCellRef.current = cell
    setHoverCell(cell)
  }

  if (plansQuery.isPending) {
    return (
      <div className="flex flex-col gap-2" role="status" aria-label="Ładowanie planów…">
        <Skeleton className="h-9 w-full rounded-lg" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    )
  }
  if (plansQuery.isError) {
    return (
      <p className="text-sm text-destructive">Nie udało się wczytać planów. Spróbuj ponownie.</p>
    )
  }
  if (plansQuery.data.length === 0) {
    return (
      <EmptyState
        icon={CalendarOff}
        message="Brak wygenerowanych planów — wygeneruj plan w czacie, żeby zobaczyć go w kalendarzu."
      />
    )
  }

  // day_number is only ever a relative offset (1..duration_days) from each
  // plan's own creation date — the API has no per-day absolute date. Map
  // every selected plan's days onto real calendar dates (and thus real
  // weekdays), merged into one shared lookup — non-overlapping selection
  // (enforced in Stage 2) means at most one plan ever claims a given date.
  let visibleDates: Date[] = []
  let totalWeeks = 1
  const dayByDateKey = new Map<string, { planId: string; day: DietDay }>()
  if (plans.length > 0) {
    let earliestMonday: Date | null = null
    let latestPlanMonday: Date | null = null
    for (const p of plans) {
      const planStartDate = startOfDay(new Date(p.created_at))
      for (const day of p.days) {
        dayByDateKey.set(dateKey(addDays(planStartDate, day.day_number - 1)), {
          planId: p.plan_id,
          day,
        })
      }
      const planFirstMonday = startOfWeek(planStartDate)
      const planLastMonday = startOfWeek(addDays(planStartDate, p.duration_days - 1))
      if (!earliestMonday || planFirstMonday < earliestMonday) earliestMonday = planFirstMonday
      if (!latestPlanMonday || planLastMonday > latestPlanMonday) latestPlanMonday = planLastMonday
    }
    const firstMonday = earliestMonday!
    // The combined range always covers at least a full year forward from
    // the earliest selected plan, so the calendar can be browsed well past
    // its actual data — weeks with nothing scheduled just render empty,
    // rather than plans being generated to artificially fill them.
    const YEAR_WEEKS = 52
    const lastMondayByYear = addDays(firstMonday, (YEAR_WEEKS - 1) * 7)
    const lastMonday = latestPlanMonday! > lastMondayByYear ? latestPlanMonday! : lastMondayByYear
    totalWeeks = Math.round((lastMonday.getTime() - firstMonday.getTime()) / (7 * 86400000)) + 1
    const visibleWeekStart = addDays(firstMonday, weekIndex * 7)
    visibleDates = Array.from({ length: 7 }, (_, i) => addDays(visibleWeekStart, i))
  }

  const dietTypes = [...new Set(plans.map((p) => p.diet_type))]
  const allRequirements = [...new Set(plans.flatMap((p) => p.requirements))]
  const hourRows = plans.length > 0 ? buildHourRows(plans.flatMap((p) => p.days)) : []
  // With one plan active, `day_number` alone is a unique, stable testid —
  // unchanged from earlier stages. With two or more, different plans can
  // both have a "day 1" visible in the same real week, so the id needs the
  // owning plan too.
  const multiplePlansActive = plans.length > 1
  function cellTestId(planId: string, dayNumber: number, suffix: string): string {
    return multiplePlansActive
      ? `cell-${planId}-day${dayNumber}-${suffix}`
      : `cell-day${dayNumber}-${suffix}`
  }
  function mealTestId(planId: string, dayNumber: number, mealName: string): string {
    return multiplePlansActive
      ? `meal-${planId}-day${dayNumber}-${mealName}`
      : `meal-day${dayNumber}-${mealName}`
  }
  function overviewTestId(planId: string, dayNumber: number): string {
    return multiplePlansActive ? `overview-${planId}-day${dayNumber}` : `overview-day${dayNumber}`
  }

  return (
    <>
      {(rescheduleMutation.isError || dropRejectedMessage) &&
        createPortal(
          <div
            data-testid="reschedule-banner"
            className="fixed top-6 left-1/2 z-[60] w-[calc(100%-2rem)] max-w-md -translate-x-1/2 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-2.5 shadow-lg"
          >
            <FieldError
              message={
                rescheduleMutation.isError
                  ? rescheduleErrorMessage(rescheduleMutation.error)
                  : dropRejectedMessage!
              }
            />
          </div>,
          document.body,
        )}
      <div className="flex flex-col gap-4">
        <div className="relative">
          <Button
            type="button"
            variant="outline"
            className="w-full justify-between font-normal"
            data-testid="plan-picker-trigger"
            onClick={() => setPickerOpen((wasOpen) => !wasOpen)}
          >
            <span className="truncate">
              {effectiveSelectedIds
                .map((id) => plansQuery.data.find((p) => p.plan_id === id))
                .filter((p): p is DietPlanSummary => !!p)
                .map((p) => planOptionLabel(p))
                .join('  +  ') || 'Wybierz plan'}
            </span>
          </Button>

          {pickerOpen && (
            <div className="absolute top-[calc(100%+6px)] right-0 left-0 z-20 flex flex-col gap-0.5 rounded-2xl border border-border bg-popover p-1.5 shadow-lg">
              <p className="px-2.5 pt-1.5 pb-1 text-[10.5px] font-bold tracking-wide text-muted-foreground uppercase">
                Wybierz plany do wyświetlenia (nienakładające się)
              </p>
              {plansQuery.data.map((p) => {
                const checked = effectiveSelectedIds.includes(p.plan_id)
                return (
                  <button
                    key={p.plan_id}
                    type="button"
                    data-testid={`plan-option-${p.plan_id}`}
                    onClick={() => togglePlanSelection(p)}
                    className={cn(
                      'flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-[13px] font-bold',
                      checked
                        ? 'bg-accent text-accent-foreground'
                        : 'text-foreground hover:bg-accent/60',
                    )}
                  >
                    <span
                      className={cn(
                        'flex size-4 shrink-0 items-center justify-center rounded border',
                        checked
                          ? 'border-primary bg-primary text-primary-foreground'
                          : 'border-border',
                      )}
                    >
                      {checked && <Check className="size-3" />}
                    </span>
                    {planOptionLabel(p)}
                  </button>
                )
              })}
            </div>
          )}
        </div>
        {overlapError && <FieldError message={overlapError} />}

        {plansPending ? (
          <div className="flex flex-col gap-3" role="status" aria-label="Ładowanie kalendarza…">
            <Skeleton className="h-9 w-full rounded-lg" />
            <Skeleton className="h-72 w-full rounded-xl" />
          </div>
        ) : plansErrored ? (
          <p className="text-sm text-destructive">Nie udało się wczytać tego planu.</p>
        ) : plans.length > 0 ? (
          <>
            <span className="text-[12.5px] font-bold text-muted-foreground">
              {formatWeekRange(visibleDates[0], visibleDates[6])}
              {dietTypes.length > 0 && ` · ${dietTypes.map(dietTypeLabel).join(', ')}`}
            </span>
            <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-3">
              <div className="flex items-center gap-1.5">
                <Button
                  type="button"
                  variant="outline"
                  size="xs"
                  onClick={() => setWeekIndex((w) => Math.max(0, w - 1))}
                  disabled={weekIndex === 0}
                >
                  ← Poprzedni tydzień
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="xs"
                  onClick={() => setWeekIndex((w) => Math.min(totalWeeks - 1, w + 1))}
                  disabled={weekIndex >= totalWeeks - 1}
                >
                  Następny tydzień →
                </Button>
              </div>
              <label className="flex items-center gap-2 text-[11px] font-bold">
                <span
                  className={cn(
                    viewMode === 'szczegolowy' ? 'text-foreground' : 'text-muted-foreground',
                  )}
                >
                  Szczegółowy
                </span>
                <Switch
                  size="sm"
                  checked={viewMode === 'ogolny'}
                  onCheckedChange={(checked) => setViewMode(checked ? 'ogolny' : 'szczegolowy')}
                />
                <span
                  className={cn(
                    viewMode === 'ogolny' ? 'text-foreground' : 'text-muted-foreground',
                  )}
                >
                  Ogólny
                </span>
              </label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={saveExportMutation.isPending}
                onClick={() => saveExportMutation.mutate()}
              >
                {saveExportMutation.isPending ? 'Zapisywanie…' : 'Zapisz'}
              </Button>
              {savedExport && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={downloadExportMutation.isPending}
                  onClick={() => downloadExportMutation.mutate()}
                >
                  {downloadExportMutation.isPending ? 'Pobieranie…' : 'Pobierz'}
                </Button>
              )}
            </div>
            {saveExportMutation.isError && (
              <FieldError message={combinedExportSaveErrorMessage(saveExportMutation.error)} />
            )}
            {downloadExportMutation.isError && (
              <FieldError
                message={combinedExportDownloadErrorMessage(downloadExportMutation.error)}
              />
            )}
            {savedExport && !downloadExportMutation.isSuccess && (
              <p className="text-[12.5px] font-bold text-secondary-foreground">
                Zapisano ✓ — kliknij „Pobierz”, aby zapisać plik na dysku.
              </p>
            )}

            {viewMode === 'ogolny' ? (
              <div
                className="grid overflow-hidden rounded-xl border border-border"
                style={{ gridTemplateColumns: 'repeat(7, 1fr)' }}
              >
                {visibleDates.map((date, i) => (
                  <div
                    key={i}
                    className={cn(
                      'border-b border-border bg-muted p-2 text-center text-[12px] font-bold',
                      i > 0 && 'border-l',
                    )}
                  >
                    <div>{DAY_LABELS[i]}</div>
                    <div className="text-[10px] font-normal text-muted-foreground">
                      {date.getDate()}.{String(date.getMonth() + 1).padStart(2, '0')}
                    </div>
                  </div>
                ))}
                {visibleDates.map((date, i) => {
                  const entry = dayByDateKey.get(dateKey(date))
                  const day = entry?.day
                  const mealsHere = day
                    ? sortMealsForOverview(day.meals.map((meal, idx) => ({ meal, idx })))
                    : []
                  return (
                    <div
                      key={i}
                      data-testid={
                        day ? overviewTestId(entry!.planId, day.day_number) : `overview-empty${i}`
                      }
                      className={cn('flex flex-col gap-1 p-1.5', i > 0 && 'border-l border-border')}
                    >
                      {mealsHere.length === 0 ? (
                        <span className="text-[10px] text-muted-foreground">—</span>
                      ) : (
                        mealsHere.map(({ meal, idx }) => (
                          <MealChip
                            key={idx}
                            meal={meal}
                            testId={mealTestId(entry!.planId, day!.day_number, meal.name)}
                            time={meal.time ?? NO_TIME}
                            isDragging={false}
                            onDragStart={() => {}}
                            draggable={false}
                          />
                        ))
                      )}
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-border">
                <div
                  className="grid min-w-[700px]"
                  style={{ gridTemplateColumns: '88px repeat(7, 1fr)' }}
                >
                  <div className="border-b border-border bg-muted p-2" />
                  {visibleDates.map((date, i) => (
                    <div
                      key={i}
                      className="border-b border-l border-border bg-muted p-2 text-center text-[12px] font-bold"
                    >
                      <div>{DAY_LABELS[i]}</div>
                      <div className="text-[10px] font-normal text-muted-foreground">
                        {date.getDate()}.{String(date.getMonth() + 1).padStart(2, '0')}
                      </div>
                    </div>
                  ))}

                  {/* "Bez pory" row — meals with no AI-suggested time; not a
                  valid drop target (the API requires a real new_time). */}
                  <div className="border-b border-border p-2 text-[11px] font-bold text-muted-foreground">
                    Bez pory
                  </div>
                  {visibleDates.map((date, i) => {
                    const entry = dayByDateKey.get(dateKey(date))
                    const day = entry?.day
                    const mealsHere = day
                      ? day.meals
                          .map((meal, idx) => ({ meal, idx }))
                          .filter(({ meal }) => !meal.time)
                      : []
                    return (
                      <div
                        key={i}
                        data-testid={
                          day
                            ? cellTestId(entry!.planId, day.day_number, 'none')
                            : `cell-empty${i}-none`
                        }
                        className="border-b border-l border-border p-1.5"
                      >
                        <div className="flex flex-col gap-1">
                          {mealsHere.map(({ meal, idx }) => (
                            <MealChip
                              key={idx}
                              meal={meal}
                              testId={mealTestId(entry!.planId, day!.day_number, meal.name)}
                              time={NO_TIME}
                              isDragging={
                                dragging?.planId === entry!.planId &&
                                dragging.dayNumber === day!.day_number &&
                                dragging.mealIndex === idx
                              }
                              onDragStart={() =>
                                startDrag({
                                  planId: entry!.planId,
                                  dayNumber: day!.day_number,
                                  mealIndex: idx,
                                  mealName: meal.name,
                                  originTime: NO_TIME,
                                })
                              }
                            />
                          ))}
                        </div>
                      </div>
                    )
                  })}

                  {hourRows.map((time) => (
                    <Fragment key={time}>
                      <div className="border-b border-border p-2 text-[11px] font-bold text-muted-foreground">
                        {time}
                      </div>
                      {visibleDates.map((date, i) => {
                        const entry = dayByDateKey.get(dateKey(date))
                        const day = entry?.day
                        const mealsHere = day
                          ? day.meals
                              .map((meal, idx) => ({ meal, idx }))
                              .filter(({ meal }) => meal.time && rowTimeForMeal(meal.time) === time)
                          : []
                        const cellPlanId = entry?.planId ?? null
                        const cellDayNumber = day?.day_number ?? null
                        const isHovered =
                          hoverCell?.time === time &&
                          hoverCell.dayNumber === cellDayNumber &&
                          hoverCell.planId === cellPlanId
                        const isInvalidDropTarget =
                          !!dragging && (cellPlanId === null || cellPlanId !== dragging.planId)
                        return (
                          <div
                            key={i}
                            data-testid={
                              day
                                ? cellTestId(entry!.planId, day.day_number, time)
                                : `cell-empty${i}-${time}`
                            }
                            onPointerEnter={() =>
                              dragging &&
                              setHover({ planId: cellPlanId, dayNumber: cellDayNumber, time })
                            }
                            onPointerLeave={() =>
                              hoverCellRef.current?.time === time &&
                              hoverCellRef.current.dayNumber === cellDayNumber &&
                              hoverCellRef.current.planId === cellPlanId &&
                              setHover(null)
                            }
                            className={cn(
                              'min-h-[34px] border-b border-l border-border p-1.5',
                              isHovered &&
                                !isInvalidDropTarget &&
                                'bg-accent/40 ring-2 ring-inset ring-primary',
                              isHovered &&
                                isInvalidDropTarget &&
                                'bg-destructive/10 ring-2 ring-inset ring-destructive/50',
                            )}
                          >
                            <div className="flex flex-col gap-1">
                              {mealsHere.map(({ meal, idx }) => (
                                <MealChip
                                  key={idx}
                                  meal={meal}
                                  testId={mealTestId(entry!.planId, day!.day_number, meal.name)}
                                  time={time}
                                  isDragging={
                                    dragging?.planId === entry!.planId &&
                                    dragging.dayNumber === day!.day_number &&
                                    dragging.mealIndex === idx
                                  }
                                  onDragStart={() =>
                                    startDrag({
                                      planId: entry!.planId,
                                      dayNumber: day!.day_number,
                                      mealIndex: idx,
                                      mealName: meal.name,
                                      originTime: time,
                                    })
                                  }
                                />
                              ))}
                            </div>
                          </div>
                        )
                      })}
                    </Fragment>
                  ))}
                </div>
              </div>
            )}

            {confirmation && (
              <p className="text-[12.5px] font-bold text-secondary-foreground">{confirmation} ✓</p>
            )}
            <p className="text-[11px] text-muted-foreground">
              {viewMode === 'ogolny'
                ? 'To podgląd bez godzin — przełącz na widok szczegółowy, żeby przeciągnięciem zmienić dzień lub godzinę posiłku.'
                : 'Przeciągnij posiłek na inną komórkę, by zmienić jego dzień i/lub godzinę.'}
            </p>

            {allRequirements.length > 0 && (
              <p className="text-[11px] text-muted-foreground">
                Uwzględnione wskazówki: {allRequirements.join(', ')}
              </p>
            )}
          </>
        ) : null}
      </div>
    </>
  )
}
