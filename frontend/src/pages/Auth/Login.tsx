import React, { useState } from 'react'
import { api } from '../../shared/api/client'
import { useAuth } from '../../shared/auth/AuthContext'
import { useLocation, useNavigate } from 'react-router-dom'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState<string | null>(null)
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation() as any
  const from = location.state?.from?.pathname || '/fin/accounts'

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const r = await api.post('/auth/login', { email, password })
      const token = (r.data && (r.data.access_token || r.data.token)) || ''
      if (token) {
        login(token)
        setStatus('ok')
        navigate(from, { replace: true })
      } else {
        setStatus('sem token')
      }
    } catch (err) {
      setStatus('erro')
    }
  }

  return (
    <form onSubmit={onSubmit} style={{ display: 'grid', gap: 8, maxWidth: 320 }}>
      <h2>Login</h2>
      <input placeholder="email" value={email} onChange={e => setEmail(e.target.value)} />
      <input placeholder="password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <button type="submit">Entrar</button>
      {status && <p>Status: {status}</p>}
    </form>
  )
}
