import { Outlet, useNavigate } from 'react-router-dom'
import { BookOpen, CalendarDays, CheckSquare, GraduationCap, LayoutDashboard, UserRound } from 'lucide-react'
import UserMenu from '@/components/UserMenu'
import { useAuth } from '@/features/auth/AuthContext'

export default function PortalLayout() {
  const { logout, user } = useAuth()
  const navigate = useNavigate()
  const isStudent = user?.role === 'STUDENT'

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className={`portal-shell${isStudent ? ' portal-shell-student' : ''}`}>
      {isStudent && (
        <aside className="student-sidebar">
          <div className="student-sidebar-header"><GraduationCap size={18} /><span>Student workspace</span></div>
          <p className="student-nav-label">STUDENT</p>
          <nav className="student-menu" aria-label="Student dashboard">
            <a className="student-menu-item student-menu-item-active" href="#student-dashboard"><LayoutDashboard size={15} />Dashboard</a>
            <a className="student-menu-item" href="#student-classes"><BookOpen size={15} />My classes</a>
            <a className="student-menu-item" href="#student-calendar"><CalendarDays size={15} />Calendar & timetable</a>
            <a className="student-menu-item" href="#student-tasks"><CheckSquare size={15} />Tasks & deadlines</a>
            <a className="student-menu-item" href="#student-record"><UserRound size={15} />My record</a>
          </nav>
          <div className="student-sidebar-footer">Southbridge International School</div>
        </aside>
      )}
      <header className="topbar">
        <div className="brand-lockup"><GraduationCap size={20} /><span>ManageBac</span></div>
        <div className="portal-actions">
          <UserMenu />
          <button className="secondary-button" type="button" onClick={handleLogout}>Log out</button>
        </div>
      </header>
      <main className={`content portal-content${isStudent ? ' portal-content-student' : ''}`}><Outlet /></main>
    </div>
  )
}
