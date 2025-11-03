export type Toast = {
  id: string
  type: 'success' | 'error' | 'info'
  title?: string
  message: string
  ttlMs?: number
}

type Listener = (t: Toast) => void
const listeners = new Set<Listener>()

export const toastBus = {
  subscribe: (fn: Listener) => { listeners.add(fn); return () => listeners.delete(fn) },
  publish: (t: Toast) => { listeners.forEach(fn => fn(t)) },
}

export function showToast(message: string, type: Toast['type'] = 'info', title?: string, ttlMs = 3000) {
  toastBus.publish({ id: `${Date.now()}-${Math.random().toString(36).slice(2,8)}`, type, title, message, ttlMs })
}

