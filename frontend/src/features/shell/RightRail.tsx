import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell, ChevronRight, Star, Users } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/EmptyState'
import { MyceloIcon } from '@/components/MyceloIcon'
import { listDietitians } from '@/api/dietitian'
import type { DietitianListingItem } from '@/api/dietitian'
import { listMyDietitianThreads } from '@/api/messaging'
import type { DietitianThread } from '@/api/messaging'
import { listNotifications, markAllNotificationsRead } from '@/api/notifications'
import type { Notification } from '@/api/notifications'
import { getMyPurchases } from '@/api/transactions'
import { useAuth } from '@/lib/auth'
import { resolveStaticUrl } from '@/lib/apiFetch'
import { notifyInfo } from '@/lib/toast'

import { DietitianProfileModal } from './DietitianProfileModal'

// Same "polling not push" decision as the human-chat message list.
const NOTIFICATIONS_POLL_INTERVAL_MS = 4000

const NOTIFICATION_LABELS: Record<Notification['type'], string> = {
  TRANSACTION_PAID: 'Nowa płatność od klienta',
  NEW_MESSAGE: 'Nowa wiadomość',
}

function NotificationRow({ notification }: { notification: Notification }) {
  return (
    <div className="flex items-start gap-2 rounded-lg px-2 py-1.5 text-left">
      <span
        className={`mt-1.5 size-1.5 shrink-0 rounded-full ${
          notification.read_at ? 'bg-transparent' : 'bg-destructive'
        }`}
      />
      <p className="text-[12.5px] leading-snug text-foreground">
        {NOTIFICATION_LABELS[notification.type]}
      </p>
    </div>
  )
}

/** One unified unread-count badge for the everyday case (new messages),
 * plus a separate one-shot toast reserved for the rarer, higher-signal
 * TRANSACTION_PAID event — a seen-ids ref keeps the toast from re-firing
 * on every poll, and doesn't fire retroactively for notifications that
 * already existed the moment this component first mounted. */
function NotificationsBell() {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const seenIds = useRef<Set<string> | null>(null)

  const notificationsQuery = useQuery({
    queryKey: ['my-notifications'],
    queryFn: listNotifications,
    refetchInterval: NOTIFICATIONS_POLL_INTERVAL_MS,
  })
  const notifications = notificationsQuery.data ?? []
  const unreadCount = notifications.filter((n) => !n.read_at).length

  useEffect(() => {
    if (!notificationsQuery.data) return
    if (seenIds.current === null) {
      seenIds.current = new Set(notificationsQuery.data.map((n) => n.id))
      return
    }
    for (const notification of notificationsQuery.data) {
      if (seenIds.current.has(notification.id)) continue
      seenIds.current.add(notification.id)
      if (notification.type === 'TRANSACTION_PAID') {
        notifyInfo('Klient opłacił transakcję.')
      }
    }
  }, [notificationsQuery.data])

  const markReadMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: (updated) => queryClient.setQueryData(['my-notifications'], updated),
  })

  return (
    <Popover
      open={open}
      onOpenChange={(nextOpen) => {
        setOpen(nextOpen)
        if (nextOpen && unreadCount > 0) markReadMutation.mutate()
      }}
    >
      <PopoverTrigger
        aria-label="Powiadomienia"
        className="relative inline-flex size-8 items-center justify-center rounded-md hover:bg-accent/60"
      >
        <MyceloIcon alert={unreadCount > 0} className="size-4.5" />
        {unreadCount > 0 && (
          <Badge
            variant="destructive"
            className="absolute -top-1 -right-1 h-4 min-w-4 justify-center rounded-full bg-destructive px-1 text-[10px] text-white"
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </Badge>
        )}
      </PopoverTrigger>
      <PopoverContent align="end" className="max-h-80 overflow-y-auto">
        {notifications.length === 0 ? (
          <EmptyState icon={Bell} message="Brak powiadomień." className="py-4" />
        ) : (
          <div className="flex flex-col gap-0.5">
            {notifications.map((notification) => (
              <NotificationRow key={notification.id} notification={notification} />
            ))}
          </div>
        )}
      </PopoverContent>
    </Popover>
  )
}

interface RightRailProps {
  onCollapse: () => void
}

function DietitianCard({
  dietitian,
  onSelect,
}: {
  dietitian: DietitianListingItem
  onSelect: (dietitianId: string) => void
}) {
  const initials = dietitian.name.slice(0, 2).toUpperCase()
  const photo = dietitian.photos[0]

  return (
    <button
      type="button"
      onClick={() => onSelect(dietitian.user_id)}
      className="w-full rounded-2xl border border-border bg-background p-3 text-left hover:bg-accent/40"
    >
      <div className="flex items-start gap-2.5">
        <Avatar className="size-9 border border-border">
          {photo && <AvatarImage src={resolveStaticUrl(photo)} alt="" />}
          <AvatarFallback className="bg-gradient-to-br from-primary to-accent-foreground/40 font-bold text-primary-foreground">
            {initials}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[13px] font-bold text-foreground">{dietitian.name}</p>
          <p className="mt-0.5 line-clamp-2 text-[11.5px] leading-snug text-muted-foreground">
            {dietitian.experience}
          </p>
        </div>
      </div>
      <div className="mt-2 flex items-center gap-1">
        {dietitian.average_rating !== null ? (
          <Badge variant="secondary" className="gap-1 rounded-full px-2 py-0.5 text-[11px] font-bold">
            <Star className="size-3 fill-current" />
            {dietitian.average_rating.toFixed(1)}
            <span className="font-normal text-muted-foreground">({dietitian.review_count})</span>
          </Badge>
        ) : (
          <span className="text-[11px] text-muted-foreground">Brak ocen</span>
        )}
      </div>
    </button>
  )
}

