import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { AuthProvider } from '@/lib/auth'

import App from './App'

function renderApp(initialEntries: string[] = ['/']) {
  const queryClient = new QueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={initialEntries}>
          <App />
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  )
}

describe('App', () => {
  it('renders the app shell at the root route', () => {
    renderApp(['/'])
    expect(screen.getByText('Cześć! W czym mogę Ci dziś pomóc?')).toBeInTheDocument()
  })

  it('renders the same shell for a /:conversationId route, showing the id', () => {
    renderApp(['/11111111-2222-3333-4444-555555555555'])
    expect(screen.getByText(/Rozmowa #11111111/)).toBeInTheDocument()
  })
})
