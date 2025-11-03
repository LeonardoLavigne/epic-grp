import axios from 'axios'
import { requestMeta } from '../telemetry/requestMeta'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:10000',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers = config.headers ?? {}
    ;(config.headers as any).Authorization = `Bearer ${token}`
  }
  return config
})

function getHeader(headers: any, name: string): string | null {
  if (!headers) return null
  const lower = name.toLowerCase()
  if (typeof headers.get === 'function') {
    try { return headers.get(lower) || headers.get(name) || null } catch { /* ignore */ }
  }
  return headers[lower] || headers[name] || null
}

api.interceptors.response.use(
  (resp) => {
    const rid = getHeader(resp.headers as any, 'x-request-id')
    if (rid) requestMeta.setLastRequestId(rid)
    return resp
  },
  (error) => {
    const rid = getHeader(error?.response?.headers as any, 'x-request-id')
    if (rid) requestMeta.setLastRequestId(rid)
    return Promise.reject(error)
  }
)
