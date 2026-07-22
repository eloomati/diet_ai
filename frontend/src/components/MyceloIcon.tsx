interface MyceloIconProps {
  /** Notification/alert state — the cap turns red, imitating a fly agaric
   * (muchomor), per the brand's own mascot rule: calm earthy brown at
   * rest, red the moment there's something new to see. */
  alert?: boolean
  className?: string
}

/** The Mycelo brand mark — a line-art mushroom (variant "C" of the
 * proposed set). Used as the browser favicon (idle state, baked into
 * `public/favicon.svg`) and reusable here for in-app placements, e.g. the
 * Phase 12 Etap 5 notification badge, which needs the same silhouette to
 * flip color rather than a separate icon. */
export function MyceloIcon({ alert = false, className }: MyceloIconProps) {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      stroke={alert ? 'var(--destructive)' : 'var(--mycelo-idle)'}
      strokeWidth={4}
      strokeLinejoin="round"
      strokeLinecap="round"
      className={className}
      role="img"
      aria-label={alert ? 'Mycelo — nowe powiadomienie' : 'Mycelo'}
    >
      <path d="M6 32 C6 14 18 6 32 6 C46 6 58 14 58 32 C52 29 46 34 40 31 C36 34 28 34 24 31 C18 34 12 29 6 32 Z" />
      <rect x="22" y="31" width="20" height="23" rx="10" />
      {alert && <circle cx="32" cy="18" r="2" fill="var(--destructive)" stroke="none" />}
    </svg>
  )
}
