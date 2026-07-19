import { apiFetch, apiFetchBlob } from '@/lib/apiFetch'
import type { DietType, Goal } from '@/api/profile'

export interface Meal {
  name: string
  calories: number
  protein: number
  carbohydrates: number
  fat: number
  time: string | null
}

export interface DietDay {
  day_number: number
  meals: Meal[]
}

export interface DietPlan {
  plan_id: string
  user_id: string
  goal: Goal
  diet_type: DietType
  duration_days: number
  requirements: string[]
  days: DietDay[]
  created_at: string
  updated_at: string
}

export interface DietPlanSummary {
  plan_id: string
  goal: Goal
  diet_type: DietType
  duration_days: number
  created_at: string
}

export interface GeneratePlanRequest {
  duration_days: number
  requirements?: string[]
}

export interface RescheduleMealRequest {
  day_number: number
  meal_name: string
  new_time: string
}

export interface DietPlanExport {
  export_id: string
  diet_plan_id: string
  filename: string
  created_at: string
}

export function generateDietPlan(payload: GeneratePlanRequest): Promise<DietPlan> {
  return apiFetch('/diet-plans/generate', { method: 'POST', body: payload })
}

export function listDietPlans(range?: { from?: string; to?: string }): Promise<DietPlanSummary[]> {
  const query = new URLSearchParams()
  if (range?.from) query.set('from', range.from)
  if (range?.to) query.set('to', range.to)
  const qs = query.toString()
  return apiFetch(`/diet-plans${qs ? `?${qs}` : ''}`)
}

export function getDietPlan(planId: string): Promise<DietPlan> {
  return apiFetch(`/diet-plans/${planId}`)
}

export function rescheduleMeal(planId: string, payload: RescheduleMealRequest): Promise<DietPlan> {
  return apiFetch(`/diet-plans/${planId}/meals`, { method: 'PATCH', body: payload })
}

export function exportDietPlan(planId: string): Promise<DietPlanExport> {
  return apiFetch(`/diet-plans/${planId}/export`, { method: 'POST' })
}

export function listDietPlanExports(planId: string): Promise<DietPlanExport[]> {
  return apiFetch(`/diet-plans/${planId}/exports`)
}

export function downloadDietPlanExport(planId: string, exportId: string): Promise<Blob> {
  return apiFetchBlob(`/diet-plans/${planId}/exports/${exportId}/download`)
}
