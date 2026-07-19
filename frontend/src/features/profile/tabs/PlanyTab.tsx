import { useQuery } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DietPlanCard } from '@/features/dietPlans/DietPlanCard'
import { ApiError } from '@/lib/apiFetch'
import { dietTypeLabel, goalLabel } from '@/lib/profileOptions'
import { getDietPlan, listDietPlans } from '@/api/dietPlans'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('pl-PL', { year: 'numeric', month: 'long', day: 'numeric' })
}

function listErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.code === 'BAD_REQUEST') {
    return 'Data początkowa musi być wcześniejsza niż data końcowa.'
  }
  return 'Nie udało się wczytać planów. Spróbuj ponownie.'
}

export function PlanyTab() {
  const [fromInput, setFromInput] = useState('')
  const [toInput, setToInput] = useState('')
  const [appliedRange, setAppliedRange] = useState<{ from?: string; to?: string }>({})
  const [expandedPlanId, setExpandedPlanId] = useState<string | null>(null)

  const plansQuery = useQuery({
    queryKey: ['diet-plans', appliedRange.from, appliedRange.to],
    // A 400 (from after to) is a client-input mistake, not worth retrying.
    queryFn: () => listDietPlans(appliedRange),
    retry: false,
  })

  const expandedPlanQuery = useQuery({
    queryKey: ['diet-plan', expandedPlanId],
    queryFn: () => getDietPlan(expandedPlanId!),
    enabled: !!expandedPlanId,
  })

  function handleFilter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setAppliedRange({ from: fromInput || undefined, to: toInput || undefined })
  }

  function toggleExpand(planId: string) {
    setExpandedPlanId((current) => (current === planId ? null : planId))
  }

  return (
    <div className="flex flex-col gap-4">
      <form className="flex flex-wrap items-end gap-2" onSubmit={handleFilter}>
        <div>
          <label htmlFor="plans-from" className="mb-1 block text-xs font-bold text-muted-foreground">
            Od
          </label>
          <Input id="plans-from" type="date" value={fromInput} onChange={(event) => setFromInput(event.target.value)} />
        </div>
        <div>
          <label htmlFor="plans-to" className="mb-1 block text-xs font-bold text-muted-foreground">
            Do
          </label>
          <Input id="plans-to" type="date" value={toInput} onChange={(event) => setToInput(event.target.value)} />
        </div>
        <Button type="submit" variant="outline">
          Filtruj
        </Button>
      </form>

      {plansQuery.isPending ? (
        <p className="text-sm text-muted-foreground">Ładowanie planów…</p>
      ) : plansQuery.isError ? (
        <p className="text-sm text-destructive">{listErrorMessage(plansQuery.error)}</p>
      ) : plansQuery.data.length === 0 ? (
        <p className="text-sm text-muted-foreground">Brak wygenerowanych planów w tym zakresie dat.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {plansQuery.data.map((plan) => (
            <li key={plan.plan_id} className="rounded-xl border border-border">
              <button
                onClick={() => toggleExpand(plan.plan_id)}
                className="flex w-full flex-wrap items-center justify-between gap-2 px-3 py-2.5 text-left hover:bg-muted/60"
              >
                <span className="text-[13px] font-bold">
                  {goalLabel(plan.goal)} · {dietTypeLabel(plan.diet_type)} · {plan.duration_days}{' '}
                  {plan.duration_days === 1 ? 'dzień' : 'dni'}
                </span>
                <span className="text-[12px] text-muted-foreground">{formatDate(plan.created_at)}</span>
              </button>
              {expandedPlanId === plan.plan_id && (
                <div className="border-t border-border p-3">
                  {expandedPlanQuery.isPending ? (
                    <p className="text-sm text-muted-foreground">Ładowanie szczegółów…</p>
                  ) : expandedPlanQuery.isError ? (
                    <p className="text-sm text-destructive">Nie udało się wczytać szczegółów planu.</p>
                  ) : (
                    expandedPlanQuery.data && <DietPlanCard plan={expandedPlanQuery.data} />
                  )}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
