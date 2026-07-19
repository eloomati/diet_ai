import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  approveDietitianApplication,
  getDietitianApplications,
  getUsers,
  rejectDietitianApplication,
} from '@/api/admin'
import type { DietitianApplicationStatus } from '@/api/admin'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ApiError } from '@/lib/apiFetch'
import { notifyError, notifySuccess } from '@/lib/toast'

type StatusFilter = DietitianApplicationStatus | 'ALL'

const STATUS_FILTER_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: 'PENDING', label: 'Oczekujące' },
  { value: 'APPROVED', label: 'Zaakceptowane' },
  { value: 'REJECTED', label: 'Odrzucone' },
  { value: 'ALL', label: 'Wszystkie' },
]

const STATUS_LABEL: Record<string, string> = {
  PENDING: 'Oczekujące',
  APPROVED: 'Zaakceptowane',
  REJECTED: 'Odrzucone',
}

const STATUS_VARIANT: Record<string, 'default' | 'secondary' | 'destructive'> = {
  PENDING: 'secondary',
  APPROVED: 'default',
  REJECTED: 'destructive',
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Coś poszło nie tak. Spróbuj ponownie.'
}

export function DietetycyTab() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('PENDING')

  const applicationsQuery = useQuery({
    queryKey: ['dietitian-applications', statusFilter],
    queryFn: () => getDietitianApplications(statusFilter === 'ALL' ? undefined : statusFilter),
  })

  // Applications only carry `user_id` — reuse the already-fetched (and
  // cached, same queryKey as UzytkownicyTab) user list to show an email
  // instead of a bare UUID, rather than adding a new backend field for it.
  const usersQuery = useQuery({ queryKey: ['admin-users'], queryFn: getUsers })
  const emailByUserId = new Map(usersQuery.data?.map((user) => [user.id, user.email]))

  const approveMutation = useMutation({
    mutationFn: approveDietitianApplication,
    onSuccess: () => {
      notifySuccess('Zgłoszenie zaakceptowane.')
      queryClient.invalidateQueries({ queryKey: ['dietitian-applications'] })
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
    onError: (error) => notifyError(errorMessage(error)),
  })

  const rejectMutation = useMutation({
    mutationFn: rejectDietitianApplication,
    onSuccess: () => {
      notifySuccess('Zgłoszenie odrzucone.')
      queryClient.invalidateQueries({ queryKey: ['dietitian-applications'] })
    },
    onError: (error) => notifyError(errorMessage(error)),
  })

  return (
    <div className="flex flex-col gap-3">
      <Select value={statusFilter} onValueChange={(value: StatusFilter | null) => value && setStatusFilter(value)}>
        <SelectTrigger className="h-7 w-[180px] text-xs">
          <SelectValue>{(value: StatusFilter) => STATUS_FILTER_OPTIONS.find((o) => o.value === value)?.label}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          {STATUS_FILTER_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {applicationsQuery.isPending && (
        <p className="text-sm text-muted-foreground">Ładowanie zgłoszeń…</p>
      )}
      {applicationsQuery.isError && (
        <p className="text-sm text-destructive">{errorMessage(applicationsQuery.error)}</p>
      )}
      {applicationsQuery.isSuccess && applicationsQuery.data.length === 0 && (
        <p className="px-4 py-8 text-center text-sm text-muted-foreground">
          Brak zgłoszeń w tej kategorii.
        </p>
      )}

      {applicationsQuery.data?.map((application) => (
        <div key={application.id} className="rounded-xl border border-border p-4">
          <div className="mb-2 flex items-center justify-between gap-2">
            <p className="font-heading text-sm font-extrabold">
              {emailByUserId.get(application.user_id) ?? application.user_id}
            </p>
            <Badge variant={STATUS_VARIANT[application.status] ?? 'secondary'}>
              {STATUS_LABEL[application.status] ?? application.status}
            </Badge>
          </div>

          <p className="mb-1 text-sm">
            <span className="font-bold text-muted-foreground">Doświadczenie: </span>
            {application.experience}
          </p>
          {application.diplomas.length > 0 && (
            <p className="mb-1 text-sm">
              <span className="font-bold text-muted-foreground">Dyplomy: </span>
              {application.diplomas.join(', ')}
            </p>
          )}
          <p className="mb-3 text-sm">
            <span className="font-bold text-muted-foreground">Opis: </span>
            {application.description}
          </p>

          {application.status === 'PENDING' && (
            <div className="flex gap-2">
              <Button
                size="sm"
                disabled={approveMutation.isPending || rejectMutation.isPending}
                onClick={() => approveMutation.mutate(application.id)}
              >
                Zaakceptuj
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="text-destructive hover:text-destructive"
                disabled={approveMutation.isPending || rejectMutation.isPending}
                onClick={() => rejectMutation.mutate(application.id)}
              >
                Odrzuć
              </Button>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
