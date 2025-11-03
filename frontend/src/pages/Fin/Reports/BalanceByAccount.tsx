import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../../shared/api/client'
import { MonthYearPicker } from '../../../shared/ui/MonthYearPicker'
import { Link } from 'react-router-dom'

interface Account { id: number; name: string; currency: string; status?: string }
interface BalanceItem { account_id: number; currency: string; balance: string }

export default function BalanceByAccount() {
  const now = new Date()
  const [year, setYear] = React.useState(now.getUTCFullYear())
  const [month, setMonth] = React.useState(now.getUTCMonth() + 1)
  const [includeClosed, setIncludeClosed] = React.useState(false)

  const accountsQ = useQuery({
    queryKey: ['accounts', {}],
    queryFn: async () => (await api.get('/fin/accounts')).data as Account[],
  })

  const balancesQ = useQuery({
    queryKey: ['report-balance', { year, month, includeClosed }],
    queryFn: async () => (await api.get('/fin/reports/balance-by-account', { params: { year, month, include_closed: includeClosed } })).data as BalanceItem[],
  })

  const accounts = accountsQ.data || []
  const nameById = new Map(accounts.map(a => [a.id, a.name]))
  const rows = balancesQ.data || []

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
            onChange={(y, m) => { setYear(y); setMonth(m) }}
          />
          <label className="label inline-flex items-center gap-2">
            <input type="checkbox" checked={includeClosed} onChange={e => setIncludeClosed(e.target.checked)} />
            incluir fechadas
          </label>
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
                {rows.map(r => (
                  <tr key={r.account_id}>
                    <td>{nameById.get(r.account_id) ?? r.account_id}</td>
                    <td>{r.currency}</td>
                    <td>{r.balance}</td>
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

