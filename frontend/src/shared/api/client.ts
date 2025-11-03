import axios from 'axios'
import { requestMeta } from '../telemetry/requestMeta'
import { showToast } from '../ui/toastBus'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:10000',
})

api.interceptors.request.use((config) => {
  // mark start time for duration
  ;(config as any).meta = { start: Date.now() }
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

function hasSkipCapture(config: any): boolean {
  const h = config?.headers || {}
  return h['X-Skip-ReqID-Capture'] === '1' || h['x-skip-reqid-capture'] === '1'
}

api.interceptors.response.use(
  (resp) => {
    const meta = (resp.config as any)?.meta
    if (!hasSkipCapture(resp.config)) {
      const rid = getHeader(resp.headers as any, 'x-request-id')
      if (rid) requestMeta.setLastRequestId(rid)
    }
    if (import.meta.env.DEV) {
      const dur = meta?.start ? `${Date.now() - meta.start}ms` : '—'
      // minimal dev log
      // eslint-disable-next-line no-console
      console.debug('[API]', resp.config.method?.toUpperCase(), resp.config.url, resp.status, dur, '')
    }
    return resp
  },
  (error) => {
    const meta = (error?.config as any)?.meta
    if (!hasSkipCapture(error?.config)) {
      const rid = getHeader(error?.response?.headers as any, 'x-request-id')
      if (rid) requestMeta.setLastRequestId(rid)
    }
    // show error toast
    const detail = error?.response?.data?.detail || error?.message || 'Request error'
    const rid = getHeader(error?.response?.headers as any, 'x-request-id')
    showToast(`${detail}${rid ? ` (rid=${rid})` : ''}`, 'error')
    if (import.meta.env.DEV) {
      const dur = meta?.start ? `${Date.now() - meta.start}ms` : '—'
      // eslint-disable-next-line no-console
      console.debug('[API:ERROR]', error?.config?.method?.toUpperCase(), error?.config?.url, error?.response?.status, dur, rid ? `rid=${rid}` : '', detail)
    }
    return Promise.reject(error)
  }
)
