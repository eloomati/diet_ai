import { useQuery } from '@tanstack/react-query'

import { listNotifications } from '@/api/notifications'

// Same query key and interval as RightRail's own NotificationsBell — React
// Query dedupes by key, so this shares its cache/polling instead of firing
// a second request.
const NOTIFICATIONS_POLL_INTERVAL_MS = 4000

export function useUnreadNotificationsCount(enabled: boolean): number {
  const notificationsQuery = useQuery({
    queryKey: ['my-notifications'],
    queryFn: listNotifications,
    refetchInterval: NOTIFICATIONS_POLL_INTERVAL_MS,
    enabled,
  })
  return (notificationsQuery.data ?? []).filter((n) => !n.read_at).length
}
