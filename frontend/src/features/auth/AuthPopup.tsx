import { useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ApiError } from '@/lib/apiFetch'
import { useAuth } from '@/lib/auth'

import { ForgotPasswordFlow } from './ForgotPasswordFlow'

interface AuthPopupProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const ERROR_MESSAGES: Record<string, string> = {
  INVALID_CREDENTIALS: 'Nieprawidłowy e-mail lub hasło.',
  INACTIVE_USER: 'To konto jest nieaktywne.',
  USER_ALREADY_EXISTS: 'Konto z tym adresem e-mail już istnieje.',
  INVALID_PASSWORD: 'Hasło musi mieć 8-128 znaków.',
  VALIDATION_ERROR: 'Sprawdź poprawność adresu e-mail i hasła.',
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return ERROR_MESSAGES[error.code] ?? error.message
  }
  return 'Coś poszło nie tak. Spróbuj ponownie.'
}

export function AuthPopup({ open, onOpenChange }: AuthPopupProps) {
  const { login, register } = useAuth()
  const [view, setView] = useState<'credentials' | 'forgot-password'>('credentials')
  const [tab, setTab] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function resetForm() {
    setView('credentials')
    setTab('login')
    setEmail('')
    setPassword('')
    setError(null)
  }

  function handleOpenChange(next: boolean) {
    onOpenChange(next)
    if (!next) resetForm()
  }

  function handleTabChange(value: string) {
    setTab(value as 'login' | 'register')
    setError(null)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (tab === 'login') {
        await login(email, password)
      } else {
        // The register endpoint only creates the account (no tokens) — log
        // in right after with the same credentials so registering also
        // starts a session, matching the mockup's one-step expectation.
        await register(email, password)
        await login(email, password)
      }
      resetForm()
      onOpenChange(false)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogTitle className="sr-only">Logowanie</DialogTitle>

        {view === 'forgot-password' ? (
          <ForgotPasswordFlow onBackToLogin={() => setView('credentials')} />
        ) : (
          <>
            <Tabs value={tab} onValueChange={handleTabChange}>
              <TabsList className="w-full">
                <TabsTrigger value="login" className="flex-1">
                  Zaloguj się
                </TabsTrigger>
                <TabsTrigger value="register" className="flex-1">
                  Zarejestruj się
                </TabsTrigger>
              </TabsList>
            </Tabs>

            <form className="flex flex-col gap-2.5" onSubmit={handleSubmit}>
              <div>
                <label className="mb-1 block text-xs font-bold text-muted-foreground">E-mail</label>
                <Input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="ty@przyklad.pl"
                  required
                />
              </div>
              <div>
                <div className="mb-1 flex items-center justify-between">
                  <label className="block text-xs font-bold text-muted-foreground">Hasło</label>
                  {tab === 'login' && (
                    <button
                      type="button"
                      onClick={() => setView('forgot-password')}
                      className="text-xs font-bold text-muted-foreground hover:text-foreground"
                    >
                      Zapomniałeś hasła?
                    </button>
                  )}
                </div>
                <Input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="••••••••"
                  minLength={8}
                  required
                />
              </div>

              {error && <p className="text-[12.5px] font-bold text-destructive">{error}</p>}

              <Button type="submit" className="mt-1.5" disabled={submitting}>
                {submitting ? 'Chwileczkę…' : tab === 'login' ? 'Zaloguj się' : 'Utwórz konto'}
              </Button>
            </form>

            <button
              onClick={() => handleOpenChange(false)}
              className="text-center text-[12.5px] font-bold text-muted-foreground hover:text-foreground"
            >
              Kontynuuj jako gość →
            </button>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
