import { Toaster } from '@/components/ui/sonner'
import { LoginPage } from '@/features/auth/LoginPage'
import { AdminShell } from '@/features/shell/AdminShell'
import { useAuth } from '@/lib/auth'

function App() {
  const { isAuthenticated, isBootstrapping } = useAuth()

  return (
    <>
      {isBootstrapping ? null : isAuthenticated ? <AdminShell /> : <LoginPage />}
      <Toaster />
    </>
  )
}

export default App
