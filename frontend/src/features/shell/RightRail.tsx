import { useQuery } from '@tanstack/react-query'
import { ChevronRight, Star, Users } from 'lucide-react'
import { useState } from 'react'

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/EmptyState'
import { listDietitians } from '@/api/dietitian'
import type { DietitianListingItem } from '@/api/dietitian'
import { getMyPurchases } from '@/api/transactions'
import { useAuth } from '@/lib/auth'
import { resolveStaticUrl } from '@/lib/apiFetch'

import { DietitianProfileModal } from './DietitianProfileModal'

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
  const initials = dietitian.email.slice(0, 2).toUpperCase()
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
          <p className="truncate text-[13px] font-bold text-foreground">{dietitian.email}</p>
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

export function RightRail({ onCollapse }: RightRailProps) {
  const { isAuthenticated } = useAuth()
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
          <Button variant="ghost" size="icon" onClick={onCollapse} aria-label="Zwiń panel">
            <ChevronRight className="size-4" />
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto px-3.5 pb-3.5">
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
