import React from 'react'
import { Link, Outlet } from 'react-router-dom'

export const AppLayout: React.FC = () => {
  return (
    <div>
      <header style={{ padding: 12, borderBottom: '1px solid #eee' }}>
        <nav style={{ display: 'flex', gap: 12 }}>
          <Link to="/">Home</Link>
          <Link to="/auth/login">Login</Link>
          <Link to="/fin/accounts">Accounts</Link>
        </nav>
      </header>
      <main style={{ padding: 16 }}>
        <Outlet />
      </main>
    </div>
  )
}
