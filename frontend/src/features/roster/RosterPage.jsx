import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useOutletContext } from 'react-router-dom'
import { ChevronDown, Menu, Plus } from 'lucide-react'
import { request } from '@/lib/apiClient'
import UserMenu from '@/components/UserMenu'
import { useAuth } from '@/features/auth/AuthContext'
import AddUserModal from './AddUserModal'
import EditProfileModal from './EditProfileModal'
import { STUDENT_FIELDS } from './editFields'
import RoleUsersTab from './RoleUsersTab'

const TONES = [
  'teal', 'purple', 'orange', 'indigo', 'amber', 'blue', 'green', 'pink',
  'red', 'cyan', 'mint', 'violet', 'gold', 'slate', 'rose', 'ruby', 'sky',
]

const ROSTER_TABS = ['Students', 'Teachers & Advisors', 'Staff', 'Parents', 'Observers', 'Admins']

function initialsOf(name) {
  return name.split(' ').map((part) => part[0]).slice(0, 2).join('')
}

export default function RosterPage() {
  const { token, actualRole } = useAuth()
  const { openMenu } = useOutletContext()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [activeTab, setActiveTab] = useState('Students')
  const [filterOpen, setFilterOpen] = useState(false)
  const [addUserOpen, setAddUserOpen] = useState(false)
  const [editingStudent, setEditingStudent] = useState(null)
  const [excludedGrades, setExcludedGrades] = useState(() => new Set())
  const [includeNoGrade, setIncludeNoGrade] = useState(true)

  const { data: filterOptions } = useQuery({
    queryKey: ['roster-filter-options'],
    queryFn: () => request('/roster-filter-options/', {}, token),
    enabled: Boolean(token),
  })

  const allGradeIds = useMemo(() => {
    if (!filterOptions) return []
    const grouped = filterOptions.groups.flatMap((group) => group.grade_levels.map((grade) => grade.id))
    const ungrouped = filterOptions.ungrouped.map((grade) => grade.id)
    return [...grouped, ...ungrouped]
  }, [filterOptions])

  const isFiltered = Boolean(filterOptions) && (excludedGrades.size > 0 || !includeNoGrade)

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['students', search, page, isFiltered, Array.from(excludedGrades).sort().join(','), includeNoGrade],
    queryFn: () => {
      const params = new URLSearchParams({ search, page: String(page) })
      if (isFiltered) {
        params.set('filter_active', 'true')
        params.set('include_no_grade', includeNoGrade ? 'true' : 'false')
        allGradeIds.filter((id) => !excludedGrades.has(id)).forEach((id) => params.append('grade_level', id))
      }
      return request(`/students/?${params.toString()}`, {}, token)
    },
    enabled: Boolean(token),
    placeholderData: (previous) => previous,
  })

  const students = data?.results ?? []

  function handleSearchChange(event) {
    setSearch(event.target.value)
    setPage(1)
  }

  function toggleGrade(id) {
    setExcludedGrades((current) => {
      const next = new Set(current)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
    setPage(1)
  }

  function toggleGroup(gradeLevels, checked) {
    setExcludedGrades((current) => {
      const next = new Set(current)
      gradeLevels.forEach((grade) => (checked ? next.delete(grade.id) : next.add(grade.id)))
      return next
    })
    setPage(1)
  }

  return (
    <div className="page-wrap">
      <header className="topbar roster-topbar">
        <button className="menu-button" onClick={openMenu} aria-label="Open navigation"><Menu size={20} /></button>
        <div className="breadcrumb"><span>School Directory</span><ChevronDown size={13} /><strong>Roster</strong></div>
        <UserMenu />
      </header>

      <main className="content roster-content">
        <div className="roster-page-heading">
          <h1 className="roster-page-title">Roster</h1>
          <nav className="roster-tabs">
            {ROSTER_TABS.map((tab) => (
              <button
                key={tab}
                className={`roster-tab ${activeTab === tab ? 'roster-tab-active' : ''}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>

        {activeTab !== 'Students' ? (
          <RoleUsersTab
            key={activeTab}
            tab={activeTab}
            token={token}
            canManagePasswords={actualRole === 'ADMIN'}
            onAddUser={() => setAddUserOpen(true)}
          />
        ) : (
          <>
            <div className="roster-header-strip">
              <div className="roster-title">Students ({data?.count ?? 0})</div>
              <div className="roster-actions">
                <input
                  className="roster-search"
                  type="text"
                  placeholder="Search by Name or E-mail"
                  value={search}
                  onChange={handleSearchChange}
                />
                <button className="add-user-button" onClick={() => setAddUserOpen(true)}>
                  <Plus size={15} />Add User
                </button>
                <button
                  className={`filter-button ${isFiltered ? 'filter-button-active' : ''}`}
                  onClick={() => setFilterOpen((current) => !current)}
                >
                  <span className="filter-icon" />Filter
                </button>
              </div>
            </div>

            {filterOpen && filterOptions && (
              <div className="filter-panel">
                <div className="filter-groups">
                  {filterOptions.groups.map((group) => (
                    <div className="filter-group" key={group.track}>
                      <label className="filter-group-label">
                        <input
                          type="checkbox"
                          checked={group.grade_levels.every((grade) => !excludedGrades.has(grade.id))}
                          onChange={(event) => toggleGroup(group.grade_levels, event.target.checked)}
                        />
                        {group.track}
                      </label>
                      {group.grade_levels.map((grade) => (
                        <label className="filter-item-label" key={grade.id}>
                          <input type="checkbox" checked={!excludedGrades.has(grade.id)} onChange={() => toggleGrade(grade.id)} />
                          {grade.display_name ?? grade.name}
                        </label>
                      ))}
                    </div>
                  ))}
                  {filterOptions.ungrouped.length > 0 && (
                    <div className="filter-group">
                      <span className="filter-group-label filter-group-label-static">Other Grade Levels</span>
                      {filterOptions.ungrouped.map((grade) => (
                        <label className="filter-item-label" key={grade.id}>
                          <input type="checkbox" checked={!excludedGrades.has(grade.id)} onChange={() => toggleGrade(grade.id)} />
                          {grade.display_name ?? grade.name}
                        </label>
                      ))}
                    </div>
                  )}
                </div>
                <label className="filter-no-grade">
                  <input
                    type="checkbox"
                    checked={includeNoGrade}
                    onChange={(event) => { setIncludeNoGrade(event.target.checked); setPage(1) }}
                  />
                  Include students without grade
                </label>
              </div>
            )}

            {isLoading && <p className="roster-state">Loading students...</p>}
            {isError && <p className="roster-state roster-state-error">{error.message}</p>}

            {!isLoading && !isError && (
              <>
                <div className="roster-table-wrap">
                  <table className="roster-table">
                    <thead>
                      <tr>
                        <th className="roster-col-name">Name</th>
                        <th className="roster-col-grade">Grade</th>
                        <th className="roster-col-parents">Parents</th>
                        <th className="roster-col-last">Status</th>
                        <th className="roster-col-actions" />
                      </tr>
                    </thead>
                    <tbody>
                      {students.map((student) => (
                        <tr key={student.id}>
                          <td className="roster-name-cell">
                            <div className="student-badge-group">
                              <span className={`student-initial ${TONES[student.id % TONES.length]}`}>{initialsOf(student.full_name)}</span>
                              <button className="name-link student-name-text" type="button" onClick={() => setEditingStudent(student)}>
                                {student.full_name}
                              </button>
                            </div>
                          </td>
                          <td className="roster-grade-cell">{student.grade ?? 'â€”'}</td>
                          <td className="roster-parent-cell">
                            {student.guardian_count > 0
                              ? <span className="parent-chip">Parents</span>
                              : <span className="parent-chip parent-chip-muted">None</span>}
                          </td>
                          <td className="roster-last-cell">{student.enrollment_status ?? 'â€”'}</td>
                          <td className="roster-action-cell"><button className="row-action" type="button" aria-label={`Edit ${student.full_name}`} onClick={() => setEditingStudent(student)}>âœŽ</button></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="roster-pagination">
                  <button className="secondary-button" disabled={!data?.previous} onClick={() => setPage((current) => current - 1)}>Previous</button>
                  <span className="roster-page-indicator">Page {page}</span>
                  <button className="secondary-button" disabled={!data?.next} onClick={() => setPage((current) => current + 1)}>Next</button>
                </div>
              </>
            )}
          </>
        )}
      </main>
      {editingStudent && (
        <EditProfileModal
          token={token}
          path="/students/"
          row={editingStudent}
          fields={STUDENT_FIELDS}
          loadDetail
          canManagePasswords={actualRole === 'ADMIN'}
          onClose={() => setEditingStudent(null)}
        />
      )}
      {addUserOpen && (
        <AddUserModal
          token={token}
          onClose={() => setAddUserOpen(false)}
        />
      )}
    </div>
  )
}
