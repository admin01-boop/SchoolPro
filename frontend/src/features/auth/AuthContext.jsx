import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { API_ROOT, setUnauthorizedHandler } from '@/lib/apiClient'

const TOKEN_KEY = 'managbac-token'
const USER_KEY = 'managbac-user'
const VIEW_AS_KEY = 'managbac-view-as'
const AuthContext = createContext(null)

function readStoredUser() {
  try {
    return JSON.parse(sessionStorage.getItem(USER_KEY))
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(() => sessionStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState(readStoredUser)
  const [viewAs, setViewAsState] = useState(() => sessionStorage.getItem(VIEW_AS_KEY))

  const setViewAs = useCallback((role) => {
    if (role) sessionStorage.setItem(VIEW_AS_KEY, role)
    else sessionStorage.removeItem(VIEW_AS_KEY)
    setViewAsState(role || null)
  }, [])

  const clearToken = useCallback(() => {
    sessionStorage.removeItem(TOKEN_KEY)
    sessionStorage.removeItem(USER_KEY)
    sessionStorage.removeItem(VIEW_AS_KEY)
    setTokenState(null)
    setUser(null)
    setViewAsState(null)
  }, [])

  const login = useCallback((newToken, newUser = null) => {
    sessionStorage.setItem(TOKEN_KEY, newToken)
    if (newUser) sessionStorage.setItem(USER_KEY, JSON.stringify(newUser))
    setTokenState(newToken)
    setUser(newUser)
  }, [])

  const updateUser = useCallback((updates) => {
    setUser((current) => {
      const updated = { ...current, ...updates }
      sessionStorage.setItem(USER_KEY, JSON.stringify(updated))
      return updated
    })
  }, [])

  const logout = useCallback(() => {
    // Revoke server-side; local sign-out must not depend on the network call.
    if (token) {
      fetch(`${API_ROOT}/auth/logout/`, { method: 'POST', headers: { Authorization: `Token ${token}` } }).catch(() => {})
    }
    clearToken()
  }, [token, clearToken])

  useEffect(() => {
    setUnauthorizedHandler(clearToken)
    return () => setUnauthorizedHandler(null)
  }, [clearToken])

  // UI-only preview for admins; the API still enforces the real role.
  const canPreview = user?.role === 'ADMIN'
  const effectiveUser = canPreview && viewAs ? { ...user, role: viewAs } : user

  return (
    <AuthContext.Provider value={{ token, user: effectiveUser, actualRole: user?.role, canPreview, viewAs, setViewAs, login, updateUser, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within an AuthProvider')
  return context
}
