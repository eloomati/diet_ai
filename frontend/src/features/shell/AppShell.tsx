import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { AuthPopup } from '@/features/auth/AuthPopup'
import { ChatCanvas } from '@/features/chat/ChatCanvas'
import { ProfileModal } from '@/features/profile/ProfileModal'
import { CATEGORY_OPTIONS, formatCategories } from '@/lib/categoryOptions'
import { useAuth } from '@/lib/auth'
import { createConversation } from '@/api/conversations'
import type { ConversationCategory, ConversationSummary } from '@/api/conversations'

import { LeftRail } from './LeftRail'
import { RightRail } from './RightRail'

export function AppShell() {
  const { isAuthenticated, isBootstrapping } = useAuth()
  const { conversationId } = useParams<{ conversationId?: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [leftCollapsed, setLeftCollapsed] = useState(false)
  const [rightCollapsed, setRightCollapsed] = useState(false)
  const [authPopupOpen, setAuthPopupOpen] = useState(false)
  const [profileModalOpen, setProfileModalOpen] = useState(false)
  const [activeCategories, setActiveCategories] = useState<ConversationCategory[]>([])

  const createConversationMutation = useMutation({
    mutationFn: (categories: ConversationCategory[]) =>
      createConversation({ title: formatCategories(categories, CATEGORY_OPTIONS.length), categories }),
    onSuccess: (conversation) => {
      setActiveCategories(conversation.categories)
      navigate(`/${conversation.conversation_id}`)
      void queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  useEffect(() => {
    // Only prompt for login once we know a stored session couldn't be
    // silently restored — otherwise a returning logged-in user would see
    // the popup flash open for a moment on every page load.
    if (!isBootstrapping && !isAuthenticated) {
      setAuthPopupOpen(true)
    }
  }, [isBootstrapping, isAuthenticated])

  function handleProfileClick() {
    if (isAuthenticated) {
      setProfileModalOpen(true)
    } else {
      setAuthPopupOpen(true)
    }
  }

  function handleStartChat(categories: ConversationCategory[]) {
    createConversationMutation.mutate(categories)
  }

  function handleSelectConversation(conversation: ConversationSummary) {
    setActiveCategories(conversation.categories)
    navigate(`/${conversation.conversation_id}`)
  }

  return (
    <div className="flex h-dvh w-full bg-background text-foreground">
      {!leftCollapsed && (
        <LeftRail
          onProfileClick={handleProfileClick}
          onCollapse={() => setLeftCollapsed(true)}
          onStartChat={handleStartChat}
          onSelectConversation={handleSelectConversation}
          activeConversationId={conversationId}
          createError={createConversationMutation.isError}
        />
      )}

      <ChatCanvas
        leftCollapsed={leftCollapsed}
        rightCollapsed={rightCollapsed}
        onExpandLeft={() => setLeftCollapsed(false)}
        onExpandRight={() => setRightCollapsed(false)}
        activeCategories={activeCategories}
        conversationId={conversationId}
      />

      {!rightCollapsed && <RightRail onCollapse={() => setRightCollapsed(true)} />}

      <AuthPopup open={authPopupOpen} onOpenChange={setAuthPopupOpen} />
      <ProfileModal open={profileModalOpen} onOpenChange={setProfileModalOpen} />
    </div>
  )
}
