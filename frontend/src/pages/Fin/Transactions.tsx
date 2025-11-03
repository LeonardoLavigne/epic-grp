import React, { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api/client'

interface Account { id: number; name: string }
interface Category { id: number; name: string; type: 'INCOME' | 'EXPENSE' }
interface Transaction {
  id: number
  account_id: number
  category_id: number | null
  amount: string
  occurred_at: string
  description?: string
  from_transfer: boolean
  transfer_id?: number | null
}

export default function Transactions() {
  const qc = useQueryClient()
  const [transferView, setTransferView] = useState<any | null>(null)
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

  const [loadingTransferId, setLoadingTransferId] = useState<number | null>(null)
  const showTransfer = async (id: number) => {
    try {
      setLoadingTransferId(id)
      const data = (await api.get(`/fin/transfers/${id}`)).data
      setTransferView(data)
    } finally {
      setLoadingTransferId(null)
    }
  }

  if (listQ.isLoading || accountsQ.isLoading || categoriesQ.isLoading) return <p>Carregando…</p>
  if (listQ.error) return <p>Erro ao carregar transações</p>

  const accounts = accountsQ.data || []
  const categories = categoriesQ.data || []
  const items = listQ.data || []

  return (
    <div className="grid gap-4">
      <div className="card">
        <div className="card-body">
          <h3 className="font-semibold mb-3">Filtros</h3>
          <div className="flex gap-3 flex-wrap items-center">
            <input className="input w-64" value={fromDate} onChange={e => setFromDate(e.target.value)} placeholder="de (ISO) 2025-01-01T00:00:00Z"/>
            <input className="input w-64" value={toDate} onChange={e => setToDate(e.target.value)} placeholder="até (ISO) 2025-01-31T23:59:59Z"/>
            <select className="select w-48" value={accountId} onChange={e => setAccountId(e.target.value ? Number(e.target.value) : '')}>
              <option value="">Conta (todas)</option>
              {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
            <select className="select w-48" value={categoryId} onChange={e => setCategoryId(e.target.value ? Number(e.target.value) : '')}>
              <option value="">Categoria (todas)</option>
              {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <select className="select w-40" value={typeFilter} onChange={e => setTypeFilter((e.target.value || '') as any)}>
              <option value="">Tipo (todos)</option>
              <option value="INCOME">INCOME</option>
              <option value="EXPENSE">EXPENSE</option>
            </select>
            <label className="label inline-flex items-center gap-2">
              <input type="checkbox" checked={includeVoided} onChange={e => setIncludeVoided(e.target.checked)} />
              incluir anuladas
            </label>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          <h3 className="font-semibold mb-3">Criar transação</h3>
          <div className="flex gap-3 flex-wrap items-center">
            <select className="select w-48" value={cAccountId} onChange={e => setCAccountId(e.target.value ? Number(e.target.value) : '')}>
              <option value="">Conta</option>
              {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
            <select className="select w-48" value={cCategoryId} onChange={e => setCCategoryId(e.target.value ? Number(e.target.value) : '')}>
              <option value="">Categoria (opcional)</option>
              {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <input className="input w-36" value={cAmount} onChange={e => setCAmount(e.target.value)} placeholder="0.00"/>
            <input className="input w-72" value={cWhen} onChange={e => setCWhen(e.target.value)} />
            <input className="input w-64" value={cDesc} onChange={e => setCDesc(e.target.value)} placeholder="descrição (opcional)" />
            <button className="btn btn-primary" onClick={() => createMut.mutate()} disabled={createMut.isPending || !(cAccountId && cAmount)}>Criar</button>
            {createMut.isError && <span className="text-red-500 text-sm">Erro ao criar</span>}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          <h3 className="font-semibold mb-3">Lista</h3>
          <table className="table">
            <thead>
              <tr><th>ID</th><th>Conta</th><th>Categoria</th><th>Valor</th><th>Quando</th><th>Ações</th></tr>
            </thead>
            <tbody>
              {items.map(tx => (
                <tr key={tx.id}>
                  <td className="whitespace-nowrap">
                    {tx.id}
                    {tx.from_transfer && (
                      <span className="ml-2 text-xs rounded bg-slate-100 px-2 py-0.5 text-slate-600" title="originou de transferência">transfer</span>
                    )}
                  </td>
                  <td>{tx.account_id}</td>
                  <td>{tx.category_id ?? '-'}</td>
                  <td>{tx.amount}</td>
                  <td className="whitespace-nowrap">{tx.occurred_at}</td>
                  <td>
                    {!tx.from_transfer && (
                      <button
                        className="btn btn-ghost"
                        onClick={() => voidMut.mutate(tx.id)}
                        disabled={voidMut.isPending}
                        title="Anular transação"
                      >
                        Void
                      </button>
                    )}
                    {tx.from_transfer && tx.transfer_id && (
                      <button
                        className="btn btn-ghost ml-2"
                        onClick={() => showTransfer(tx.transfer_id!)}
                        disabled={loadingTransferId === tx.transfer_id}
                        title="Ver transferência"
                      >
                        {loadingTransferId === tx.transfer_id ? 'Carregando…' : 'Ver transferência'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {transferView && (
            <div className="mt-4 p-4 border rounded bg-slate-50">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold">Transferência #{transferView.id}</h4>
                <button className="btn btn-ghost" onClick={() => setTransferView(null)}>Fechar</button>
              </div>
              <div className="grid gap-1 text-sm text-slate-700">
                <div><span className="text-slate-500">Src:</span> {transferView.src_account_id} — {transferView.src_amount} {transferView.rate_base}</div>
                <div><span className="text-slate-500">Dst:</span> {transferView.dst_account_id} — {transferView.dst_amount} {transferView.rate_quote}</div>
                <div><span className="text-slate-500">FX:</span> 1 {transferView.rate_base} = {transferView.rate_value} {transferView.rate_quote}</div>
                <div><span className="text-slate-500">Quando:</span> {transferView.occurred_at}</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
