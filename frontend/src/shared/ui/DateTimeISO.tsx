import React from 'react'

type Props = {
  value: string // ISO 8601 with timezone
  onChange: (iso: string) => void
  className?: string
}

function toLocalInputValue(iso: string): string {
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return ''
    const pad = (n: number) => n.toString().padStart(2, '0')
    const yyyy = d.getFullYear()
    const MM = pad(d.getMonth() + 1)
    const dd = pad(d.getDate())
    const hh = pad(d.getHours())
    const mm = pad(d.getMinutes())
    return `${yyyy}-${MM}-${dd}T${hh}:${mm}`
  } catch {
    return ''
  }
}

function toISO(value: string): string {
  // value is local 'YYYY-MM-DDTHH:MM'
  try {
    const d = new Date(value)
    return d.toISOString()
  } catch {
    return value
  }
}

export const DateTimeISO: React.FC<Props> = ({ value, onChange, className = '' }) => {
  const local = React.useMemo(() => toLocalInputValue(value), [value])
  return (
    <input
      type="datetime-local"
      className={`input ${className}`}
      value={local}
      onChange={(e) => onChange(toISO(e.target.value))}
    />
  )
}
