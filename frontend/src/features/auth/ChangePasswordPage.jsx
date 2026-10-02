import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, GraduationCap } from 'lucide-react'
import { request } from '@/lib/apiClient'
import { useAuth } from '@/features/auth/AuthContext'
import { homePathFor } from '@/features/auth/roles'

export default function ChangePasswordPage() {
  const { token, user, updateUser } = useAuth()
  const navigate = useNavigate()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    if (newPassword !== confirmPassword) {
      setError('The new passwords do not match.')
      return
    }
    setLoading(true)
    try {
      await request('/auth/change-password/', {
        method: 'POST',
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      }, token)
      updateUser({ must_change_password: false })
      navigate(homePathFor(user), { replace: true })
    } catch (changeError) {
      setError(changeError.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="login-shell">
      <section className="login-card">
        <div className="brand-lockup"><GraduationCap size={22} /><span>ManageBac</span></div>
        <p className="eyebrow">Account security</p>
        <h1>Change your password</h1>
        <p className="login-copy">Choose a new password to continue.</p>
        <form onSubmit={handleSubmit}>
          <label>Current password<input type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} autoComplete="current-password" required /></label>
          <label>New password<input type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} autoComplete="new-password" required minLength={10} /></label>
          <label>Confirm new password<input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} autoComplete="new-password" required minLength={10} /></label>
          {error && <p className="error-message"><AlertCircle size={16} />{error}</p>}
          <button className="primary-button login-button" type="submit" disabled={loading}>
            {loading ? 'Changing password...' : 'Change password'}
          </button>
        </form>
      </section>
    </main>
  )
}