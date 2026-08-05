'use client'

import { Button } from '@econexao/ui/button'
import { FeedbackState } from '@econexao/ui/feedback-state'
import { useModalA11y } from '@econexao/ui/use-modal-a11y'
import { FormEvent, useState } from 'react'
import { getAdminErrorMessage } from '../../lib/admin-api'
import { savePoiDraft } from '../../lib/poi-draft'
import { CatalogItemApi } from './app-analytics-view'

interface PoiEditorModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (savedPoi: CatalogItemApi) => void
  initialData: CatalogItemApi | null
  routeSlug: string
  regionId: string
}

export function PoiEditorModal({
  isOpen,
  onClose,
  onSave,
  initialData,
  routeSlug,
  regionId,
}: PoiEditorModalProps) {
  const [displayName, setDisplayName] = useState(
    initialData?.actor?.display_name || '',
  )
  const [categoryName, setCategoryName] = useState(
    initialData?.actor?.category?.name || 'Gastronomia',
  )
  const [address, setAddress] = useState(
    initialData?.public_locations?.[0]?.formatted_address ||
      initialData?.public_locations?.[0]?.locality ||
      '',
  )
  const [phone, setPhone] = useState(
    initialData?.public_contact_channels?.[0]?.public_value || '',
  )
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')

  const [prevInitialData, setPrevInitialData] = useState(initialData)
  const [prevIsOpen, setPrevIsOpen] = useState(isOpen)

  if (initialData !== prevInitialData || isOpen !== prevIsOpen) {
    setPrevInitialData(initialData)
    setPrevIsOpen(isOpen)
    setDisplayName(initialData?.actor?.display_name || '')
    setCategoryName(initialData?.actor?.category?.name || 'Gastronomia')
    setAddress(
      initialData?.public_locations?.[0]?.formatted_address ||
        initialData?.public_locations?.[0]?.locality ||
        '',
    )
    setPhone(initialData?.public_contact_channels?.[0]?.public_value || '')
    setSubmitError('')
  }

  const dialogRef = useModalA11y<HTMLDivElement>(isOpen, onClose)

  if (!isOpen || !initialData?.actor) return null
  const actor = initialData.actor

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitError('')
    setIsSubmitting(true)

    try {
      await savePoiDraft({
        actorId: actor.id,
        address,
        category: categoryName,
        displayName,
        phone,
        regionId,
      })
      const updatedItem: CatalogItemApi = {
        ...initialData,
        actor: {
          ...actor,
          display_name: displayName,
          category: {
            name: categoryName,
            slug: categoryName.toLowerCase().replace(/\s+/g, '-'),
          },
        },
        public_locations: [
          {
            formatted_address: address,
            locality: address,
          },
        ],
        public_contact_channels: phone
          ? [
              {
                channel_type: 'whatsapp',
                public_value: phone,
              },
            ]
          : [],
      }
      onSave(updatedItem)
      onClose()
    } catch (error) {
      setSubmitError(
        getAdminErrorMessage(
          error,
          'O rascunho não pôde ser salvo. Revise os dados e tente novamente.',
        ),
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" role="presentation">
      <div
        ref={dialogRef}
        aria-labelledby="poi-modal-title"
        aria-modal="true"
        className="poi-modal-content"
        role="dialog"
        tabIndex={-1}
      >
        <div className="modal-header">
          <div>
            <span className="modal-eyebrow">Edição Direta no Painel</span>
            <h2 id="poi-modal-title">Editar Ponto de Apoio</h2>
          </div>
          <button
            data-autofocus
            aria-label="Fechar modal"
            className="modal-close-button"
            onClick={onClose}
            type="button"
          >
            ✕
          </button>
        </div>

        <p className="modal-subtitle">
          Rota de destino: <strong>{routeSlug || 'Rota selecionada'}</strong>. A
          pré-visualização só é atualizada depois que a API confirma o rascunho.
        </p>

        <form className="form-stack" onSubmit={handleSubmit}>
          {submitError ? (
            <FeedbackState
              message={submitError}
              title="Não foi possível salvar o rascunho"
              variant="error"
            />
          ) : null}
          <label>
            Nome Comercial / Exibição público *
            <input
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Ex: Barraca do Seu Zé"
              required
              value={displayName}
            />
          </label>

          <div className="form-row">
            <label>
              Categoria *
              <select
                onChange={(e) => setCategoryName(e.target.value)}
                value={categoryName}
              >
                <option value="Gastronomia">Gastronomia</option>
                <option value="Hospedagem">Hospedagem</option>
                <option value="Apoio Técnico">Apoio Técnico</option>
                <option value="Artesanato & Cultura">
                  Artesanato & Cultura
                </option>
                <option value="Comunidade & Guias">Comunidade & Guias</option>
                <option value="Emergência & Saúde">Emergência & Saúde</option>
              </select>
            </label>

            <div>
              <span className="field-label">Destino editorial</span>
              <p className="panel-hint">
                Salvar cria um rascunho. Revisão e publicação usam ações
                próprias do workflow.
              </p>
            </div>
          </div>

          <label>
            Endereço / Localidade
            <input
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Ex: Praia de Pindobal, Santarém - PA"
              value={address}
            />
          </label>

          <label>
            Telefone / WhatsApp Autorizado (E.164)
            <input
              onChange={(e) => setPhone(e.target.value)}
              placeholder="Ex: +5593991234567"
              value={phone}
            />
          </label>

          <div className="modal-actions">
            <Button onClick={onClose} type="button" variant="secondary">
              Cancelar
            </Button>
            <Button isLoading={isSubmitting} type="submit">
              💾 Salvar alterações como rascunho
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
