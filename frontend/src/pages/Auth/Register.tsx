import React from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../shared/api/client'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'

const schema = z.object({
  email: z.string().email('email inválido'),
  password: z.string().min(6, 'mínimo 6 caracteres'),
})
type FormValues = z.infer<typeof schema>

export default function Register() {
  const navigate = useNavigate()
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({ resolver: zodResolver(schema) })
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null)
  const [okMsg, setOkMsg] = React.useState<string | null>(null)

  const onSubmit = async (data: FormValues) => {
    setErrorMsg(null)
    setOkMsg(null)
    try {
      await api.post('/auth/register', data)
      setOkMsg('registrado, redirecionando para login…')
      setTimeout(() => navigate('/auth/login'), 800)
    } catch (e: any) {
      const detail = e?.response?.data?.detail || 'erro ao registrar'
      setErrorMsg(String(detail))
    }
  }

  return (
    <div className="max-w-md mx-auto">
      <div className="card">
        <div className="card-body">
          <h2 className="text-lg font-semibold mb-1">Registrar</h2>
          <p className="text-slate-600 mb-4">Crie sua conta para começar.</p>
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
              <button type="submit" disabled={isSubmitting} className="btn btn-primary">Registrar</button>
              {okMsg && <span className="text-emerald-600 text-sm">{okMsg}</span>}
              {errorMsg && <span className="text-red-500 text-sm">{errorMsg}</span>}
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
