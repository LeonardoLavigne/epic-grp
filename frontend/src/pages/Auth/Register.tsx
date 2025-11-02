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
    <form onSubmit={handleSubmit(onSubmit)} className="grid gap-2 max-w-80">
      <h2>Registrar</h2>
      <input placeholder="email" {...register('email')} className="px-2 py-1 rounded text-black" />
      {errors.email && <span className="text-red-400 text-sm">{errors.email.message}</span>}
      <input placeholder="password" type="password" {...register('password')} className="px-2 py-1 rounded text-black" />
      {errors.password && <span className="text-red-400 text-sm">{errors.password.message}</span>}
      <button type="submit" disabled={isSubmitting} className="bg-emerald-500 hover:bg-emerald-600 text-white px-3 py-1 rounded">Registrar</button>
      {okMsg && <p className="text-emerald-300">{okMsg}</p>}
      {errorMsg && <p className="text-red-400">{errorMsg}</p>}
    </form>
  )
}

