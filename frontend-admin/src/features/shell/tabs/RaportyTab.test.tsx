import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { RaportyTab } from './RaportyTab'

describe('RaportyTab', () => {
  it('shows a placeholder empty state', () => {
    render(<RaportyTab />)

    expect(
      screen.getByText('Raporty będą dostępne w kolejnej wersji panelu.'),
    ).toBeInTheDocument()
  })
})
