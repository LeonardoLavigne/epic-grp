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
    <div style={{ display: 'grid', gap: 16 }}>
      <h2>Categories</h2>

      <section style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <select value={typeFilter} onChange={e => setTypeFilter((e.target.value || '') as CategoryType | '')}>
          <option value="">Todas</option>
          <option value="INCOME">INCOME</option>
          <option value="EXPENSE">EXPENSE</option>
        </select>
        <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <input type="checkbox" checked={includeInactive} onChange={e => setIncludeInactive(e.target.checked)} />
          incluir inativas
        </label>
      </section>

      <section>
        <h3>Criar categoria</h3>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <input placeholder="Nome" value={newName} onChange={e => setNewName(e.target.value)} />
          <select value={newType} onChange={e => setNewType(e.target.value as CategoryType)}>
            <option value="EXPENSE">EXPENSE</option>
            <option value="INCOME">INCOME</option>
          </select>
          <button onClick={() => createMut.mutate()} disabled={!newName.trim() || createMut.isPending}>Criar</button>
          {createMut.isError && <span style={{ color: 'red' }}>Erro ao criar</span>}
        </div>
      </section>

      <section>
        <h3>Merge de categorias</h3>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <span>De</span>
          <select value={mergeSrc} onChange={e => setMergeSrc(e.target.value ? Number(e.target.value) : '')}>
            <option value="">Selecione</option>
            {categories.map(c => (
              <option key={c.id} value={c.id}>{c.name} ({c.type})</option>
            ))}
          </select>
          <span>para</span>
          <select value={mergeDst} onChange={e => setMergeDst(e.target.value ? Number(e.target.value) : '')}>
            <option value="">Selecione</option>
            {categories.map(c => (
              <option key={c.id} value={c.id}>{c.name} ({c.type})</option>
            ))}
          </select>
          <button onClick={() => (typeof mergeSrc === 'number' && typeof mergeDst === 'number') && mergeMut.mutate({ src: mergeSrc, dst: mergeDst })} disabled={mergeMut.isPending || !(mergeSrc && mergeDst) || mergeSrc === mergeDst}>
            Merge
          </button>
          {mergeMut.isError && <span style={{ color: 'red' }}>Erro no merge</span>}
        </div>
      </section>

      <section>
        <h3>Lista</h3>
        <table>
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
                  <button onClick={() => deactivateMut.mutate(cat.id)} disabled={deactivateMut.isPending}>Desativar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
