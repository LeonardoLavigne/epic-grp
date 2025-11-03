import React from 'react'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { api } from '../../../shared/api/client'
import { MonthYearPicker } from '../../../shared/ui/MonthYearPicker'
import { Link } from 'react-router-dom'
import { useSearchParams } from 'react-router-dom'
import { formatMoney } from '../../../shared/format/money'
import { exportCSV } from '../../../shared/export/csv'

interface Item { category_id: number; category_name: string; type: 'INCOME' | 'EXPENSE'; total: string }

export default function MonthlyByCategory() {
  const now = new Date()
  const [sp, setSp] = useSearchParams()
  const initialYear = Number(sp.get('year')) || now.getUTCFullYear()
  const initialMonth = Number(sp.get('month')) || (now.getUTCMonth() + 1)
  const initialClosed = sp.get('include_closed') === 'true'
  const initialInactive = sp.get('include_inactive') === 'true'
  const [year, setYear] = React.useState(initialYear)
  const [month, setMonth] = React.useState(initialMonth)
  const [includeClosed, setIncludeClosed] = React.useState(initialClosed)
  const [includeInactive, setIncludeInactive] = React.useState(initialInactive)

  const query = useQuery({
    queryKey: ['report-monthly', { year, month, includeClosed, includeInactive }],
    queryFn: async () => (await api.get('/fin/reports/monthly-by-category', { params: { year, month, include_closed: includeClosed, include_inactive: includeInactive } })).data as Item[],
    placeholderData: keepPreviousData,
  })

  const rows = (query.data || []).slice().sort((a, b) => Number(b.total) - Number(a.total))
  const totalsByType = rows.reduce<Record<string, number>>((acc, r) => {
    const v = Number(r.total)
    acc[r.type] = (acc[r.type] || 0) + (Number.isFinite(v) ? v : 0)
    return acc
  }, {})

  const onChangeFilters = (y: number, m: number, closed: boolean, inactive: boolean) => {
    setYear(y); setMonth(m); setIncludeClosed(closed); setIncludeInactive(inactive)
    const next = new URLSearchParams(sp)
    next.set('year', String(y))
    next.set('month', String(m))
    next.set('include_closed', String(closed))
    next.set('include_inactive', String(inactive))
    setSp(next, { replace: true })
  }

  const onExport = () => {
    exportCSV(`monthly_by_category_${year}-${String(month).padStart(2,'0')}.csv`, rows.map(r => ({
      category: r.category_name,
      type: r.type,
      total: r.total,
    })))
  }

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
          <MonthYearPicker year={year} month={month} onChange={(y, m) => onChangeFilters(y, m, includeClosed, includeInactive)} />
          <label className="label inline-flex items-center gap-2">
            <input type="checkbox" checked={includeClosed} onChange={e => onChangeFilters(year, month, e.target.checked, includeInactive)} />
            incluir contas fechadas
          </label>
          <label className="label inline-flex items-center gap-2">
            <input type="checkbox" checked={includeInactive} onChange={e => onChangeFilters(year, month, includeClosed, e.target.checked)} />
            incluir categorias inativas
          </label>
          <button className="btn btn-ghost" onClick={onExport}>Export CSV</button>
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
                {rows.length === 0 && (
                  <tr><td colSpan={3} className="text-slate-500">Sem dados no período</td></tr>
                )}
                {rows.map((r) => (
                  <tr key={r.category_id}>
                    <td>{r.category_name}</td>
                    <td className={r.type === 'INCOME' ? 'text-emerald-600' : 'text-red-600'}>{r.type}</td>
                    <td>{formatMoney(r.total, 'EUR')}</td>
                  </tr>
                ))}
              </tbody>
              {(totalsByType['INCOME'] || totalsByType['EXPENSE']) && (
                <tfoot>
                  {typeof totalsByType['INCOME'] === 'number' && (
                    <tr>
                      <td colSpan={2} className="text-right font-medium">Total INCOME</td>
                      <td className="font-medium">{formatMoney(totalsByType['INCOME'] || 0, 'EUR')}</td>
                    </tr>
                  )}
                  {typeof totalsByType['EXPENSE'] === 'number' && (
                    <tr>
                      <td colSpan={2} className="text-right font-medium">Total EXPENSE</td>
                      <td className="font-medium">{formatMoney(totalsByType['EXPENSE'] || 0, 'EUR')}</td>
                    </tr>
                  )}
                </tfoot>
              )}
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
