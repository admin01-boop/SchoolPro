import { Navigate } from 'react-router-dom'
import { useAuth } from '@/features/auth/AuthContext'
import { homePathFor } from '@/features/auth/roles'

export default function PortalHome() {
  const { user } = useAuth()
  const homePath = homePathFor(user)

  if (homePath !== '/me') return <Navigate to={homePath} replace />

  return (
    <p className="roster-state" role="status">
      Your account can sign in, but a portal for your role is not available yet.
    </p>
  )
}
