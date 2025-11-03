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
    <div className="max-w-md mx-auto">
      <div className="card">
        <div className="card-body">
          <h2 className="text-lg font-semibold mb-1">Login</h2>
          <p className="text-slate-600 mb-4">Entre para acessar os módulos.</p>
          <form onSubmit={handleSubmit(onSubmit)} className="grid gap-3">
            <div>
              <label className="label">Email</label>
              <input placeholder="you@example.com" {...register('email')} className="input" />
              {errors.email && <span className="text-red-500 text-xs">{errors.email.message}</span>}
            </div>
            <div>
              <label className="label">Senha</label>
              <input placeholder="••••••••" type="password" {...register('password')} className="input" />
              {errors.password && <span className="text-red-500 text-xs">{errors.password.message}</span>}
            </div>
            <div className="flex items-center gap-2">
              <button type="submit" disabled={isSubmitting} className="btn btn-primary">Entrar</button>
              {status && <span className="text-slate-600 text-sm">{status}</span>}
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
