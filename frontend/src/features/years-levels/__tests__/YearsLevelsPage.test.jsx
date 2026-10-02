import { beforeEach, describe, expect, test, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Outlet, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '@/features/auth/AuthContext'
import YearsLevelsPage from '../YearsLevelsPage'

function renderYearsLevelsPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route element={<Outlet context={{ openMenu: vi.fn() }} />}>
              <Route path="/" element={<YearsLevelsPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  )
}

const gridResponse = {
  academic_years: [
    { id: 1, name: '2026-2027', is_current: true },
    { id: 2, name: '2027-2028', is_current: false },
  ],
  selected_academic_year: 1,
  grade_numbering_format: 'YEAR_12_13',
  year_levels: [{ id: 7, name: 'Year 7', grade_display_name: 'Grade 6' }],
  frameworks: [{ id: 1, name: 'Cambridge', tracks: [{ id: 1, name: 'Lower Secondary', order: 1 }] }],
  mappings: {
    '7:1': { is_enabled: true, custom_label: 'Year 7', stats: { classes: 0, students: 0 } },
  },
}

describe('YearsLevelsPage', () => {
  beforeEach(() => {
    sessionStorage.setItem('managbac-token', 'test-token')
    global.fetch = vi.fn().mockImplementation((url, options) => {
      const yearId = Number(new URL(url, 'http://localhost').searchParams.get('academic_year')) || 1
      const response = options?.method === 'PUT'
        ? { reconciliation: { linked: 0 } }
        : { ...gridResponse, selected_academic_year: yearId }
      return Promise.resolve({ ok: true, text: async () => JSON.stringify(response) })
    })
  })

  test('saves the selected year format and curriculum mapping', async () => {
    const user = userEvent.setup()
    renderYearsLevelsPage()

    const yearSelector = await screen.findByRole('combobox', { name: 'Academic year' })
    await user.selectOptions(yearSelector, '2')
    expect(yearSelector).toHaveValue('2')
    await user.click(await screen.findByRole('radio', { name: 'Grade 11 & 12' }))
    expect(screen.getByRole('combobox', { name: 'Academic year' })).toHaveValue('2')
    expect(global.fetch.mock.calls.some(([url]) => String(url).includes('academic_year=2'))).toBe(true)
    await user.click(screen.getByRole('button', { name: 'Save Changes' }))

    const saveCall = global.fetch.mock.calls.find(([, options]) => options?.method === 'PUT')
    expect(JSON.parse(saveCall[1].body)).toMatchObject({
      academic_year: 2,
      grade_numbering_format: 'GRADE_11_12',
      mappings: [{ year_level: 7, track: 1, is_enabled: true, custom_label: 'Year 7' }],
    })
  })
})
