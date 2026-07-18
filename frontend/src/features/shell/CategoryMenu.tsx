import { Check, Plus } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { CATEGORY_OPTIONS } from '@/lib/categoryOptions'
import { cn } from '@/lib/utils'
import type { ConversationCategory } from '@/api/conversations'

interface CategoryMenuProps {
  onStartChat: (categories: ConversationCategory[]) => void
}

export function CategoryMenu({ onStartChat }: CategoryMenuProps) {
  const [open, setOpen] = useState(false)
  const [selected, setSelected] = useState<ConversationCategory[]>([])

  function toggleOpen() {
    setOpen((wasOpen) => {
      if (!wasOpen) setSelected([])
      return !wasOpen
    })
  }

  function toggleCategory(value: ConversationCategory) {
    setSelected((current) =>
      current.includes(value) ? current.filter((c) => c !== value) : [...current, value],
    )
  }

  function handleConfirm() {
    if (selected.length === 0) return
    onStartChat(selected)
    setOpen(false)
  }

  return (
    <div className="relative">
      <Button variant="outline" className="w-full justify-start gap-2" onClick={toggleOpen}>
        <Plus className="size-4" />
        Nowy czat
      </Button>

      {open && (
        <div className="absolute top-[calc(100%+6px)] right-0 left-0 z-20 flex flex-col gap-0.5 rounded-2xl border border-border bg-popover p-1.5 shadow-lg">
          <p className="px-2.5 pt-1.5 pb-1 text-[10.5px] font-bold tracking-wide text-muted-foreground uppercase">
            Wybierz kategorie (min. 1)
          </p>
          {CATEGORY_OPTIONS.map((option) => {
            const checked = selected.includes(option.value)
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => toggleCategory(option.value)}
                className={cn(
                  'flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-[13px] font-bold',
                  checked ? 'bg-accent text-accent-foreground' : 'text-foreground hover:bg-accent/60',
                )}
              >
                <span
                  className={cn(
                    'flex size-4 items-center justify-center rounded border',
                    checked ? 'border-primary bg-primary text-primary-foreground' : 'border-border',
                  )}
                >
                  {checked && <Check className="size-3" />}
                </span>
                {option.emoji} {option.label}
              </button>
            )
          })}
          <Button className="mt-1" disabled={selected.length === 0} onClick={handleConfirm}>
            Rozpocznij czat
          </Button>
        </div>
      )}
    </div>
  )
}
