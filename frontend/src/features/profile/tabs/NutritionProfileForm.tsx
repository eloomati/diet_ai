import { useEffect, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { createProfile, getProfile, updateProfile } from '@/api/profile'
import type { ActivityLevel, DietType, Goal, NutritionProfile, WeeklyObligation } from '@/api/profile'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ApiError } from '@/lib/apiFetch'
import {
  ACTIVITY_LEVEL_OPTIONS,
  DIET_TYPE_OPTIONS,
  GOAL_OPTIONS,
  activityLevelLabel,
  dietTypeLabel,
  goalLabel,
} from '@/lib/profileOptions'

import { WeeklyObligationsEditor } from './WeeklyObligationsEditor'

interface FormState {
  age: string
  height_cm: string
  weight_kg: string
  activity_level: ActivityLevel
  goal: Goal
  diet_type: DietType
  weekly_obligations: WeeklyObligation[]
}

const EMPTY_FORM: FormState = {
  age: '',
  height_cm: '',
  weight_kg: '',
  activity_level: 'MODERATE',
  goal: 'MAINTENANCE',
  diet_type: 'STANDARD',
  weekly_obligations: [],
}

function toFormState(profile: NutritionProfile): FormState {
  return {
    age: String(profile.age),
    height_cm: String(profile.height_cm),
    weight_kg: String(profile.weight_kg),
    activity_level: profile.activity_level,
    goal: profile.goal,
    diet_type: profile.diet_type,
    weekly_obligations: profile.weekly_obligations,
  }
}

const ERROR_MESSAGES: Record<string, string> = {
  VALIDATION_ERROR: 'Sprawdź poprawność danych: wiek 1-120, wzrost 50-250 cm, waga 20-400 kg.',
  CONFLICT: 'Ten profil już istnieje — dane zostały odświeżone, spróbuj zapisać ponownie.',
  NOT_FOUND: 'Ten profil już nie istnieje — uzupełnij dane, żeby utworzyć go od nowa.',
  BAD_REQUEST: 'Godzina końca zobowiązania musi być późniejsza niż początku.',
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return ERROR_MESSAGES[error.code] ?? error.message
  return 'Coś poszło nie tak. Spróbuj ponownie.'
}

