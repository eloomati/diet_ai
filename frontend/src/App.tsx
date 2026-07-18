import { Route, Routes } from 'react-router-dom'

import { AppShell } from '@/features/shell/AppShell'

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />} />
      <Route path="/:conversationId" element={<AppShell />} />
    </Routes>
  )
}

export default App
