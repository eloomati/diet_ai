import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { getMyDietitianApplication, submitDietitianApplication } from '@/api/dietitian'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { FieldError } from '@/components/FieldError'
import { Textarea } from '@/components/ui/textarea'
import { ApiError } from '@/lib/apiFetch'

const STATUS_LABEL: Record<string, string> = {
  PENDING: 'Zgłoszenie w trakcie rozpatrywania',
  APPROVED: 'Zgłoszenie zaakceptowane',
  REJECTED: 'Zgłoszenie odrzucone',
}

const STATUS_VARIANT: Record<string, 'secondary' | 'default' | 'destructive'> = {
  PENDING: 'secondary',
  APPROVED: 'default',
  REJECTED: 'destructive',
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Coś poszło nie tak. Spróbuj ponownie.'
}

export function DietitianApplicationSection() {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [experience, setExperience] = useState('')
  const [diplomas, setDiplomas] = useState('')
  const [description, setDescription] = useState('')

  const applicationQuery = useQuery({
    queryKey: ['dietitian-application'],
    // A 404 just means "no application submitted yet" — the normal first state.
    queryFn: getMyDietitianApplication,
    retry: false,
  })

  const submitMutation = useMutation({
    mutationFn: submitDietitianApplication,
    onSuccess: (application) => {
      queryClient.setQueryData(['dietitian-application'], application)
      setOpen(false)
    },
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    submitMutation.mutate({
      experience,
      diplomas: diplomas
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean),
      description,
    })
  }

  const applicationMissing =
    applicationQuery.isError &&
    applicationQuery.error instanceof ApiError &&
    applicationQuery.error.code === 'NOT_FOUND'

  if (applicationQuery.isPending) return null

  if (applicationQuery.isSuccess) {
    const status = applicationQuery.data.status
    return (
      <div className="flex justify-end">
        <Badge variant={STATUS_VARIANT[status] ?? 'secondary'}>{STATUS_LABEL[status] ?? status}</Badge>
      </div>
    )
  }

  if (!applicationMissing) return null

  return (
    <div className="flex justify-end">
      <Button variant="outline" onClick={() => setOpen(true)}>
        Zgłoszenie dietetyka
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Zgłoszenie dietetyka</DialogTitle>
          </DialogHeader>
          <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="dietitian-experience" className="mb-1 block text-xs font-bold text-muted-foreground">
                Doświadczenie
              </label>
              <Textarea
                id="dietitian-experience"
                value={experience}
                onChange={(event) => setExperience(event.target.value)}
                required
              />
            </div>

            <div>
              <label htmlFor="dietitian-diplomas" className="mb-1 block text-xs font-bold text-muted-foreground">
                Dyplomy (jeden na linię)
              </label>
              <Textarea
                id="dietitian-diplomas"
                value={diplomas}
                onChange={(event) => setDiplomas(event.target.value)}
              />
            </div>

            <div>
              <label htmlFor="dietitian-description" className="mb-1 block text-xs font-bold text-muted-foreground">
                Opis
              </label>
              <Textarea
                id="dietitian-description"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                required
              />
            </div>

            {submitMutation.isError && <FieldError message={errorMessage(submitMutation.error)} />}

            <Button type="submit" className="w-fit" disabled={submitMutation.isPending}>
              {submitMutation.isPending ? 'Wysyłanie…' : 'Wyślij zgłoszenie'}
            </Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
