import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { request } from '@/lib/apiClient'
import EditProfileModal from './EditProfileModal'
import { LOGIN_FIELDS, PARENT_FIELDS } from './editFields'

const dash = (value) => value || '-'
const statusOf = (row) => (row.is_active ? 'Active' : 'Inactive')

const EMPLOYEE_ID = { name: 'employee_id', label: 'Employee ID' }
const HIRE_DATE = { name: 'hire_date', label: 'Hire Date', type: 'date' }
const PHONE = { name: 'phone', label: 'Phone' }

// Every roster tab except Students reads its own table; `editFields` are the columns editable from the name link.
const TAB_CONFIG = {
  'Teachers & Advisors': {
    path: '/roster-teachers/',
    editFields: [...LOGIN_FIELDS, EMPLOYEE_ID, HIRE_DATE],
    columns: [
      ['Name', (row) => row.full_name],
      ['Employee ID', (row) => dash(row.employee_id)],
      ['E-mail', (row) => dash(row.email)],
      ['Status', statusOf],
    ],
  },
  Staff: {
    path: '/roster-staff/',
    editFields: [
      ...LOGIN_FIELDS,
      EMPLOYEE_ID,
      HIRE_DATE,
      { name: 'job_title', label: 'Job Title' },
      { name: 'department', label: 'Department' },
    ],
    columns: [
      ['Name', (row) => row.full_name],
      ['Employee ID', (row) => dash(row.employee_id)],
      ['Job title', (row) => dash(row.job_title)],
      ['Department', (row) => dash(row.department)],
      ['E-mail', (row) => dash(row.email)],
      ['Status', statusOf],
    ],
  },
  Parents: {
    path: '/roster-parents/',
    editFields: PARENT_FIELDS,
    columns: [
      ['Name', (row) => row.full_name],
      ['Phone', (row) => dash(row.phone_1)],
      ['E-mail', (row) => dash(row.email)],
      ['Children', (row) => dash(row.children.map((child) => child.full_name).join(', '))],
      ['Login', (row) => (row.has_login ? 'Yes' : 'No login')],
    ],
  },
  Observers: {
    path: '/roster-observers/',
    editFields: [...LOGIN_FIELDS, { name: 'organization', label: 'Organization' }, PHONE],
    columns: [
      ['Name', (row) => row.full_name],
      ['Organization', (row) => dash(row.organization)],
      ['Phone', (row) => dash(row.phone)],
      ['E-mail', (row) => dash(row.email)],
      ['Status', statusOf],
    ],
  },
  Admins: {
    path: '/roster-admins/',
    editFields: [...LOGIN_FIELDS, EMPLOYEE_ID, { name: 'job_title', label: 'Job Title' }, PHONE],
    columns: [
      ['Name', (row) => row.full_name],
      ['Employee ID', (row) => dash(row.employee_id)],
      ['Job title', (row) => dash(row.job_title)],
      ['E-mail', (row) => dash(row.email)],
      ['Status', statusOf],
    ],
  },
}

export default function RoleUsersTab({ tab, token, canManagePasswords, onAddUser }) {
  const config = TAB_CONFIG[tab]
  const columns = config.columns
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [editing, setEditing] = useState(null)

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['roster-users', tab, search, page],
    queryFn: () => {
      const params = new URLSearchParams({ search, page: String(page) })
      return request(`${config.path}?${params.toString()}`, {}, token)
    },
    enabled: Boolean(token),
    placeholderData: (previous) => previous,
  })

  const rows = data?.results ?? []

  return (
    <>
      <div className="roster-header-strip">
        <div className="roster-title">{tab} ({data?.count ?? 0})</div>
        <div className="roster-actions">
          <input
            className="roster-search"
            type="text"
            placeholder="Search by Name or E-mail"
            value={search}
            onChange={(event) => { setSearch(event.target.value); setPage(1) }}
          />
          <button className="add-user-button" onClick={onAddUser}><Plus size={15} />Add User</button>
        </div>
      </div>

      {isLoading && <p className="roster-state">Loading users...</p>}
      {isError && <p className="roster-state roster-state-error">{error.message}</p>}

      {!isLoading && !isError && (
        <>
          <div className="roster-table-wrap">
            <table className="roster-table">
              <thead>
                <tr>
                  {columns.map(([label]) => <th key={label}>{label}</th>)}
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id}>
                    {columns.map(([label, render], index) => (
                      <td key={label}>
                        {index === 0 ? (
                          <button className="name-link" type="button" onClick={() => setEditing(row)}>{render(row)}</button>
                        ) : render(row)}
                      </td>
                    ))}
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
      {editing && (
        <EditProfileModal
          token={token}
          path={config.path}
          row={editing}
          fields={config.editFields}
          canManagePasswords={canManagePasswords}
          onClose={() => setEditing(null)}
        />
      )}
    </>
  )
}
