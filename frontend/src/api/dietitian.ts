import { apiFetch } from '@/lib/apiFetch'

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

export interface SubmitDietitianApplicationRequest {
  experience: string
  diplomas: string[]
  description: string
}

export function getMyDietitianApplication(): Promise<DietitianApplication> {
  return apiFetch('/dietitian/applications/me')
}

export function submitDietitianApplication(
  payload: SubmitDietitianApplicationRequest,
): Promise<DietitianApplication> {
  return apiFetch('/dietitian/applications', { method: 'POST', body: payload })
}
