import type { LucideIcon } from 'lucide-react'

import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon: LucideIcon
  message: string
  className?: string
}

/** Same shape as the main app's `EmptyState` — one consistent treatment for
 * "nothing here yet", reused for the tabs that stay honest placeholders
 * beyond this stage (Raporty, Transakcje until Etap 3 wires it up). */
export function EmptyState({ icon: Icon, message, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center gap-2 px-4 py-12 text-center', className)}>
      <Icon className="size-5 text-muted-foreground/60" />
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  )
}
