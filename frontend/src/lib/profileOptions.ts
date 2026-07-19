import type { ActivityLevel, DayOfWeek, DietType, Goal } from '@/api/profile'

export interface ProfileOption<T extends string> {
  value: T
  label: string
}

export const ACTIVITY_LEVEL_OPTIONS: ProfileOption<ActivityLevel>[] = [
  { value: 'LOW', label: 'Niska (praca siedząca, brak treningów)' },
  { value: 'MODERATE', label: 'Umiarkowana (1-3 treningi/tydzień)' },
  { value: 'HIGH', label: 'Wysoka (4-6 treningów/tydzień)' },
  { value: 'VERY_HIGH', label: 'Bardzo wysoka (codzienne treningi/praca fizyczna)' },
]

export const GOAL_OPTIONS: ProfileOption<Goal>[] = [
  { value: 'WEIGHT_LOSS', label: 'Redukcja masy ciała' },
  { value: 'MUSCLE_GAIN', label: 'Budowa masy mięśniowej' },
  { value: 'MAINTENANCE', label: 'Utrzymanie wagi' },
  { value: 'PERFORMANCE', label: 'Poprawa wydolności' },
]

export const DIET_TYPE_OPTIONS: ProfileOption<DietType>[] = [
  { value: 'STANDARD', label: 'Standardowa' },
  { value: 'VEGETARIAN', label: 'Wegetariańska' },
  { value: 'VEGAN', label: 'Wegańska' },
  { value: 'KETO', label: 'Ketogeniczna' },
  { value: 'PALEO', label: 'Paleo' },
  { value: 'GLUTEN_FREE', label: 'Bezglutenowa' },
]

export const DAY_OF_WEEK_OPTIONS: ProfileOption<DayOfWeek>[] = [
  { value: 'MON', label: 'Poniedziałek' },
  { value: 'TUE', label: 'Wtorek' },
  { value: 'WED', label: 'Środa' },
  { value: 'THU', label: 'Czwartek' },
  { value: 'FRI', label: 'Piątek' },
  { value: 'SAT', label: 'Sobota' },
  { value: 'SUN', label: 'Niedziela' },
]

function labelLookup<T extends string>(options: ProfileOption<T>[]): (value: T) => string {
  const byValue = new Map(options.map((option) => [option.value, option.label]))
  return (value) => byValue.get(value) ?? value
}

export const activityLevelLabel = labelLookup(ACTIVITY_LEVEL_OPTIONS)
export const goalLabel = labelLookup(GOAL_OPTIONS)
export const dietTypeLabel = labelLookup(DIET_TYPE_OPTIONS)
export const dayOfWeekLabel = labelLookup(DAY_OF_WEEK_OPTIONS)
