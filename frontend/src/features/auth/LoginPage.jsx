import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, ArrowLeft, GraduationCap } from 'lucide-react'
import { API_ROOT } from '@/lib/apiClient'
import { useAuth } from '@/features/auth/AuthContext'
import { homePathFor } from '@/features/auth/roles'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const response = await fetch(`${API_ROOT}/auth-token/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username, password }),
      })
      const result = await response.json()
      if (!response.ok) throw new Error(result.non_field_errors?.[0] || 'Login failed')
      login(result.token, {
        username: result.username,
        role: result.role,
        must_change_password: result.must_change_password,
      })
      navigate(result.must_change_password ? '/change-password' : homePathFor({ role: result.role }), { replace: true })
    } catch (loginError) {
      setError(loginError.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="login-shell">
      <div className="login-ornament" aria-hidden="true" />
      <section className="login-card">
        <div className="brand-lockup"><GraduationCap size={22} /><span>ManageBac</span></div>
        <p className="eyebrow">School administration</p>
        <h1>Welcome back</h1>
        <p className="login-copy">Sign in to manage your school settings and academic structure.</p>
        <form onSubmit={handleSubmit}>
          <label>Username<input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" /></label>
          <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required /></label>
          {error && <p className="error-message"><AlertCircle size={16} />{error}</p>}
          <button className="primary-button login-button" type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}<ArrowLeft size={16} className="login-arrow" />
          </button>
        </form>
        <p className="login-footnote">Use your Django admin account.</p>
      </section>
    </main>
  )
}
