import { apiFetch } from '@/lib/apiFetch'

export type MessageSender = 'USER' | 'DIETITIAN'

export interface DietitianThread {
  id: string
  user_id: string
  dietitian_id: string
  created_at: string
  other_participant_name: string | null
}

export interface DietitianMessage {
  id: string
  thread_id: string
  sender: MessageSender
  content: string
  diet_plan_id: string | null
  created_at: string
}

export interface SendDietitianMessageRequest {
  content: string
  diet_plan_id?: string | null
}

export function listMyDietitianThreads(): Promise<DietitianThread[]> {
  return apiFetch('/messaging/threads')
}

export function listThreadMessages(threadId: string): Promise<DietitianMessage[]> {
  return apiFetch(`/messaging/threads/${threadId}/messages`)
}

export function sendDietitianMessage(
  threadId: string,
  payload: SendDietitianMessageRequest,
): Promise<DietitianMessage> {
  return apiFetch(`/messaging/threads/${threadId}/messages`, { method: 'POST', body: payload })
}
