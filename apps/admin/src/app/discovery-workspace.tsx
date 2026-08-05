'use client'

import { Button } from '@econexao/ui/button'
import { FeedbackState } from '@econexao/ui/feedback-state'
import Image from 'next/image'
import { FormEvent, useEffect, useState } from 'react'
import {
  adminMutation,
  adminRequest,
  getAdminErrorMessage,
} from '../lib/admin-api'
import googleMapsLogoDark from '../assets/google-maps-logo-dark.png'
import googleMapsLogoLight from '../assets/google-maps-logo-light.png'

interface AdminUser {
  username: string
  actions: string[]
}

interface AdminSession {
  authenticated: boolean
  user: AdminUser | null
}

interface PlaceCandidate {
  place_id: string
  display_name: string
  formatted_address: string
  latitude: number | null
  longitude: number | null
  primary_type: string
  google_maps_uri: string
}

export interface GooglePlacesPreview {
  run_id: string
  attribution: string
  result_count: number
  candidates: PlaceCandidate[]
}

function safeGoogleMapsUrl(value: string) {
  try {
    const url = new URL(value)
    const googleHost =
      url.hostname === 'google.com' || url.hostname.endsWith('.google.com')
    return url.protocol === 'https:' && googleHost ? url.toString() : null
  } catch {
    return null
  }
}

export function GooglePlacesPreviewSection({
  preview,
}: {
  preview: GooglePlacesPreview
}) {
  return (
    <section aria-labelledby="preview-title" className="preview-panel">
      <div className="preview-heading">
        <div>
          <div className="provider-attribution">
            <span>Conteúdo fornecido por</span>
            <span
              aria-label="Google Maps"
              className="google-maps-logo"
              role="img"
              translate="no"
            >
              <Image
                alt=""
                className="google-maps-logo--dark"
                height={36}
                src={googleMapsLogoDark}
                width={196}
              />
              <Image
                alt=""
                className="google-maps-logo--light"
                height={36}
                src={googleMapsLogoLight}
                width={196}
              />
            </span>
          </div>
          <h2 id="preview-title">Prévia efêmera</h2>
        </div>
        <span className="result-count">{preview.result_count} candidatos</span>
      </div>
      <p className="provider-notice">
        Estes dados não foram importados para a ECOnexão. Verifique cada
        candidato em fonte autorizada antes de criar um rascunho. A busca usa o
        centro, o raio e os tipos informados e recebe do Google Maps a ordem por
        popularidade.
      </p>
      {preview.candidates.length ? (
        <ol className="candidate-list">
          {preview.candidates.map((candidate) => {
            const googleMapsUrl = safeGoogleMapsUrl(candidate.google_maps_uri)
            return (
              <li className="candidate-card" key={candidate.place_id}>
                <h3>{candidate.display_name || 'Nome não informado'}</h3>
                <dl>
                  <div>
                    <dt>Tipo</dt>
                    <dd>{candidate.primary_type || 'Não informado'}</dd>
                  </div>
                  <div>
                    <dt>Endereço</dt>
                    <dd>{candidate.formatted_address || 'Não informado'}</dd>
                  </div>
                  <div>
                    <dt>Coordenadas</dt>
                    <dd>
                      {candidate.latitude !== null &&
                      candidate.longitude !== null
                        ? `${candidate.latitude.toFixed(6)}, ${candidate.longitude.toFixed(6)}`
                        : 'Não informadas'}
                    </dd>
                  </div>
                </dl>
                {googleMapsUrl ? (
                  <a href={googleMapsUrl} rel="noreferrer" target="_blank">
                    Abrir resultado no Google Maps
                  </a>
                ) : null}
              </li>
            )
          })}
        </ol>
      ) : (
        <FeedbackState
          message="Tente ampliar o raio ou ajustar os tipos consultados."
          title="Nenhum candidato encontrado"
          variant="empty"
        />
      )}
    </section>
  )
}

