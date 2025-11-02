import React from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../shared/auth/AuthContext'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '../shared/ui/Button'

export const AppLayout: React.FC = () => {
  const { isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const onLogout = () => {
    logout()
    qc.clear()
    navigate('/auth/login')
  }
  const linkClass = ({ isActive }: { isActive: boolean }) => `px-2 py-1 rounded-md ${isActive ? 'bg-accent-200 text-ink' : 'text-slate-700 hover:bg-slate-100'}`
  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/70 backdrop-blur supports-[backdrop-filter]:bg-white/60">
        <div className="container-page py-3 flex items-center gap-4">
          <Link to="/" className="text-lg font-semibold text-ink">Epic GRP</Link>
          <nav className="flex items-center gap-2">
            <NavLink to="/" className={linkClass} end>Home</NavLink>
            <NavLink to="/fin/accounts" className={linkClass}>Accounts</NavLink>
            <NavLink to="/fin/categories" className={linkClass}>Categories</NavLink>
            <NavLink to="/fin/transactions" className={linkClass}>Transactions</NavLink>
            <NavLink to="/fin/transfers" className={linkClass}>Transfers</NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-2">
            {!isAuthenticated && <Link to="/auth/login" className="btn btn-ghost">Login</Link>}
            {!isAuthenticated && <Link to="/auth/register" className="btn btn-primary">Register</Link>}
            {isAuthenticated && <Button onClick={onLogout} variant="ghost">Logout</Button>}
          </div>
        </div>
      </header>
      <main className="container-page">
        <Outlet />
      </main>
    </div>
  )
}
