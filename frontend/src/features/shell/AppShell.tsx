import { useState } from 'react'

import { AuthPopup } from '@/features/auth/AuthPopup'
import { ChatCanvas } from '@/features/chat/ChatCanvas'
import { ProfileModal } from '@/features/profile/ProfileModal'
import { useAuth } from '@/lib/auth'
import type { ConversationCategory } from '@/api/conversations'

import { LeftRail } from './LeftRail'
import { RightRail } from './RightRail'

export function AppShell() {
  const { isAuthenticated } = useAuth()

  const [leftCollapsed, setLeftCollapsed] = useState(false)
  const [rightCollapsed, setRightCollapsed] = useState(false)
  const [authPopupOpen, setAuthPopupOpen] = useState(true)
  const [profileModalOpen, setProfileModalOpen] = useState(false)
  const [activeCategories, setActiveCategories] = useState<ConversationCategory[]>([])

  function handleProfileClick() {
    if (isAuthenticated) {
      setProfileModalOpen(true)
    } else {
      setAuthPopupOpen(true)
    }
  }

  return (
    <div className="flex h-dvh w-full bg-background text-foreground">
      {!leftCollapsed && (
        <LeftRail
          onProfileClick={handleProfileClick}
          onCollapse={() => setLeftCollapsed(true)}
          onStartChat={setActiveCategories}
        />
      )}

      <ChatCanvas
        leftCollapsed={leftCollapsed}
        rightCollapsed={rightCollapsed}
        onExpandLeft={() => setLeftCollapsed(false)}
        onExpandRight={() => setRightCollapsed(false)}
        activeCategories={activeCategories}
      />

      {!rightCollapsed && <RightRail onCollapse={() => setRightCollapsed(true)} />}

      <AuthPopup open={authPopupOpen} onOpenChange={setAuthPopupOpen} />
      <ProfileModal open={profileModalOpen} onOpenChange={setProfileModalOpen} />
    </div>
  )
}
