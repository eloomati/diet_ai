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

export interface DietitianProfile {
  id: string
  user_id: string
  experience: string
  diplomas: string[]
  description: string
  photos: string[]
  created_at: string
}

export interface UpdateDietitianProfileRequest {
  experience?: string
  diplomas?: string[]
  description?: string
}

export function getMyDietitianProfile(): Promise<DietitianProfile> {
  return apiFetch('/dietitian/profile/me')
}

export function updateDietitianProfile(
  payload: UpdateDietitianProfileRequest,
): Promise<DietitianProfile> {
  return apiFetch('/dietitian/profile', { method: 'PUT', body: payload })
}

export function uploadDietitianProfilePhoto(file: File): Promise<DietitianProfile> {
  const formData = new FormData()
  formData.append('file', file)
  return apiFetch('/dietitian/profile/photos', { method: 'POST', body: formData })
}

export function removeDietitianProfilePhoto(index: number): Promise<DietitianProfile> {
  return apiFetch(`/dietitian/profile/photos/${index}`, { method: 'DELETE' })
}

export interface DietitianListingItem {
  user_id: string
  email: string
  experience: string
  description: string
  photos: string[]
  average_rating: number | null
  review_count: number
}

/** Public — no authentication required, real marketplace-style browsing. */
export function listDietitians(): Promise<DietitianListingItem[]> {
  return apiFetch('/dietitian', { skipAuth: true })
}

export interface PublicReview {
  rating: number
  comment: string
  created_at: string
}

export interface PublicDietitianProfile {
  user_id: string
  email: string
  experience: string
  diplomas: string[]
  description: string
  photos: string[]
  created_at: string
  average_rating: number | null
  review_count: number
  reviews: PublicReview[]
}

/** Public — no authentication required, same as the listing it's reached from. */
export function getPublicDietitianProfile(dietitianId: string): Promise<PublicDietitianProfile> {
  return apiFetch(`/dietitian/${dietitianId}`, { skipAuth: true })
}
