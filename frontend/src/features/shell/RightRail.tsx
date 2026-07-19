import { ChevronRight } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

interface RightRailProps {
  onCollapse: () => void
}

export function RightRail({ onCollapse }: RightRailProps) {
  return (
    <>
      <div className="fixed inset-0 z-30 bg-black/40 md:hidden" onClick={onCollapse} aria-hidden="true" data-testid="rail-backdrop" />
      <aside className="fixed inset-y-0 right-0 z-40 flex h-full w-58 flex-col border-l border-border bg-card md:static md:z-auto">
        <div className="flex items-center justify-between p-3.5 pb-2">
          <span className="text-xs font-bold tracking-wide text-muted-foreground uppercase">
            Co nowego
          </span>
          <Button variant="ghost" size="icon" onClick={onCollapse} aria-label="Zwiń panel">
            <ChevronRight className="size-4" />
          </Button>
        </div>
        <div className="m-3.5 mt-1.5 rounded-2xl border-2 border-dashed border-border p-5 text-center">
          <p className="text-[12.5px] leading-relaxed text-muted-foreground">
            Tu będą pojawiać się nowości i zapowiedzi rozwoju aplikacji.
          </p>
          <Badge variant="secondary" className="mt-2.5 rounded-full px-2.5 py-1 text-[11px] font-bold">
            wkrótce
          </Badge>
        </div>
      </aside>
    </>
  )
}
