import { Badge } from '@/components/ui/badge'
import { MyceloIcon } from '@/components/MyceloIcon'

interface MyceloNotificationBadgeProps {
  unreadCount: number
  onClick: () => void
  className?: string
}

/** Same mushroom + count pill as RightRail's own notification bell, reused
 * next to the collapsed right rail's expand button — so an unread
 * notification stays visible even while the rail itself is collapsed. */
export function MyceloNotificationBadge({
  unreadCount,
  onClick,
  className,
}: MyceloNotificationBadgeProps) {
  if (unreadCount === 0) return null

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Powiadomienia"
      className={`relative inline-flex size-9 items-center justify-center rounded-md border border-border bg-background hover:bg-accent/60 ${className ?? ''}`}
    >
      <MyceloIcon alert className="size-4" />
      <Badge
        variant="destructive"
        className="absolute -top-1 -right-1 h-4 min-w-4 justify-center rounded-full bg-destructive px-1 text-[10px] text-white"
      >
        {unreadCount > 9 ? '9+' : unreadCount}
      </Badge>
    </button>
  )
}
