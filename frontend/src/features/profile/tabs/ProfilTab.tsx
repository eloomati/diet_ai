import { Button } from '@/components/ui/button'
import { useAuth } from '@/lib/auth'

export function ProfilTab() {
  const { logout } = useAuth()

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">
        Formularz profilu żywieniowego (wiek, wzrost, waga, cel, typ diety, cotygodniowe
        zobowiązania) pojawi się w Etapie 2.
      </p>
      <Button variant="outline" className="w-fit" onClick={() => void logout()}>
        Wyloguj się
      </Button>
    </div>
  )
}
