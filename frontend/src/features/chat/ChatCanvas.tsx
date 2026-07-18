import { ArrowUp, Menu, Sparkles } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { categoryEmoji } from '@/lib/categoryOptions'
import type { ConversationCategory } from '@/api/conversations'

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

interface ChatCanvasProps {
  leftCollapsed: boolean
  rightCollapsed: boolean
  onExpandLeft: () => void
  onExpandRight: () => void
  activeCategories: ConversationCategory[]
  /** From the /:conversationId route param — read here, not yet fetched (Etap 3). */
  conversationId?: string
}

export function ChatCanvas({
  leftCollapsed,
  rightCollapsed,
  onExpandLeft,
  onExpandRight,
  activeCategories,
  conversationId,
}: ChatCanvasProps) {
  const [message, setMessage] = useState('')

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
          {activeCategories.length > 0 ? (
            activeCategories.map((category) => (
              <span
                key={category}
                className="rounded-full bg-secondary px-2.5 py-1 text-[11px] font-bold text-secondary-foreground"
              >
                {categoryEmoji(category)} {category}
              </span>
            ))
          ) : conversationId ? (
            <span className="font-mono text-[12.5px] font-bold text-muted-foreground">
              Rozmowa #{conversationId.slice(0, 8)}
            </span>
          ) : (
            <span className="text-[13.5px] font-bold text-muted-foreground">Nowa rozmowa</span>
          )}
        </div>
        {rightCollapsed && (
          <Button
            variant="outline"
            size="icon"
            className="absolute top-2 right-3.5"
            onClick={onExpandRight}
            aria-label="Rozwiń panel"
          >
            <Sparkles className="size-3.5" />
          </Button>
        )}
      </header>

      <div className="flex-1 overflow-y-auto px-5 pt-5">
        <div className="mx-auto mt-[6%] max-w-xl text-center">
          <p className="mb-3.5 inline-block rounded-full bg-accent px-3 py-1 text-xs font-bold text-accent-foreground uppercase">
            Diet AI
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
      </div>

      <form
        className="flex flex-col items-center gap-2.5 px-5 py-5"
        onSubmit={(event) => event.preventDefault()}
      >
        <Button type="button" variant="secondary" size="sm" className="rounded-full">
          <span className="size-1.5 rounded-full bg-current" />
          Generuj plan
        </Button>
        <div className="flex w-full max-w-xl items-center gap-2 rounded-full border border-border bg-card py-1.5 pr-1.5 pl-4.5 shadow-sm focus-within:border-primary">
          <input
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Napisz wiadomość…"
            className="flex-1 border-none bg-transparent py-2 text-sm outline-none placeholder:text-muted-foreground/70"
          />
          <Button type="submit" size="icon" className="size-8.5 rounded-full" aria-label="Wyślij">
            <ArrowUp className="size-4" />
          </Button>
        </div>
      </form>
    </main>
  )
}
