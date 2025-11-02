import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../shared/api/client'

export default function Accounts() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['accounts'],
    queryFn: async () => (await api.get('/fin/accounts')).data,
  })

  if (isLoading) return <p>Carregando…</p>
  if (error) return <p>Erro ao carregar contas</p>

  return (
    <div>
      <h2>Accounts</h2>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  )
}
