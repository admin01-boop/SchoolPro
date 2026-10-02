import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  ArrowLeft, BookOpen, Building2, CalendarDays, ChevronDown, CircleHelp,
  FileText, GraduationCap, Home, LayoutGrid, LogOut, Search, Settings, ShieldCheck, Users, X,
} from 'lucide-react'

const navigation = [
  { label: 'Name, Address & Logo', icon: Building2 },
  { label: 'Key Academic Functions', icon: BookOpen, to: '/settings/key-academic-functions' },
  { label: 'Years & Levels', icon: LayoutGrid, to: '/settings/years-levels' },
  { label: 'Chat', icon: CircleHelp },
  { label: 'Discussions & User Mentions', icon: Users },
  { label: 'Quick Links', icon: FileText },
  { label: 'ManageBac AI', icon: Search },
  { label: 'Terminology', icon: FileText },
  { label: 'Brand Customisation', icon: Settings },
]

const secondaryNavigation = [
  { label: 'Services Manager', icon: Settings },
  { label: 'School Directory', icon: Users },
  { label: 'Import Manager', icon: FileText },
  { label: 'Data Exchange', icon: ArrowLeft },
  { label: 'Attendance & Calendars', icon: CalendarDays },
  { label: 'Behaviour & Discipline', icon: ShieldCheck },
  { label: 'Security & Permissions', icon: ShieldCheck },
  { label: 'Academic Terms', icon: BookOpen },
  { label: 'Billing', icon: FileText },
  { label: 'Integrations', icon: LayoutGrid },
  { label: 'Develop', icon: Settings },
]

const schoolDirectorySections = [{ label: 'Roster', to: '/directory/roster' }]

export default function Sidebar({ onLogout, open, onClose }) {
  const [directoryOpen, setDirectoryOpen] = useState(true)
  const [schoolSettingsOpen, setSchoolSettingsOpen] = useState(true)

  return (
    <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
      <div className="sidebar-brand">
        <div className="brand-mark"><GraduationCap size={17} /></div>
        <span>School Settings</span>
        <button className="mobile-close" onClick={onClose} aria-label="Close menu"><X size={17} /></button>
      </div>
      <nav className="settings-nav">
        <NavLink to="/admin/home" end onClick={onClose} className={({ isActive }) => `nav-item ${isActive ? 'nav-item-active' : ''}`}>
          <Home size={15} />Home
        </NavLink>
        <div className="nav-group">
          <button className="nav-item" aria-expanded={schoolSettingsOpen} onClick={() => setSchoolSettingsOpen((current) => !current)}>
            <Settings size={15} />School Settings
            <ChevronDown className={`nav-chevron ${schoolSettingsOpen ? 'nav-chevron-open' : ''}`} size={14} />
          </button>
          {schoolSettingsOpen && navigation.map(({ label, to }) => to ? (
            <NavLink key={label} to={to} onClick={onClose} className={({ isActive }) => `nav-item nav-subitem ${isActive ? 'nav-item-active' : ''}`}>
              {label}
            </NavLink>
          ) : (
            <button className="nav-item nav-subitem" key={label}>{label}</button>
          ))}
        </div>
      </nav>
      <div className="nav-divider" />
      <nav className="settings-nav secondary-nav">
        {secondaryNavigation.map(({ label, icon: Icon }) => label === 'School Directory' ? (
          <div className="nav-group" key={label}>
            <button className="nav-item" aria-expanded={directoryOpen} onClick={() => setDirectoryOpen((current) => !current)}>
              <Icon size={15} />{label}
              <ChevronDown className={`nav-chevron ${directoryOpen ? 'nav-chevron-open' : ''}`} size={14} />
            </button>
            {directoryOpen && schoolDirectorySections.map((section) => (
              <NavLink
                key={section.label}
                to={section.to}
                onClick={onClose}
                className={({ isActive }) => `nav-item nav-subitem ${isActive ? 'nav-item-active' : ''}`}
              >
                {section.label}
              </NavLink>
            ))}
          </div>
        ) : (
          <button className="nav-item" key={label}><Icon size={15} />{label}</button>
        ))}
      </nav>
      <button className="logout-button" onClick={onLogout}><LogOut size={15} />Log out</button>
    </aside>
  )
}
