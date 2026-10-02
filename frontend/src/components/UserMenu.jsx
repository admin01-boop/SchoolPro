import { ChevronDown } from 'lucide-react'
import { useAuth } from '@/features/auth/AuthContext'

const ROLE_LABELS = {
  STUDENT: 'Student',
  TEACHER: 'Teacher',
  PARENT: 'Parent',
  OBSERVER: 'Observer',
  ADMIN: 'Admin',
  STAFF: 'Staff',
}

export default function UserMenu() {
  const { user, canPreview, setViewAs } = useAuth()
  return (
    <div className="user-menu">
      <span>{user?.username ?? 'Account'}</span>
      {canPreview ? (
        <select
          className="role-pill"
          aria-label="View as role"
          value={user.role}
          onChange={(event) => setViewAs(event.target.value === 'ADMIN' ? null : event.target.value)}
        >
          {Object.entries(ROLE_LABELS).map(([role, label]) => <option key={role} value={role}>{label}</option>)}
        </select>
      ) : (
        user?.role && <span className="role-pill">{ROLE_LABELS[user.role] ?? user.role}</span>
      )}
      <ChevronDown size={14} />
    </div>
  )
}
