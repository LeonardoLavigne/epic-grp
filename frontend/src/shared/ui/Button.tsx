import React from 'react'

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'ghost'
}

export const Button: React.FC<Props> = ({ variant = 'primary', className = '', ...props }) => {
  const base = 'btn'
  const v = variant === 'primary' ? 'btn-primary' : 'btn-ghost'
  return <button className={`${base} ${v} ${className}`} {...props} />
}