function ThreadCard({
  thread,
  onOpen,
}: {
  thread: DietitianThread
  onOpen: (threadId: string) => void
}) {
  const name = thread.other_participant_name ?? 'Nieznany użytkownik'
  const initials = name.slice(0, 2).toUpperCase()

  return (
    <button
      type="button"
      onClick={() => onOpen(thread.id)}
      className="w-full rounded-2xl border border-border bg-background p-3 text-left hover:bg-accent/40"
    >
      <div className="flex items-center gap-2.5">
        <Avatar className="size-9 border border-border">
          <AvatarFallback className="bg-gradient-to-br from-secondary to-secondary-foreground/30 font-bold text-secondary-foreground">
            {initials}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[13px] font-bold text-foreground">{name}</p>
          <p className="text-[11px] text-muted-foreground">Otwórz czat</p>
        </div>
      </div>
    </button>
  )
}

export function RightRail({ onCollapse }: RightRailProps) {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [selectedDietitianId, setSelectedDietitianId] = useState<string | null>(null)

  const dietitiansQuery = useQuery({
    queryKey: ['dietitian-listing'],
    queryFn: listDietitians,
  })
  const purchasesQuery = useQuery({
    queryKey: ['my-purchases'],
    queryFn: getMyPurchases,
    enabled: isAuthenticated,
  })
  // Symmetric on purpose — GET /messaging/threads already returns a
  // thread regardless of which side the caller is on, so this one query
  // serves a buyer's dietitian-contacts list and a dietitian's client
  // list with no role branching needed here.
  const threadsQuery = useQuery({
    queryKey: ['my-dietitian-threads'],
    queryFn: listMyDietitianThreads,
    enabled: isAuthenticated,
  })
  const threads = threadsQuery.data ?? []

  const engagedDietitianIds = new Set(
    (purchasesQuery.data ?? [])
      .map((purchase) => purchase.dietitian_id)
      .filter((id): id is string => id !== null),
  )
  const dietitians = dietitiansQuery.data ?? []
  const pinned = dietitians.filter((d) => engagedDietitianIds.has(d.user_id))
  const rest = dietitians.filter((d) => !engagedDietitianIds.has(d.user_id))

  return (
    <>
      <div className="fixed inset-0 z-30 bg-black/40 md:hidden" onClick={onCollapse} aria-hidden="true" data-testid="rail-backdrop" />
      <aside className="fixed inset-y-0 right-0 z-40 flex h-full w-64 flex-col border-l border-border bg-card md:static md:z-auto">
        <div className="flex items-center justify-between p-3.5 pb-2">
          <span className="text-xs font-bold tracking-wide text-muted-foreground uppercase">
            Dietetycy
          </span>
          <div className="flex items-center gap-0.5">
            {isAuthenticated && <NotificationsBell />}
            <Button variant="ghost" size="icon" onClick={onCollapse} aria-label="Zwiń panel">
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-3.5 pb-3.5">
          {threads.length > 0 && (
            <div className="mb-3 flex flex-col gap-2">
              <span className="text-[11px] font-bold tracking-wide text-muted-foreground uppercase">
                Wiadomości
              </span>
              {threads.map((thread) => (
                <ThreadCard
                  key={thread.id}
                  thread={thread}
                  onOpen={(threadId) => navigate(`/dietitian-chat/${threadId}`)}
                />
              ))}
            </div>
          )}

          {dietitiansQuery.isPending ? (
            <div className="flex flex-col gap-2" role="status" aria-label="Ładowanie listy dietetyków…">
              <Skeleton className="h-20 w-full rounded-2xl" />
              <Skeleton className="h-20 w-full rounded-2xl" />
              <Skeleton className="h-20 w-full rounded-2xl" />
            </div>
          ) : dietitiansQuery.isError ? (
            <p className="px-1 py-4 text-xs text-destructive">
              Nie udało się wczytać listy dietetyków.
            </p>
          ) : dietitians.length === 0 ? (
            <EmptyState icon={Users} message="Brak dostępnych dietetyków." />
          ) : (
            <div className="flex flex-col gap-3">
              {pinned.length > 0 && (
                <div className="flex flex-col gap-2">
                  <span className="text-[11px] font-bold tracking-wide text-muted-foreground uppercase">
                    Twoi dietetycy
                  </span>
                  {pinned.map((dietitian) => (
                    <DietitianCard
                      key={dietitian.user_id}
                      dietitian={dietitian}
                      onSelect={setSelectedDietitianId}
                    />
                  ))}
                </div>
              )}
              <div className="flex flex-col gap-2">
                {pinned.length > 0 && (
                  <span className="text-[11px] font-bold tracking-wide text-muted-foreground uppercase">
                    Wszyscy dietetycy
                  </span>
                )}
                {rest.map((dietitian) => (
                  <DietitianCard
                    key={dietitian.user_id}
                    dietitian={dietitian}
                    onSelect={setSelectedDietitianId}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </aside>

      <DietitianProfileModal
        dietitianId={selectedDietitianId}
        onOpenChange={(open) => {
          if (!open) setSelectedDietitianId(null)
        }}
      />
    </>
  )
}
