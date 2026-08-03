'use client'

import { useState, useSyncExternalStore } from 'react'
import {
  getConsentChoice,
  setConsentChoice,
  type ConsentChoice,
} from '../lib/analytics-sdk'
import { useModalA11y } from '../lib/use-modal-a11y'

function subscribe(callback: () => void) {
  if (typeof window === 'undefined') return () => {}
  window.addEventListener('storage', callback)
  return () => window.removeEventListener('storage', callback)
}

function getSnapshot(): ConsentChoice {
  return getConsentChoice()
}

function getServerSnapshot(): ConsentChoice {
  return 'necessary'
}

export function AnalyticsConsentBanner() {
  const choice = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
  const [showConfigModal, setShowConfigModal] = useState(false)
  const configDialogRef = useModalA11y<HTMLDivElement>(showConfigModal, () =>
    setShowConfigModal(false),
  )

  if (choice !== null) {
    return null
  }

  const handleChoice = (selected: 'necessary' | 'granted') => {
    setConsentChoice(selected)
    setShowConfigModal(false)
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event('storage'))
    }
  }

  return (
    <>
      <aside
        aria-label="Aviso de Privacidade e Métricas"
        className="fixed bottom-0 left-0 right-0 z-50 p-4 border-t border-[var(--color-border,#DDE3D9)] bg-[var(--color-surface,#FFFFFF)] dark:bg-[var(--color-surface,#101610)] shadow-lg transition-all"
      >
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="text-sm text-[var(--color-text,#172015)] dark:text-[var(--color-text,#F5F7F3)]">
            <p className="font-semibold mb-1">Privacidade e Uso de Dados</p>
            <p className="text-[var(--color-text-muted,#5E695A)] dark:text-[var(--color-text-muted,#AFB9AC)]">
              Usamos armazenamento necessário para o aplicativo funcionar. Com
              sua permissão, também coletamos métricas pseudonimizadas para
              entender quais telas e rotas são úteis. Você pode alterar a
              qualquer momento.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => handleChoice('necessary')}
              className="px-4 py-2 text-sm font-medium border border-[var(--color-border,#DDE3D9)] rounded-lg hover:bg-[var(--color-surface-subtle,#EFF2EC)] dark:hover:bg-[var(--color-surface-subtle,#141C14)] transition-colors"
            >
              Usar apenas necessários
            </button>
            <button
              type="button"
              onClick={() => setShowConfigModal(true)}
              className="px-3 py-2 text-sm text-[var(--color-text-muted,#5E695A)] hover:underline"
            >
              Configurar
            </button>
            <button
              type="button"
              onClick={() => handleChoice('granted')}
              className="px-4 py-2 text-sm font-medium text-white bg-[var(--color-primary,#33601E)] rounded-lg hover:opacity-90 transition-opacity"
            >
              Permitir métricas
            </button>
          </div>
        </div>
      </aside>

      {showConfigModal && (
        <div
          ref={configDialogRef}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="consent-config-title"
          tabIndex={-1}
        >
          <div className="w-full max-w-lg p-6 bg-[var(--color-surface,#FFFFFF)] dark:bg-[var(--color-surface,#101610)] rounded-xl border border-[var(--color-border,#DDE3D9)] shadow-2xl space-y-4">
            <h3 id="consent-config-title" className="text-lg font-bold">
              Configurações de Privacidade
            </h3>

            <div className="space-y-3 text-sm">
              <div className="p-3 border rounded-lg border-[var(--color-border,#DDE3D9)] bg-[var(--color-surface-subtle,#EFF2EC)] dark:bg-[var(--color-surface-subtle,#141C14)]">
                <p className="font-semibold mb-1">
                  Funcionamento Necessário (Sempre Ativo)
                </p>
                <p className="text-xs text-[var(--color-text-muted,#5E695A)]">
                  Salva preferências no dispositivo, mantém mapas offline e
                  protege contra abusos. Nenhum dado comportamental é enviado.
                </p>
              </div>

              <div className="p-3 border rounded-lg border-[var(--color-border,#DDE3D9)]">
                <p className="font-semibold mb-1">
                  Métricas Opcionais de Navegação
                </p>
                <p className="text-xs text-[var(--color-text-muted,#5E695A)]">
                  Mede acessos a rotas, mapas e pontos de apoio de forma
                  pseudonimizada e agregada. Sem rastreamento de localização ou
                  dados pessoais.
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                data-autofocus
                type="button"
                onClick={() => handleChoice('necessary')}
                className="px-4 py-2 text-sm font-medium border rounded-lg"
              >
                Apenas Necessários
              </button>
              <button
                type="button"
                onClick={() => handleChoice('granted')}
                className="px-4 py-2 text-sm font-medium text-white bg-[var(--color-primary,#33601E)] rounded-lg"
              >
                Aceitar Todos
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
