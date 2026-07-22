import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowUp, Menu, Sparkles } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'

import { FieldError } from '@/components/FieldError'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { MyceloNotificationBadge } from '@/components/MyceloNotificationBadge'
import { useUnreadNotificationsCount } from '@/hooks/useUnreadNotificationsCount'
import { getDietPlan, listDietPlans } from '@/api/dietPlans'
import { listMyDietitianThreads, listThreadMessages, sendDietitianMessage } from '@/api/messaging'
import type { DietitianMessage } from '@/api/messaging'
import { DietPlanCard } from '@/features/dietPlans/DietPlanCard'
import { useAuth } from '@/lib/auth'
import { ApiError } from '@/lib/apiFetch'
import { goalLabel } from '@/lib/profileOptions'

// No WebSocket for the human side either — same "confirmed polling
// decision" already governing the AI conversation and Stage 4's own
// notification badges.
const POLL_INTERVAL_MS = 4000
const PLAN_MESSAGE_CONTENT = 'Przesyłam mój wygenerowany plan.'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Coś poszło nie tak. Spróbuj ponownie.'
}

function PlanMessageBubble({ dietPlanId }: { dietPlanId: string }) {
  const planQuery = useQuery({
    queryKey: ['diet-plan', dietPlanId],
    queryFn: () => getDietPlan(dietPlanId),
    retry: false,
  })

  if (planQuery.isPending) {
    return <Skeleton className="mx-auto h-24 w-full max-w-2xl rounded-2xl" />
  }
  if (planQuery.isError) {
    return (
      <p className="mx-auto max-w-2xl text-center text-[12.5px] text-muted-foreground">
        Ten plan nie jest już dostępny.
      </p>
    )
  }
  return <DietPlanCard plan={planQuery.data} />
}

