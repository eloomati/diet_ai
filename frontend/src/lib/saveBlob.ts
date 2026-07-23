/** Saves a blob to disk via a throwaway `<a download>` — no server-side
 * presigned URL exists (SFTP has no equivalent), so the file arrives as a
 * blob in memory and has to be handed to the browser this way. */
export function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
