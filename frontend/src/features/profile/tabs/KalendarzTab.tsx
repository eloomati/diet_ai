import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CalendarOff } from 'lucide-react'
import { Fragment, useEffect, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import { EmptyState } from '@/components/EmptyState'
import { ApiError } from '@/lib/apiFetch'
import { dietTypeLabel, goalLabel } from '@/lib/profileOptions'
import { cn } from '@/lib/utils'
import { getDietPlan, listDietPlans, rescheduleMeal } from '@/api/dietPlans'
import type { DietDay, DietPlan, DietPlanSummary, Meal } from '@/api/dietPlans'

const DAY_LABELS = ['Pon', 'Wt', 'Śr', 'Czw', 'Pt', 'Sob', 'Ndz']
const BASE_HOUR_START = 7
const BASE_HOUR_END = 21
const ROW_STEP_MINUTES = 30
const NO_TIME = ''

interface DraggedMeal {
  dayNumber: number
  mealName: string
  originTime: string
}

/** `dayNumber: null` means "this column has no plan day at all" (still a
 * trackable hover target, since a drop there is still handled — forced
 * back to the dragged meal's own day, per the same-day-only constraint). */
interface HoverCell {
  dayNumber: number | null
  time: string
}

function rescheduleErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.code === 'BAD_REQUEST') {
    return 'Nie udało się przenieść posiłku — plan mógł się zmienić w międzyczasie.'
  }
  return 'Nie udało się zmienić godziny posiłku. Spróbuj ponownie.'
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('pl-PL', { year: 'numeric', month: 'long', day: 'numeric' })
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
  const endFormatted = end.toLocaleDateString('pl-PL', { day: 'numeric', month: 'long', year: 'numeric' })
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
 * include any meal that falls outside that range, so nothing is hidden. */
