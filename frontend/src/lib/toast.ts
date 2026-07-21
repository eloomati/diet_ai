import { toast } from 'sonner'

/** Surfaces a background-action failure as a toast — for mutations with
 * no persistent inline error UI of their own (e.g. archive/delete, where a
 * passing notification fits better than a message that lingers in the
 * layout). */
export function notifyError(message: string): void {
  toast.error(message)
}

/** Same spirit as notifyError, for a background action that succeeded. */
export function notifyInfo(message: string): void {
  toast(message)
}
