import { Star } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'

import { getPublicDietitianProfile } from '@/api/dietitian'
import { OFFER_LABEL, OFFER_PRICE } from '@/api/transactions'
import type { OfferType } from '@/api/transactions'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ApiError, resolveStaticUrl } from '@/lib/apiFetch'

const OFFERS: OfferType[] = ['PLAN_REVIEW', 'INDIVIDUAL_PLAN']

interface DietitianProfileModalProps {
  dietitianId: string | null
  onOpenChange: (open: boolean) => void
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Coś poszło nie tak. Spróbuj ponownie.'
}

export function DietitianProfileModal({ dietitianId, onOpenChange }: DietitianProfileModalProps) {
  const profileQuery = useQuery({
    queryKey: ['dietitian-profile', dietitianId],
    queryFn: () => getPublicDietitianProfile(dietitianId!),
    enabled: dietitianId !== null,
  })

  return (
    <Dialog open={dietitianId !== null} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[80vh] max-h-[640px] w-full flex-col overflow-hidden p-0 sm:max-w-2xl">
        <DialogTitle className="sr-only">Profil dietetyka</DialogTitle>
        <ScrollArea className="min-h-0 flex-1">
          <div className="p-6">
            {profileQuery.isPending ? (
              <p className="text-sm text-muted-foreground">Ładowanie profilu…</p>
            ) : profileQuery.isError ? (
              <p className="text-sm text-destructive">{errorMessage(profileQuery.error)}</p>
            ) : (
              <div className="flex flex-col gap-6">
                <div className="flex items-start gap-3">
                  <Avatar size="lg" className="border border-border">
                    {profileQuery.data.photos[0] && (
                      <AvatarImage src={resolveStaticUrl(profileQuery.data.photos[0])} alt="" />
                    )}
                    <AvatarFallback className="bg-gradient-to-br from-primary to-accent-foreground/40 font-bold text-primary-foreground">
                      {profileQuery.data.email.slice(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="font-heading text-lg font-extrabold">{profileQuery.data.email}</p>
                    {profileQuery.data.average_rating !== null ? (
                      <Badge
                        variant="secondary"
                        className="mt-1 gap-1 rounded-full px-2 py-0.5 text-xs font-bold"
                      >
                        <Star className="size-3 fill-current" />
                        {profileQuery.data.average_rating.toFixed(1)}
                        <span className="font-normal text-muted-foreground">
                          ({profileQuery.data.review_count})
                        </span>
                      </Badge>
                    ) : (
                      <p className="mt-1 text-xs text-muted-foreground">Brak ocen</p>
                    )}
                  </div>
                </div>

                <div>
                  <p className="mb-1 text-xs font-bold tracking-wide text-muted-foreground uppercase">
                    Doświadczenie
                  </p>
                  <p className="text-sm">{profileQuery.data.experience}</p>
                </div>

                {profileQuery.data.diplomas.length > 0 && (
                  <div>
                    <p className="mb-1 text-xs font-bold tracking-wide text-muted-foreground uppercase">
                      Dyplomy
                    </p>
                    <ul className="list-disc pl-5 text-sm">
                      {profileQuery.data.diplomas.map((diploma) => (
                        <li key={diploma}>{diploma}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div>
                  <p className="mb-1 text-xs font-bold tracking-wide text-muted-foreground uppercase">
                    Opis
                  </p>
                  <p className="text-sm whitespace-pre-line">{profileQuery.data.description}</p>
                </div>

                {profileQuery.data.photos.length > 0 && (
                  <div>
                    <p className="mb-1 text-xs font-bold tracking-wide text-muted-foreground uppercase">
                      Zdjęcia
                    </p>
                    <div className="flex flex-wrap gap-3">
                      {profileQuery.data.photos.map((photo) => (
                        <img
                          key={photo}
                          src={resolveStaticUrl(photo)}
                          alt=""
                          className="size-24 rounded-lg border border-border object-cover"
                        />
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <p className="mb-2 text-xs font-bold tracking-wide text-muted-foreground uppercase">
                    Oferty
                  </p>
                  <div className="flex flex-col gap-2">
                    {OFFERS.map((offer) => (
                      <div
                        key={offer}
                        className="flex items-center justify-between gap-2 rounded-xl border border-border p-3"
                      >
                        <div>
                          <p className="text-sm font-bold">{OFFER_LABEL[offer]}</p>
                          <p className="text-xs text-muted-foreground">{OFFER_PRICE[offer]} zł</p>
                        </div>
                        {/* Stage 4 wires this up to actually create a
                            transaction and show the payment stub — this
                            stage only presents the offers. */}
                        <Button size="sm" disabled title="Wkrótce dostępne">
                          Zgłoś się
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="mb-2 text-xs font-bold tracking-wide text-muted-foreground uppercase">
                    Opinie ({profileQuery.data.review_count})
                  </p>
                  {profileQuery.data.reviews.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Brak opinii.</p>
                  ) : (
                    <div className="flex flex-col gap-2">
                      {profileQuery.data.reviews.map((review, index) => (
                        <div key={index} className="rounded-xl border border-border p-3">
                          <div className="flex items-center gap-1">
                            <Star className="size-3 fill-current text-primary" />
                            <span className="text-sm font-bold">{review.rating}/10</span>
                            <span className="ml-auto text-xs text-muted-foreground">
                              {new Date(review.created_at).toLocaleDateString('pl-PL')}
                            </span>
                          </div>
                          <p className="mt-1 text-sm">{review.comment}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}
