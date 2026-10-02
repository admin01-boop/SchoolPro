import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { useNavigate } from 'react-router-dom'
import Sidebar from '@/components/Sidebar'
import { useAuth } from '@/features/auth/AuthContext'

export default function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false)
  const { logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="app-shell">
      <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} onLogout={handleLogout} />
      <Outlet context={{ openMenu: () => setMenuOpen(true) }} />
    </div>
  )
}
