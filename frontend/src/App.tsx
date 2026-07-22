import { Route, Routes } from 'react-router-dom'

import { Toaster } from '@/components/ui/sonner'
import { AppShell } from '@/features/shell/AppShell'

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<AppShell />} />
        <Route path="/dietitian-chat/:threadId" element={<AppShell />} />
        <Route path="/:conversationId" element={<AppShell />} />
      </Routes>
      <Toaster />
    </>
  )
}

export default App
