import { cn } from '@/lib/utils'

interface FieldErrorProps {
  message: string
  className?: string
}

/** One consistent style for an inline action/form error — previously
 * reinvented per file with 4 different size/weight combinations for the
 * same role. Not for full content-replacing error states (an empty
 * conversation/list that failed to load entirely) — those stay `text-sm`,
 * which was already consistent across the app. */
export function FieldError({ message, className }: FieldErrorProps) {
  return <p className={cn('text-[12.5px] font-bold text-destructive', className)}>{message}</p>
}
