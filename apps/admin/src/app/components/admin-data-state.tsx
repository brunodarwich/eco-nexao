import { FeedbackState } from '@econexao/ui/feedback-state'
import {
  classifyAdminResponse,
  type AdminRequestError,
} from '../../lib/admin-api'

export { classifyAdminResponse }
export type { AdminRequestError }

export function AdminDataState({
  error,
  onRetry,
}: {
  error: AdminRequestError
  onRetry?: () => void
}) {
  const messages: Record<
    AdminRequestError,
    { title: string; message: string }
  > = {
    unauthorized: {
      title: 'Sessão necessária',
      message:
        'Sua sessão administrativa expirou ou não foi encontrada. Entre novamente para continuar.',
    },
    forbidden: {
      title: 'Acesso não autorizado',
      message:
        'Sua conta não tem permissão para consultar os dados desta área ou região.',
    },
    'rate-limited': {
      title: 'Muitas tentativas',
      message:
        'A API limitou temporariamente as consultas. Aguarde alguns instantes e tente novamente.',
    },
    'server-error': {
      title: 'Falha no serviço',
      message:
        'O serviço administrativo encontrou um erro. Tente novamente em instantes.',
    },
    unavailable: {
      title: 'Serviço indisponível',
      message:
        'Não foi possível alcançar o serviço administrativo. Verifique a conexão e tente novamente.',
    },
  }
  const copy = messages[error]

  return (
    <FeedbackState
      action={
        onRetry ? (
          <button onClick={onRetry} type="button">
            Tentar novamente
          </button>
        ) : undefined
      }
      message={copy.message}
      title={copy.title}
      variant="error"
    />
  )
}
