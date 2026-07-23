import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { activateUser, banUser, changeUserRole, deleteUser, getUsers } from '@/api/admin'
import type { UserSummary } from '@/api/admin'
import type { UserRole } from '@/api/auth'
import { PaginationControls } from '@/components/PaginationControls'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ApiError } from '@/lib/apiFetch'
import { useAuth } from '@/lib/auth'
import { notifyError, notifySuccess } from '@/lib/toast'

const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: 'USER', label: 'Użytkownik' },
  { value: 'DIET_USER', label: 'Dietetyk' },
  { value: 'ADMIN', label: 'Administrator' },
  { value: 'SUPER_ADMIN', label: 'Super administrator' },
]

function roleLabel(role: UserRole): string {
  return ROLE_OPTIONS.find((option) => option.value === role)?.label ?? role
}

const STATUS_VARIANT: Record<string, 'default' | 'secondary' | 'destructive'> = {
  ACTIVE: 'default',
  INACTIVE: 'secondary',
  BLOCKED: 'destructive',
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Coś poszło nie tak. Spróbuj ponownie.'
}

const PAGE_SIZE = 20

export function UzytkownicyTab() {
  const { user: currentUser } = useAuth()
  const queryClient = useQueryClient()
  const [userPendingDelete, setUserPendingDelete] = useState<UserSummary | null>(null)
  const [offset, setOffset] = useState(0)

  const usersQuery = useQuery({
    queryKey: ['admin-users', offset],
    queryFn: () => getUsers({ limit: PAGE_SIZE, offset }),
  })

  const activateMutation = useMutation({
    mutationFn: activateUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
    onError: (error) => notifyError(errorMessage(error)),
  })

  const banMutation = useMutation({
    mutationFn: banUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
    onError: (error) => notifyError(errorMessage(error)),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      notifySuccess('Konto zostało usunięte.')
      setUserPendingDelete(null)
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
    onError: (error) => notifyError(errorMessage(error)),
  })

  const changeRoleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: UserRole }) =>
      changeUserRole(userId, role),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
    onError: (error) => notifyError(errorMessage(error)),
  })

  if (usersQuery.isPending) {
    return <p className="text-sm text-muted-foreground">Ładowanie użytkowników…</p>
  }

  if (usersQuery.isError) {
    return <p className="text-sm text-destructive">{errorMessage(usersQuery.error)}</p>
  }

  const isSuperAdmin = currentUser?.role === 'SUPER_ADMIN'

  return (
    <div className="flex flex-col gap-2">
      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs font-bold text-muted-foreground uppercase">
              <th className="px-3 py-2">E-mail</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Rola</th>
              <th className="px-3 py-2">Utworzono</th>
              <th className="px-3 py-2">Akcje</th>
            </tr>
          </thead>
          <tbody>
            {usersQuery.data.items.map((user) => {
              const isSelf = user.id === currentUser?.user_id
              return (
                <tr key={user.id} className="border-b border-border last:border-0">
                  <td className="px-3 py-2">{user.email}</td>
                  <td className="px-3 py-2">
                    <Badge variant={STATUS_VARIANT[user.status] ?? 'secondary'}>
                      {user.status}
                    </Badge>
                  </td>
                  <td className="px-3 py-2">
                    {isSuperAdmin && !isSelf ? (
                      <Select
                        value={user.role}
                        onValueChange={(value: UserRole | null) => {
                          if (value) changeRoleMutation.mutate({ userId: user.id, role: value })
                        }}
                      >
                        <SelectTrigger className="h-7 w-[170px] text-xs">
                          <SelectValue>{(value: UserRole) => roleLabel(value)}</SelectValue>
                        </SelectTrigger>
                        <SelectContent>
                          {ROLE_OPTIONS.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      roleLabel(user.role)
                    )}
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">
                    {new Date(user.created_at).toLocaleDateString('pl-PL')}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-1.5">
                      {user.status === 'BLOCKED' ? (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={activateMutation.isPending}
                          onClick={() => activateMutation.mutate(user.id)}
                        >
                          Aktywuj
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={banMutation.isPending || isSelf}
                          onClick={() => banMutation.mutate(user.id)}
                        >
                          Zablokuj
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-destructive hover:text-destructive"
                        disabled={isSelf}
                        onClick={() => setUserPendingDelete(user)}
                      >
                        Usuń
                      </Button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <PaginationControls
        offset={offset}
        limit={PAGE_SIZE}
        total={usersQuery.data.total}
        onOffsetChange={setOffset}
      />

      <Dialog
        open={userPendingDelete !== null}
        onOpenChange={(open) => !open && setUserPendingDelete(null)}
      >
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Usunąć konto?</DialogTitle>
            <DialogDescription>
              Konto <b>{userPendingDelete?.email}</b> oraz wszystkie powiązane z nim dane (rozmowy,
              profil żywieniowy, plany) zostaną trwale usunięte. Tej operacji nie można cofnąć.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setUserPendingDelete(null)}>
              Anuluj
            </Button>
            <Button
              variant="destructive"
              disabled={deleteMutation.isPending}
              onClick={() => userPendingDelete && deleteMutation.mutate(userPendingDelete.id)}
            >
              {deleteMutation.isPending ? 'Usuwanie…' : 'Usuń'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
