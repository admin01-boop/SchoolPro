import { beforeEach, describe, expect, test, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../AuthContext'
import ChangePasswordPage from '../ChangePasswordPage'

describe('ChangePasswordPage', () => {
  beforeEach(() => {
    sessionStorage.setItem('managbac-token', 'change-token')
    sessionStorage.setItem('managbac-user', JSON.stringify({
      username: 'staffer', role: 'STAFF', must_change_password: true,
    }))
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
      text: async () => '',
    })
  })

  test('changes the password and returns the user to their home page', async () => {
    const user = userEvent.setup()
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/change-password']}>
          <Routes>
            <Route path="/change-password" element={<ChangePasswordPage />} />
            <Route path="/staff/home" element={<h1>Staff home</h1>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>,
    )

    await user.type(screen.getByLabelText('Current password'), 'Temporary-Password-789!')
    await user.type(screen.getByLabelText('New password'), 'Permanent-Password-456!')
    await user.type(screen.getByLabelText('Confirm new password'), 'Permanent-Password-456!')
    await user.click(screen.getByRole('button', { name: 'Change password' }))

    expect(await screen.findByRole('heading', { name: 'Staff home' })).toBeInTheDocument()
    expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/change-password/', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        current_password: 'Temporary-Password-789!',
        new_password: 'Permanent-Password-456!',
      }),
    }))
    expect(JSON.parse(sessionStorage.getItem('managbac-user')).must_change_password).toBe(false)
  })
})