import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, Info } from 'lucide-react'
import { useState } from 'react'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/lib/auth'
import { formatCategories } from '@/lib/categoryOptions'
import { listConversations } from '@/api/conversations'
import type { ConversationCategory, ConversationSummary } from '@/api/conversations'
import { cn } from '@/lib/utils'

import { AboutDialog } from './AboutDialog'
import { CategoryMenu } from './CategoryMenu'

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
    <aside className="flex h-full w-62 flex-col border-r border-border bg-card">
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
          <p className="mt-1.5 text-[11.5px] font-bold text-destructive">
            Nie udało się utworzyć rozmowy. Spróbuj ponownie.
          </p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-2.5">
        {isAuthenticated ? (
          conversationsQuery.isPending ? (
            <p className="px-2.5 py-4 text-xs text-muted-foreground">Ładowanie…</p>
          ) : conversationsQuery.isError ? (
            <p className="px-2.5 py-4 text-xs text-destructive">
              Nie udało się wczytać historii rozmów.
            </p>
          ) : conversationsQuery.data.length === 0 ? (
            <p className="px-2.5 py-4 text-xs text-muted-foreground">Brak jeszcze żadnych rozmów.</p>
          ) : (
            <ul className="flex flex-col gap-0.5 py-1.5">
              {conversationsQuery.data.map((conversation) => (
                <li key={conversation.conversation_id}>
                  <button
                    onClick={() => onSelectConversation(conversation)}
                    className={cn(
                      'w-full rounded-lg px-2.5 py-2 text-left text-[13px] font-bold hover:bg-accent/60',
                      conversation.conversation_id === activeConversationId
                        ? 'bg-accent text-accent-foreground'
                        : 'text-foreground',
                    )}
                  >
                    <span className="block truncate">{conversation.title}</span>
                    <span className="block truncate text-[11px] font-normal text-muted-foreground">
                      {formatCategories(conversation.categories)}
                      {conversation.status === 'ARCHIVED' ? ' · zarchiwizowana' : ''}
                    </span>
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
  )
}
