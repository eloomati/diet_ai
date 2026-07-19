import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'

import type { WeeklyObligation } from '@/api/profile'

import { WeeklyObligationsEditor } from './WeeklyObligationsEditor'

function ControlledEditor({ initial = [] }: { initial?: WeeklyObligation[] }) {
  const [value, setValue] = useState<WeeklyObligation[]>(initial)
  return <WeeklyObligationsEditor value={value} onChange={setValue} />
}

describe('WeeklyObligationsEditor', () => {
  it('shows an empty state, then adds an obligation and clears the mini-form', async () => {
    const user = userEvent.setup()
    render(<ControlledEditor />)

    expect(screen.getByText('Brak stałych zobowiązań w tygodniu.')).toBeInTheDocument()

    await user.type(screen.getByLabelText('Od'), '09:00')
    await user.type(screen.getByLabelText('Do'), '17:00')
    await user.type(screen.getByLabelText('Nazwa'), 'Praca')
    await user.click(screen.getByRole('button', { name: 'Dodaj' }))

    expect(screen.queryByText('Brak stałych zobowiązań w tygodniu.')).not.toBeInTheDocument()
    const removeButton = screen.getByRole('button', { name: 'Usuń zobowiązanie: Praca' })
    expect(removeButton.parentElement).toHaveTextContent('Poniedziałek 09:00–17:00 · Praca')
    expect(screen.getByLabelText('Nazwa')).toHaveValue('')
  })

  it('keeps "Dodaj" disabled and shows a hint when end time is not after start time', async () => {
    const user = userEvent.setup()
    render(<ControlledEditor />)

    await user.type(screen.getByLabelText('Od'), '17:00')
    await user.type(screen.getByLabelText('Do'), '09:00')
    await user.type(screen.getByLabelText('Nazwa'), 'Praca')

    expect(screen.getByRole('button', { name: 'Dodaj' })).toBeDisabled()
    expect(
      screen.getByText('Godzina końca musi być późniejsza niż początku.'),
    ).toBeInTheDocument()
  })

  it('removes an obligation from the list', async () => {
    const user = userEvent.setup()
    render(
      <ControlledEditor
        initial={[{ day_of_week: 'TUE', start_time: '08:00', end_time: '10:00', label: 'Trening' }]}
      />,
    )

    expect(screen.getByText(/Trening/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Usuń zobowiązanie: Trening' }))

    expect(screen.queryByText(/Trening/)).not.toBeInTheDocument()
    expect(screen.getByText('Brak stałych zobowiązań w tygodniu.')).toBeInTheDocument()
  })
})
