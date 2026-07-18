import { apiFetch } from '@/lib/apiFetch'

export type ActivityLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH'
export type Goal = 'WEIGHT_LOSS' | 'MUSCLE_GAIN' | 'MAINTENANCE' | 'PERFORMANCE'
export type DietType = 'STANDARD' | 'VEGETARIAN' | 'VEGAN' | 'KETO' | 'PALEO' | 'GLUTEN_FREE'
export type DayOfWeek = 'MON' | 'TUE' | 'WED' | 'THU' | 'FRI' | 'SAT' | 'SUN'

export interface WeeklyObligation {
  day_of_week: DayOfWeek
  start_time: string
  end_time: string
  label: string
}

export interface NutritionProfile {
  profile_id: string
  user_id: string
  age: number
  height_cm: number
  weight_kg: number
  activity_level: ActivityLevel
  goal: Goal
  diet_type: DietType
  weekly_obligations: WeeklyObligation[]
  created_at: string
  updated_at: string
}

export interface UpsertProfileRequest {
  age?: number
  height_cm?: number
  weight_kg?: number
  activity_level?: ActivityLevel
  goal?: Goal
  diet_type?: DietType
  weekly_obligations?: WeeklyObligation[]
}

export function getProfile(): Promise<NutritionProfile> {
  return apiFetch('/profile')
}

export function createProfile(payload: UpsertProfileRequest): Promise<NutritionProfile> {
  return apiFetch('/profile', { method: 'POST', body: payload })
}

export function updateProfile(payload: UpsertProfileRequest): Promise<NutritionProfile> {
  return apiFetch('/profile', { method: 'PUT', body: payload })
}
