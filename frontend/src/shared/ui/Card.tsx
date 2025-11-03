import React from 'react'

export const Card: React.FC<{ className?: string; children: React.ReactNode } & React.HTMLAttributes<HTMLDivElement>> = ({ className = '', children, ...rest }) => (
  <div className={`card ${className}`} {...rest}><div className="card-body">{children}</div></div>
)

