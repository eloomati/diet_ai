import type { LucideIcon } from 'lucide-react'

import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon: LucideIcon
  message: string
  className?: string
}

/** One consistent visual treatment for "nothing here yet" across the app
 * (history/plans/calendar previously each rolled their own — some centered,
 * some not, none with an icon) — wording stays per call site, only the
 * layout is shared. */
export function EmptyState({ icon: Icon, message, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center gap-2 px-4 py-8 text-center', className)}>
      <Icon className="size-5 text-muted-foreground/60" />
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  )
}
