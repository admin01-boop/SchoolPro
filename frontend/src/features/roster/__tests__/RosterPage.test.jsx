import { beforeEach, describe, expect, test, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Outlet, Route, Routes } from 'react-router-dom'
import RosterPage from '../RosterPage'
import { AuthProvider } from '@/features/auth/AuthContext'

function renderRoster() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route element={<Outlet context={{ openMenu: vi.fn() }} />}>
              <Route path="/" element={<RosterPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  )
}

describe('RosterPage', () => {
  beforeEach(() => {
    sessionStorage.setItem('managbac-token', 'test-token')
    sessionStorage.setItem('managbac-user', JSON.stringify({ username: 'admin', role: 'ADMIN', must_change_password: false }))
    global.fetch = vi.fn().mockImplementation((url) => {
      if (url.includes('/roster-teachers/')) {
        return Promise.resolve({
          ok: true,
          text: async () => JSON.stringify({
            count: 1,
            next: null,
            previous: null,
            results: [{ id: 9, full_name: 'Tara Lee', first_name: 'Tara', last_name: 'Lee', username: 'tara', email: 'tara@example.com', employee_id: 'E1', hire_date: null, is_active: true, must_change_password: false }],
          }),
        })
      }
      if (url.includes('/roster-parents/')) {
        return Promise.resolve({
          ok: true,
          text: async () => JSON.stringify({
            count: 1,
            next: null,
            previous: null,
            results: [{
              id: 4, full_name: 'Imported Parent', email: '', phone_1: '012', has_login: false,
              children: [{ student_id: 1, full_name: 'Jane Roe', relationship: 'MOTHER' }],
            }],
          }),
        })
      }
      if (url.includes('/roster-admins/')) {
        return Promise.resolve({
          ok: true,
          text: async () => JSON.stringify({
            count: 1,
            next: null,
            previous: null,
            results: [{ id: 7, username: 'adam', full_name: 'Adam Ng', email: '', employee_id: 'A1', job_title: 'Principal', phone: '', is_active: true }],
          }),
        })
      }
      if (url.includes('/roster-users/')) {
        return Promise.resolve({
          ok: true,
          text: async () => JSON.stringify({
            id: 2,
            username: 'casey-roe-k4p8v2',
            user_type: 'STUDENT',
            welcome_email_sent: false,
            initial_password: 'temporary-password',
          }),
        })
      }
      if (url.includes('/students/1/')) {
        return Promise.resolve({
          ok: true,
          text: async () => JSON.stringify({
            id: 1, student_id: 'S1', full_name: 'Jane Roe', khmer_name: '', sex: 'FEMALE',
            date_of_birth: '2014-01-01', frn: '', nationality_1: 'Cambodian', nationality_2: '', remark: '',
          }),
        })
      }
      const body = url.includes('/roster-filter-options/')
        ? { groups: [], ungrouped: [] }
        : url.includes('/roster-user-options/')
          ? { grade_levels: [], parents: [], parents_enabled: true }
          : {
          count: 1,
          next: null,
          previous: null,
          results: [
            { id: 1, full_name: 'Jane Roe', grade: 'Year 7', enrollment_status: 'New Enrollment', guardian_count: 1 },
          ],
        }
      return Promise.resolve({ ok: true, text: async () => JSON.stringify(body) })
    })
  })

  test('renders students fetched from the real API instead of mock data', async () => {
    renderRoster()
    expect(await screen.findByText('Jane Roe')).toBeInTheDocument()
    expect(screen.getByText('Year 7')).toBeInTheDocument()
    expect(screen.getByText('New Enrollment')).toBeInTheDocument()
    expect(screen.getByText('Students (1)')).toBeInTheDocument()
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/students/'),
      expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'Token test-token' }) }),
    )
  })

  test('lists users by role on the other tabs', async () => {
    const user = userEvent.setup()
    renderRoster()

    await user.click(await screen.findByRole('button', { name: 'Teachers & Advisors' }))
    expect(await screen.findByText('Tara Lee')).toBeInTheDocument()
    expect(screen.getByText('Teachers & Advisors (1)')).toBeInTheDocument()
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/roster-teachers/'),
      expect.anything(),
    )

    await user.click(screen.getByRole('button', { name: 'Parents' }))
    expect(await screen.findByText('Imported Parent')).toBeInTheDocument()
    expect(screen.getByText('No login')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Admins' }))
    expect(await screen.findByText('Adam Ng')).toBeInTheDocument()
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/roster-admins/'),
      expect.anything(),
    )
  })

  test('edits a teacher profile by clicking the name on the Teachers tab', async () => {
    const user = userEvent.setup()
    renderRoster()

    await user.click(await screen.findByRole('button', { name: 'Teachers & Advisors' }))
    await user.click(await screen.findByRole('button', { name: 'Tara Lee' }))
    const dialog = await screen.findByRole('dialog')
    await user.type(within(dialog).getByLabelText('New password'), 'Temporary-Password-789!')
    const employeeId = within(dialog).getByLabelText('Employee ID')
    await user.clear(employeeId)
    await user.type(employeeId, 'E77')
    await user.click(within(dialog).getByRole('button', { name: 'Save' }))

    await vi.waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    const patchCall = global.fetch.mock.calls.find(([url, options]) => url.includes('/roster-teachers/9/') && options?.method === 'PATCH')
    expect(patchCall).toBeDefined()
    expect(JSON.parse(patchCall[1].body)).toMatchObject({
      first_name: 'Tara', last_name: 'Lee', email: 'tara@example.com', employee_id: 'E77', hire_date: null,
      password: 'Temporary-Password-789!', require_password_change: true,
    })
  })

  test('edits a student by clicking the name on the Students tab', async () => {
    const user = userEvent.setup()
    renderRoster()

    await user.click(await screen.findByRole('button', { name: 'Jane Roe' }))
    const dialog = await screen.findByRole('dialog')
    const khmerName = await within(dialog).findByLabelText('Khmer Name')
    expect(within(dialog).getByLabelText('Nationality')).toHaveValue('Cambodian')
    await user.type(khmerName, 'Khmer Jane')
    await user.click(within(dialog).getByRole('button', { name: 'Save' }))

    await vi.waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    const patchCall = global.fetch.mock.calls.find(([url, options]) => url.includes('/students/1/') && options?.method === 'PATCH')
    expect(patchCall).toBeDefined()
    expect(JSON.parse(patchCall[1].body)).toMatchObject({
      student_id: 'S1', full_name: 'Jane Roe', khmer_name: 'Khmer Jane', sex: 'FEMALE', date_of_birth: '2014-01-01',
    })
  })

  test('edits a parent by clicking the name on the Parents tab', async () => {
    const user = userEvent.setup()
    renderRoster()

    await user.click(await screen.findByRole('button', { name: 'Parents' }))
    await user.click(await screen.findByRole('button', { name: 'Imported Parent' }))
    const dialog = await screen.findByRole('dialog')
    const phone = within(dialog).getByLabelText('Phone')
    await user.clear(phone)
    await user.type(phone, '099')
    await user.click(within(dialog).getByRole('button', { name: 'Save' }))

    await vi.waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    const patchCall = global.fetch.mock.calls.find(([url, options]) => url.includes('/roster-parents/4/') && options?.method === 'PATCH')
    expect(patchCall).toBeDefined()
    expect(JSON.parse(patchCall[1].body)).toMatchObject({ full_name: 'Imported Parent', phone_1: '099' })
  })

  test('creates a student account from the Add User form', async () => {
    const user = userEvent.setup()
    renderRoster()

    await user.click(await screen.findByRole('button', { name: 'Add User' }))
    const dialog = await screen.findByRole('dialog')
    await user.type(within(dialog).getByLabelText(/First Name/), 'Casey')
    await user.type(within(dialog).getByLabelText(/Last Name/), 'Roe')
    await user.type(within(dialog).getByLabelText('E-mail Address'), 'casey@example.com')
    await user.type(within(dialog).getByLabelText(/Student ID/), 'S200')
    await user.selectOptions(within(dialog).getByLabelText('Sex *'), 'FEMALE')
    await user.type(within(dialog).getByLabelText(/Date of Birth/), '2014-05-01')
    await user.click(within(dialog).getByRole('button', { name: 'Add User' }))

    expect(await within(dialog).findByText(/account was created/i)).toBeInTheDocument()
    const createCall = global.fetch.mock.calls.find(([url]) => url.includes('/roster-users/'))
    expect(createCall).toBeDefined()
    expect(JSON.parse(createCall[1].body)).toMatchObject({
      user_type: 'STUDENT',
      first_name: 'Casey',
      last_name: 'Roe',
      email: 'casey@example.com',
      student_id: 'S200',
      sex: 'FEMALE',
      date_of_birth: '2014-05-01',
      parent_ids: [],
    })
  })
})
