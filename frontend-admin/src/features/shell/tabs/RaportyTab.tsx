import { BarChart3 } from 'lucide-react'

import { EmptyState } from '@/components/EmptyState'

export function RaportyTab() {
  return (
    <EmptyState
      icon={BarChart3}
      message="Raporty będą dostępne w kolejnej wersji panelu."
    />
  )
}
