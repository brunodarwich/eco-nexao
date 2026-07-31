import type { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  isLoading?: boolean
  variant?: 'primary' | 'secondary'
}

export function Button({
  children,
  className = '',
  disabled,
  isLoading = false,
  variant = 'primary',
  ...props
}: ButtonProps) {
  const variantClass = variant === 'secondary' ? 'ui-button--secondary' : ''

  return (
    <button
      aria-busy={isLoading || undefined}
      className={`ui-button ${variantClass} ${className}`.trim()}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? <span aria-hidden="true" className="ui-spinner" /> : null}
      {isLoading ? 'Carregando…' : children}
    </button>
  )
}
