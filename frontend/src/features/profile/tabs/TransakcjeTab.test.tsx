import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { TransakcjeTab } from './TransakcjeTab'

describe('TransakcjeTab', () => {
  it('shows a placeholder empty state', () => {
    render(<TransakcjeTab />)

    expect(
      screen.getByText('Transakcje pojawią się tutaj, gdy moduł płatności zostanie wdrożony.'),
    ).toBeInTheDocument()
  })
})
