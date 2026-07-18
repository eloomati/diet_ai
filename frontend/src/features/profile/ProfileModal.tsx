import { useEffect } from 'react'

import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAuth } from '@/lib/auth'

import { KalendarzTab } from './tabs/KalendarzTab'
import { PlanyTab } from './tabs/PlanyTab'
import { ProfilTab } from './tabs/ProfilTab'

interface ProfileModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function ProfileModal({ open, onOpenChange }: ProfileModalProps) {
  const { isAuthenticated } = useAuth()

  // Logging out from inside the modal (Profil tab) shouldn't leave a
  // signed-out user staring at their own Plany/Kalendarz tabs.
  useEffect(() => {
    if (open && !isAuthenticated) onOpenChange(false)
  }, [open, isAuthenticated, onOpenChange])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[80vh] max-h-[640px] w-full flex-col overflow-hidden p-0 sm:max-w-3xl">
        <DialogTitle className="sr-only">Profil</DialogTitle>
        <Tabs defaultValue="profil" className="flex h-full flex-col gap-0">
          <TabsList variant="line" className="h-auto justify-start gap-1 border-b border-border px-3 pt-2.5">
            <TabsTrigger value="profil" className="px-4 py-2.5 font-heading text-sm font-extrabold">
              Profil
            </TabsTrigger>
            <TabsTrigger value="plany" className="px-4 py-2.5 font-heading text-sm font-extrabold">
              Plany
            </TabsTrigger>
            <TabsTrigger value="kalendarz" className="px-4 py-2.5 font-heading text-sm font-extrabold">
              Kalendarz
            </TabsTrigger>
          </TabsList>

          <ScrollArea className="flex-1">
            <TabsContent value="profil" className="p-6">
              <ProfilTab />
            </TabsContent>
            <TabsContent value="plany" className="p-6">
              <PlanyTab />
            </TabsContent>
            <TabsContent value="kalendarz" className="p-6">
              <KalendarzTab />
            </TabsContent>
          </ScrollArea>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
