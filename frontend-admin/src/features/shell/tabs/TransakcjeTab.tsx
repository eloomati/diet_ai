import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  getTransactions,
  getUsers,
  markTransactionPaid,
  markTransactionUnpaid,
} from '@/api/admin'
import type { OfferType, TransactionStatus } from '@/api/admin'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/apiFetch'
import { notifyError } from '@/lib/toast'

const OFFER_LABEL: Record<OfferType, string> = {
  PLAN_REVIEW: 'Ocena wygenerowanego planu',
  INDIVIDUAL_PLAN: 'Indywidualny plan',
}

const STATUS_VARIANT: Record<TransactionStatus, 'secondary' | 'default'> = {
  UNPAID: 'secondary',
  PAID: 'default',
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Coś poszło nie tak. Spróbuj ponownie.'
}

export function TransakcjeTab() {
  const queryClient = useQueryClient()

  const transactionsQuery = useQuery({ queryKey: ['admin-transactions'], queryFn: getTransactions })
  // Same reuse as DietetycyTab — transactions only carry `user_id`/
  // `dietitian_id`, not emails; the already-cached ['admin-users'] query
  // (shared with UzytkownicyTab) resolves both into something readable.
  const usersQuery = useQuery({ queryKey: ['admin-users'], queryFn: getUsers })
  const emailByUserId = new Map(usersQuery.data?.map((user) => [user.id, user.email]))

  const markPaidMutation = useMutation({
    mutationFn: markTransactionPaid,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-transactions'] }),
    onError: (error) => notifyError(errorMessage(error)),
  })

  const markUnpaidMutation = useMutation({
    mutationFn: markTransactionUnpaid,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-transactions'] }),
    onError: (error) => notifyError(errorMessage(error)),
  })

  if (transactionsQuery.isPending) {
    return <p className="text-sm text-muted-foreground">Ładowanie transakcji…</p>
  }

  if (transactionsQuery.isError) {
    return <p className="text-sm text-destructive">{errorMessage(transactionsQuery.error)}</p>
  }

  if (transactionsQuery.data.length === 0) {
    return (
      <p className="px-4 py-8 text-center text-sm text-muted-foreground">
        Brak transakcji.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-border text-xs font-bold text-muted-foreground uppercase">
            <th className="px-3 py-2">Kupujący</th>
            <th className="px-3 py-2">Dietetyk</th>
            <th className="px-3 py-2">Oferta</th>
            <th className="px-3 py-2">Kwota</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Utworzono</th>
            <th className="px-3 py-2">Akcje</th>
          </tr>
        </thead>
        <tbody>
          {transactionsQuery.data.map((transaction) => (
            <tr key={transaction.id} className="border-b border-border last:border-0">
              <td className="px-3 py-2">{emailByUserId.get(transaction.user_id) ?? transaction.user_id}</td>
              <td className="px-3 py-2">
                {transaction.dietitian_id
                  ? (emailByUserId.get(transaction.dietitian_id) ?? transaction.dietitian_id)
                  : '—'}
              </td>
              <td className="px-3 py-2">{OFFER_LABEL[transaction.offer_type]}</td>
              <td className="px-3 py-2">{transaction.amount} zł</td>
              <td className="px-3 py-2">
                <Badge variant={STATUS_VARIANT[transaction.status]}>{transaction.status}</Badge>
              </td>
              <td className="px-3 py-2 text-muted-foreground">
                {new Date(transaction.created_at).toLocaleDateString('pl-PL')}
              </td>
              <td className="px-3 py-2">
                {transaction.status === 'UNPAID' ? (
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={markPaidMutation.isPending}
                    onClick={() => markPaidMutation.mutate(transaction.id)}
                  >
                    Oznacz jako opłacone
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={markUnpaidMutation.isPending}
                    onClick={() => markUnpaidMutation.mutate(transaction.id)}
                  >
                    Oznacz jako nieopłacone
                  </Button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
