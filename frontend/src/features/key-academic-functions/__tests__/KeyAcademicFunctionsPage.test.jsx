import { beforeEach, describe, expect, test, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Outlet, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '@/features/auth/AuthContext'
import KeyAcademicFunctionsPage from '../KeyAcademicFunctionsPage'

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={['/settings/key-academic-functions']}>
          <Routes>
            <Route element={<Outlet context={{ openMenu: vi.fn() }} />}>
              <Route path="/settings/key-academic-functions" element={<KeyAcademicFunctionsPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  )
}

const initialSettings = {
  configuration: {
    classes_enabled: true,
    parents_association_enabled: true,
    annotations_enabled: true,
    term_grade_calculation: 'PERCENTAGE',
    points_based_averaging: true,
    year_level_behaviour: 'MATCH_GROUP',
  },
  curricula: [
    { id: 1, code: 'cambridge-igcse', provider: 'Cambridge Assessment International Education', name: 'Cambridge IGCSE', is_enabled: true, is_customizable: false, short_name: '', full_title: '' },
    { id: 2, code: 'ib-diploma', provider: 'International Baccalaureate', name: 'IB Diploma', is_enabled: false, is_customizable: false, short_name: '', full_title: '' },
    { id: 3, code: 'national-high-school', provider: 'National Curriculum', name: 'High School', is_enabled: true, is_customizable: true, short_name: 'HS', full_title: '' },
  ],
}

describe('KeyAcademicFunctionsPage', () => {
  beforeEach(() => {
    sessionStorage.setItem('managbac-token', 'test-token')
    global.fetch = vi.fn().mockImplementation((url, options) => {
      if (options?.method === 'PUT') {
        const payload = JSON.parse(options.body)
        const curricula = initialSettings.curricula.map((option) => {
          const update = payload.curricula.find((item) => item.id === option.id)
          return update ? { ...option, ...update } : option
        })
        return Promise.resolve({
          ok: true,
          text: async () => JSON.stringify({ configuration: payload.configuration, curricula }),
        })
      }
      return Promise.resolve({ ok: true, text: async () => JSON.stringify(initialSettings) })
    })
  })

  test('saves curriculum selections, academic toggles, calculation settings, and labels', async () => {
    const user = userEvent.setup()
    renderPage()

    expect(await screen.findByRole('heading', { name: 'Key Academic Functions' })).toBeInTheDocument()
    await user.click(screen.getByRole('checkbox', { name: 'Classes' }))
    await user.click(screen.getByRole('checkbox', { name: 'IB Diploma' }))
    await user.click(screen.getByRole('radio', { name: 'Use Absolute weights' }))
    await user.click(screen.getByRole('checkbox', { name: 'Use Points-based averaging' }))
    await user.click(screen.getByRole('radio', { name: 'Preserve Year Level' }))
    await user.clear(screen.getByRole('textbox', { name: 'High School short label' }))
    await user.type(screen.getByRole('textbox', { name: 'High School short label' }), 'HSX')
    await user.type(screen.getByRole('textbox', { name: 'High School full title' }), 'Senior School')
    await user.click(screen.getByRole('button', { name: 'Save Changes' }))

    expect(await screen.findByText('Key Academic Functions have been saved.')).toBeInTheDocument()
    const saveCall = global.fetch.mock.calls.find(([, options]) => options?.method === 'PUT')
    expect(JSON.parse(saveCall[1].body)).toMatchObject({
      configuration: {
        classes_enabled: false,
        parents_association_enabled: true,
        annotations_enabled: true,
        term_grade_calculation: 'ABSOLUTE',
        points_based_averaging: false,
        year_level_behaviour: 'PRESERVE',
      },
      curricula: [
        { id: 1, is_enabled: true },
        { id: 2, is_enabled: true },
        { id: 3, is_enabled: true, short_name: 'HSX', full_title: 'Senior School' },
      ],
    })
  })
})
