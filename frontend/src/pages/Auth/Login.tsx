import React from 'react'
import { api } from '../../shared/api/client'
import { useAuth } from '../../shared/auth/AuthContext'
import { useLocation, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useQueryClient } from '@tanstack/react-query'

const schema = z.object({
  email: z.string().email('email inválido'),
  password: z.string().min(1, 'senha obrigatória'),
})

type FormValues = z.infer<typeof schema>

export default function Login() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({ resolver: zodResolver(schema) })
  const [status, setStatus] = React.useState<string | null>(null)
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation() as any
  const from = location.state?.from?.pathname || '/fin/accounts'
  const qc = useQueryClient()

  const onSubmit = async (data: FormValues) => {
    try {
      const r = await api.post('/auth/login', data)
      const token = (r.data && (r.data.access_token || r.data.token)) || ''
      if (token) {
        login(token)
        qc.clear()
        setStatus('ok')
        navigate(from, { replace: true })
      } else {
        setStatus('sem token')
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'erro'
      setStatus(`erro: ${detail}`)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="grid gap-2 max-w-80">
      <h2>Login</h2>
      <input placeholder="email" {...register('email')} className="px-2 py-1 rounded text-black" />
      {errors.email && <span className="text-red-400 text-sm">{errors.email.message}</span>}
      <input placeholder="password" type="password" {...register('password')} className="px-2 py-1 rounded text-black" />
      {errors.password && <span className="text-red-400 text-sm">{errors.password.message}</span>}
      <button type="submit" disabled={isSubmitting} className="bg-emerald-500 hover:bg-emerald-600 text-white px-3 py-1 rounded">Entrar</button>
      {status && <p>Status: {status}</p>}
    </form>
  )
}
