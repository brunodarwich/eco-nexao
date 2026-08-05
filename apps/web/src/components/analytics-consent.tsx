'use client'

import { useState, useSyncExternalStore } from 'react'
import {
  CONSENT_CHANGE_EVENT,
  getConsentChoice,
  setConsentChoice,
  type ConsentChoice,
} from '../lib/analytics-sdk'
import { useModalA11y } from '@econexao/ui/use-modal-a11y'

function subscribe(callback: () => void) {
  if (typeof window === 'undefined') return () => {}
  window.addEventListener('storage', callback)
  window.addEventListener(CONSENT_CHANGE_EVENT, callback)
  return () => {
    window.removeEventListener('storage', callback)
    window.removeEventListener(CONSENT_CHANGE_EVENT, callback)
  }
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

  const handleChoice = (selected: 'necessary' | 'granted') => {
    setConsentChoice(selected)
    setShowConfigModal(false)
  }

  return (
    <>
      {choice === null ? (
        <aside
          aria-label="Aviso de Privacidade e Métricas"
          className="analytics-consent-banner"
        >
          <div className="analytics-consent-banner__inner">
            <div className="analytics-consent-copy">
              <strong>Privacidade e uso de dados</strong>
              <p>
                Usamos armazenamento necessário para o aplicativo funcionar. Com
                sua permissão, também coletamos métricas pseudonimizadas para
                entender quais telas e rotas são úteis. Você pode alterar a
                escolha a qualquer momento.
              </p>
            </div>

            <div className="analytics-consent-actions">
              <button
                className="ui-button ui-button--secondary"
                onClick={() => handleChoice('necessary')}
                type="button"
              >
                Usar apenas necessários
              </button>
              <button
                className="ui-button ui-button--secondary"
                onClick={() => setShowConfigModal(true)}
                type="button"
              >
                Configurar
              </button>
              <button
                className="ui-button ui-button--primary"
                onClick={() => handleChoice('granted')}
                type="button"
              >
                Permitir métricas
              </button>
            </div>
          </div>
        </aside>
      ) : (
        <button
          className="analytics-privacy-control ui-button ui-button--secondary"
          onClick={() => setShowConfigModal(true)}
          type="button"
        >
          Privacidade e métricas
        </button>
      )}

      {showConfigModal && (
        <div
          ref={configDialogRef}
          className="analytics-consent-dialog-backdrop"
          role="dialog"
          aria-modal="true"
          aria-labelledby="consent-config-title"
          tabIndex={-1}
        >
          <div className="analytics-consent-dialog">
            <h2 id="consent-config-title">Configurações de Privacidade</h2>

            <div className="analytics-consent-options">
              <section className="analytics-consent-option">
                <strong>Funcionamento necessário — sempre ativo</strong>
                <p>
                  Salva preferências no dispositivo, mantém mapas offline e
                  protege contra abusos. Nenhum dado comportamental é enviado.
                </p>
              </section>

              <section className="analytics-consent-option">
                <strong>Métricas opcionais de navegação</strong>
                <p>
                  Mede acessos a rotas, mapas e pontos de apoio de forma
                  pseudonimizada e agregada. Sem rastreamento de localização ou
                  dados pessoais.
                </p>
              </section>
            </div>

            <div className="analytics-consent-actions">
              <button
                className="ui-button ui-button--secondary"
                data-autofocus
                onClick={() => handleChoice('necessary')}
                type="button"
              >
                Apenas Necessários
              </button>
              <button
                className="ui-button ui-button--primary"
                onClick={() => handleChoice('granted')}
                type="button"
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
