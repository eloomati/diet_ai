import { useState, type FormEvent } from 'react'

import { confirmEmailVerification } from '@/api/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ApiError } from '@/lib/apiFetch'
import { useAuth } from '@/lib/auth'

import { NutritionProfileForm } from './NutritionProfileForm'

function verifyErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.code === 'BAD_REQUEST') {
    return 'Kod jest nieprawidłowy, wygasł lub został już użyty.'
  }
  return 'Coś poszło nie tak. Spróbuj ponownie.'
}

export function ProfilTab() {
  const { user, logout, refreshUser } = useAuth()
  const [token, setToken] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleVerify(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await confirmEmailVerification(token)
      // Re-fetch /auth/me rather than a local "done" flag — so the ✓ badge
      // reflects the real, confirmed status if this tab is reopened later.
      await refreshUser()
    } catch (err) {
      setError(verifyErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {user && <p className="text-sm text-foreground">Zalogowano jako <b>{user.email}</b></p>}

      <div className="rounded-xl border border-border p-4">
        <p className="mb-3 text-xs font-bold tracking-wide text-muted-foreground uppercase">
          Profil żywieniowy
        </p>
        <NutritionProfileForm />
      </div>

      <div className="rounded-xl border border-border p-4">
        <p className="mb-2 text-xs font-bold tracking-wide text-muted-foreground uppercase">
          Weryfikacja e-maila
        </p>
        {user?.email_verified ? (
          <p className="text-sm text-secondary-foreground">Adres e-mail zweryfikowany ✓</p>
        ) : (
          <form className="flex items-end gap-2" onSubmit={handleVerify}>
            <div className="flex-1">
              <label
                htmlFor="email-verification-token"
                className="mb-1 block text-xs font-bold text-muted-foreground"
              >
                Kod z e-maila powitalnego
              </label>
              <Input
                id="email-verification-token"
                value={token}
                onChange={(event) => setToken(event.target.value)}
                required
              />
            </div>
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Chwileczkę…' : 'Zweryfikuj'}
            </Button>
          </form>
        )}
        {error && <p className="mt-2 text-[12.5px] font-bold text-destructive">{error}</p>}
      </div>

      <Button variant="outline" className="w-fit" onClick={() => void logout()}>
        Wyloguj się
      </Button>
    </div>
  )
}
