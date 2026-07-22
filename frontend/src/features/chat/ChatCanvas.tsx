import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Archive, ArrowUp, Menu, Sparkles, Trash2 } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { FieldError } from '@/components/FieldError'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { MyceloNotificationBadge } from '@/components/MyceloNotificationBadge'
import { categoryEmoji } from '@/lib/categoryOptions'
import { ApiError } from '@/lib/apiFetch'
import { notifyError, notifyInfo } from '@/lib/toast'
import { useAuth } from '@/lib/auth'
import { useUnreadNotificationsCount } from '@/hooks/useUnreadNotificationsCount'
import { archiveConversation, deleteConversation, getConversation, sendMessage } from '@/api/conversations'
import type { ConversationCategory, ConversationDetail, Message } from '@/api/conversations'
import { generateDietPlan } from '@/api/dietPlans'
import { DietPlanCard } from '@/features/dietPlans/DietPlanCard'

interface HeroChip {
  emoji: string
  label: string
  category: ConversationCategory
  prompt: string
}

const HERO_CHIPS: HeroChip[] = [
  {
    emoji: '🥗',
    label: 'Zaplanuj dietę',
    category: 'DIET',
    prompt: 'Chcę schudnąć, jestem wegetarianką i trenuję 3x w tygodniu.',
  },
  {
    emoji: '🏃',
    label: 'Trening a jedzenie',
    category: 'FITNESS',
    prompt: 'Biegam 5 razy w tygodniu — co jeść przed i po treningu?',
  },
  {
    emoji: '💊',
    label: 'Suplementy',
    category: 'SUPPLEMENTS',
    prompt: 'Czy warto suplementować witaminę D zimą?',
  },
]

const ARCHIVED_NOTICE = 'Ta rozmowa jest zarchiwizowana — nie można już do niej pisać.'

function sendErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.code === 'CONFLICT') {
    return ARCHIVED_NOTICE
  }
  return 'Nie udało się wysłać wiadomości. Spróbuj ponownie.'
}

const GENERATE_ERROR_MESSAGES: Record<string, string> = {
  NOT_FOUND: 'Uzupełnij najpierw profil żywieniowy (zakładka Profil), żeby wygenerować plan.',
}

function generateErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return GENERATE_ERROR_MESSAGES[error.code] ?? 'Nie udało się wygenerować planu. Spróbuj ponownie.'
  return 'Nie udało się wygenerować planu. Spróbuj ponownie.'
}

