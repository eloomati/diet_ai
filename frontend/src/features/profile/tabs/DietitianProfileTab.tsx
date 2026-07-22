import { X } from 'lucide-react'
import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  getMyDietitianProfile,
  removeDietitianProfilePhoto,
  updateDietitianProfile,
  uploadDietitianProfilePhoto,
} from '@/api/dietitian'
import type { DietitianProfile } from '@/api/dietitian'
import { FieldError } from '@/components/FieldError'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { ApiError, resolveStaticUrl } from '@/lib/apiFetch'
import { notifyError } from '@/lib/toast'

const MAX_PHOTOS = 3

interface FormState {
  experience: string
  diplomas: string
  description: string
  firstName: string
  lastName: string
}

function toFormState(profile: DietitianProfile): FormState {
  return {
    experience: profile.experience,
    diplomas: profile.diplomas.join('\n'),
    description: profile.description,
    firstName: profile.first_name ?? '',
    lastName: profile.last_name ?? '',
  }
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Coś poszło nie tak. Spróbuj ponownie.'
}

export function DietitianProfileTab() {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const profileQuery = useQuery({ queryKey: ['dietitian-profile'], queryFn: getMyDietitianProfile })
  const [form, setForm] = useState<FormState>({
    experience: '',
    diplomas: '',
    description: '',
    firstName: '',
    lastName: '',
  })

  useEffect(() => {
    if (profileQuery.data) setForm(toFormState(profileQuery.data))
  }, [profileQuery.data])

  const saveMutation = useMutation({
    mutationFn: updateDietitianProfile,
    onSuccess: (profile) => queryClient.setQueryData(['dietitian-profile'], profile),
  })

  const uploadMutation = useMutation({
    mutationFn: uploadDietitianProfilePhoto,
    onSuccess: (profile) => queryClient.setQueryData(['dietitian-profile'], profile),
    onError: (error) => notifyError(errorMessage(error)),
  })

  const removeMutation = useMutation({
    mutationFn: removeDietitianProfilePhoto,
    onSuccess: (profile) => queryClient.setQueryData(['dietitian-profile'], profile),
    onError: (error) => notifyError(errorMessage(error)),
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    saveMutation.mutate({
      experience: form.experience,
      diplomas: form.diplomas
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean),
      description: form.description,
      first_name: form.firstName.trim() || null,
      last_name: form.lastName.trim() || null,
    })
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (file) uploadMutation.mutate(file)
  }

  if (profileQuery.isPending) {
    return <p className="text-sm text-muted-foreground">Ładowanie profilu…</p>
  }

  if (profileQuery.isError) {
    return <p className="text-sm text-destructive">{errorMessage(profileQuery.error)}</p>
  }

  const photos = profileQuery.data.photos

  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-xl border border-border p-4">
        <p className="mb-3 text-xs font-bold tracking-wide text-muted-foreground uppercase">
          Profil dietetyka
        </p>
        <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
          <p className="text-[12.5px] text-muted-foreground">
            Podanie imienia i nazwiska jest opcjonalne — jeśli je uzupełnisz, będą
            widoczne publicznie zamiast Twojej domyślnej nazwy wyświetlanej.
          </p>
          <div className="flex gap-3">
            <div className="flex-1">
              <label htmlFor="dietitian-profile-first-name" className="mb-1 block text-xs font-bold text-muted-foreground">
                Imię (opcjonalnie)
              </label>
              <Input
                id="dietitian-profile-first-name"
                value={form.firstName}
                onChange={(event) => setForm((current) => ({ ...current, firstName: event.target.value }))}
              />
            </div>
            <div className="flex-1">
              <label htmlFor="dietitian-profile-last-name" className="mb-1 block text-xs font-bold text-muted-foreground">
                Nazwisko (opcjonalnie)
              </label>
              <Input
                id="dietitian-profile-last-name"
                value={form.lastName}
                onChange={(event) => setForm((current) => ({ ...current, lastName: event.target.value }))}
              />
            </div>
          </div>

          <div>
            <label htmlFor="dietitian-profile-experience" className="mb-1 block text-xs font-bold text-muted-foreground">
              Doświadczenie
            </label>
            <Textarea
              id="dietitian-profile-experience"
              value={form.experience}
              onChange={(event) => setForm((current) => ({ ...current, experience: event.target.value }))}
              required
            />
          </div>

          <div>
            <label htmlFor="dietitian-profile-diplomas" className="mb-1 block text-xs font-bold text-muted-foreground">
              Dyplomy (jeden na linię)
            </label>
            <Textarea
              id="dietitian-profile-diplomas"
              value={form.diplomas}
              onChange={(event) => setForm((current) => ({ ...current, diplomas: event.target.value }))}
            />
          </div>

          <div>
            <label htmlFor="dietitian-profile-description" className="mb-1 block text-xs font-bold text-muted-foreground">
              Opis
            </label>
            <Textarea
              id="dietitian-profile-description"
              value={form.description}
              onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              required
            />
          </div>

          {saveMutation.isError && <FieldError message={errorMessage(saveMutation.error)} />}
          {saveMutation.isSuccess && !saveMutation.isPending && (
            <p className="text-[12.5px] font-bold text-secondary-foreground">Zapisano ✓</p>
          )}

          <Button type="submit" className="w-fit" disabled={saveMutation.isPending}>
            {saveMutation.isPending ? 'Zapisywanie…' : 'Zapisz zmiany'}
          </Button>
        </form>
      </div>

      <div className="rounded-xl border border-border p-4">
        <p className="mb-3 text-xs font-bold tracking-wide text-muted-foreground uppercase">
          Zdjęcia ({photos.length}/{MAX_PHOTOS})
        </p>
        <div className="flex flex-wrap gap-3">
          {photos.map((photo, index) => (
            <div key={photo} className="group relative size-24 overflow-hidden rounded-lg border border-border">
              <img src={resolveStaticUrl(photo)} alt="" className="size-full object-cover" />
              <button
                type="button"
                onClick={() => removeMutation.mutate(index)}
                disabled={removeMutation.isPending}
                aria-label="Usuń zdjęcie"
                className="absolute top-1 right-1 rounded-full bg-black/60 p-1 text-white hover:bg-black/80"
              >
                <X className="size-3" />
              </button>
            </div>
          ))}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={handleFileChange}
        />
        <Button
          type="button"
          variant="outline"
          className="mt-3 w-fit"
          disabled={photos.length >= MAX_PHOTOS || uploadMutation.isPending}
          onClick={() => fileInputRef.current?.click()}
        >
          {uploadMutation.isPending ? 'Wysyłanie…' : 'Dodaj zdjęcie'}
        </Button>
      </div>
    </div>
  )
}
