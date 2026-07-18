import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface AuthPopupProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function AuthPopup({ open, onOpenChange }: AuthPopupProps) {
  const [tab, setTab] = useState<'login' | 'register'>('login')

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm" showCloseButton>
        <DialogTitle className="sr-only">Logowanie</DialogTitle>

        <Tabs value={tab} onValueChange={(value) => setTab(value as 'login' | 'register')}>
          <TabsList className="w-full">
            <TabsTrigger value="login" className="flex-1">
              Zaloguj się
            </TabsTrigger>
            <TabsTrigger value="register" className="flex-1">
              Zarejestruj się
            </TabsTrigger>
          </TabsList>
        </Tabs>

        <form className="flex flex-col gap-2.5" onSubmit={(event) => event.preventDefault()}>
          <div>
            <label className="mb-1 block text-xs font-bold text-muted-foreground">E-mail</label>
            <Input type="email" placeholder="ty@przyklad.pl" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-bold text-muted-foreground">Hasło</label>
            <Input type="password" placeholder="••••••••" />
          </div>
          <Button type="submit" className="mt-1.5">
            {tab === 'login' ? 'Zaloguj się' : 'Utwórz konto'}
          </Button>
        </form>

        <button
          onClick={() => onOpenChange(false)}
          className="text-center text-[12.5px] font-bold text-muted-foreground hover:text-foreground"
        >
          Kontynuuj jako gość →
        </button>
      </DialogContent>
    </Dialog>
  )
}
