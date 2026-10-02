import { useAuth } from '@/features/auth/AuthContext'

export default function BasicAccountHomePage({ title, role }) {
  const { user } = useAuth()

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">{title}</p>
          <h1>Welcome, {user?.username || 'user'}</h1>
        </div>
      </div>
      <section className="portal-card" aria-label="Basic account information">
        <h2>Basic information</h2>
        <dl className="portal-details">
          <div><dt>Username</dt><dd>{user?.username || '-'}</dd></div>
          <div><dt>Role</dt><dd>{role}</dd></div>
        </dl>
      </section>
    </>
  )
}