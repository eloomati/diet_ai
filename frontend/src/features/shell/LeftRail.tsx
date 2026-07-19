import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, Info, MessageSquare } from 'lucide-react'
import { useState } from 'react'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/EmptyState'
import { FieldError } from '@/components/FieldError'
import { useAuth } from '@/lib/auth'
import { categoryEmoji, categoryLabel } from '@/lib/categoryOptions'
import { listConversations } from '@/api/conversations'
import type { ConversationCategory, ConversationSummary } from '@/api/conversations'
import { cn } from '@/lib/utils'

import { AboutDialog } from './AboutDialog'
import { CategoryMenu } from './CategoryMenu'

const MAX_VISIBLE_TAGS = 2

function ConversationRowTags({ conversation }: { conversation: ConversationSummary }) {
  const shown = conversation.categories.slice(0, MAX_VISIBLE_TAGS)
  const extra = conversation.categories.length - shown.length

  return (
    <span className="mt-1 flex flex-wrap items-center gap-1">
      {shown.map((category) => (
        <Badge
          key={category}
          className="rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-bold text-muted-foreground"
        >
          {categoryEmoji(category)} {categoryLabel(category)}
        </Badge>
      ))}
      {extra > 0 && (
        <Badge className="rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-bold text-muted-foreground">
          +{extra}
        </Badge>
      )}
      {conversation.status === 'ARCHIVED' && (
        <Badge variant="outline" className="rounded-full px-1.5 py-0.5 text-[10px] font-bold text-muted-foreground">
          Archiwum
        </Badge>
      )}
    </span>
  )
}

interface LeftRailProps {
  onProfileClick: () => void
  onCollapse: () => void
  onStartChat: (categories: ConversationCategory[]) => void
  onSelectConversation: (conversation: ConversationSummary) => void
  activeConversationId?: string
  createError: boolean
}

export function LeftRail({
  onProfileClick,
  onCollapse,
  onStartChat,
  onSelectConversation,
  activeConversationId,
  createError,
}: LeftRailProps) {
  const { isAuthenticated, user } = useAuth()
  const [aboutOpen, setAboutOpen] = useState(false)
  const initials = user?.email.slice(0, 2).toUpperCase() ?? '?'

  const conversationsQuery = useQuery({
    queryKey: ['conversations'],
    queryFn: listConversations,
    enabled: isAuthenticated,
  })

  return (
    <>
      {/* Below `md` the rail is an overlay, not a column — the backdrop
          closes it on click. `md:hidden` alone keeps it invisible on
          desktop, no viewport check needed here. */}
      <div className="fixed inset-0 z-30 bg-black/40 md:hidden" onClick={onCollapse} aria-hidden="true" data-testid="rail-backdrop" />
      <aside className="fixed inset-y-0 left-0 z-40 flex h-full w-62 flex-col border-r border-border bg-card md:static md:z-auto">
      <div className="flex items-center justify-between p-3.5 pb-2.5">
        <button onClick={onProfileClick} aria-label="Profil">
          <Avatar className="size-9 border border-border">
            <AvatarFallback className="bg-gradient-to-br from-primary to-accent-foreground/40 font-bold text-primary-foreground">
              {initials}
            </AvatarFallback>
          </Avatar>
        </button>
        <Button variant="ghost" size="icon" onClick={onCollapse} aria-label="Zwiń panel">
          <ChevronLeft className="size-4" />
        </Button>
      </div>

      <div className="px-3.5 pb-3">
        <CategoryMenu onStartChat={onStartChat} />
        {createError && (
          <FieldError message="Nie udało się utworzyć rozmowy. Spróbuj ponownie." className="mt-1.5" />
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-2.5">
        {isAuthenticated ? (
          conversationsQuery.isPending ? (
            <div className="flex flex-col gap-1.5 px-2.5 py-1.5" role="status" aria-label="Ładowanie historii rozmów…">
              <Skeleton className="h-11 w-full rounded-lg" />
              <Skeleton className="h-11 w-full rounded-lg" />
              <Skeleton className="h-11 w-full rounded-lg" />
            </div>
          ) : conversationsQuery.isError ? (
            <p className="px-2.5 py-4 text-xs text-destructive">
              Nie udało się wczytać historii rozmów.
            </p>
          ) : conversationsQuery.data.length === 0 ? (
            <EmptyState icon={MessageSquare} message="Brak jeszcze żadnych rozmów." />
          ) : (
            <ul className="flex flex-col gap-0.5 py-1.5">
              {[...conversationsQuery.data]
                .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
                .map((conversation) => (
                  <li key={conversation.conversation_id}>
                    <button
                      onClick={() => onSelectConversation(conversation)}
                      className={cn(
                        'w-full rounded-lg px-2.5 py-2 text-left text-[13px] font-bold hover:bg-accent/60',
                        conversation.conversation_id === activeConversationId
                          ? 'bg-accent text-accent-foreground'
                          : 'text-foreground',
                        conversation.status === 'ARCHIVED' && 'opacity-60',
                      )}
                    >
                      <span className="block truncate">{conversation.title}</span>
                      <ConversationRowTags conversation={conversation} />
                    </button>
                  </li>
                ))}
            </ul>
          )
        ) : (
          <div className="m-1 rounded-xl bg-muted p-3">
            <p className="mb-2 text-[12.5px] leading-relaxed text-muted-foreground">
              Zaloguj się, aby zapisywać i przeglądać historię rozmów.
            </p>
            <button
              onClick={onProfileClick}
              className="text-[12.5px] font-bold text-primary underline underline-offset-2"
            >
              Zaloguj się →
            </button>
          </div>
        )}
      </div>

      <div className="border-t border-border/70 p-3.5 pt-2.5">
        <Button
          variant="ghost"
          className="h-auto w-full justify-start gap-1.5 px-1 py-1.5 text-muted-foreground"
          onClick={() => setAboutOpen(true)}
        >
          <Info className="size-3.5" />
          <span className="text-[12.5px] font-bold">O nas</span>
        </Button>
        <p className="mt-0.5 px-1 text-[11px] text-muted-foreground/70">Diet AI · wersja beta</p>
      </div>

      <AboutDialog open={aboutOpen} onOpenChange={setAboutOpen} />
      </aside>
    </>
  )
}
