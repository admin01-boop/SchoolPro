import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { request } from '@/lib/apiClient'

function EditForm({ token, path, row, initial, fields, canManagePasswords, onClose }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState(() => Object.fromEntries(
    fields.map(({ name }) => [name, initial[name] ?? '']),
  ))
  const [password, setPassword] = useState('')
  const [requirePasswordChange, setRequirePasswordChange] = useState(initial.must_change_password ?? true)
  const hasLinkedLogin = path === '/students/'
    ? Boolean(initial.user)
    : path === '/roster-parents/'
      ? Boolean(initial.has_login)
      : true

  const save = useMutation({
    mutationFn: (payload) => request(`${path}${row.id}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['roster-users'] })
      await queryClient.invalidateQueries({ queryKey: ['students'] })
      onClose()
    },
  })

  function updateField(event) {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  function submit(event) {
    event.preventDefault()
    // Empty date inputs must be sent as null; the API rejects an empty string for dates.
    const payload = Object.fromEntries(fields.map(({ name, type }) => [
      name,
      type === 'date' && form[name] === '' ? null : form[name],
    ]))
    if (canManagePasswords && hasLinkedLogin) {
      if (password) payload.password = password
      payload.require_password_change = requirePasswordChange
    }
    save.mutate(payload)
  }

  return (
    <form className="roster-modal-form" onSubmit={submit}>
      <div className="roster-modal-body">
        <section className="add-user-section">
          <div className="add-user-grid">
            {fields.map(({ name, label, type = 'text', required, options }) => (
              <label key={name} className={`add-user-field ${type === 'textarea' ? 'add-user-field-wide' : ''}`}>
                <span>{label}{required && <b> *</b>}</span>
                {type === 'select' ? (
                  <select name={name} value={form[name]} onChange={updateField} required={required}>
                    <option value="">Select</option>
                    {options.map(([value, text]) => <option key={value} value={value}>{text}</option>)}
                  </select>
                ) : type === 'textarea' ? (
                  <textarea name={name} value={form[name]} onChange={updateField} rows={3} />
                ) : (
                  <input name={name} type={type} value={form[name]} onChange={updateField} required={required} />
                )}
              </label>
            ))}
          </div>
        </section>
        {canManagePasswords && hasLinkedLogin && (
          <section className="add-user-section password-edit-section">
            <h3>Password</h3>
            <div className="add-user-grid">
              <label className="add-user-field add-user-field-wide">
                <span>New password</span>
                <input
                  type="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(event) => {
                    setPassword(event.target.value)
                    if (!password && event.target.value) setRequirePasswordChange(true)
                  }}
                  placeholder="Leave blank to keep the current password"
                />
              </label>
              <label className="password-change-toggle">
                <input
                  type="checkbox"
                  checked={requirePasswordChange}
                  onChange={(event) => setRequirePasswordChange(event.target.checked)}
                />
                <span>Require password change at next login</span>
              </label>
            </div>
          </section>
        )}
        {save.isError && <p className="add-user-error" role="alert">{save.error.message}</p>}
      </div>

      <footer className="roster-modal-footer">
        <button className="secondary-button" type="button" onClick={onClose}>Cancel</button>
        <button className="primary-button" type="submit" disabled={save.isPending}>
          {save.isPending ? 'Saving...' : 'Save'}
        </button>
      </footer>
    </form>
  )
}

// `loadDetail` is for rows whose list view omits some editable fields (students).
export default function EditProfileModal({ token, path, row, fields, loadDetail = false, canManagePasswords = false, onClose }) {
  const detail = useQuery({
    queryKey: ['roster-detail', path, row.id],
    queryFn: () => request(`${path}${row.id}/`, {}, token),
    enabled: loadDetail && Boolean(token),
    gcTime: 0,
  })

  return (
    <div className="roster-modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="roster-modal" role="dialog" aria-modal="true" aria-labelledby="edit-profile-title">
        <header className="roster-modal-header">
          <div>
            <p className="roster-modal-eyebrow">School Directory</p>
            <h2 id="edit-profile-title">Edit {row.full_name}</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </header>

        {loadDetail && detail.isLoading && <p className="roster-state">Loading...</p>}
        {loadDetail && detail.isError && <p className="roster-state roster-state-error">{detail.error.message}</p>}
        {(!loadDetail || detail.data) && (
          <EditForm
            token={token}
            path={path}
            row={row}
            initial={loadDetail ? detail.data : row}
            fields={fields}
            canManagePasswords={canManagePasswords}
            onClose={onClose}
          />
        )}
      </section>
    </div>
  )
}
