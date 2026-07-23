import { apiFetch } from '@/lib/apiFetch'

export type NotificationType = 'TRANSACTION_PAID' | 'NEW_MESSAGE'

export interface Notification {
  id: string
  type: NotificationType
  reference_id: string
  created_at: string
  read_at: string | null
}

export function listNotifications(): Promise<Notification[]> {
  return apiFetch('/notifications')
}

export function markAllNotificationsRead(): Promise<Notification[]> {
  return apiFetch('/notifications/mark-all-read', { method: 'POST' })
}