export function NutritionProfileForm() {
  const queryClient = useQueryClient()
  const profileQuery = useQuery({
    queryKey: ['profile'],
    // A 404 here just means "no profile yet" — a normal, expected first
    // state, not a transient failure worth retrying.
    queryFn: getProfile,
    retry: false,
  })

  const hasProfile = profileQuery.isSuccess
  const profileMissing =
    profileQuery.isError && profileQuery.error instanceof ApiError && profileQuery.error.code === 'NOT_FOUND'

  const [form, setForm] = useState<FormState>(EMPTY_FORM)

  useEffect(() => {
    if (profileQuery.data) setForm(toFormState(profileQuery.data))
  }, [profileQuery.data])

  const saveMutation = useMutation({
    mutationFn: (payload: {
      age: number
      height_cm: number
      weight_kg: number
      activity_level: ActivityLevel
      goal: Goal
      diet_type: DietType
      weekly_obligations: WeeklyObligation[]
    }) => (hasProfile ? updateProfile(payload) : createProfile(payload)),
    onSuccess: (profile) => {
      queryClient.setQueryData(['profile'], profile)
    },
    onError: (error) => {
      // CONFLICT (profile already exists) or NOT_FOUND (profile was
      // removed) both mean our cached create-vs-edit assumption is stale —
      // resync with the server instead of leaving the form stuck retrying
      // the wrong request type.
      if (error instanceof ApiError && (error.code === 'CONFLICT' || error.code === 'NOT_FOUND')) {
        void queryClient.invalidateQueries({ queryKey: ['profile'] })
      }
    },
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    saveMutation.mutate({
      age: Number(form.age),
      height_cm: Number(form.height_cm),
      weight_kg: Number(form.weight_kg),
      activity_level: form.activity_level,
      goal: form.goal,
      diet_type: form.diet_type,
      weekly_obligations: form.weekly_obligations,
    })
  }

  if (profileQuery.isPending) {
    return <p className="text-sm text-muted-foreground">Ładowanie profilu…</p>
  }

  if (profileQuery.isError && !profileMissing) {
    return <p className="text-sm text-destructive">{errorMessage(profileQuery.error)}</p>
  }

  return (
    <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
      {profileMissing && (
        <p className="text-sm text-muted-foreground">
          Nie masz jeszcze profilu żywieniowego — uzupełnij dane, żeby dostać plany skrojone pod
          siebie.
        </p>
      )}

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label htmlFor="profile-age" className="mb-1 block text-xs font-bold text-muted-foreground">
            Wiek
          </label>
          <Input
            id="profile-age"
            type="number"
            min={1}
            max={120}
            value={form.age}
            onChange={(event) => setForm((current) => ({ ...current, age: event.target.value }))}
            required
          />
          <p className="mt-0.5 text-[11px] text-muted-foreground">1-120 lat</p>
        </div>
        <div>
          <label htmlFor="profile-height" className="mb-1 block text-xs font-bold text-muted-foreground">
            Wzrost (cm)
          </label>
          <Input
            id="profile-height"
            type="number"
            min={50}
            max={250}
            value={form.height_cm}
            onChange={(event) => setForm((current) => ({ ...current, height_cm: event.target.value }))}
            required
          />
          <p className="mt-0.5 text-[11px] text-muted-foreground">50-250 cm</p>
        </div>
        <div>
          <label htmlFor="profile-weight" className="mb-1 block text-xs font-bold text-muted-foreground">
            Waga (kg)
          </label>
          <Input
            id="profile-weight"
            type="number"
            min={20}
            max={400}
            step={0.1}
            value={form.weight_kg}
            onChange={(event) => setForm((current) => ({ ...current, weight_kg: event.target.value }))}
            required
          />
          <p className="mt-0.5 text-[11px] text-muted-foreground">20-400 kg</p>
        </div>
      </div>

      <div>
        <label className="mb-1 block text-xs font-bold text-muted-foreground">Aktywność fizyczna</label>
        <Select
          value={form.activity_level}
          onValueChange={(value: ActivityLevel | null) => {
            if (value) setForm((current) => ({ ...current, activity_level: value }))
          }}
        >
          <SelectTrigger className="w-full">
            <SelectValue>{(value: ActivityLevel) => activityLevelLabel(value)}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {ACTIVITY_LEVEL_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <label className="mb-1 block text-xs font-bold text-muted-foreground">Cel</label>
        <Select
          value={form.goal}
          onValueChange={(value: Goal | null) => {
            if (value) setForm((current) => ({ ...current, goal: value }))
          }}
        >
          <SelectTrigger className="w-full">
            <SelectValue>{(value: Goal) => goalLabel(value)}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {GOAL_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <label className="mb-1 block text-xs font-bold text-muted-foreground">Typ diety</label>
        <Select
          value={form.diet_type}
          onValueChange={(value: DietType | null) => {
            if (value) setForm((current) => ({ ...current, diet_type: value }))
          }}
        >
          <SelectTrigger className="w-full">
            <SelectValue>{(value: DietType) => dietTypeLabel(value)}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {DIET_TYPE_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <label className="mb-1 block text-xs font-bold text-muted-foreground">Cotygodniowe zobowiązania</label>
        <WeeklyObligationsEditor
          value={form.weekly_obligations}
          onChange={(obligations) => setForm((current) => ({ ...current, weekly_obligations: obligations }))}
        />
      </div>

      {saveMutation.isError && (
        <p className="text-[12.5px] font-bold text-destructive">{errorMessage(saveMutation.error)}</p>
      )}
      {saveMutation.isSuccess && !saveMutation.isPending && (
        <p className="text-[12.5px] font-bold text-secondary-foreground">Zapisano ✓</p>
      )}

      <Button type="submit" className="w-fit" disabled={saveMutation.isPending}>
        {saveMutation.isPending ? 'Zapisywanie…' : hasProfile ? 'Zapisz zmiany' : 'Utwórz profil'}
      </Button>
    </form>
  )
}
