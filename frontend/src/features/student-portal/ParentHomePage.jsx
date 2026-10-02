import { useQuery } from '@tanstack/react-query'
import { request } from '@/lib/apiClient'
import { useAuth } from '@/features/auth/AuthContext'

const dash = (value) => value || '-'

const SAMPLE_CHILDREN = [
  { student_id: 'S0000', full_name: 'Sample Child', grade: 'Year 7', enrollment_status: 'Existing' },
]

export default function ParentHomePage() {
  const { token, user, actualRole } = useAuth()
  const isRealParent = actualRole === 'PARENT'
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['my-children'],
    queryFn: () => request('/me/children/', {}, token),
    enabled: Boolean(token) && isRealParent,
  })
  const children = isRealParent ? data : SAMPLE_CHILDREN

  if (isRealParent && isLoading) return <p className="roster-state">Loading your children...</p>
  if (isRealParent && isError) return <p className="roster-state roster-state-error">{error.message}</p>

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">{isRealParent ? 'Parent portal' : 'Parent portal (preview with sample data)'}</p>
          <h1>Welcome, {user.username}</h1>
        </div>
      </div>

      <section className="portal-card" aria-label="Children">
        <h2>My children</h2>
        {children.length === 0 ? (
          <p className="portal-muted">No children are linked to your account.</p>
        ) : (
          <ul className="portal-list">
            {children.map((child) => (
              <li key={child.student_id}>
                {child.full_name}{' '}
                <span className="portal-muted">({dash(child.grade)}, {dash(child.enrollment_status)})</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  )
}
