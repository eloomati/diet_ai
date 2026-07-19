import type { ConversationCategory } from '@/api/conversations'

export interface CategoryOption {
  value: ConversationCategory
  label: string
  emoji: string
}

export const CATEGORY_OPTIONS: CategoryOption[] = [
  { value: 'GENERAL', label: 'Ogólny', emoji: '💬' },
  { value: 'DIET', label: 'Dieta', emoji: '🥗' },
  { value: 'BREAKFAST', label: 'Śniadanie', emoji: '🍳' },
  { value: 'FITNESS', label: 'Fitness', emoji: '🏋️' },
  { value: 'RUNNING', label: 'Bieganie', emoji: '🏃' },
  { value: 'GYM', label: 'Siłownia', emoji: '💪' },
  { value: 'HEALTH', label: 'Zdrowie', emoji: '❤️' },
  { value: 'SUPPLEMENTS', label: 'Suplementy', emoji: '💊' },
]

const LABEL_BY_VALUE = new Map(CATEGORY_OPTIONS.map((option) => [option.value, option]))

export function formatCategories(categories: ConversationCategory[], max = 2): string {
  const labels = categories.map((value) => LABEL_BY_VALUE.get(value)?.label ?? value)
  const shown = labels.slice(0, max).join(', ')
  const extra = labels.length - max
  return extra > 0 ? `${shown} +${extra}` : shown
}

export function categoryEmoji(value: ConversationCategory): string {
  return LABEL_BY_VALUE.get(value)?.emoji ?? ''
}

export function categoryLabel(value: ConversationCategory): string {
  return LABEL_BY_VALUE.get(value)?.label ?? value
}
