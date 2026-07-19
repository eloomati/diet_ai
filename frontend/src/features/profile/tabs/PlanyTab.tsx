import { useMutation, useQuery } from '@tanstack/react-query'
import { ClipboardX } from 'lucide-react'
import { useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/EmptyState'
import { FieldError } from '@/components/FieldError'
import { DietPlanCard } from '@/features/dietPlans/DietPlanCard'
import { ApiError } from '@/lib/apiFetch'
import { dietTypeLabel, goalLabel } from '@/lib/profileOptions'
import { downloadDietPlanExport, exportDietPlan, getDietPlan, listDietPlans } from '@/api/dietPlans'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('pl-PL', { year: 'numeric', month: 'long', day: 'numeric' })
}

function listErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.code === 'BAD_REQUEST') {
    return 'Data początkowa musi być wcześniejsza niż data końcowa.'
  }
  return 'Nie udało się wczytać planów. Spróbuj ponownie.'
}

/** Saves a blob to disk via a throwaway `<a download>` — no server-side
 * presigned URL exists (SFTP has no equivalent), so the file arrives as a
 * blob in memory and has to be handed to the browser this way. */
function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

async function exportAndDownloadPlan(planId: string) {
  const { export_id, filename } = await exportDietPlan(planId)
  const blob = await downloadDietPlanExport(planId, export_id)
  saveBlob(blob, filename)
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

  const exportMutation = useMutation({
    mutationFn: exportAndDownloadPlan,
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
        <div className="flex flex-col gap-2" role="status" aria-label="Ładowanie planów…">
          <Skeleton className="h-11 w-full rounded-xl" />
          <Skeleton className="h-11 w-full rounded-xl" />
        </div>
      ) : plansQuery.isError ? (
        <p className="text-sm text-destructive">{listErrorMessage(plansQuery.error)}</p>
      ) : plansQuery.data.length === 0 ? (
        <EmptyState icon={ClipboardX} message="Brak wygenerowanych planów w tym zakresie dat." />
      ) : (
        <ul className="flex flex-col gap-2">
          {plansQuery.data.map((plan) => {
            const isExportingThis = exportMutation.isPending && exportMutation.variables === plan.plan_id
            const exportFailedThis = exportMutation.isError && exportMutation.variables === plan.plan_id
            return (
            <li key={plan.plan_id} className="rounded-xl border border-border">
              <div className="flex items-center gap-2 px-3 py-2.5 hover:bg-muted/60">
                <button
                  onClick={() => toggleExpand(plan.plan_id)}
                  className="flex flex-1 flex-wrap items-center justify-between gap-2 text-left"
                >
                  <span className="text-[13px] font-bold">
                    {goalLabel(plan.goal)} · {dietTypeLabel(plan.diet_type)} · {plan.duration_days}{' '}
                    {plan.duration_days === 1 ? 'dzień' : 'dni'}
                  </span>
                  <span className="text-[12px] text-muted-foreground">{formatDate(plan.created_at)}</span>
                </button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={isExportingThis}
                  onClick={() => exportMutation.mutate(plan.plan_id)}
                >
                  {isExportingThis ? 'Pobieranie…' : 'Pobierz'}
                </Button>
              </div>
              {exportFailedThis && (
                <FieldError message="Nie udało się wyeksportować planu. Spróbuj ponownie." className="px-3 pb-2" />
              )}
              {expandedPlanId === plan.plan_id && (
                <div className="border-t border-border p-3">
                  {expandedPlanQuery.isPending ? (
                    <div className="flex flex-col gap-1.5" role="status" aria-label="Ładowanie szczegółów…">
                      <Skeleton className="h-5 w-2/3 rounded" />
                      <Skeleton className="h-8 w-full rounded-lg" />
                      <Skeleton className="h-8 w-full rounded-lg" />
                    </div>
                  ) : expandedPlanQuery.isError ? (
                    <p className="text-sm text-destructive">Nie udało się wczytać szczegółów planu.</p>
                  ) : (
                    expandedPlanQuery.data && <DietPlanCard plan={expandedPlanQuery.data} />
                  )}
                </div>
              )}
            </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
