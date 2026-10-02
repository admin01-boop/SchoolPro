import { beforeEach, describe, expect, test, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '@/features/auth/AuthContext'
import { homePathFor } from '@/features/auth/roles'
import PortalHome from '../PortalHome'
import StudentHomePage from '../StudentHomePage'
import ParentHomePage from '../ParentHomePage'
import TeacherHomePage from '../TeacherHomePage'
import ObserverHomePage from '../ObserverHomePage'
import StaffHomePage from '../StaffHomePage'

function renderPortal(role) {
  sessionStorage.setItem('managbac-token', 'test-token')
  sessionStorage.setItem('managbac-user', JSON.stringify({ username: 'someone', role }))
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={['/me']}>
          <Routes>
            <Route path="/me" element={<PortalHome />} />
            <Route path="/student/home" element={<StudentHomePage />} />
            <Route path="/parent/home" element={<ParentHomePage />} />
            <Route path="/teacher/home" element={<TeacherHomePage />} />
            <Route path="/observer/home" element={<ObserverHomePage />} />
            <Route path="/staff/home" element={<StaffHomePage />} />
            <Route path="/admin/home" element={<p>Admin home screen</p>} />
            <Route path="/directory/roster" element={<p>Roster screen</p>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  )
}

const student = {
  student_id: 'S1',
  full_name: 'Kid Roe',
  khmer_name: '',
  sex: 'FEMALE',
  date_of_birth: '2014-01-01',
  nationality_1: 'Cambodian',
  nationality_2: '',
  grade: 'Year 7',
  enrollment_status: 'Existing',
  guardians: [{ full_name: 'Mum Roe', relationship: 'Mother' }],
}

describe('PortalHome', () => {
  beforeEach(() => {
    sessionStorage.clear()
    global.fetch = vi.fn().mockResolvedValue({ ok: true, text: async () => JSON.stringify(student) })
  })

  test('a student sees their own record from the API', async () => {
    renderPortal('STUDENT')

    expect(await screen.findByRole('heading', { name: 'Welcome, Kid' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'My classes' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Weekly timetable' })).toBeInTheDocument()
    expect(screen.getByText('Year 7')).toBeInTheDocument()
    expect(screen.getByText('Mum Roe')).toBeInTheDocument()
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/me/student/'),
      expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'Token test-token' }) }),
    )
  })

  test.each([
    ['TEACHER', 'Teacher'],
    ['OBSERVER', 'Observer'],
    ['STAFF', 'Staff'],
  ])('%s sees its own basic home page and makes no API call', (role, roleLabel) => {
    renderPortal(role)

    expect(screen.getByRole('heading', { name: 'Welcome, someone' })).toBeInTheDocument()
    expect(screen.getByText(roleLabel, { selector: 'dd' })).toBeInTheDocument()
    expect(screen.getByText('someone', { selector: 'dd' })).toBeInTheDocument()
    expect(global.fetch).not.toHaveBeenCalled()
  })

  test('a parent sees their linked children from the API', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify([{ student_id: 'S1', full_name: 'Kid Roe', grade: 'Year 7', enrollment_status: 'Existing' }]),
    })
    renderPortal('PARENT')

    expect(await screen.findByText('Kid Roe')).toBeInTheDocument()
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/v1/me/children/'), expect.anything())
  })

  test('management roles are sent to the admin home', () => {
    renderPortal('ADMIN')

    expect(screen.getByText('Admin home screen')).toBeInTheDocument()
    expect(global.fetch).not.toHaveBeenCalled()
  })
})

describe('homePathFor', () => {
  test.each([
    ['ADMIN', '/admin/home'],
    ['STUDENT', '/student/home'],
    ['PARENT', '/parent/home'],
    ['TEACHER', '/teacher/home'],
    ['OBSERVER', '/observer/home'],
    ['STAFF', '/staff/home'],
  ])('routes %s to its own home page', (role, path) => {
    expect(homePathFor({ role })).toBe(path)
  })
})
