import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

interface AuthContextValue {
  token: string | null
  isAuthenticated: boolean
  login: (t: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))

  useEffect(() => {
    if (token) localStorage.setItem('token', token)
    else localStorage.removeItem('token')
  }, [token])

  const value = useMemo<AuthContextValue>(() => ({
    token,
    isAuthenticated: !!token,
    login: (t: string) => setToken(t),
    logout: () => setToken(null),
  }), [token])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
