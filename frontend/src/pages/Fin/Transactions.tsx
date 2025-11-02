import React, { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api/client'

interface Account { id: number; name: string }
interface Category { id: number; name: string; type: 'INCOME' | 'EXPENSE' }
interface Transaction { id: number; account_id: number; category_id: number | null; amount: string; occurred_at: string; description?: string }

export default function Transactions() {
  const qc = useQueryClient()
  // Filters
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [accountId, setAccountId] = useState<number | ''>('')
  const [categoryId, setCategoryId] = useState<number | ''>('')
  const [typeFilter, setTypeFilter] = useState<'INCOME' | 'EXPENSE' | ''>('')
  const [includeVoided, setIncludeVoided] = useState(false)

  // Create
  const [cAccountId, setCAccountId] = useState<number | ''>('')
  const [cCategoryId, setCCategoryId] = useState<number | ''>('')
  const [cAmount, setCAmount] = useState('0.00')
  const [cWhen, setCWhen] = useState<string>(() => new Date().toISOString())
  const [cDesc, setCDesc] = useState('')

  const accountsQ = useQuery({ queryKey: ['accounts', {}], queryFn: async () => (await api.get('/fin/accounts')).data as Account[] })
  const categoriesQ = useQuery({ queryKey: ['categories', {}], queryFn: async () => (await api.get('/fin/categories')).data as Category[] })

  const params = useMemo(() => {
    const p: Record<string, any> = {}
    if (fromDate) p.from_date = fromDate
    if (toDate) p.to_date = toDate
    if (accountId) p.account_id = accountId
    if (categoryId) p.category_id = categoryId
    if (typeFilter) p.type = typeFilter
    if (includeVoided) p.include_voided = true
    return p
  }, [fromDate, toDate, accountId, categoryId, typeFilter, includeVoided])

  const listQ = useQuery({
    queryKey: ['transactions', params],
    queryFn: async () => (await api.get('/fin/transactions', { params })).data as Transaction[],
  })

  const createMut = useMutation({
    mutationFn: async () => (await api.post('/fin/transactions', {
      account_id: cAccountId,
      category_id: cCategoryId || null,
      amount: cAmount,
      occurred_at: cWhen,
      description: cDesc || undefined,
    })).data as Transaction,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['transactions'] }); setCAmount('0.00'); setCDesc('') },
  })

  const voidMut = useMutation({
    mutationFn: async (id: number) => (await api.post(`/fin/transactions/${id}/void`)).data as Transaction,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['transactions'] }),
  })

  if (listQ.isLoading || accountsQ.isLoading || categoriesQ.isLoading) return <p>Carregando…</p>
  if (listQ.error) return <p>Erro ao carregar transações</p>

  const accounts = accountsQ.data || []
  const categories = categoriesQ.data || []
  const items = listQ.data || []

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <h2>Transactions</h2>

      <section style={{ display: 'grid', gap: 8 }}>
        <h3>Filtros</h3>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <label>
            de (ISO): <input value={fromDate} onChange={e => setFromDate(e.target.value)} placeholder="2025-01-01T00:00:00Z"/>
          </label>
          <label>
            até (ISO): <input value={toDate} onChange={e => setToDate(e.target.value)} placeholder="2025-01-31T23:59:59Z"/>
          </label>
          <label>
            conta:
            <select value={accountId} onChange={e => setAccountId(e.target.value ? Number(e.target.value) : '')}>
              <option value="">Todas</option>
              {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </label>
          <label>
            categoria:
            <select value={categoryId} onChange={e => setCategoryId(e.target.value ? Number(e.target.value) : '')}>
              <option value="">Todas</option>
              {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </label>
          <label>
            tipo:
            <select value={typeFilter} onChange={e => setTypeFilter((e.target.value || '') as any)}>
              <option value="">Todos</option>
              <option value="INCOME">INCOME</option>
              <option value="EXPENSE">EXPENSE</option>
            </select>
          </label>
          <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input type="checkbox" checked={includeVoided} onChange={e => setIncludeVoided(e.target.checked)} />
            incluir anuladas (voided)
          </label>
        </div>
      </section>

      <section style={{ display: 'grid', gap: 8 }}>
        <h3>Criar transação</h3>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <label>
            conta:
            <select value={cAccountId} onChange={e => setCAccountId(e.target.value ? Number(e.target.value) : '')}>
              <option value="">Selecione</option>
              {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </label>
          <label>
            categoria:
            <select value={cCategoryId} onChange={e => setCCategoryId(e.target.value ? Number(e.target.value) : '')}>
              <option value="">(opcional)</option>
              {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </label>
          <label>
            valor:
            <input value={cAmount} onChange={e => setCAmount(e.target.value)} placeholder="0.00"/>
          </label>
          <label>
            quando (ISO):
            <input value={cWhen} onChange={e => setCWhen(e.target.value)} />
          </label>
          <input value={cDesc} onChange={e => setCDesc(e.target.value)} placeholder="descrição (opcional)" />
          <button onClick={() => createMut.mutate()} disabled={createMut.isPending || !(cAccountId && cAmount)}>Criar</button>
          {createMut.isError && <span style={{ color: 'red' }}>Erro ao criar</span>}
        </div>
      </section>

      <section>
        <h3>Lista</h3>
        <table>
          <thead>
            <tr><th>ID</th><th>Conta</th><th>Categoria</th><th>Valor</th><th>Quando</th><th>Ações</th></tr>
          </thead>
          <tbody>
            {items.map(tx => (
              <tr key={tx.id}>
                <td>{tx.id}</td>
                <td>{tx.account_id}</td>
                <td>{tx.category_id ?? '-'}</td>
                <td>{tx.amount}</td>
                <td>{tx.occurred_at}</td>
                <td>
                  <button onClick={() => voidMut.mutate(tx.id)} disabled={voidMut.isPending}>Void</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
