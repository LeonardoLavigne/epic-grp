import React, { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api/client'

interface Account { id: number; name: string; currency: string; status?: string }

export default function Accounts() {
  const qc = useQueryClient()
  const [nameFilter, setNameFilter] = useState('')
  const [newName, setNewName] = useState('')
  const [newCurrency, setNewCurrency] = useState('EUR')

  const params = useMemo(() => {
    const p: Record<string, string> = {}
    if (nameFilter.trim()) p.name = nameFilter.trim()
    return p
  }, [nameFilter])

  const { data, isLoading, error } = useQuery({
    queryKey: ['accounts', params],
    queryFn: async () => (await api.get('/fin/accounts', { params })).data as Account[],
  })

  const createMut = useMutation({
    mutationFn: async () => (await api.post('/fin/accounts', { name: newName, currency: newCurrency })).data,
    onSuccess: () => { setNewName(''); qc.invalidateQueries({ queryKey: ['accounts'] }) },
  })

  const closeMut = useMutation({
    mutationFn: async (id: number) => (await api.post(`/fin/accounts/${id}/close`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['accounts'] }),
  })

  if (isLoading) return <p>Carregando…</p>
  if (error) return <p>Erro ao carregar contas</p>

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <h2>Accounts</h2>

      <section style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input placeholder="filtrar por nome" value={nameFilter} onChange={e => setNameFilter(e.target.value)} />
      </section>

      <section>
        <h3>Criar conta</h3>
        <div style={{ display: 'flex', gap: 8 }}>
          <input placeholder="Nome" value={newName} onChange={e => setNewName(e.target.value)} />
          <select value={newCurrency} onChange={e => setNewCurrency(e.target.value)}>
            <option>EUR</option>
            <option>BRL</option>
            <option>USD</option>
          </select>
          <button onClick={() => createMut.mutate()} disabled={!newName.trim() || createMut.isPending}>Criar</button>
        </div>
        {createMut.isError && <p>Erro ao criar</p>}
      </section>

      <section>
        <h3>Lista</h3>
        <table>
          <thead>
            <tr><th>ID</th><th>Nome</th><th>Currency</th><th>Status</th><th>Ações</th></tr>
          </thead>
          <tbody>
            {(data || []).map((acc) => (
              <tr key={acc.id}>
                <td>{acc.id}</td>
                <td>{acc.name}</td>
                <td>{acc.currency}</td>
                <td>{acc.status || '-'}</td>
                <td>
                  <button onClick={() => closeMut.mutate(acc.id)} disabled={closeMut.isPending}>Fechar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
