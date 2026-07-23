import { toast } from 'sonner'

/** Surfaces a background-action failure as a toast — for mutations with
 * no persistent inline error UI of their own. */
export function notifyError(message: string): void {
  toast.error(message)
}

export function notifySuccess(message: string): void {
  toast.success(message)
}