export function DiscoveryWorkspace() {
  const [session, setSession] = useState<AdminSession | null>(null)
  const [sessionError, setSessionError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [preview, setPreview] = useState<GooglePlacesPreview | null>(null)
  const [previewError, setPreviewError] = useState('')

  useEffect(() => {
    let active = true
    adminRequest<AdminSession>('auth/session')
      .then((payload) => {
        if (active) setSession(payload)
      })
      .catch((error: unknown) => {
        if (active)
          setSessionError(
            getAdminErrorMessage(
              error,
              'Não foi possível consultar a sessão administrativa.',
            ),
          )
      })
    return () => {
      active = false
    }
  }, [])

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSessionError('')
    setIsSubmitting(true)
    const form = new FormData(event.currentTarget)
    try {
      const payload = await adminMutation<AdminSession>('auth/login', {
        body: JSON.stringify({
          username: form.get('username'),
          password: form.get('password'),
        }),
        headers: { 'Content-Type': 'application/json' },
        method: 'POST',
      })
      setSession(payload)
    } catch (error) {
      setSessionError(getAdminErrorMessage(error, 'Não foi possível entrar.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function logout() {
    setIsSubmitting(true)
    try {
      await adminMutation('auth/logout', {
        method: 'POST',
      })
      setSession({ authenticated: false, user: null })
      setPreview(null)
    } catch (error) {
      setSessionError(
        getAdminErrorMessage(error, 'Não foi possível encerrar a sessão.'),
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  async function discover(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setPreview(null)
    setPreviewError('')
    setIsSubmitting(true)
    const form = new FormData(event.currentTarget)
    try {
      const payload = await adminMutation<GooglePlacesPreview>(
        'discovery/google-places/preview',
        {
          body: JSON.stringify({
            region_slug: form.get('region_slug'),
            route_slug: form.get('route_slug'),
            latitude: Number(form.get('latitude')),
            longitude: Number(form.get('longitude')),
            radius_meters: Number(form.get('radius_meters')),
            included_types: String(form.get('included_types'))
              .split(',')
              .map((value) => value.trim())
              .filter(Boolean),
            max_results: Number(form.get('max_results')),
          }),
          headers: { 'Content-Type': 'application/json' },
          method: 'POST',
        },
      )
      setPreview(payload)
    } catch (error) {
      setPreviewError(
        getAdminErrorMessage(
          error,
          'A descoberta externa não pôde ser executada.',
        ),
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  if (sessionError && session === null) {
    return (
      <FeedbackState
        message={sessionError}
        title="Falha ao carregar a sessão"
        variant="error"
      />
    )
  }
  if (session === null) {
    return (
      <FeedbackState
        message="Validando o acesso ao painel."
        title="Carregando sessão"
        variant="loading"
      />
    )
  }
  if (!session.authenticated || !session.user) {
    return (
      <section className="auth-card">
        <h2>Acesso administrativo</h2>
        <p>Entre com uma conta autorizada da equipe editorial.</p>
        <form className="form-stack" onSubmit={login}>
          <label>
            Usuário
            <input autoComplete="username" name="username" required />
          </label>
          <label>
            Senha
            <input
              autoComplete="current-password"
              name="password"
              required
              type="password"
            />
          </label>
          {sessionError ? (
            <p className="form-error" role="alert">
              {sessionError}
            </p>
          ) : null}
          <Button isLoading={isSubmitting} type="submit">
            Entrar
          </Button>
        </form>
      </section>
    )
  }

  const canDiscover = session.user.actions.includes('discover_external')
  return (
    <div className="workspace">
      <div className="session-bar">
        <p>
          Sessão de <strong>{session.user.username}</strong>
        </p>
        <Button
          isLoading={isSubmitting}
          onClick={logout}
          type="button"
          variant="secondary"
        >
          Sair
        </Button>
      </div>
      {!canDiscover ? (
        <FeedbackState
          message="Solicite a um administrador o papel editorial necessário."
          title="Sem permissão para descoberta externa"
          variant="error"
        />
      ) : (
        <section className="discovery-card">
          <p className="provider-label">Ferramenta opcional</p>
          <h2>Descobrir candidatos no Google Maps</h2>
          <p>
            A consulta cria referências técnicas para curadoria. Ela nunca
            publica nem preenche um registro automaticamente.
          </p>
          <form className="discovery-form" onSubmit={discover}>
            <label>
              Região
              <input name="region_slug" placeholder="slug-da-regiao" required />
            </label>
            <label>
              Rota
              <input name="route_slug" placeholder="slug-da-rota" required />
            </label>
            <label>
              Latitude do centro
              <input
                inputMode="decimal"
                max="90"
                min="-90"
                name="latitude"
                required
                step="any"
                type="number"
              />
            </label>
            <label>
              Longitude do centro
              <input
                inputMode="decimal"
                max="180"
                min="-180"
                name="longitude"
                required
                step="any"
                type="number"
              />
            </label>
            <label>
              Raio em metros
              <input
                defaultValue="5000"
                max="50000"
                min="1"
                name="radius_meters"
                required
                type="number"
              />
            </label>
            <label>
              Limite de resultados
              <input
                defaultValue="10"
                max="20"
                min="1"
                name="max_results"
                required
                type="number"
              />
            </label>
            <label className="field-wide">
              Tipos, separados por vírgula
              <input
                defaultValue="restaurant, guest_house, tourist_attraction"
                name="included_types"
                required
              />
            </label>
            <div className="field-wide form-actions">
              <Button isLoading={isSubmitting} type="submit">
                Consultar Google Maps
              </Button>
              <span>A prévia desaparece ao sair ou recarregar a página.</span>
            </div>
          </form>
          {previewError ? (
            <FeedbackState
              message={previewError}
              title="Descoberta indisponível"
              variant="error"
            />
          ) : null}
        </section>
      )}
      {preview ? <GooglePlacesPreviewSection preview={preview} /> : null}
    </div>
  )
}