function MessageBubble({ message, isMine }: { message: DietitianMessage; isMine: boolean }) {
  if (message.diet_plan_id) {
    return <PlanMessageBubble dietPlanId={message.diet_plan_id} />
  }
  return (
    <div className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}>
      <p
        className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-[14px] leading-relaxed whitespace-pre-wrap ${
          isMine
            ? 'rounded-br-sm bg-primary text-primary-foreground'
            : 'rounded-bl-sm bg-card text-card-foreground shadow-sm'
        }`}
      >
        {message.content}
      </p>
    </div>
  )
}

interface HumanChatCanvasProps {
  leftCollapsed: boolean
  rightCollapsed: boolean
  onExpandLeft: () => void
  onExpandRight: () => void
  /** From the /dietitian-chat/:threadId route param. */
  threadId: string
}

export function HumanChatCanvas({
  leftCollapsed,
  rightCollapsed,
  onExpandLeft,
  onExpandRight,
  threadId,
}: HumanChatCanvasProps) {
  const { isAuthenticated, user } = useAuth()
  const unreadNotificationsCount = useUnreadNotificationsCount(isAuthenticated)
  const queryClient = useQueryClient()
  const [message, setMessage] = useState('')
  const [planPickerOpen, setPlanPickerOpen] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const threadsQuery = useQuery({
    queryKey: ['my-dietitian-threads'],
    queryFn: listMyDietitianThreads,
    enabled: isAuthenticated,
  })
  const thread = threadsQuery.data?.find((t) => t.id === threadId)
  // Which side of the pair the caller is — decides bubble alignment below.
  const myRole = thread && user && thread.user_id === user.user_id ? 'USER' : 'DIETITIAN'

  const messagesQuery = useQuery({
    queryKey: ['dietitian-thread-messages', threadId],
    queryFn: () => listThreadMessages(threadId),
    refetchInterval: POLL_INTERVAL_MS,
  })
  const messages = messagesQuery.data ?? []

  const plansQuery = useQuery({
    queryKey: ['diet-plans', undefined, undefined],
    queryFn: () => listDietPlans(),
    retry: false,
  })

  useEffect(() => {
    scrollRef.current?.scrollTo?.({ top: scrollRef.current.scrollHeight })
  }, [messages.length])

  const sendMutation = useMutation({
    mutationFn: (payload: { content: string; diet_plan_id?: string | null }) =>
      sendDietitianMessage(threadId, payload),
    onSuccess: (created) => {
      queryClient.setQueryData(
        ['dietitian-thread-messages', threadId],
        (old?: DietitianMessage[]) => (old ? [...old, created] : [created]),
      )
      setMessage('')
      setPlanPickerOpen(false)
    },
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const content = message.trim()
    if (!content || sendMutation.isPending) return
    sendMutation.mutate({ content })
  }

  function handleSendPlan(planId: string | null) {
    if (!planId || sendMutation.isPending) return
    sendMutation.mutate({ content: PLAN_MESSAGE_CONTENT, diet_plan_id: planId })
  }

  const isLoading = messagesQuery.isPending || threadsQuery.isPending

  return (
    <main className="bg-human-chat-background flex min-w-0 flex-1 flex-col">
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
        <span className="text-[13.5px] font-bold text-foreground">
          {thread?.other_participant_email ?? 'Rozmowa z dietetykiem'}
        </span>
        {rightCollapsed && (
          <div className="absolute top-2 right-3.5 flex items-center gap-1.5">
            <MyceloNotificationBadge unreadCount={unreadNotificationsCount} onClick={onExpandRight} />
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

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 pt-5">
        {isLoading ? (
          <div
            className="mx-auto flex max-w-2xl flex-col gap-3 pb-3"
            role="status"
            aria-label="Ładowanie wiadomości…"
          >
            <Skeleton className="h-10 w-2/5 self-end rounded-2xl rounded-br-sm" />
            <Skeleton className="h-16 w-3/5 self-start rounded-2xl rounded-bl-sm" />
          </div>
        ) : messagesQuery.isError ? (
          <p className="mx-auto mt-8 text-center text-sm text-destructive">
            Nie udało się wczytać wiadomości.
          </p>
        ) : messages.length === 0 ? (
          <p className="mx-auto mt-8 text-center text-sm text-muted-foreground">
            Brak jeszcze żadnych wiadomości. Napisz pierwszy!
          </p>
        ) : (
          <div className="mx-auto flex max-w-2xl flex-col gap-3 pb-3">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} isMine={msg.sender === myRole} />
            ))}
          </div>
        )}
      </div>

      <form className="flex flex-col items-center gap-2.5 px-5 py-5" onSubmit={handleSubmit}>
        {planPickerOpen &&
          (plansQuery.data && plansQuery.data.length > 0 ? (
            <div className="flex w-full max-w-xl items-center gap-2">
              <Select onValueChange={handleSendPlan}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Wybierz plan do wysłania" />
                </SelectTrigger>
                <SelectContent>
                  {plansQuery.data.map((plan) => (
                    <SelectItem key={plan.plan_id} value={plan.plan_id}>
                      {goalLabel(plan.goal)} · {plan.duration_days} dni
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setPlanPickerOpen(false)}
              >
                Anuluj
              </Button>
            </div>
          ) : (
            <p className="text-[12.5px] text-muted-foreground">
              Nie masz jeszcze żadnych wygenerowanych planów.
            </p>
          ))}
        {sendMutation.isError && <FieldError message={errorMessage(sendMutation.error)} />}
        <div className="flex w-full max-w-xl items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="rounded-full"
            onClick={() => setPlanPickerOpen((open) => !open)}
          >
            <span className="size-1.5 rounded-full bg-current" />
            Wyślij mój plan
          </Button>
        </div>
        <div className="flex w-full max-w-xl items-center gap-2 rounded-full border border-border bg-card py-1.5 pr-1.5 pl-4.5 shadow-sm focus-within:border-primary">
          <input
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Napisz wiadomość…"
            disabled={sendMutation.isPending}
            className="flex-1 border-none bg-transparent py-2 text-sm outline-none placeholder:text-muted-foreground/70 disabled:opacity-60"
          />
          <Button
            type="submit"
            size="icon"
            className="size-8.5 rounded-full"
            aria-label="Wyślij"
            disabled={!message.trim() || sendMutation.isPending}
          >
            <ArrowUp className="size-4" />
          </Button>
        </div>
      </form>
    </main>
  )
}
