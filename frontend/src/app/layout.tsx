import React from 'react'
import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../shared/auth/AuthContext'
import { useQueryClient } from '@tanstack/react-query'

export const AppLayout: React.FC = () => {
  const { isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const onLogout = () => {
    logout()
    qc.clear()
    navigate('/auth/login')
  }
  return (
    <div>
      <header style={{ padding: 12, borderBottom: '1px solid #eee' }}>
        <nav style={{ display: 'flex', gap: 12 }}>
          <Link to="/">Home</Link>
          {!isAuthenticated && <Link to="/auth/login">Login</Link>}
          {!isAuthenticated && <Link to="/auth/register">Register</Link>}
          {isAuthenticated && <button onClick={onLogout}>Logout</button>}
          <Link to="/fin/accounts">Accounts</Link>
          <Link to="/fin/categories">Categories</Link>
          <Link to="/fin/transactions">Transactions</Link>
        </nav>
      </header>
      <main style={{ padding: 16 }}>
        <Outlet />
      </main>
    </div>
  )
}
