type Listener = (id: string | null) => void

let lastRequestId: string | null = null
const listeners = new Set<Listener>()

export const requestMeta = {
  getLastRequestId: () => lastRequestId,
  setLastRequestId: (id: string | null) => {
    lastRequestId = id
    listeners.forEach(l => l(id))
  },
  subscribe: (listener: Listener) => {
    listeners.add(listener)
    return () => listeners.delete(listener)
  },
}

