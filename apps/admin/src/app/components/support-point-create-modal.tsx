'use client'

import { Button } from '@econexao/ui/button'
import { FeedbackState } from '@econexao/ui/feedback-state'
import { useModalA11y } from '@econexao/ui/use-modal-a11y'
import { FormEvent, useState } from 'react'
import { adminMutation, getAdminErrorMessage } from '../../lib/admin-api'
import type { RouteApiSummary } from '../../lib/dashboard-routes'

export interface CreatedSupportPointResult {
  id: string
  actor_kind: string
  editorial_status: string
  partnership_type: string
  region_id: string
  location_id: string
  contact_ids: string[]
  route_links: Array<{
    id: string
    route_id: string
    stage_id: string | null
  }>
  created_at: string
}

export interface SupportPointCategoryOption {
  id: string
  name: string
}

interface SupportPointCreateModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (result: CreatedSupportPointResult) => void
  regionId: string
  regionSlug: string
  routes: RouteApiSummary[]
  selectedRouteSlug?: string
  categories?: SupportPointCategoryOption[]
}

const DEFAULT_CATEGORIES: SupportPointCategoryOption[] = [
  {
    id: '2cf8aa62-c48f-4b49-a882-ecfad96a0976',
    name: 'Alimentação & Gastronomia',
  },
  { id: '813b2b6f-a1fc-4e79-8421-09fa03cb7e09', name: 'Hospedagem & Apoio' },
  { id: 'e706d05c-9f73-4543-9d6d-dbb93d60d87e', name: 'Emergência & Saúde' },
]

