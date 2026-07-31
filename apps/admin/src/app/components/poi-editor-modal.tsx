'use client'

import { Button } from '@econexao/ui/button'
import { FormEvent, useEffect, useState } from 'react'
import { CatalogItemApi } from './app-analytics-view'

interface PoiEditorModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (savedPoi: CatalogItemApi) => void
  initialData: CatalogItemApi | null
  routeSlug: string
  regionSlug: string
}

export function PoiEditorModal({
  isOpen,
  onClose,
  onSave,
  initialData,
  routeSlug,
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
  const [editorialStatus, setEditorialStatus] = useState('Rascunho')
  const [isSubmitting, setIsSubmitting] = useState(false)

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
    setEditorialStatus(initialData?.editorial_status || 'Rascunho')
  }

  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', handleKeyDown)
      return () => {
        window.removeEventListener('keydown', handleKeyDown)
      }
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const isEditing = Boolean(initialData)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSubmitting(true)

    const updatedItem: CatalogItemApi = {
      id: initialData?.id || `poi-custom-${Date.now()}`,
      editorial_status: editorialStatus,
      actor: {
        id: initialData?.actor?.id || `actor-${Date.now()}`,
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

    setTimeout(() => {
      onSave(updatedItem)
      setIsSubmitting(false)
      onClose()
    }, 200)
  }

  return (
    <div className="modal-overlay" role="presentation">
      <div
        aria-labelledby="poi-modal-title"
        aria-modal="true"
        className="poi-modal-content"
        role="dialog"
      >
        <div className="modal-header">
          <div>
            <span className="modal-eyebrow">Edição Direta no Painel</span>
            <h2 id="poi-modal-title">
              {isEditing
                ? 'Editar Ponto de Apoio'
                : 'Novo Ponto de Apoio Manual'}
            </h2>
          </div>
          <button
            aria-label="Fechar modal"
            className="modal-close-button"
            onClick={onClose}
            type="button"
          >
            ✕
          </button>
        </div>

        <p className="modal-subtitle">
          Rota de destino: <strong>{routeSlug || 'Rota selecionada'}</strong>.
          As edições salvam o rascunho com pré-visualização imediata.
        </p>

        <form className="form-stack" onSubmit={handleSubmit}>
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

            <label>
              Status Editorial *
              <select
                onChange={(e) => setEditorialStatus(e.target.value)}
                value={editorialStatus}
              >
                <option value="Rascunho">Rascunho (Não publicado)</option>
                <option value="Em Revisão">Em Revisão Editorial</option>
                <option value="Publicado">Publicado no App</option>
              </select>
            </label>
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
              💾 {isEditing ? 'Salvar Alterações' : 'Cadastrar Ponto'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
