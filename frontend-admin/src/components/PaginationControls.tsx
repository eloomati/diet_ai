import { ChevronLeft, ChevronRight } from 'lucide-react'

import { Button } from '@/components/ui/button'

interface PaginationControlsProps {
  offset: number
  limit: number
  total: number
  onOffsetChange: (offset: number) => void
}

/** Shared prev/next pager for the three admin list tabs (Users, Dietitian
 * Applications, Transactions) — all three page the same way (fixed page
 * size, offset-based), so one control covers all of them rather than each
 * tab reinventing its own. Hidden entirely when everything fits on one
 * page, so it never crowds a short list. */
export function PaginationControls({
  offset,
  limit,
  total,
  onOffsetChange,
}: PaginationControlsProps) {
  if (total <= limit) return null

  const from = total === 0 ? 0 : offset + 1
  const to = Math.min(offset + limit, total)

  return (
    <div className="flex items-center justify-between border-t border-border pt-2.5">
      <p className="text-xs text-muted-foreground">
        {from}–{to} z {total}
      </p>
      <div className="flex items-center gap-1.5">
        <Button
          type="button"
          variant="outline"
          size="icon-sm"
          disabled={offset === 0}
          onClick={() => onOffsetChange(Math.max(0, offset - limit))}
          aria-label="Poprzednia strona"
        >
          <ChevronLeft />
        </Button>
        <Button
          type="button"
          variant="outline"
          size="icon-sm"
          disabled={to >= total}
          onClick={() => onOffsetChange(offset + limit)}
          aria-label="Następna strona"
        >
          <ChevronRight />
        </Button>
      </div>
    </div>
  )
}
