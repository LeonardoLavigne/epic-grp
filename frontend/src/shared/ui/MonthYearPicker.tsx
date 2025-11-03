import React from 'react'

type Props = {
  year: number
  month: number
  onChange: (y: number, m: number) => void
  className?: string
}

export const MonthYearPicker: React.FC<Props> = ({ year, month, onChange, className = '' }) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <select className="select w-28" value={month} onChange={(e) => onChange(year, Number(e.target.value))}>
        {Array.from({ length: 12 }).map((_, i) => (
          <option key={i + 1} value={i + 1}>{i + 1}</option>
        ))}
      </select>
      <input className="input w-24" type="number" value={year} onChange={(e) => onChange(Number(e.target.value), month)} />
    </div>
  )
}

