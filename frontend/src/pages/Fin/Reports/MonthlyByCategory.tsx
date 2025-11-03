import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../../shared/api/client'
import { MonthYearPicker } from '../../../shared/ui/MonthYearPicker'
import { Link } from 'react-router-dom'

interface Item { category_id: number; category_name: string; type: 'INCOME' | 'EXPENSE'; total: string }

export default function MonthlyByCategory() {
  const now = new Date()
  const [year, setYear] = React.useState(now.getUTCFullYear())
  const [month, setMonth] = React.useState(now.getUTCMonth() + 1)
  const [includeClosed, setIncludeClosed] = React.useState(false)
  const [includeInactive, setIncludeInactive] = React.useState(false)

  const query = useQuery({
    queryKey: ['report-monthly', { year, month, includeClosed, includeInactive }],
    queryFn: async () => (await api.get('/fin/reports/monthly-by-category', { params: { year, month, include_closed: includeClosed, include_inactive: includeInactive } })).data as Item[],
  })

  const rows = query.data || []

  return (
    <div className="grid gap-4">
      <div className="card">
        <div className="card-body flex items-center gap-3 flex-wrap">
          <h2 className="text-lg font-semibold">Reports · Monthly by Category</h2>
          <Link className="btn btn-ghost" to="/fin/reports/balance-by-account">Balance by Account</Link>
        </div>
      </div>
      <div className="card">
        <div className="card-body flex items-center gap-3 flex-wrap">
          <MonthYearPicker year={year} month={month} onChange={(y, m) => { setYear(y); setMonth(m) }} />
          <label className="label inline-flex items-center gap-2">
            <input type="checkbox" checked={includeClosed} onChange={e => setIncludeClosed(e.target.checked)} />
            incluir contas fechadas
          </label>
          <label className="label inline-flex items-center gap-2">
            <input type="checkbox" checked={includeInactive} onChange={e => setIncludeInactive(e.target.checked)} />
            incluir categorias inativas
          </label>
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          {query.isLoading && <p>Carregando…</p>}
          {query.error && <p className="text-red-500">Erro ao carregar relatório</p>}
          {!query.isLoading && !query.error && (
            <table className="table">
              <thead>
                <tr><th>Categoria</th><th>Tipo</th><th>Total</th></tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.category_id}>
                    <td>{r.category_name}</td>
                    <td>{r.type}</td>
                    <td>{r.total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}

