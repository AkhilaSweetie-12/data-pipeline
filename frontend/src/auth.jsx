import { createContext, useContext, useState } from 'react'
import { login as apiLogin } from './api'

const AuthContext = createContext(null)

const WRITE_ROLES = ['admin', 'data_engineer']

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('user')
    return raw ? JSON.parse(raw) : null
  })

  const signIn = async (username, password) => {
    const data = await apiLogin(username, password)
    const u = { username: data.username, role: data.role }
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(u))
    setUser(u)
    return u
  }

  const signOut = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  const canWrite = user && WRITE_ROLES.includes(user.role)
  const isAdmin = user && user.role === 'admin'

  return (
    <AuthContext.Provider value={{ user, signIn, signOut, canWrite, isAdmin }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
