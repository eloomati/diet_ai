import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { AuthProvider } from '@/lib/auth'

import App from './App'

describe('App', () => {
  it('renders the app shell without crashing', () => {
    const queryClient = new QueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </QueryClientProvider>,
    )

    expect(screen.getByText('Cześć! W czym mogę Ci dziś pomóc?')).toBeInTheDocument()
  })
})
