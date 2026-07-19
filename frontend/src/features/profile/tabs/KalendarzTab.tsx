import { useQuery } from '@tanstack/react-query'
import { Fragment, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { dietTypeLabel, goalLabel } from '@/lib/profileOptions'
import { getDietPlan, listDietPlans } from '@/api/dietPlans'
import type { DietDay, DietPlanSummary } from '@/api/dietPlans'

const WEEK_SIZE = 7
const NO_TIME = ''

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('pl-PL', { year: 'numeric', month: 'long', day: 'numeric' })
}

function planOptionLabel(plan: DietPlanSummary): string {
  return `${formatDate(plan.created_at)} · ${goalLabel(plan.goal)} · ${plan.duration_days} ${
    plan.duration_days === 1 ? 'dzień' : 'dni'
  }`
}

function buildTimeRows(days: DietDay[]): string[] {
  const times = new Set<string>()
  let hasNoTime = false
  for (const day of days) {
    for (const meal of day.meals) {
      if (meal.time) times.add(meal.time)
      else hasNoTime = true
    }
  }
  const sorted = [...times].sort()
  return hasNoTime ? [...sorted, NO_TIME] : sorted
}

export function KalendarzTab() {
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
  const effectivePlanId = selectedPlanId ?? plansQuery.data?.[0]?.plan_id ?? null

  const planQuery = useQuery({
    queryKey: ['diet-plan', effectivePlanId],
    queryFn: () => getDietPlan(effectivePlanId!),
    retry: false,
    enabled: !!effectivePlanId,
  })

  function handleSelectPlan(planId: string) {
    setSelectedPlanId(planId)
    setWeekIndex(0)
  }

  if (plansQuery.isPending) {
    return <p className="text-sm text-muted-foreground">Ładowanie planów…</p>
  }
  if (plansQuery.isError) {
    return <p className="text-sm text-destructive">Nie udało się wczytać planów. Spróbuj ponownie.</p>
  }
  if (plansQuery.data.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Brak wygenerowanych planów — wygeneruj plan w czacie, żeby zobaczyć go w kalendarzu.
      </p>
    )
  }

  const days = planQuery.data?.days ?? []
  const totalWeeks = Math.max(1, Math.ceil(days.length / WEEK_SIZE))
  const visibleDays = days.slice(weekIndex * WEEK_SIZE, weekIndex * WEEK_SIZE + WEEK_SIZE)
  const timeRows = buildTimeRows(visibleDays)

  return (
    <div className="flex flex-col gap-4">
      <Select value={effectivePlanId ?? undefined} onValueChange={(value) => value && handleSelectPlan(value)}>
        <SelectTrigger className="w-full">
          <SelectValue>
            {(planId: string) => {
              const plan = plansQuery.data.find((p) => p.plan_id === planId)
              return plan ? planOptionLabel(plan) : planId
            }}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {plansQuery.data.map((plan) => (
            <SelectItem key={plan.plan_id} value={plan.plan_id}>
              {planOptionLabel(plan)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {planQuery.isPending ? (
        <p className="text-sm text-muted-foreground">Ładowanie kalendarza…</p>
      ) : planQuery.isError ? (
        <p className="text-sm text-destructive">Nie udało się wczytać tego planu.</p>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setWeekIndex((w) => Math.max(0, w - 1))}
              disabled={weekIndex === 0}
            >
              ← Poprzedni tydzień
            </Button>
            <span className="text-[12.5px] font-bold text-muted-foreground">
              Dni {weekIndex * WEEK_SIZE + 1}-{weekIndex * WEEK_SIZE + visibleDays.length} ·{' '}
              {dietTypeLabel(planQuery.data.diet_type)}
            </span>
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

          <div className="overflow-x-auto rounded-xl border border-border">
            <div
              className="grid min-w-[560px]"
              style={{ gridTemplateColumns: `88px repeat(${visibleDays.length}, 1fr)` }}
            >
              <div className="border-b border-border bg-muted p-2" />
              {visibleDays.map((day) => (
                <div
                  key={day.day_number}
                  className="border-b border-l border-border bg-muted p-2 text-center text-[12px] font-bold"
                >
                  Dzień {day.day_number}
                </div>
              ))}

              {timeRows.map((time) => (
                <Fragment key={time || 'none'}>
                  <div className="border-b border-border p-2 text-[11px] font-bold text-muted-foreground">
                    {time || 'Bez pory'}
                  </div>
                  {visibleDays.map((day) => {
                    const meal = day.meals.find((m) => (m.time ?? NO_TIME) === time)
                    return (
                      <div key={`${day.day_number}-${time || 'none'}`} className="border-b border-l border-border p-1.5">
                        {meal && (
                          <div className="rounded-lg bg-card p-1.5 text-[11px] shadow-sm">
                            <p className="font-bold">{meal.name}</p>
                            <p className="text-muted-foreground">{meal.calories} kcal</p>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </Fragment>
              ))}
            </div>
          </div>

          {planQuery.data.requirements.length > 0 && (
            <p className="text-[11.5px] text-muted-foreground">
              Uwzględnione wskazówki: {planQuery.data.requirements.join(', ')}
            </p>
          )}
        </>
      )}
    </div>
  )
}
