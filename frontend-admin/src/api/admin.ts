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

export function getUsers(): Promise<UserSummary[]> {
  return apiFetch('/admin/users')
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
): Promise<DietitianApplication[]> {
  const query = status ? `?status=${status}` : ''
  return apiFetch(`/admin/dietitian-applications${query}`)
}

export function approveDietitianApplication(applicationId: string): Promise<DietitianApplication> {
  return apiFetch(`/admin/dietitian-applications/${applicationId}/approve`, { method: 'POST' })
}

export function rejectDietitianApplication(applicationId: string): Promise<DietitianApplication> {
  return apiFetch(`/admin/dietitian-applications/${applicationId}/reject`, { method: 'POST' })
}
