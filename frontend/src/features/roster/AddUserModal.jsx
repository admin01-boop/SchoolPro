import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { request } from '@/lib/apiClient'

const USER_TYPES = [
  ['STUDENT', 'Student'],
  ['TEACHER', 'Teacher & Advisor'],
  ['STAFF', 'Staff'],
  ['PARENT', 'Parent'],
  ['OBSERVER', 'Observer'],
  ['ADMIN', 'Admin'],
]

const INITIAL_FORM = {
  user_type: 'STUDENT',
  first_name: '',
  last_name: '',
  email: '',
  ui_language: 'en',
  student_id: '',
  sex: '',
  date_of_birth: '',
  grade_level: '',
  parent_ids: [],
  send_welcome_email: true,
}

export default function AddUserModal({ token, onClose }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState(INITIAL_FORM)
  const { data: options, isLoading: optionsLoading, isError: optionsError } = useQuery({
    queryKey: ['roster-user-options'],
    queryFn: () => request('/roster-user-options/', {}, token),
    enabled: Boolean(token) && form.user_type === 'STUDENT',
  })
  const gradeOptions = useMemo(() => options?.grade_levels ?? [], [options])
  const parents = options?.parents ?? []

  const createUser = useMutation({
    mutationFn: (payload) => request('/roster-users/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['students'] })
      await queryClient.invalidateQueries({ queryKey: ['roster-users'] })
    },
  })

  function updateField(event) {
    const { name, value, type, checked } = event.target
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
  }

  function submit(event) {
    event.preventDefault()
    const payload = {
      user_type: form.user_type,
      first_name: form.first_name,
      last_name: form.last_name,
      email: form.email,
      ui_language: form.ui_language,
      send_welcome_email: form.send_welcome_email,
    }
    if (form.user_type === 'STUDENT') {
      Object.assign(payload, {
        student_id: form.student_id,
        sex: form.sex,
        date_of_birth: form.date_of_birth,
        grade_level: form.grade_level || null,
        parent_ids: form.parent_ids,
      })
    }
    createUser.mutate(payload)
  }

  const result = createUser.data

  return (
    <div className="roster-modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="roster-modal" role="dialog" aria-modal="true" aria-labelledby="add-user-title">
        <header className="roster-modal-header">
          <div>
            <p className="roster-modal-eyebrow">School Directory</p>
            <h2 id="add-user-title">{result ? 'User Added' : 'Add User'}</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </header>

        {result ? (
          <div className="roster-modal-result" role="status">
              <p>{result.welcome_email_sent ? 'The welcome email was sent.' : 'The account was created; welcome email was not sent.'}</p>
            <dl>
              <div><dt>Username</dt><dd>{result.username}</dd></div>
              {!result.welcome_email_sent && <div><dt>Initial password</dt><dd><code>{result.initial_password}</code></dd></div>}
            </dl>
            <button className="primary-button" type="button" onClick={onClose}>Done</button>
          </div>
        ) : (
          <form className="roster-modal-form" onSubmit={submit}>
            <div className="roster-modal-body">
              <section className="add-user-section">
                <h3>User Details</h3>
                <div className="add-user-grid">
                  <label className="add-user-field">
                    <span>User Type</span>
                    <select name="user_type" value={form.user_type} onChange={updateField}>
                      {USER_TYPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                    </select>
                  </label>
                  <label className="add-user-field">
                    <span>First Name <b>*</b></span>
                    <input name="first_name" value={form.first_name} onChange={updateField} required />
                  </label>
                  <label className="add-user-field">
                    <span>Last Name <b>*</b></span>
                    <input name="last_name" value={form.last_name} onChange={updateField} required />
                  </label>
                  <label className="add-user-field">
                    <span>E-mail Address</span>
                    <input name="email" type="email" required value={form.email} onChange={updateField} />
                  </label>
                  <label className="add-user-field">
                    <span>UI Language</span>
                    <select name="ui_language" value={form.ui_language} onChange={updateField}>
                      <option value="en">English</option>
                      <option value="km">Khmer</option>
                    </select>
                  </label>
                </div>
              </section>

              {form.user_type === 'STUDENT' && (
                <section className="add-user-section add-user-student-section">
                  <h3>Student Details</h3>
                  <div className="add-user-grid">
                    <label className="add-user-field">
                      <span>Student ID <b>*</b></span>
                      <input name="student_id" value={form.student_id} onChange={updateField} maxLength={20} required />
                    </label>
                    <label className="add-user-field">
                      <span>Year Group or PYP Homeroom</span>
                      <select name="grade_level" value={form.grade_level} onChange={updateField}>
                        <option value="">Select a year group</option>
                        {gradeOptions.map((grade) => (
                          <option key={grade.id} value={grade.id}>{grade.display_name ?? grade.name}</option>
                        ))}
                      </select>
                    </label>
                    <label className="add-user-field">
                      <span>Sex <b>*</b></span>
                      <select name="sex" value={form.sex} onChange={updateField} required>
                        <option value="">Select sex</option>
                        <option value="FEMALE">Female</option>
                        <option value="MALE">Male</option>
                      </select>
                    </label>
                    <label className="add-user-field">
                      <span>Date of Birth <b>*</b></span>
                      <input name="date_of_birth" type="date" value={form.date_of_birth} onChange={updateField} required />
                    </label>
                    <label className="add-user-field add-user-field-wide">
                      <span>Parents</span>
                      <select
                        name="parent_ids"
                        multiple
                        value={form.parent_ids}
                        onChange={(event) => setForm((current) => ({
                          ...current,
                          parent_ids: Array.from(event.target.selectedOptions, (option) => option.value),
                        }))}
                        disabled={optionsLoading || optionsError || !options?.parents_enabled}
                      >
                        {parents.map((parent) => <option key={parent.id} value={parent.id}>{parent.full_name}</option>)}
                      </select>
                      {(optionsError || (options && !options.parents_enabled)) && <small>Parents Association is unavailable.</small>}
                    </label>
                  </div>
                </section>
              )}

              <section className="add-user-section add-user-email-section">
                <h3>Email Options</h3>
                <label className="add-user-checkbox">
                  <input name="send_welcome_email" type="checkbox" checked={form.send_welcome_email} onChange={updateField} />
                  <span>Send welcome e-mail with login instructions</span>
                </label>
              </section>

              {createUser.isError && <p className="add-user-error" role="alert">{createUser.error.message}</p>}
            </div>

            <footer className="roster-modal-footer">
              <button className="secondary-button" type="button" onClick={onClose}>Cancel</button>
              <button className="primary-button" type="submit" disabled={createUser.isPending}>
                {createUser.isPending ? 'Adding...' : 'Add User'}
              </button>
            </footer>
          </form>
        )}
      </section>
    </div>
  )
}