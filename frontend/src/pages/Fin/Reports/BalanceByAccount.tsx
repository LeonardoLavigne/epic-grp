import React from 'react'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { api } from '../../../shared/api/client'
import { MonthYearPicker } from '../../../shared/ui/MonthYearPicker'
import { Link } from 'react-router-dom'
import { useSearchParams } from 'react-router-dom'
import { formatMoney } from '../../../shared/format/money'
import { exportCSV } from '../../../shared/export/csv'

interface Account { id: number; name: string; currency: string; status?: string }
interface BalanceItem { account_id: number; currency: string; balance: string }

export default function BalanceByAccount() {
  const now = new Date()
  const [sp, setSp] = useSearchParams()
  const initialYear = Number(sp.get('year')) || now.getUTCFullYear()
  const initialMonth = Number(sp.get('month')) || (now.getUTCMonth() + 1)
  const initialClosed = sp.get('include_closed') === 'true'
  const [year, setYear] = React.useState(initialYear)
  const [month, setMonth] = React.useState(initialMonth)
  const [includeClosed, setIncludeClosed] = React.useState(initialClosed)

  const accountsQ = useQuery({
    queryKey: ['accounts', {}],
    queryFn: async () => (await api.get('/fin/accounts')).data as Account[],
  })

  const balancesQ = useQuery({
    queryKey: ['report-balance', { year, month, includeClosed }],
    queryFn: async () => (await api.get('/fin/reports/balance-by-account', { params: { year, month, include_closed: includeClosed } })).data as BalanceItem[],
    placeholderData: keepPreviousData,
  })

  const accounts = accountsQ.data || []
  const nameById = new Map(accounts.map(a => [a.id, a.name]))
  const rows = (balancesQ.data || []).slice().sort((a, b) => (nameById.get(a.account_id) || '').localeCompare(nameById.get(b.account_id) || ''))

  const byCurrency = rows.reduce<Record<string, number>>((acc, r) => {
    const v = Number(r.balance)
    acc[r.currency] = (acc[r.currency] || 0) + (Number.isFinite(v) ? v : 0)
    return acc
  }, {})

  const onChangeFilters = (y: number, m: number, closed: boolean) => {
    setYear(y); setMonth(m); setIncludeClosed(closed)
    const next = new URLSearchParams(sp)
    next.set('year', String(y))
    next.set('month', String(m))
    next.set('include_closed', String(closed))
    setSp(next, { replace: true })
  }

  const onExport = () => {
    exportCSV(`balance_by_account_${year}-${String(month).padStart(2,'0')}.csv`, rows.map(r => ({
      account: nameById.get(r.account_id) ?? r.account_id,
      currency: r.currency,
      balance: r.balance,
    })))
  }

  return (
    <div className="grid gap-4">
      <div className="card">
        <div className="card-body flex items-center gap-3 flex-wrap">
          <h2 className="text-lg font-semibold">Reports · Balance by Account</h2>
          <Link className="btn btn-ghost" to="/fin/reports/monthly-by-category">Monthly by Category</Link>
        </div>
      </div>
      <div className="card">
        <div className="card-body flex items-center gap-3 flex-wrap">
          <MonthYearPicker
            year={year}
            month={month}
            onChange={(y, m) => onChangeFilters(y, m, includeClosed)}
          />
          <label className="label inline-flex items-center gap-2">
            <input type="checkbox" checked={includeClosed} onChange={e => onChangeFilters(year, month, e.target.checked)} />
            incluir fechadas
          </label>
          <button className="btn btn-ghost" onClick={onExport}>Export CSV</button>
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          {(accountsQ.isLoading || balancesQ.isLoading) && <p>Carregando…</p>}
          {(accountsQ.error || balancesQ.error) && <p className="text-red-500">Erro ao carregar relatório</p>}
          {!balancesQ.isLoading && !balancesQ.error && (
            <table className="table">
              <thead>
                <tr><th>Conta</th><th>Moeda</th><th>Saldo</th></tr>
              </thead>
              <tbody>
                {rows.length === 0 && (
                  <tr><td colSpan={3} className="text-slate-500">Sem dados no período</td></tr>
                )}
                {rows.map(r => (
                  <tr key={r.account_id}>
                    <td>{nameById.get(r.account_id) ?? r.account_id}</td>
                    <td>{r.currency}</td>
                    <td>{formatMoney(r.balance, r.currency)}</td>
                  </tr>
                ))}
              </tbody>
              {Object.keys(byCurrency).length > 0 && (
                <tfoot>
                  {Object.entries(byCurrency).map(([cur, total]) => (
                    <tr key={cur}>
                      <td colSpan={2} className="text-right font-medium">Total {cur}</td>
                      <td className="font-medium">{formatMoney(total, cur)}</td>
                    </tr>
                  ))}
                </tfoot>
              )}
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
