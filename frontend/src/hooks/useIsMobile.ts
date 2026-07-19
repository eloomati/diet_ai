import { useState } from 'react'

const MOBILE_QUERY = '(max-width: 767px)'

/** Matches Tailwind's default `md` breakpoint (768px). Only meant to pick
 * a sensible *initial* state (e.g. a rail's default collapsed state) —
 * deliberately doesn't subscribe to live resizes, so it won't force-toggle
 * UI state a user already opened or closed by hand. */
export function useIsMobile(): boolean {
  const [isMobile] = useState(() => window.matchMedia(MOBILE_QUERY).matches)
  return isMobile
}
