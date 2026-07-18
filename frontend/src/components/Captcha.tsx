import { useEffect, useRef } from 'react'

declare global {
  interface Window {
    turnstile?: {
      render: (
        container: HTMLElement,
        options: { sitekey: string; callback: (token: string) => void },
      ) => string
      remove: (widgetId: string) => void
    }
  }
}

const SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY as string | undefined
const SCRIPT_SRC = 'https://challenges.cloudflare.com/turnstile/v0/api.js'
const DEV_PLACEHOLDER_TOKEN = 'dev-mode-no-turnstile-configured'

let scriptLoadPromise: Promise<void> | null = null

function loadTurnstileScript(): Promise<void> {
  if (window.turnstile) return Promise.resolve()
  scriptLoadPromise ??= new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = SCRIPT_SRC
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load the Turnstile script'))
    document.head.appendChild(script)
  })
  return scriptLoadPromise
}

interface CaptchaProps {
  onToken: (token: string) => void
}

/**
 * Cloudflare Turnstile widget. Without a configured site key (local dev
 * without a Cloudflare account, or the test environment) it skips the real
 * widget and hands back a placeholder token instead — the backend's default
 * CAPTCHA_PROVIDER=mock accepts any token, so this keeps register/reset
 * usable without external setup, same spirit as EMAIL_PROVIDER=mock.
 */
export function Captcha({ onToken }: CaptchaProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const widgetIdRef = useRef<string | null>(null)
  const onTokenRef = useRef(onToken)
  onTokenRef.current = onToken

  useEffect(() => {
    if (!SITE_KEY) {
      onTokenRef.current(DEV_PLACEHOLDER_TOKEN)
      return
    }

    let cancelled = false
    loadTurnstileScript().then(() => {
      if (cancelled || !containerRef.current || !window.turnstile) return
      widgetIdRef.current = window.turnstile.render(containerRef.current, {
        sitekey: SITE_KEY,
        callback: (token) => onTokenRef.current(token),
      })
    })

    return () => {
      cancelled = true
      if (widgetIdRef.current && window.turnstile) {
        window.turnstile.remove(widgetIdRef.current)
      }
    }
  }, [])

  if (!SITE_KEY) return null

  return <div ref={containerRef} />
}