function buildHourRows(plan: DietPlan): string[] {
  let minMinutes = BASE_HOUR_START * 60
  let maxMinutes = BASE_HOUR_END * 60
  for (const day of plan.days) {
    for (const meal of day.meals) {
      if (!meal.time) continue
      const [h, m] = meal.time.split(':').map(Number)
      const total = h * 60 + m
      minMinutes = Math.min(minMinutes, Math.floor(total / ROW_STEP_MINUTES) * ROW_STEP_MINUTES)
      maxMinutes = Math.max(maxMinutes, Math.ceil((total + 1) / ROW_STEP_MINUTES) * ROW_STEP_MINUTES)
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
  dayNumber: number
  time: string
  isDragging: boolean
  onDragStart: () => void
  draggable?: boolean
}

function MealChip({ meal, dayNumber, time, isDragging, onDragStart, draggable = true }: MealChipProps) {
  return (
    <div
      data-testid={`meal-day${dayNumber}-${meal.name}`}
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

/** Time-of-day order for the "Ogólny" overview column — meals without a
 * time (still "Bez pory") sort after every timed meal, not intermixed. */
function sortMealsForOverview(meals: Meal[]): Meal[] {
  return [...meals].sort((a, b) => {
    if (a.time && b.time) return a.time.localeCompare(b.time)
    if (a.time) return -1
    if (b.time) return 1
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

  // No separate "auto-select" effect: deriving the effective id directly
  // during render (falling back to the newest plan) means `Select` never
  // flips from uncontrolled (undefined) to controlled once data arrives.
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null)
  const [weekIndex, setWeekIndex] = useState(0)
  const [viewMode, setViewMode] = useState<'szczegolowy' | 'ogolny'>('szczegolowy')
  const effectivePlanId = selectedPlanId ?? plansQuery.data?.[0]?.plan_id ?? null

  const planQuery = useQuery({
    queryKey: ['diet-plan', effectivePlanId],
    queryFn: () => getDietPlan(effectivePlanId!),
    retry: false,
    enabled: !!effectivePlanId,
  })

  // Dragging is pointer-events-based (not native HTML5 drag/drop), matching
  // the mechanic already proven in the approved mockup. The backend's
  // PATCH .../meals can only change a meal's *time* within its existing
  // day — there's no field to move it to a different day — so a cross-day
  // drop is allowed visually (matching the mockup's free-canvas feel) but
  // always resolves back onto the meal's own day, keeping only the new time.
  const [dragging, setDragging] = useState<DraggedMeal | null>(null)
  const [hoverCell, setHoverCell] = useState<HoverCell | null>(null)
  const [confirmation, setConfirmation] = useState<string | null>(null)

  // Refs mirror the drag state so the window-level "pointerup anywhere"
  // safety net (added once on mount) always reads the latest values —
  // an effect re-run per state change would risk a stale closure since
  // hoverCell updates continuously while a drag is in progress.
  const draggingRef = useRef<DraggedMeal | null>(null)
  const hoverCellRef = useRef<HoverCell | null>(null)

  const rescheduleMutation = useMutation({
    mutationFn: (payload: { day_number: number; meal_name: string; new_time: string }) =>
      rescheduleMeal(effectivePlanId!, payload),
    onSuccess: (updatedPlan) => {
      queryClient.setQueryData(['diet-plan', effectivePlanId], updatedPlan)
    },
  })
  const rescheduleMutationRef = useRef(rescheduleMutation)
  rescheduleMutationRef.current = rescheduleMutation

  function finishDrag() {
    const activeDrag = draggingRef.current
    const target = hoverCellRef.current
    if (activeDrag && target && target.time !== activeDrag.originTime) {
      const dayChanged = target.dayNumber !== activeDrag.dayNumber
      rescheduleMutationRef.current.mutate(
        { day_number: activeDrag.dayNumber, meal_name: activeDrag.mealName, new_time: `${target.time}:00` },
        {
          onSuccess: () => {
            setConfirmation(
              dayChanged
                ? `Zmieniono godzinę na ${target.time} — dnia nie można zmienić przez przeciąganie.`
                : `Przeniesiono „${activeDrag.mealName}” na ${target.time}.`,
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

  function handleSelectPlan(planId: string) {
    setSelectedPlanId(planId)
    setWeekIndex(0)
  }

  function startDrag(meal: DraggedMeal) {
    draggingRef.current = meal
    setDragging(meal)
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
    return <p className="text-sm text-destructive">Nie udało się wczytać planów. Spróbuj ponownie.</p>
  }
  if (plansQuery.data.length === 0) {
    return (
      <EmptyState
        icon={CalendarOff}
        message="Brak wygenerowanych planów — wygeneruj plan w czacie, żeby zobaczyć go w kalendarzu."
      />
    )
  }

  const plan = planQuery.data

  // day_number is only ever a relative offset (1..duration_days) from the
  // plan's own creation date — the API has no per-day absolute date. Map it
  // onto real calendar dates (and thus real weekdays) so the grid can show
  // a genuine Mon-Sun week, including days the plan doesn't cover.
  let visibleDates: Date[] = []
  let totalWeeks = 1
  const dayByDateKey = new Map<string, DietDay>()
  if (plan) {
    const planStartDate = startOfDay(new Date(plan.created_at))
    for (const day of plan.days) {
      dayByDateKey.set(dateKey(addDays(planStartDate, day.day_number - 1)), day)
    }
    const firstMonday = startOfWeek(planStartDate)
    const lastDayDate = addDays(planStartDate, plan.duration_days - 1)
    const lastMonday = startOfWeek(lastDayDate)
    totalWeeks = Math.round((lastMonday.getTime() - firstMonday.getTime()) / (7 * 86400000)) + 1
    const visibleWeekStart = addDays(firstMonday, weekIndex * 7)
    visibleDates = Array.from({ length: 7 }, (_, i) => addDays(visibleWeekStart, i))
  }

  const hourRows = plan ? buildHourRows(plan) : []

  return (
    <div className="flex flex-col gap-4">
      <Select value={effectivePlanId ?? undefined} onValueChange={(value) => value && handleSelectPlan(value)}>
        <SelectTrigger className="w-full">
          <SelectValue>
            {(planId: string) => {
              const p = plansQuery.data.find((item) => item.plan_id === planId)
              return p ? planOptionLabel(p) : planId
            }}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {plansQuery.data.map((p) => (
            <SelectItem key={p.plan_id} value={p.plan_id}>
              {planOptionLabel(p)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {planQuery.isPending ? (
        <div className="flex flex-col gap-3" role="status" aria-label="Ładowanie kalendarza…">
          <Skeleton className="h-9 w-full rounded-lg" />
          <Skeleton className="h-72 w-full rounded-xl" />
        </div>
      ) : planQuery.isError ? (
        <p className="text-sm text-destructive">Nie udało się wczytać tego planu.</p>
      ) : plan ? (
        <>
          <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-3">
            <div className="flex items-center gap-1.5">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setWeekIndex((w) => Math.max(0, w - 1))}
                disabled={weekIndex === 0}
              >
                ← Poprzedni tydzień
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setWeekIndex((w) => Math.min(totalWeeks - 1, w + 1))}
                disabled={weekIndex >= totalWeeks - 1}
              >
                Następny tydzień →
              </Button>
            </div>
            <span className="text-[12.5px] font-bold text-muted-foreground">
              {formatWeekRange(visibleDates[0], visibleDates[6])} · {dietTypeLabel(plan.diet_type)}
            </span>
            <label className="flex items-center gap-2 text-[11px] font-bold">
              <span className={cn(viewMode === 'szczegolowy' ? 'text-foreground' : 'text-muted-foreground')}>
                Szczegółowy
              </span>
              <Switch
                size="sm"
                checked={viewMode === 'ogolny'}
                onCheckedChange={(checked) => setViewMode(checked ? 'ogolny' : 'szczegolowy')}
              />
              <span className={cn(viewMode === 'ogolny' ? 'text-foreground' : 'text-muted-foreground')}>Ogólny</span>
            </label>
          </div>

          {viewMode === 'ogolny' ? (
            <div className="grid overflow-hidden rounded-xl border border-border" style={{ gridTemplateColumns: 'repeat(7, 1fr)' }}>
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
                const day = dayByDateKey.get(dateKey(date))
                const mealsHere = day ? sortMealsForOverview(day.meals) : []
                return (
                  <div
                    key={i}
                    data-testid={day ? `overview-day${day.day_number}` : `overview-empty${i}`}
                    className={cn('flex flex-col gap-1 p-1.5', i > 0 && 'border-l border-border')}
                  >
                    {mealsHere.length === 0 ? (
                      <span className="text-[10px] text-muted-foreground">—</span>
                    ) : (
                      mealsHere.map((meal) => (
                        <MealChip
                          key={meal.name}
                          meal={meal}
                          dayNumber={day!.day_number}
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
            <div className="grid min-w-[700px]" style={{ gridTemplateColumns: '88px repeat(7, 1fr)' }}>
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
              <div className="border-b border-border p-2 text-[11px] font-bold text-muted-foreground">Bez pory</div>
              {visibleDates.map((date, i) => {
                const day = dayByDateKey.get(dateKey(date))
                const mealsHere = day ? day.meals.filter((m) => !m.time) : []
                return (
                  <div
                    key={i}
                    data-testid={day ? `cell-day${day.day_number}-none` : `cell-empty${i}-none`}
                    className="border-b border-l border-border p-1.5"
                  >
                    <div className="flex flex-col gap-1">
                      {mealsHere.map((meal) => (
                        <MealChip
                          key={meal.name}
                          meal={meal}
                          dayNumber={day!.day_number}
                          time={NO_TIME}
                          isDragging={dragging?.dayNumber === day!.day_number && dragging.mealName === meal.name}
                          onDragStart={() => startDrag({ dayNumber: day!.day_number, mealName: meal.name, originTime: NO_TIME })}
                        />
                      ))}
                    </div>
                  </div>
                )
              })}

              {hourRows.map((time) => (
                <Fragment key={time}>
                  <div className="border-b border-border p-2 text-[11px] font-bold text-muted-foreground">{time}</div>
                  {visibleDates.map((date, i) => {
                    const day = dayByDateKey.get(dateKey(date))
                    const mealsHere = day ? day.meals.filter((m) => m.time && rowTimeForMeal(m.time) === time) : []
                    const cellDayNumber = day?.day_number ?? null
                    const isHovered = hoverCell?.time === time && hoverCell.dayNumber === cellDayNumber
                    const isForeignDay = !!dragging && cellDayNumber !== dragging.dayNumber
                    return (
                      <div
                        key={i}
                        data-testid={day ? `cell-day${day.day_number}-${time}` : `cell-empty${i}-${time}`}
                        onPointerEnter={() => dragging && setHover({ dayNumber: cellDayNumber, time })}
                        onPointerLeave={() =>
                          hoverCellRef.current?.time === time &&
                          hoverCellRef.current.dayNumber === cellDayNumber &&
                          setHover(null)
                        }
                        className={cn(
                          'min-h-[34px] border-b border-l border-border p-1.5',
                          isHovered && !isForeignDay && 'bg-accent/40 ring-2 ring-inset ring-primary',
                          isHovered && isForeignDay && 'bg-destructive/10 ring-2 ring-inset ring-destructive/50',
                        )}
                      >
                        <div className="flex flex-col gap-1">
                          {mealsHere.map((meal) => (
                            <MealChip
                              key={meal.name}
                              meal={meal}
                              dayNumber={day!.day_number}
                              time={time}
                              isDragging={dragging?.dayNumber === day!.day_number && dragging.mealName === meal.name}
                              onDragStart={() =>
                                startDrag({ dayNumber: day!.day_number, mealName: meal.name, originTime: time })
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

          {rescheduleMutation.isError && (
            <p className="text-[12.5px] font-bold text-destructive">
              {rescheduleErrorMessage(rescheduleMutation.error)}
            </p>
          )}
          {confirmation && <p className="text-[12.5px] font-bold text-secondary-foreground">{confirmation} ✓</p>}
          <p className="text-[11px] text-muted-foreground">
            {viewMode === 'ogolny'
              ? 'To podgląd bez godzin — przełącz na widok szczegółowy, żeby przeciągnięciem zmienić godzinę posiłku.'
              : 'Przeciągnij posiłek, by zmienić godzinę — dnia nie można zmienić przez przeciąganie.'}
          </p>

          {plan.requirements.length > 0 && (
            <p className="text-[11.5px] text-muted-foreground">
              Uwzględnione wskazówki: {plan.requirements.join(', ')}
            </p>
          )}
        </>
      ) : null}
    </div>
  )
}
