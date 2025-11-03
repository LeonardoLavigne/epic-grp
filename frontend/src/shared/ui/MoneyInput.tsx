import React from 'react'

type Props = {
  value: string
  onChange: (v: string) => void
  className?: string
  placeholder?: string
}

// Minimal money input: keeps digits and a single decimal separator (dot),
// converts comma to dot, and trims to 2 decimal places visually.
export const MoneyInput: React.FC<Props> = ({ value, onChange, className = '', placeholder = '0.00' }) => {
  const handle = (e: React.ChangeEvent<HTMLInputElement>) => {
    let v = e.target.value.replace(/,/g, '.')
    // keep only digits and dot
    v = v.replace(/[^0-9.]/g, '')
    // keep first dot only
    const first = v.indexOf('.')
    if (first !== -1) {
      v = v.slice(0, first + 1) + v.slice(first + 1).replace(/\./g, '')
    }
    // optional: limit to 2 decimals for display (BE handles final validation)
    if (first !== -1 && v.length > first + 3) {
      v = v.slice(0, first + 3)
    }
    onChange(v)
  }
  return <input className={`input ${className}`} value={value} onChange={handle} placeholder={placeholder} inputMode="decimal" />
}
