import { apiFetch } from '@/lib/apiFetch'
import type { UserRole } from '@/api/auth'

export interface UserSummary {
  id: string
  email: string
  status: string
  role: UserRole
  email_verified: boolean
  created_at: string
}

export interface ChangeUserRoleResponse {
  user_id: string
  email: string
  role: UserRole
}

export interface Page<T> {
  items: T[]
  total: number
}

export interface PageParams {
  limit?: number
  offset?: number
}

function toQueryString(params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) query.set(key, String(value))
  }
  const qs = query.toString()
  return qs ? `?${qs}` : ''
}

export function getUsers(params: PageParams = {}): Promise<Page<UserSummary>> {
  return apiFetch(`/admin/users${toQueryString({ ...params })}`)
}

export function activateUser(userId: string): Promise<UserSummary> {
  return apiFetch(`/admin/users/${userId}/activate`, { method: 'POST' })
}

export function banUser(userId: string): Promise<UserSummary> {
  return apiFetch(`/admin/users/${userId}/ban`, { method: 'POST' })
}

export function deleteUser(userId: string): Promise<void> {
  return apiFetch(`/admin/users/${userId}`, { method: 'DELETE' })
}

export function changeUserRole(userId: string, newRole: UserRole): Promise<ChangeUserRoleResponse> {
  return apiFetch(`/admin/users/${userId}/role`, { method: 'PATCH', body: { new_role: newRole } })
}

export type DietitianApplicationStatus = 'PENDING' | 'APPROVED' | 'REJECTED'

export interface DietitianApplication {
  id: string
  user_id: string
  experience: string
  diplomas: string[]
  description: string
  status: DietitianApplicationStatus
  created_at: string
}

export function getDietitianApplications(
  status?: DietitianApplicationStatus,
  params: PageParams = {},
): Promise<Page<DietitianApplication>> {
  return apiFetch(`/admin/dietitian-applications${toQueryString({ status, ...params })}`)
}

export function approveDietitianApplication(applicationId: string): Promise<DietitianApplication> {
  return apiFetch(`/admin/dietitian-applications/${applicationId}/approve`, { method: 'POST' })
}

export function rejectDietitianApplication(applicationId: string): Promise<DietitianApplication> {
  return apiFetch(`/admin/dietitian-applications/${applicationId}/reject`, { method: 'POST' })
}

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

export function getTransactions(params: PageParams = {}): Promise<Page<Transaction>> {
  return apiFetch(`/admin/transactions${toQueryString({ ...params })}`)
}

export function markTransactionPaid(transactionId: string): Promise<Transaction> {
  return apiFetch(`/admin/transactions/${transactionId}/mark-paid`, { method: 'POST' })
}

export function markTransactionUnpaid(transactionId: string): Promise<Transaction> {
  return apiFetch(`/admin/transactions/${transactionId}/mark-unpaid`, { method: 'POST' })
}
