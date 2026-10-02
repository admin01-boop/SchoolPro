import { describe, expect, test, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Sidebar from '../Sidebar'

describe('Sidebar', () => {
  test('School Directory only exposes Roster as a submenu item', () => {
    render(
      <MemoryRouter>
        <Sidebar open onClose={() => {}} onLogout={() => {}} />
      </MemoryRouter>,
    )
    expect(screen.getByText('School Directory')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Roster' })).toBeInTheDocument()
    expect(screen.queryByText('Memberships')).not.toBeInTheDocument()
    expect(screen.queryByText('Bulk Update')).not.toBeInTheDocument()
  })

  test('logout button triggers onLogout', () => {
    const onLogout = vi.fn()
    render(
      <MemoryRouter>
        <Sidebar open onClose={() => {}} onLogout={onLogout} />
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByText('Log out'))
    expect(onLogout).toHaveBeenCalledTimes(1)
  })
})
