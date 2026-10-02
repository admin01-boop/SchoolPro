import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/features/auth/AuthContext'
import AppLayout from '@/layouts/AppLayout'
import LoginPage from '@/features/auth/LoginPage'
import ChangePasswordPage from '@/features/auth/ChangePasswordPage'
import { homePathFor, isManagementUser } from '@/features/auth/roles'
import KeyAcademicFunctionsPage from '@/features/key-academic-functions/KeyAcademicFunctionsPage'
import RosterPage from '@/features/roster/RosterPage'
import AdminHomePage from '@/features/admin-home/AdminHomePage'
import PortalHome from '@/features/student-portal/PortalHome'
import StudentHomePage from '@/features/student-portal/StudentHomePage'
import ParentHomePage from '@/features/student-portal/ParentHomePage'
import TeacherHomePage from '@/features/student-portal/TeacherHomePage'
import ObserverHomePage from '@/features/student-portal/ObserverHomePage'
import StaffHomePage from '@/features/student-portal/StaffHomePage'
import YearsLevelsPage from '@/features/years-levels/YearsLevelsPage'
import PortalLayout from '@/layouts/PortalLayout'
import '@/styles/app.css'

const queryClient = new QueryClient()

function RequireAuth({ children }) {
  const { token, user } = useAuth()
  const location = useLocation()
  if (!token) return <Navigate to="/login" replace />
  if (user?.must_change_password && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" replace />
  }
  return children
}

function RequirePasswordChange({ children }) {
  const { user } = useAuth()
  return user?.must_change_password ? children : <Navigate to={homePathFor(user)} replace />
}

function RequireManagement({ children }) {
  const { user } = useAuth()
  return isManagementUser(user) ? children : <Navigate to={homePathFor(user)} replace />
}

function RequireRole({ role, children }) {
  const { user } = useAuth()
  return user?.role === role ? children : <Navigate to={homePathFor(user)} replace />
}

function RedirectIfAuthed({ children }) {
  const { token, user } = useAuth()
  return token ? <Navigate to={user?.must_change_password ? '/change-password' : homePathFor(user)} replace /> : children
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<RedirectIfAuthed><LoginPage /></RedirectIfAuthed>} />
            <Route path="/change-password" element={<RequireAuth><RequirePasswordChange><ChangePasswordPage /></RequirePasswordChange></RequireAuth>} />
            <Route path="/" element={<RequireAuth><RequireManagement><AppLayout /></RequireManagement></RequireAuth>}>
              <Route index element={<Navigate to="admin/home" replace />} />
              <Route path="admin/home" element={<AdminHomePage />} />
              <Route path="directory/roster" element={<RosterPage />} />
              <Route path="settings/key-academic-functions" element={<KeyAcademicFunctionsPage />} />
              <Route path="settings/years-levels" element={<YearsLevelsPage />} />
            </Route>
            <Route element={<RequireAuth><PortalLayout /></RequireAuth>}>
              <Route path="me" element={<PortalHome />} />
              <Route path="student/home" element={<RequireRole role="STUDENT"><StudentHomePage /></RequireRole>} />
              <Route path="parent/home" element={<RequireRole role="PARENT"><ParentHomePage /></RequireRole>} />
              <Route path="teacher/home" element={<RequireRole role="TEACHER"><TeacherHomePage /></RequireRole>} />
              <Route path="observer/home" element={<RequireRole role="OBSERVER"><ObserverHomePage /></RequireRole>} />
              <Route path="staff/home" element={<RequireRole role="STAFF"><StaffHomePage /></RequireRole>} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
