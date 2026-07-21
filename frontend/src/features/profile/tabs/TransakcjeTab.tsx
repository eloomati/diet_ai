import { Wallet } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'

import { getMyTransactionsAsDietitian } from '@/api/transactions'
import type { OfferType, TransactionStatus } from '@/api/transactions'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/EmptyState'
import { ApiError } from '@/lib/apiFetch'

const OFFER_LABEL: Record<OfferType, string> = {
  PLAN_REVIEW: 'Ocena wygenerowanego planu',
  INDIVIDUAL_PLAN: 'Indywidualny plan',
}

const STATUS_LABEL: Record<TransactionStatus, string> = {
  UNPAID: 'Nieopłacone',
  PAID: 'Opłacone',
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
  const transactionsQuery = useQuery({
    queryKey: ['my-transactions-as-dietitian'],
    queryFn: getMyTransactionsAsDietitian,
  })

  if (transactionsQuery.isPending) {
    return <p className="text-sm text-muted-foreground">Ładowanie transakcji…</p>
  }

  if (transactionsQuery.isError) {
    return <p className="text-sm text-destructive">{errorMessage(transactionsQuery.error)}</p>
  }

  if (transactionsQuery.data.length === 0) {
    return (
      <EmptyState
        icon={Wallet}
        message="Nie masz jeszcze żadnych transakcji."
      />
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {transactionsQuery.data.map((transaction) => (
        <div
          key={transaction.id}
          className="flex items-center justify-between gap-2 rounded-xl border border-border p-3"
        >
          <div>
            <p className="text-sm font-bold">{OFFER_LABEL[transaction.offer_type]}</p>
            <p className="text-xs text-muted-foreground">
              {new Date(transaction.created_at).toLocaleDateString('pl-PL')} · {transaction.amount} zł
            </p>
          </div>
          <Badge variant={STATUS_VARIANT[transaction.status]}>
            {STATUS_LABEL[transaction.status]}
          </Badge>
        </div>
      ))}
    </div>
  )
}
