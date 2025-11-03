import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

export const ReadyIndicator: React.FC = () => {
  const { data, isError, isLoading } = useQuery({
    queryKey: ['ready'],
    queryFn: async () => (await api.get('/ready', { headers: { 'X-Skip-ReqID-Capture': '1' } })).data as { status: string },
    refetchInterval: 30000,
  })

  const ok = !isLoading && !isError && data?.status === 'ok'
  const color = isLoading ? 'bg-amber-400' : ok ? 'bg-brand-600' : 'bg-red-500'
  const label = isLoading ? 'Checking' : ok ? 'Ready' : 'Degraded'

  return (
    <div className="flex items-center gap-2 text-xs text-slate-600" title="/ready">
      <span className={`inline-block w-2.5 h-2.5 rounded-full ${color}`}></span>
      <span>{label}</span>
    </div>
  )
}
