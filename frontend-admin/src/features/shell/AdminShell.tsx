import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAuth } from '@/lib/auth'

import { DietetycyTab } from './tabs/DietetycyTab'
import { RaportyTab } from './tabs/RaportyTab'
import { TransakcjeTab } from './tabs/TransakcjeTab'
import { UzytkownicyTab } from './tabs/UzytkownicyTab'

const MAIN_APP_URL = import.meta.env.VITE_MAIN_APP_URL ?? 'http://localhost:5173'

export function AdminShell() {
  const { user, logout } = useAuth()

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between border-b border-border px-6 py-3">
        <div>
          <p className="font-heading text-base font-extrabold">Mycelo — Panel administracyjny</p>
          {user && <p className="text-xs text-muted-foreground">{user.email}</p>}
        </div>
        <div className="flex items-center gap-3">
          <a
            href={MAIN_APP_URL}
            className="text-sm font-medium text-primary hover:underline"
          >
            ← Powrót do aplikacji
          </a>
          <Button variant="outline" onClick={() => void logout()}>
            Wyloguj się
          </Button>
        </div>
      </header>

      <main className="flex-1 px-6 py-4">
        {/* Base UI's Tabs root only gets a column layout (list above panel)
            via a Tailwind selector keyed off an attribute it doesn't
            actually set on this version — same latent bug the main app's
            ProfileModal avoids by forcing flex-col explicitly here too. */}
        <Tabs defaultValue="uzytkownicy" className="flex flex-col gap-0">
          <TabsList variant="line" className="border-b border-border">
            <TabsTrigger value="raporty">Raporty</TabsTrigger>
            <TabsTrigger value="uzytkownicy">Użytkownicy</TabsTrigger>
            <TabsTrigger value="dietetycy">Dietetycy</TabsTrigger>
            <TabsTrigger value="transakcje">Transakcje</TabsTrigger>
          </TabsList>

          <TabsContent value="raporty" className="pt-4">
            <RaportyTab />
          </TabsContent>
          <TabsContent value="uzytkownicy" className="pt-4">
            <UzytkownicyTab />
          </TabsContent>
          <TabsContent value="dietetycy" className="pt-4">
            <DietetycyTab />
          </TabsContent>
          <TabsContent value="transakcje" className="pt-4">
            <TransakcjeTab />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
