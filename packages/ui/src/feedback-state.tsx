import type { ReactNode } from 'react'

interface FeedbackStateProps {
  action?: ReactNode
  message: string
  title: string
  variant: 'empty' | 'error' | 'loading'
}

export function FeedbackState({
  action,
  message,
  title,
  variant,
}: FeedbackStateProps) {
  const isError = variant === 'error'
  const isLoading = variant === 'loading'

  return (
    <section
      aria-busy={isLoading || undefined}
      aria-live={isError ? 'assertive' : 'polite'}
      className={`ui-feedback ui-feedback--${variant}`}
      role={isError ? 'alert' : 'status'}
    >
      {isLoading ? <span aria-hidden="true" className="ui-spinner" /> : null}
      <h2 className="ui-feedback__title">{title}</h2>
      <p className="ui-feedback__message">{message}</p>
      {action}
    </section>
  )
}
