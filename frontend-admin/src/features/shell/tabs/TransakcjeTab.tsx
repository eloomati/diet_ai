import { Wallet } from 'lucide-react'

import { EmptyState } from '@/components/EmptyState'

export function TransakcjeTab() {
  return (
    <EmptyState
      icon={Wallet}
      message="Transakcje pojawią się tutaj po wdrożeniu modułu płatności."
    />
  )
}