export function SupportPointCreateModal({
  isOpen,
  onClose,
  onSave,
  regionId,
  regionSlug,
  routes,
  selectedRouteSlug,
  categories = DEFAULT_CATEGORIES,
}: SupportPointCreateModalProps) {
  const [step, setStep] = useState<1 | 2 | 3 | 4 | 5>(1)

  // Step 1: Actor
  const [publicName, setPublicName] = useState('')
  const [legalName, setLegalName] = useState('')
  const [categoryId, setCategoryId] = useState(
    categories[0]?.id || '2cf8aa62-c48f-4b49-a882-ecfad96a0976',
  )
  const [shortDescription, setShortDescription] = useState('')
  const [servicesText, setServicesText] = useState('')

  // Step 2: Location
  const [locationLabel, setLocationLabel] = useState('Entrada principal')
  const [locality, setLocality] = useState('')
  const [latitude, setLatitude] = useState('-2.497')
  const [longitude, setLongitude] = useState('-54.952')
  const [publicVisibility, setPublicVisibility] = useState(true)

  // Step 3: Contact
  const [channelType, setChannelType] = useState<
    'phone' | 'whatsapp' | 'email' | 'website' | 'instagram'
  >('whatsapp')
  const [contactValue, setContactValue] = useState('')
  const [sourceReference, setSourceReference] = useState(
    'planilha:linha-manual',
  )

  // Step 4: Route link
  const selectedRoute =
    routes.find((r) => r.slug === selectedRouteSlug) || routes[0]
  const [selectedRouteId, setSelectedRouteId] = useState(
    selectedRoute?.id || '',
  )
  const [editorialPosition, setEditorialPosition] = useState('1')

  // Submission & Idempotency
  const [idempotencyKey, setIdempotencyKey] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [createdResult, setCreatedResult] =
    useState<CreatedSupportPointResult | null>(null)

  const dialogRef = useModalA11y<HTMLDivElement>(isOpen, onClose)

  if (!isOpen) return null

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitError('')
    setIsSubmitting(true)

    const latNum = parseFloat(latitude)
    const lngNum = parseFloat(longitude)

    if (isNaN(latNum) || latNum < -90 || latNum > 90) {
      setSubmitError('Latitude inválida. Deve ser um número entre -90 e 90.')
      setIsSubmitting(false)
      return
    }

    if (isNaN(lngNum) || lngNum < -180 || lngNum > 180) {
      setSubmitError('Longitude inválida. Deve ser um número entre -180 e 180.')
      setIsSubmitting(false)
      return
    }

    const routeIdToUse = selectedRouteId || selectedRoute?.id
    if (!routeIdToUse) {
      setSubmitError('Selecione uma rota válida pertencente à região.')
      setIsSubmitting(false)
      return
    }

    const contactsPayload = contactValue.trim()
      ? [
          {
            channel_type: channelType,
            value: contactValue.trim(),
            is_public: true,
            source_type: 'consolidated_sheet',
            source_reference: sourceReference || 'planilha:manual',
            verified_at: new Date().toISOString(),
          },
        ]
      : []

    const payload = {
      actor: {
        category_id: categoryId,
        public_name: publicName.trim(),
        legal_name: legalName.trim(),
        short_description: shortDescription.trim(),
        services: servicesText
          ? servicesText
              .split(',')
              .map((s) => s.trim())
              .filter(Boolean)
          : [],
      },
      location: {
        label: locationLabel.trim() || 'Entrada principal',
        address_fields: {
          locality: locality.trim() || regionSlug,
          administrative_area: 'PA',
          country_code: 'BR',
        },
        latitude: latNum,
        longitude: lngNum,
        public_visibility: publicVisibility,
      },
      contacts: contactsPayload,
      route_links: [
        {
          route_id: routeIdToUse,
          stage_id: null,
          route_role: 'support',
          editorial_position: parseInt(editorialPosition, 10) || 1,
          is_featured: false,
          sponsorship_label: '',
        },
      ],
    }

    const keyToUse = idempotencyKey || crypto.randomUUID()
    if (!idempotencyKey) setIdempotencyKey(keyToUse)

    try {
      const result = await adminMutation<CreatedSupportPointResult>(
        'catalog/support-points/',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Key': keyToUse,
          },
          body: JSON.stringify(payload),
        },
      )
      setCreatedResult(result)
      onSave(result)
    } catch (error) {
      setSubmitError(
        getAdminErrorMessage(
          error,
          'Não foi possível cadastrar o ponto de apoio. Revise os dados e tente novamente.',
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
        aria-labelledby="support-point-modal-title"
        aria-modal="true"
        className="poi-modal-content"
        role="dialog"
        tabIndex={-1}
      >
        <div className="modal-header">
          <div>
            <span className="modal-eyebrow">Cadastro Manual no Painel</span>
            <h2 id="support-point-modal-title">Novo Ponto de Apoio</h2>
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
          Território: <strong>{regionSlug || 'Região ativa'}</strong>. O
          cadastro cria um agregado completo obrigatoriamente em estado{' '}
          <strong>Rascunho</strong>.
        </p>

        {createdResult ? (
          <div className="form-stack">
            <FeedbackState
              message={`Ponto de apoio cadastrado com sucesso! ID do rascunho: ${createdResult.id}. O ponto permanecerá em rascunho até ser publicado pelo workflow editorial.`}
              title="Rascunho criado com sucesso"
              variant="loading"
            />
            <div className="modal-actions">
              <Button onClick={onClose} type="button" variant="secondary">
                Fechar
              </Button>
            </div>
          </div>
        ) : (
          <>
            {/* Abas / Passos */}
            <div
              aria-label="Etapas do cadastro"
              className="wizard-steps"
              role="tablist"
            >
              <button
                aria-selected={step === 1}
                className={`wizard-step-button ${step === 1 ? 'is-active' : ''}`}
                onClick={() => setStep(1)}
                role="tab"
                type="button"
              >
                1. Dados Básicos
              </button>
              <button
                aria-selected={step === 2}
                className={`wizard-step-button ${step === 2 ? 'is-active' : ''}`}
                onClick={() => setStep(2)}
                role="tab"
                type="button"
              >
                2. Localização
              </button>
              <button
                aria-selected={step === 3}
                className={`wizard-step-button ${step === 3 ? 'is-active' : ''}`}
                onClick={() => setStep(3)}
                role="tab"
                type="button"
              >
                3. Contatos
              </button>
              <button
                aria-selected={step === 4}
                className={`wizard-step-button ${step === 4 ? 'is-active' : ''}`}
                onClick={() => setStep(4)}
                role="tab"
                type="button"
              >
                4. Rota
              </button>
              <button
                aria-selected={step === 5}
                className={`wizard-step-button ${step === 5 ? 'is-active' : ''}`}
                onClick={() => setStep(5)}
                role="tab"
                type="button"
              >
                5. Resumo
              </button>
            </div>

            <form className="form-stack" onSubmit={handleSubmit}>
              {submitError ? (
                <FeedbackState
                  message={submitError}
                  title="Erro ao criar ponto de apoio"
                  variant="error"
                />
              ) : null}

              {step === 1 && (
                <fieldset className="form-step-fieldset">
                  <legend className="sr-only">Passo 1: Dados Básicos</legend>
                  <label>
                    Nome Exibição Público *
                    <input
                      onChange={(e) => setPublicName(e.target.value)}
                      placeholder="Ex: Refúgio dos Três Rios"
                      required
                      value={publicName}
                    />
                  </label>

                  <label>
                    Razão Social / Nome Jurídico (Opcional)
                    <input
                      onChange={(e) => setLegalName(e.target.value)}
                      placeholder="Ex: Três Rios Turismo LTDA"
                      value={legalName}
                    />
                  </label>

                  <label>
                    Categoria *
                    <select
                      onChange={(e) => setCategoryId(e.target.value)}
                      value={categoryId}
                    >
                      {categories.map((cat) => (
                        <option key={cat.id} value={cat.id}>
                          {cat.name}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label>
                    Descrição Curta *
                    <input
                      maxLength={180}
                      onChange={(e) => setShortDescription(e.target.value)}
                      placeholder="Ex: Apoio a visitantes com água, sanitários e informações locais."
                      required
                      value={shortDescription}
                    />
                  </label>

                  <label>
                    Serviços Oferecidos (separados por vírgula)
                    <input
                      onChange={(e) => setServicesText(e.target.value)}
                      placeholder="Ex: Água potável, Sanitários, Informações"
                      value={servicesText}
                    />
                  </label>

                  <div className="modal-actions">
                    <Button onClick={() => setStep(2)} type="button">
                      Próximo: Localização →
                    </Button>
                  </div>
                </fieldset>
              )}

              {step === 2 && (
                <fieldset className="form-step-fieldset">
                  <legend className="sr-only">Passo 2: Localização</legend>
                  <label>
                    Identificação do Local *
                    <input
                      onChange={(e) => setLocationLabel(e.target.value)}
                      placeholder="Ex: Entrada principal"
                      required
                      value={locationLabel}
                    />
                  </label>

                  <label>
                    Localidade / Bairro / Comunidade
                    <input
                      onChange={(e) => setLocality(e.target.value)}
                      placeholder="Ex: Alter do Chão, Santarém - PA"
                      value={locality}
                    />
                  </label>

                  <div className="form-row">
                    <label>
                      Latitude (-90 a 90) *
                      <input
                        onChange={(e) => setLatitude(e.target.value)}
                        placeholder="-2.497"
                        required
                        type="text"
                        value={latitude}
                      />
                    </label>

                    <label>
                      Longitude (-180 a 180) *
                      <input
                        onChange={(e) => setLongitude(e.target.value)}
                        placeholder="-54.952"
                        required
                        type="text"
                        value={longitude}
                      />
                    </label>
                  </div>

                  <label className="checkbox-label">
                    <input
                      checked={publicVisibility}
                      onChange={(e) => setPublicVisibility(e.target.checked)}
                      type="checkbox"
                    />
                    Visibilidade pública da localização
                  </label>

                  <div className="modal-actions">
                    <Button
                      onClick={() => setStep(1)}
                      type="button"
                      variant="secondary"
                    >
                      ← Voltar
                    </Button>
                    <Button onClick={() => setStep(3)} type="button">
                      Próximo: Contatos →
                    </Button>
                  </div>
                </fieldset>
              )}

              {step === 3 && (
                <fieldset className="form-step-fieldset">
                  <legend className="sr-only">
                    Passo 3: Contatos Públicos
                  </legend>
                  <p className="panel-hint">
                    Contatos são opcionais no rascunho. Quando informados, devem
                    ser públicos e verificados com proveniência.
                  </p>

                  <div className="form-row">
                    <label>
                      Canal de Contato
                      <select
                        onChange={(e) =>
                          setChannelType(
                            e.target.value as
                              | 'phone'
                              | 'whatsapp'
                              | 'email'
                              | 'website'
                              | 'instagram',
                          )
                        }
                        value={channelType}
                      >
                        <option value="whatsapp">WhatsApp (E.164)</option>
                        <option value="phone">Telefone (E.164)</option>
                        <option value="email">E-mail</option>
                        <option value="website">Website (HTTPS)</option>
                        <option value="instagram">Instagram (HTTPS)</option>
                      </select>
                    </label>

                    <label>
                      Valor do Contato
                      <input
                        onChange={(e) => setContactValue(e.target.value)}
                        placeholder="Ex: +5593991234567 ou email@exemplo.org"
                        value={contactValue}
                      />
                    </label>
                  </div>

                  <label>
                    Referência de Proveniência na Planilha
                    <input
                      onChange={(e) => setSourceReference(e.target.value)}
                      placeholder="Ex: planilha:linha-042"
                      value={sourceReference}
                    />
                  </label>

                  <div className="modal-actions">
                    <Button
                      onClick={() => setStep(2)}
                      type="button"
                      variant="secondary"
                    >
                      ← Voltar
                    </Button>
                    <Button onClick={() => setStep(4)} type="button">
                      Próximo: Rota →
                    </Button>
                  </div>
                </fieldset>
              )}

              {step === 4 && (
                <fieldset className="form-step-fieldset">
                  <legend className="sr-only">Passo 4: Vínculo com Rota</legend>
                  <label>
                    Rota Principal do Ponto *
                    <select
                      onChange={(e) => setSelectedRouteId(e.target.value)}
                      value={selectedRouteId}
                    >
                      {routes.map((r) => (
                        <option key={r.id || r.slug} value={r.id || r.slug}>
                          {r.title}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label>
                    Posição Editorial na Rota
                    <input
                      onChange={(e) => setEditorialPosition(e.target.value)}
                      type="number"
                      value={editorialPosition}
                    />
                  </label>

                  <div className="modal-actions">
                    <Button
                      onClick={() => setStep(3)}
                      type="button"
                      variant="secondary"
                    >
                      ← Voltar
                    </Button>
                    <Button onClick={() => setStep(5)} type="button">
                      Próximo: Resumo →
                    </Button>
                  </div>
                </fieldset>
              )}

              {step === 5 && (
                <fieldset className="form-step-fieldset">
                  <legend className="sr-only">
                    Passo 5: Resumo e Confirmação
                  </legend>
                  <div className="summary-box">
                    <h4>Resumo do Agregado</h4>
                    <p>
                      <strong>Nome:</strong> {publicName || 'Não informado'}
                    </p>
                    <p>
                      <strong>Descrição:</strong>{' '}
                      {shortDescription || 'Não informada'}
                    </p>
                    <p>
                      <strong>Localização:</strong> {locationLabel} ({latitude},{' '}
                      {longitude})
                    </p>
                    <p>
                      <strong>Contato:</strong>{' '}
                      {contactValue
                        ? `${channelType}: ${contactValue}`
                        : 'Nenhum informado'}
                    </p>
                    <p>
                      <strong>Território:</strong> {regionSlug}{' '}
                      {regionId ? `(${regionId})` : ''}
                    </p>
                    <p>
                      <strong>Estado Inicial:</strong> <code>draft</code>{' '}
                      (Rascunho)
                    </p>
                  </div>

                  <p className="panel-hint">
                    A publicação exige revisão humana separada pelo workflow
                    editorial. Não há publicação automática nesta ação.
                  </p>

                  <div className="modal-actions">
                    <Button
                      onClick={() => setStep(4)}
                      type="button"
                      variant="secondary"
                    >
                      ← Voltar
                    </Button>
                    <Button
                      disabled={
                        isSubmitting || !publicName || !shortDescription
                      }
                      isLoading={isSubmitting}
                      type="submit"
                    >
                      💾 Confirmar e Criar Rascunho
                    </Button>
                  </div>
                </fieldset>
              )}
            </form>
          </>
        )}
      </div>
    </div>
  )
}