function MessageBubble({ message }: { message: Message }) {
  if (message.role === 'SYSTEM') {
    return <p className="text-center text-[12px] text-muted-foreground">{message.content}</p>
  }
  const isUser = message.role === 'USER'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <p
        className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-[14px] leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'rounded-br-sm bg-primary text-primary-foreground'
            : 'rounded-bl-sm bg-card text-card-foreground shadow-sm'
        }`}
      >
        {message.content}
      </p>
    </div>
  )
}

interface ChatCanvasProps {
  leftCollapsed: boolean
  rightCollapsed: boolean
  onExpandLeft: () => void
  onExpandRight: () => void
  /** From the /:conversationId route param. */
  conversationId?: string
}

export function ChatCanvas({
  leftCollapsed,
  rightCollapsed,
  onExpandLeft,
  onExpandRight,
  conversationId,
}: ChatCanvasProps) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const unreadNotificationsCount = useUnreadNotificationsCount(isAuthenticated)
  const [message, setMessage] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)

  const conversationQuery = useQuery({
    queryKey: ['conversation', conversationId],
    // A missing/deleted conversation (404) is a permanent state, not a
    // transient failure worth retrying.
    queryFn: () => getConversation(conversationId!),
    retry: false,
    enabled: !!conversationId,
  })

  const messages = conversationQuery.data?.messages ?? []

  useEffect(() => {
    scrollRef.current?.scrollTo?.({ top: scrollRef.current.scrollHeight })
  }, [messages.length])

  const OPTIMISTIC_USER_MESSAGE_ID = 'optimistic-user-message'

  const sendMessageMutation = useMutation({
    mutationFn: (content: string) => sendMessage(conversationId!, content),
    // The user's own bubble appears immediately on submit, not only once the
    // full AI round trip completes — the assistant's reply still arrives via
    // onSuccess below, reconciling this temporary message with its real id.
    onMutate: (content: string) => {
      const previous = queryClient.getQueryData<ConversationDetail>(['conversation', conversationId])
      queryClient.setQueryData(['conversation', conversationId], (old?: ConversationDetail) =>
        old && {
          ...old,
          messages: [
            ...old.messages,
            {
              id: OPTIMISTIC_USER_MESSAGE_ID,
              role: 'USER' as const,
              content,
              created_at: new Date().toISOString(),
            },
          ],
        },
      )
      setMessage('')
      return { previous }
    },
    onSuccess: (result, content) => {
      const now = new Date().toISOString()
      queryClient.setQueryData(['conversation', conversationId], (old?: ConversationDetail) =>
        old && {
          ...old,
          messages: [
            ...old.messages.filter((msg) => msg.id !== OPTIMISTIC_USER_MESSAGE_ID),
            { id: result.user_message_id, role: 'USER' as const, content, created_at: now },
            {
              id: result.assistant_message_id,
              role: 'ASSISTANT' as const,
              content: result.assistant_content,
              created_at: now,
            },
          ],
        },
      )
      void queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
    onError: (_error, content, context) => {
      queryClient.setQueryData(['conversation', conversationId], context?.previous)
      setMessage(content)
    },
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const content = message.trim()
    if (!conversationId || !content || sendMessageMutation.isPending) return
    sendMessageMutation.mutate(content)
  }

  const archiveMutation = useMutation({
    mutationFn: () => archiveConversation(conversationId!),
    onSuccess: (updated) => {
      queryClient.setQueryData(['conversation', conversationId], updated)
      void queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
    onError: () => notifyError('Nie udało się zarchiwizować rozmowy. Spróbuj ponownie.'),
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteConversation(conversationId!),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ['conversation', conversationId] })
      void queryClient.invalidateQueries({ queryKey: ['conversations'] })
      navigate('/')
    },
    onError: () => notifyError('Nie udało się usunąć rozmowy. Spróbuj ponownie.'),
  })

  function handleDelete() {
    if (window.confirm('Czy na pewno chcesz usunąć tę rozmowę? Tej operacji nie można cofnąć.')) {
      deleteMutation.mutate()
    }
  }

  const generatePlanMutation = useMutation({
    mutationFn: () =>
      generateDietPlan({
        duration_days: 3,
        requirements: message.trim() ? [message.trim()] : undefined,
      }),
    onSuccess: () => notifyInfo('Plan wygenerowany! Zobacz go poniżej.'),
    onError: (error) => notifyError(generateErrorMessage(error)),
  })

  const isArchived = conversationQuery.data?.status === 'ARCHIVED'

  // Once a send is in flight (or has completed), keep showing the message
  // list instead of snapping back to the hero — otherwise the "pisze
  // odpowiedź…" indicator for a brand-new conversation's first message
  // would be hidden behind the hero until the reply arrives.
  const showHero =
    !conversationId || (conversationQuery.isSuccess && messages.length === 0 && sendMessageMutation.isIdle)

  return (
    <main className="flex min-w-0 flex-1 flex-col">
      <header className="relative flex min-h-12 items-center justify-center gap-2.5 border-b border-border/70 px-4 py-3.5">
        {leftCollapsed && (
          <Button
            variant="outline"
            size="icon"
            className="absolute top-2 left-3.5"
            onClick={onExpandLeft}
            aria-label="Rozwiń panel"
          >
            <Menu className="size-3.5" />
          </Button>
        )}
        <div className="flex flex-wrap items-center justify-center gap-1.5">
          {conversationId ? (
            conversationQuery.data ? (
              <>
                {conversationQuery.data.categories.map((category) => (
                  <Badge key={category} variant="secondary" className="rounded-full px-2.5 py-1 text-[11px] font-bold">
                    {categoryEmoji(category)} {category}
                  </Badge>
                ))}
                {isArchived && (
                  <Badge className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-bold text-muted-foreground">
                    Zarchiwizowana
                  </Badge>
                )}
                {!isArchived && (
                  <Button
                    variant="ghost"
                    size="icon-xs"
                    className="rounded-full text-muted-foreground"
                    onClick={() => archiveMutation.mutate()}
                    disabled={archiveMutation.isPending}
                    aria-label="Archiwizuj rozmowę"
                  >
                    <Archive className="size-3.5" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon-xs"
                  className="rounded-full text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                  onClick={handleDelete}
                  disabled={deleteMutation.isPending}
                  aria-label="Usuń rozmowę"
                >
                  <Trash2 className="size-3.5" />
                </Button>
              </>
            ) : conversationQuery.isError ? (
              <span className="text-[13.5px] font-bold text-destructive">Nie znaleziono rozmowy</span>
            ) : (
              <span className="font-mono text-[12.5px] font-bold text-muted-foreground">
                Rozmowa #{conversationId.slice(0, 8)}
              </span>
            )
          ) : (
            <span className="text-[13.5px] font-bold text-muted-foreground">Nowa rozmowa</span>
          )}
        </div>
        {rightCollapsed && (
          <div className="absolute top-2 right-3.5 flex items-center gap-1.5">
            {isAuthenticated && (
              <MyceloNotificationBadge unreadCount={unreadNotificationsCount} onClick={onExpandRight} />
            )}
            <Button
              variant="outline"
              size="icon"
              onClick={onExpandRight}
              aria-label="Rozwiń panel"
            >
              <Sparkles className="size-3.5" />
            </Button>
          </div>
        )}
      </header>

      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto px-5 pt-5">
        {showHero ? (
          <div className="mx-auto mt-[6%] max-w-xl text-center">
            <p className="mb-3.5 inline-block rounded-full bg-accent px-3 py-1 text-xs font-bold text-accent-foreground uppercase">
              Mycelo
            </p>
            <h1 className="mb-2.5 font-[family-name:var(--font-heading)] text-[27px] leading-tight text-balance">
              Cześć! W czym mogę Ci dziś pomóc?
            </h1>
            <p className="mb-5 text-[14.5px] leading-relaxed text-muted-foreground">
              Zapytaj o dietę, trening albo napisz, co ostatnio jadłaś/-eś — zaproponuję plan skrojony
              pod Ciebie.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {HERO_CHIPS.map((chip) => (
                <button
                  key={chip.category}
                  onClick={() => setMessage(chip.prompt)}
                  className="rounded-full border border-border bg-card px-3.5 py-2 text-[13px] font-bold hover:border-primary hover:bg-accent hover:text-accent-foreground"
                >
                  {chip.emoji} {chip.label}
                </button>
              ))}
            </div>
          </div>
        ) : conversationQuery.isPending ? (
          <div className="mx-auto flex max-w-2xl flex-col gap-3 pb-3" role="status" aria-label="Ładowanie rozmowy…">
            <Skeleton className="h-10 w-2/5 self-end rounded-2xl rounded-br-sm" />
            <Skeleton className="h-16 w-3/5 self-start rounded-2xl rounded-bl-sm" />
            <Skeleton className="h-10 w-1/3 self-end rounded-2xl rounded-br-sm" />
          </div>
        ) : conversationQuery.isError ? (
          <p className="mx-auto mt-8 text-center text-sm text-destructive">
            Nie udało się wczytać tej rozmowy — mogła zostać usunięta.
          </p>
        ) : (
          <div className="mx-auto flex max-w-2xl flex-col gap-3 pb-3">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {sendMessageMutation.isPending && (
              <p className="text-[13px] text-muted-foreground">Mycelo pisze odpowiedź…</p>
            )}
          </div>
        )}

        {generatePlanMutation.isPending && (
          <p className="mx-auto mt-4 max-w-2xl text-center text-sm text-muted-foreground">
            Generowanie planu…
          </p>
        )}
        {generatePlanMutation.data && (
          <div className="mx-auto mt-4 max-w-2xl pb-3">
            <DietPlanCard plan={generatePlanMutation.data} />
          </div>
        )}
      </div>

      <form className="flex flex-col items-center gap-2.5 px-5 py-5" onSubmit={handleSubmit}>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          className="rounded-full"
          onClick={() => generatePlanMutation.mutate()}
          disabled={generatePlanMutation.isPending}
        >
          <span className="size-1.5 rounded-full bg-current" />
          {generatePlanMutation.isPending ? 'Generowanie…' : 'Generuj plan'}
        </Button>
        {isArchived ? (
          <p className="text-[12.5px] font-bold text-muted-foreground">{ARCHIVED_NOTICE}</p>
        ) : (
          sendMessageMutation.isError && <FieldError message={sendErrorMessage(sendMessageMutation.error)} />
        )}
        <div className="flex w-full max-w-xl items-center gap-2 rounded-full border border-border bg-card py-1.5 pr-1.5 pl-4.5 shadow-sm focus-within:border-primary">
          <input
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Napisz wiadomość…"
            disabled={isArchived || sendMessageMutation.isPending}
            className="flex-1 border-none bg-transparent py-2 text-sm outline-none placeholder:text-muted-foreground/70 disabled:opacity-60"
          />
          <Button
            type="submit"
            size="icon"
            className="size-8.5 rounded-full"
            aria-label="Wyślij"
            disabled={!conversationId || !message.trim() || isArchived || sendMessageMutation.isPending}
          >
            <ArrowUp className="size-4" />
          </Button>
        </div>
      </form>
    </main>
  )
}
