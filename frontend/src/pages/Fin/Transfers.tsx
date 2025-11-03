import React, { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '../../shared/api/client'
import { MoneyInput } from '../../shared/ui/MoneyInput'
import { DateTimeISO } from '../../shared/ui/DateTimeISO'

interface Account { id: number; name: string; currency: string }
interface TransferOut {
  id: number
  src_account_id: number
  dst_account_id: number
  src_amount: string
  dst_amount: string
  rate_value: string
  rate_base: string
  rate_quote: string
  occurred_at: string
  fx_rate_2dp?: string
  vet_2dp?: string
  ref_rate_2dp?: string
  fees_per_unit_2dp?: string
  fees_pct?: string
}

export default function Transfers() {
  const accountsQ = useQuery({ queryKey: ['accounts', {}], queryFn: async () => (await api.get('/fin/accounts')).data as Account[] })

  const [srcAccount, setSrcAccount] = useState<number | ''>('')
  const [dstAccount, setDstAccount] = useState<number | ''>('')
  const [srcAmount, setSrcAmount] = useState('0.00')
  const [dstAmount, setDstAmount] = useState('')
  // VET (2 casas) mapeia para fx_rate no backend
  const [vet, setVet] = useState('')
  const [when, setWhen] = useState<string>(() => new Date().toISOString())
  const [status, setStatus] = useState<string | null>(null)

  const createMut = useMutation({
    mutationFn: async () => {
      const payload: any = {
        src_account_id: srcAccount,
        dst_account_id: dstAccount,
        src_amount: srcAmount,
        occurred_at: when,
      }
      if (dstAmount) payload.dst_amount = dstAmount
      if (vet) payload.fx_rate = vet
      return (await api.post('/fin/transfers', payload)).data as { transfer: TransferOut }
    },
    onSuccess: (res) => setStatus(`Transfer #${res.transfer.id} criada`),
    onError: (err: any) => setStatus(`Erro: ${err?.response?.data?.detail || 'falha ao criar'}`),
  })

  // GET/VOID by id
  const [fetchId, setFetchId] = useState('')
  const [fetched, setFetched] = useState<TransferOut | null>(null)
  const getMut = useMutation({
    mutationFn: async () => (await api.get(`/fin/transfers/${fetchId}`)).data as TransferOut,
    onSuccess: (tr) => { setFetched(tr); setStatus(null) },
    onError: (err: any) => setStatus(`Erro: ${err?.response?.data?.detail || 'não encontrado'}`),
  })
  const voidMut = useMutation({
    mutationFn: async () => (await api.post(`/fin/transfers/${fetchId}/void`)).data as TransferOut,
    onSuccess: (tr) => { setFetched(tr); setStatus(`Transfer ${tr.id} voided`) },
    onError: (err: any) => setStatus(`Erro: ${err?.response?.data?.detail || 'falha ao anular'}`),
  })

  const accounts = accountsQ.data || []
  const canCreate = srcAccount && dstAccount && srcAmount
  // auto-cálculo: quando usuario preencher VET e srcAmount, sugerir dstAmount; se limpar VET, não forçar
  React.useEffect(() => {
    const s = Number(srcAmount || '0')
    const v = Number(vet || '0')
    if (s > 0 && v > 0) {
      const vdst = (s * v).toFixed(2)
      setDstAmount(vdst)
    }
  }, [srcAmount, vet])

  return (
    <div className="grid gap-4">
      <div className="card">
        <div className="card-body">
          <h3 className="font-semibold mb-3">Criar transferência</h3>
          <div className="flex gap-3 flex-wrap items-center">
            <select className="select w-56" value={srcAccount} onChange={e => setSrcAccount(e.target.value ? Number(e.target.value) : '')}>
              <option value="">Conta origem</option>
              {accounts.map(a => <option key={a.id} value={a.id}>{a.name} ({a.currency})</option>)}
            </select>
            <select className="select w-56" value={dstAccount} onChange={e => setDstAccount(e.target.value ? Number(e.target.value) : '')}>
              <option value="">Conta destino</option>
              {accounts.map(a => <option key={a.id} value={a.id}>{a.name} ({a.currency})</option>)}
            </select>
            <div>
              <label className="label">Valor origem</label>
              <MoneyInput value={srcAmount} onChange={setSrcAmount} className="w-36" />
            </div>
            <div>
              <label className="label">Valor destino (opcional)</label>
              <MoneyInput value={dstAmount} onChange={setDstAmount} className="w-36" />
            </div>
            <div>
              <label className="label">VET (2 casas, opcional)</label>
              <MoneyInput value={vet} onChange={setVet} className="w-32" />
            </div>
            <div>
              <label className="label">Quando</label>
              <DateTimeISO value={when} onChange={setWhen} className="w-64" />
            </div>
            <button className="btn btn-primary" onClick={() => createMut.mutate()} disabled={!canCreate || createMut.isPending}>Criar</button>
            {status && <span className="text-slate-600 text-sm">{status}</span>}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          <h3 className="font-semibold mb-3">Consultar/Anular por ID</h3>
          <div className="flex gap-3 items-center flex-wrap">
            <input className="input w-40" placeholder="transfer id" value={fetchId} onChange={e => setFetchId(e.target.value)} />
            <button className="btn btn-ghost" onClick={() => getMut.mutate()} disabled={!fetchId}>Buscar</button>
            <button className="btn btn-ghost" onClick={() => voidMut.mutate()} disabled={!fetchId}>Void</button>
          </div>
          {fetched && (
            <div className="mt-3 text-sm text-slate-700">
              <div><b>ID:</b> {fetched.id}</div>
              <div><b>Contas:</b> {fetched.src_account_id} → {fetched.dst_account_id}</div>
              <div><b>Valores:</b> {fetched.src_amount} → {fetched.dst_amount}</div>
              <div><b>{(fetched.ref_rate_2dp ? 'FX (ref)' : 'FX')}:</b> {fetched.ref_rate_2dp ?? fetched.fx_rate_2dp ?? fetched.rate_value} ({fetched.rate_base}/{fetched.rate_quote})</div>
              {typeof fetched.vet_2dp !== 'undefined' && (
                <div><b>VET:</b> {fetched.vet_2dp}</div>
              )}
              {typeof fetched.fees_per_unit_2dp !== 'undefined' && (
                <div><b>Taxas implícitas:</b> {fetched.fees_per_unit_2dp}{fetched.fees_pct ? ` (${fetched.fees_pct}%)` : ''}</div>
              )}
              <div><b>Quando:</b> {fetched.occurred_at}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
