import React from 'react'
import { requestMeta } from '../telemetry/requestMeta'

export const RequestID: React.FC = () => {
  const [rid, setRid] = React.useState<string | null>(requestMeta.getLastRequestId())
  const [copied, setCopied] = React.useState(false)
  React.useEffect(() => requestMeta.subscribe(setRid), [])

  const onCopy = async () => {
    if (!rid) return
    try {
      await navigator.clipboard.writeText(rid)
      setCopied(true)
      setTimeout(() => setCopied(false), 800)
    } catch {}
  }

  return (
    <div className="flex items-center gap-2 text-xs text-slate-600" title="X-Request-ID">
      <span className="text-slate-500">ReqID:</span>
      <code className="bg-slate-100 px-1 rounded">{rid ? rid.slice(0, 8) : '—'}</code>
      <button className="btn btn-ghost px-2 py-1" onClick={onCopy} disabled={!rid}>{copied ? 'Copied' : 'Copy'}</button>
    </div>
  )
}

