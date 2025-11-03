import React from 'react'
import { toastBus, type Toast } from './toastBus'

export const Toaster: React.FC = () => {
  const [items, setItems] = React.useState<Toast[]>([])

  React.useEffect(() => {
    const unsub = toastBus.subscribe((t) => {
      setItems((prev) => [...prev, t])
      setTimeout(() => {
        setItems((prev) => prev.filter(i => i.id !== t.id))
      }, t.ttlMs ?? 3000)
    })
    return unsub
  }, [])

  return (
    <div className="fixed top-3 right-3 z-50 flex flex-col gap-2">
      {items.map(t => (
        <div key={t.id} className={`shadow-soft rounded-xl border px-4 py-3 text-sm bg-white ${
          t.type === 'success' ? 'border-emerald-200' : t.type === 'error' ? 'border-red-200' : 'border-slate-200'
        }`}>
          {t.title && <div className="font-medium mb-0.5">{t.title}</div>}
          <div className={t.type === 'error' ? 'text-red-600' : 'text-slate-700'}>{t.message}</div>
        </div>
      ))}
    </div>
  )
}

