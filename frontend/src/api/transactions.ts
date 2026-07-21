import { apiFetch } from '@/lib/apiFetch'

export type OfferType = 'PLAN_REVIEW' | 'INDIVIDUAL_PLAN'
export type TransactionStatus = 'UNPAID' | 'PAID'

export interface Transaction {
  id: string
  user_id: string
  dietitian_id: string | null
  offer_type: OfferType
  amount: string
  status: TransactionStatus
  created_at: string
  paid_at: string | null
}

export function getMyTransactionsAsDietitian(): Promise<Transaction[]> {
  return apiFetch('/transactions/me')
}
