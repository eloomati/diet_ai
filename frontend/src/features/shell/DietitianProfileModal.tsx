import { Star } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { getPublicDietitianProfile } from '@/api/dietitian'
import { OFFER_LABEL, OFFER_PRICE, createTransaction, getMyPurchases } from '@/api/transactions'
import type { OfferType, Transaction } from '@/api/transactions'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useAuth } from '@/lib/auth'
import { ApiError, resolveStaticUrl } from '@/lib/apiFetch'
import { notifyError, notifyInfo } from '@/lib/toast'

const OFFERS: OfferType[] = ['PLAN_REVIEW', 'INDIVIDUAL_PLAN']

interface DietitianProfileModalProps {
  dietitianId: string | null
  onOpenChange: (open: boolean) => void
}

interface ActivePayment {
  offerType: OfferType
  transaction: Transaction
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Coś poszło nie tak. Spróbuj ponownie.'
}

function OfferRow({
  offer,
  existing,
  disabledReason,
  isPending,
  onApply,
  onGoToPayment,
}: {
  offer: OfferType
  existing: Transaction | undefined
  disabledReason: string | null
  isPending: boolean
  onApply: (offer: OfferType) => void
  onGoToPayment: (offer: OfferType, transaction: Transaction) => void
}) {
  return (
    <div className="flex items-center justify-between gap-2 rounded-xl border border-border p-3">
      <div>
        <p className="text-sm font-bold">{OFFER_LABEL[offer]}</p>
        <p className="text-xs text-muted-foreground">{OFFER_PRICE[offer]} zł</p>
      </div>
      {existing?.status === 'PAID' ? (
        <Badge className="gap-1 rounded-full px-2 py-0.5 text-xs font-bold">Opłacone ✓</Badge>
      ) : existing ? (
        <Button size="sm" variant="outline" onClick={() => onGoToPayment(offer, existing)}>
          Przejdź do płatności
        </Button>
      ) : disabledReason ? (
        <Button size="sm" disabled title={disabledReason}>
          Zgłoś się
        </Button>
      ) : (
        <Button size="sm" onClick={() => onApply(offer)} disabled={isPending}>
          {isPending ? 'Wysyłanie…' : 'Zgłoś się'}
        </Button>
      )}
    </div>
  )
}

export function DietitianProfileModal({ dietitianId, onOpenChange }: DietitianProfileModalProps) {
  const { isAuthenticated, user } = useAuth()
  const queryClient = useQueryClient()
  const [activePayment, setActivePayment] = useState<ActivePayment | null>(null)

  useEffect(() => {
    setActivePayment(null)
  }, [dietitianId])

  const profileQuery = useQuery({
    queryKey: ['dietitian-profile', dietitianId],
    queryFn: () => getPublicDietitianProfile(dietitianId!),
    enabled: dietitianId !== null,
  })
  const purchasesQuery = useQuery({
    queryKey: ['my-purchases'],
    queryFn: getMyPurchases,
    enabled: isAuthenticated,
  })

  const createMutation = useMutation({
    mutationFn: (offerType: OfferType) =>
      createTransaction({ dietitian_id: dietitianId!, offer_type: offerType }),
    onSuccess: (transaction) => {
      void queryClient.invalidateQueries({ queryKey: ['my-purchases'] })
      setActivePayment({ offerType: transaction.offer_type, transaction })
    },
    onError: (error) => notifyError(errorMessage(error)),
  })

  function existingTransactionFor(offer: OfferType): Transaction | undefined {
    return purchasesQuery.data?.find((t) => t.dietitian_id === dietitianId && t.offer_type === offer)
  }

  function disabledReasonFor(): string | null {
    if (!isAuthenticated) return 'Zaloguj się, aby się zgłosić'
    if (user?.user_id === dietitianId) return 'Nie możesz zgłosić się do własnej oferty'
    return null
  }

  function handlePay() {
    notifyInfo('Dziękujemy! Administrator potwierdzi płatność ręcznie.')
    setActivePayment(null)
  }

  return (
    <Dialog open={dietitianId !== null} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[80vh] max-h-[640px] w-full flex-col overflow-hidden p-0 sm:max-w-2xl">
        <DialogTitle className="sr-only">Profil dietetyka</DialogTitle>
        <ScrollArea className="min-h-0 flex-1">
          <div className="p-6">
            {activePayment ? (
              <div className="flex flex-col gap-4">
                <button
                  type="button"
                  onClick={() => setActivePayment(null)}
                  className="w-fit text-xs font-bold text-muted-foreground hover:text-foreground"
                >
                  ← Wróć do profilu
                </button>
                <div className="rounded-xl border border-border p-4">
                  <p className="text-xs font-bold tracking-wide text-muted-foreground uppercase">
                    Płatność
                  </p>
                  <p className="mt-2 text-sm font-bold">{OFFER_LABEL[activePayment.offerType]}</p>
                  <p className="text-sm text-muted-foreground">
                    {activePayment.transaction.amount} zł
                  </p>
                  <p className="mt-3 text-xs text-muted-foreground">
                    To wersja demonstracyjna — nie ma tu prawdziwej bramki płatności ani
                    formularza karty. Po kliknięciu "Zapłać" administrator ręcznie potwierdzi
                    wpłatę z panelu administracyjnego.
                  </p>
                  <Button className="mt-4 w-fit" onClick={handlePay}>
                    Zapłać
                  </Button>
                </div>
              </div>
            ) : profileQuery.isPending ? (
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
                      <OfferRow
                        key={offer}
                        offer={offer}
                        existing={existingTransactionFor(offer)}
                        disabledReason={disabledReasonFor()}
                        isPending={createMutation.isPending && createMutation.variables === offer}
                        onApply={(o) => createMutation.mutate(o)}
                        onGoToPayment={(offerType, transaction) =>
                          setActivePayment({ offerType, transaction })
                        }
                      />
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
