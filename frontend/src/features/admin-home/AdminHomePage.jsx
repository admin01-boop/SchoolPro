import { useOutletContext } from 'react-router-dom'
import { Menu } from 'lucide-react'
import UserMenu from '@/components/UserMenu'
import BasicAccountHomePage from '@/features/student-portal/BasicAccountHomePage'

export default function AdminHomePage() {
  const { openMenu } = useOutletContext()

  return (
    <div className="page-wrap">
      <header className="topbar">
        <button className="menu-button" type="button" onClick={openMenu} aria-label="Open menu">
          <Menu size={18} />
        </button>
        <div className="breadcrumb"><strong>Home</strong></div>
        <UserMenu />
      </header>
      <main className="content">
        <BasicAccountHomePage title="Admin Home" role="Admin" />
      </main>
    </div>
  )
}