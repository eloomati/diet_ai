import { useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ApiError } from '@/lib/apiFetch'
import { InsufficientRoleError, useAuth } from '@/lib/auth'

function errorMessage(error: unknown): string {
  if (error instanceof InsufficientRoleError) return error.message
  if (error instanceof ApiError) {
    if (error.code === 'INVALID_CREDENTIALS') return 'Nieprawidłowy e-mail lub hasło.'
    return error.message
  }
  return 'Coś poszło nie tak. Spróbuj ponownie.'
}

export function LoginPage() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm rounded-xl border border-border bg-card p-6">
        <p className="mb-1 font-heading text-lg font-extrabold">Mycelo</p>
        <p className="mb-6 text-sm text-muted-foreground">Panel administracyjny</p>

        <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="login-email" className="mb-1 block text-xs font-bold text-muted-foreground">
              E-mail
            </label>
            <Input
              id="login-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>

          <div>
            <label htmlFor="login-password" className="mb-1 block text-xs font-bold text-muted-foreground">
              Hasło
            </label>
            <Input
              id="login-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>

          {error && <p className="text-[12.5px] font-bold text-destructive">{error}</p>}

          <Button type="submit" className="mt-2" disabled={submitting}>
            {submitting ? 'Logowanie…' : 'Zaloguj się'}
          </Button>
        </form>
      </div>
    </div>
  )
}
