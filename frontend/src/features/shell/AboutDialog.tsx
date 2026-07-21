import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'

interface AboutDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function AboutDialog({ open, onOpenChange }: AboutDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>O nas</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">
          Mycelo to asystent żywieniowy oparty o AI — czat, profil żywieniowy i generowanie planów
          dietetycznych w jednym miejscu. Ta sekcja będzie rozbudowana w kolejnych wersjach.
        </p>
      </DialogContent>
    </Dialog>
  )
}
