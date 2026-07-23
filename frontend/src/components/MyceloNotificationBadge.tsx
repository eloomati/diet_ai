import { Badge } from '@/components/ui/badge'
import { MyceloIcon } from '@/components/MyceloIcon'

interface MyceloNotificationBadgeProps {
  unreadCount: number
  onClick: () => void
  className?: string
}

/** Same mushroom + count pill as RightRail's own notification bell, reused
 * next to the collapsed right rail's expand button. Always rendered while
 * the rail is collapsed — it doubles as the button to reopen it, not just
 * an unread-notification indicator — with the alert coloring/count pill
 * layered on only once there's actually something unread. */
export function MyceloNotificationBadge({
  unreadCount,
  onClick,
  className,
}: MyceloNotificationBadgeProps) {
  const hasUnread = unreadCount > 0

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Powiadomienia"
      className={`relative inline-flex size-9 items-center justify-center rounded-md hover:bg-accent/60 ${className ?? ''}`}
    >
      <MyceloIcon alert={hasUnread} className="size-4" />
      {hasUnread && (
        <Badge
          variant="destructive"
          className="absolute -top-1 -right-1 h-4 min-w-4 justify-center rounded-full bg-destructive px-1 text-[10px] text-white"
        >
          {unreadCount > 9 ? '9+' : unreadCount}
        </Badge>
      )}
    </button>
  )
}
