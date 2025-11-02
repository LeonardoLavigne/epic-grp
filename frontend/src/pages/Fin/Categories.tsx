import React, { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api/client'

type CategoryType = 'INCOME' | 'EXPENSE'
interface Category { id: number; name: string; type: CategoryType }

export default function Categories() {
  const qc = useQueryClient()
  const [typeFilter, setTypeFilter] = useState<CategoryType | ''>('')
  const [includeInactive, setIncludeInactive] = useState(false)

  const [newName, setNewName] = useState('')
  const [newType, setNewType] = useState<CategoryType>('EXPENSE')

  const [mergeSrc, setMergeSrc] = useState<number | ''>('')
  const [mergeDst, setMergeDst] = useState<number | ''>('')

  const params = useMemo(() => {
    const p: Record<string, any> = {}
    if (typeFilter) p.type = typeFilter
    if (includeInactive) p.include_inactive = true
    return p
  }, [typeFilter, includeInactive])

  const { data, isLoading, error } = useQuery({
    queryKey: ['categories', params],
    queryFn: async () => (await api.get('/fin/categories', { params })).data as Category[],
  })

  const createMut = useMutation({
    mutationFn: async () => (await api.post('/fin/categories', { name: newName, type: newType })).data as Category,
    onSuccess: () => { setNewName(''); qc.invalidateQueries({ queryKey: ['categories'] }) },
  })

  const deactivateMut = useMutation({
    mutationFn: async (id: number) => (await api.post(`/fin/categories/${id}/deactivate`)).data as Category,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['categories'] }),
  })

  const mergeMut = useMutation({
    mutationFn: async ({ src, dst }: { src: number; dst: number }) => (await api.post('/fin/categories/merge', { src_category_id: src, dst_category_id: dst })).data,
    onSuccess: () => { setMergeSrc(''); setMergeDst(''); qc.invalidateQueries({ queryKey: ['categories'] }) },
  })

  if (isLoading) return <p>Carregando…</p>
  if (error) return <p>Erro ao carregar categorias</p>

  const categories = (data || [])

  return (
    <div className="grid gap-4">
      <div className="card">
        <div className="card-body flex items-center gap-3 flex-wrap">
          <select className="select w-40" value={typeFilter} onChange={e => setTypeFilter((e.target.value || '') as CategoryType | '')}>
            <option value="">Todas</option>
            <option value="INCOME">INCOME</option>
            <option value="EXPENSE">EXPENSE</option>
          </select>
          <label className="label inline-flex items-center gap-2">
            <input type="checkbox" checked={includeInactive} onChange={e => setIncludeInactive(e.target.checked)} />
            incluir inativas
          </label>
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          <h3 className="font-semibold mb-3">Criar categoria</h3>
          <div className="flex gap-3 flex-wrap items-center">
            <input className="input max-w-xs" placeholder="Nome" value={newName} onChange={e => setNewName(e.target.value)} />
            <select className="select w-40" value={newType} onChange={e => setNewType(e.target.value as CategoryType)}>
              <option value="EXPENSE">EXPENSE</option>
              <option value="INCOME">INCOME</option>
            </select>
            <button className="btn btn-primary" onClick={() => createMut.mutate()} disabled={!newName.trim() || createMut.isPending}>Criar</button>
            {createMut.isError && <span className="text-red-500 text-sm">Erro ao criar</span>}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          <h3 className="font-semibold mb-3">Merge de categorias</h3>
          <div className="flex gap-3 flex-wrap items-center">
            <span className="label">De</span>
            <select className="select w-56" value={mergeSrc} onChange={e => setMergeSrc(e.target.value ? Number(e.target.value) : '')}>
              <option value="">Selecione</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>{c.name} ({c.type})</option>
              ))}
            </select>
            <span className="label">para</span>
            <select className="select w-56" value={mergeDst} onChange={e => setMergeDst(e.target.value ? Number(e.target.value) : '')}>
              <option value="">Selecione</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>{c.name} ({c.type})</option>
              ))}
            </select>
            <button className="btn btn-ghost" onClick={() => (typeof mergeSrc === 'number' && typeof mergeDst === 'number') && mergeMut.mutate({ src: mergeSrc, dst: mergeDst })} disabled={mergeMut.isPending || !(mergeSrc && mergeDst) || mergeSrc === mergeDst}>Merge</button>
            {mergeMut.isError && <span className="text-red-500 text-sm">Erro no merge</span>}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          <h3 className="font-semibold mb-3">Lista</h3>
          <table className="table">
            <thead>
              <tr><th>ID</th><th>Nome</th><th>Tipo</th><th>Ações</th></tr>
            </thead>
            <tbody>
              {categories.map((cat) => (
                <tr key={cat.id}>
                  <td>{cat.id}</td>
                  <td>{cat.name}</td>
                  <td>{cat.type}</td>
                  <td>
                    <button className="btn btn-ghost" onClick={() => deactivateMut.mutate(cat.id)} disabled={deactivateMut.isPending}>Desativar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
