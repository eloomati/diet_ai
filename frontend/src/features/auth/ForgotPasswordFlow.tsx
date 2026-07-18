import { useState, type FormEvent } from 'react'

import { confirmPasswordReset, requestPasswordReset } from '@/api/auth'
import { Captcha } from '@/components/Captcha'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ApiError } from '@/lib/apiFetch'

const ERROR_MESSAGES: Record<string, string> = {
  BAD_REQUEST: 'Kod jest nieprawidłowy, wygasł lub został już użyty.',
  INVALID_PASSWORD: 'Nowe hasło musi mieć 8-128 znaków.',
  VALIDATION_ERROR: 'Sprawdź poprawność wprowadzonych danych.',
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return ERROR_MESSAGES[error.code] ?? error.message
  }
  return 'Coś poszło nie tak. Spróbuj ponownie.'
}

interface ForgotPasswordFlowProps {
  onBackToLogin: () => void
}

/**
 * The backend only ever emails a raw token (see EmailSender in
 * architecture.md) — no clickable frontend link — so this is a two-step
 * form: request a reset, then come back and paste the token + new password.
 */
export function ForgotPasswordFlow({ onBackToLogin }: ForgotPasswordFlowProps) {
  const [step, setStep] = useState<'request' | 'confirm' | 'done'>('request')
  const [email, setEmail] = useState('')
  const [token, setToken] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [captchaToken, setCaptchaToken] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await requestPasswordReset(email, captchaToken)
      setStep('confirm')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleConfirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await confirmPasswordReset(token, newPassword)
      setStep('done')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  if (step === 'done') {
    return (
      <div className="flex flex-col gap-3 text-center">
        <p className="text-sm text-foreground">Hasło zostało zmienione. Możesz się teraz zalogować.</p>
        <Button onClick={onBackToLogin}>Wróć do logowania</Button>
      </div>
    )
  }

  if (step === 'confirm') {
    return (
      <div className="flex flex-col gap-2.5">
        <p className="text-[12.5px] text-muted-foreground">
          Jeśli konto istnieje, wysłaliśmy e-mail z kodem resetującym (ważnym 30 minut). Wklej go
          poniżej razem z nowym hasłem.
        </p>
        <form className="flex flex-col gap-2.5" onSubmit={handleConfirm}>
          <div>
            <label htmlFor="reset-token" className="mb-1 block text-xs font-bold text-muted-foreground">
              Kod z e-maila
            </label>
            <Input
              id="reset-token"
              value={token}
              onChange={(event) => setToken(event.target.value)}
              required
            />
          </div>
          <div>
            <label
              htmlFor="reset-new-password"
              className="mb-1 block text-xs font-bold text-muted-foreground"
            >
              Nowe hasło
            </label>
            <Input
              id="reset-new-password"
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              placeholder="••••••••"
              minLength={8}
              required
            />
          </div>
          {error && <p className="text-[12.5px] font-bold text-destructive">{error}</p>}
          <Button type="submit" disabled={submitting}>
            {submitting ? 'Chwileczkę…' : 'Ustaw nowe hasło'}
          </Button>
        </form>
        <button
          onClick={onBackToLogin}
          className="text-center text-[12.5px] font-bold text-muted-foreground hover:text-foreground"
        >
          ← Wróć do logowania
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2.5">
      <p className="text-[12.5px] text-muted-foreground">
        Podaj adres e-mail konta — wyślemy kod do zresetowania hasła.
      </p>
      <form className="flex flex-col gap-2.5" onSubmit={handleRequest}>
        <div>
          <label htmlFor="reset-email" className="mb-1 block text-xs font-bold text-muted-foreground">
            E-mail
          </label>
          <Input
            id="reset-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="ty@przyklad.pl"
            required
          />
        </div>
        <Captcha onToken={setCaptchaToken} />

        {error && <p className="text-[12.5px] font-bold text-destructive">{error}</p>}
        <Button type="submit" disabled={submitting || !captchaToken}>
          {submitting ? 'Wysyłanie…' : 'Wyślij kod resetujący'}
        </Button>
      </form>
      <div className="flex justify-between text-[12.5px] font-bold">
        <button onClick={onBackToLogin} className="text-muted-foreground hover:text-foreground">
          ← Wróć do logowania
        </button>
        <button onClick={() => setStep('confirm')} className="text-muted-foreground hover:text-foreground">
          Mam już kod →
        </button>
      </div>
    </div>
  )
}
