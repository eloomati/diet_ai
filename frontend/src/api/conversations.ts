import { apiFetch } from '@/lib/apiFetch'

export type ConversationCategory =
  | 'GENERAL'
  | 'DIET'
  | 'BREAKFAST'
  | 'FITNESS'
  | 'RUNNING'
  | 'GYM'
  | 'HEALTH'
  | 'SUPPLEMENTS'

export type ConversationStatus = 'ACTIVE' | 'ARCHIVED'
export type MessageRole = 'USER' | 'ASSISTANT' | 'SYSTEM'

export interface Message {
  id: string
  role: MessageRole
  content: string
  created_at: string
}

export interface ConversationSummary {
  conversation_id: string
  title: string
  categories: ConversationCategory[]
  status: ConversationStatus
  updated_at: string
}

export interface ConversationDetail {
  conversation_id: string
  title: string
  categories: ConversationCategory[]
  status: ConversationStatus
  messages: Message[]
}

export interface CreateConversationRequest {
  title: string
  categories: ConversationCategory[]
}

export interface CreateConversationResponse {
  conversation_id: string
  title: string
  categories: ConversationCategory[]
  status: ConversationStatus
}

export interface SendMessageResponse {
  conversation_id: string
  user_message_id: string
  assistant_message_id: string
  assistant_content: string
}

export function createConversation(
  payload: CreateConversationRequest,
): Promise<CreateConversationResponse> {
  return apiFetch('/conversations', { method: 'POST', body: payload })
}

export function listConversations(): Promise<ConversationSummary[]> {
  return apiFetch('/conversations')
}

export function getConversation(conversationId: string): Promise<ConversationDetail> {
  return apiFetch(`/conversations/${conversationId}`)
}

export function sendMessage(conversationId: string, content: string): Promise<SendMessageResponse> {
  return apiFetch(`/conversations/${conversationId}/messages`, { method: 'POST', body: { content } })
}

export function archiveConversation(conversationId: string): Promise<ConversationDetail> {
  return apiFetch(`/conversations/${conversationId}/archive`, { method: 'POST' })
}

export function deleteConversation(conversationId: string): Promise<void> {
  return apiFetch(`/conversations/${conversationId}`, { method: 'DELETE' })
}
