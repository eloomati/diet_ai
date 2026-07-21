import { apiFetch } from '@/lib/apiFetch'

export type OfferType = 'PLAN_REVIEW' | 'INDIVIDUAL_PLAN'
export type TransactionStatus = 'UNPAID' | 'PAID'

export const OFFER_LABEL: Record<OfferType, string> = {
  PLAN_REVIEW: 'Ocena wygenerowanego planu',
  INDIVIDUAL_PLAN: 'Indywidualny plan',
}

/** Mirrors the backend's own fixed `OFFER_PRICES` table (never client-supplied) —
 * shown here only for display before any transaction exists. */
export const OFFER_PRICE: Record<OfferType, string> = {
  PLAN_REVIEW: '49.00',
  INDIVIDUAL_PLAN: '149.00',
}

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

export function getMyPurchases(): Promise<Transaction[]> {
  return apiFetch('/transactions/me/purchases')
}
