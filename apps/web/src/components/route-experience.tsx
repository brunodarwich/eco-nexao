'use client'

import { Button } from '@econexao/ui/button'
import { FeedbackState } from '@econexao/ui/feedback-state'
import {
  Accessibility,
  AlertTriangle,
  ArrowLeft,
  BadgeDollarSign,
  Clock3,
  Compass,
  Gauge,
  Info,
  MapPin,
  Play,
  Share2,
  ShieldAlert,
} from 'lucide-react'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import {
  contactHref,
  directionsHref,
  formatPublicAddress,
} from '@/lib/contact-links'
import {
  getPublishedRoute,
  getPublishedRouteCatalog,
  type RouteCatalogItem,
  type RouteDetail,
} from '@/lib/public-api'
import { RouteMap } from './route-map'
import { RouteFavoriteButton, RouteLocalActions } from './route-local-actions'
import { ReportIssueModal } from './report-issue-modal'
import { trackEvent } from '@/lib/analytics-sdk'

type RouteTab = 'overview' | 'map' | 'catalog'

interface RouteExperienceProps {
  initialActorSlug?: string
  regionSlug: string
  routeSlug: string
  tab: RouteTab
}

const difficultyLabels: Record<RouteDetail['difficulty'], string> = {
  easy: 'Fácil',
  hard: 'Difícil',
  moderate: 'Moderada',
}

const contactLabels = {
  email: 'Enviar e-mail',
  instagram: 'Abrir Instagram',
  phone: 'Ligar',
  website: 'Visitar site',
  whatsapp: 'Abrir WhatsApp',
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'long',
    timeZone: 'America/Fortaleza',
  }).format(new Date(value))
}

function formatDuration(minutes: number) {
  const hours = Math.floor(minutes / 60)
  const remainder = minutes % 60
  return `${hours ? `${hours} h` : ''}${hours && remainder ? ' ' : ''}${
    remainder ? `${remainder} min` : ''
  }`
}

function formatCost(minimum?: string | null, maximum?: string | null) {
  const compactCurrency = (value: string) => {
    const amount = Number(value)
    return Number.isInteger(amount)
      ? `R$ ${amount}`
      : new Intl.NumberFormat('pt-BR', {
          currency: 'BRL',
          maximumFractionDigits: 2,
          style: 'currency',
        }).format(amount)
  }

  if (minimum && maximum) {
    return `${compactCurrency(minimum)}–${compactCurrency(maximum).replace(
      'R$ ',
      '',
    )}`
  }
  if (minimum) return `A partir de ${compactCurrency(minimum)}`
  if (maximum) return `Até ${compactCurrency(maximum)}`
  return 'Consulte localmente'
}

function RouteShareButton({ routeName }: { routeName: string }) {
  const [message, setMessage] = useState('')

  async function shareRoute() {
    const shareData = {
      text: `Conheça ${routeName} na ECOnexão.`,
      title: routeName,
      url: window.location.href,
    }

    try {
      if (navigator.share) {
        await navigator.share(shareData)
        setMessage('Rota compartilhada.')
        return
      }

      await navigator.clipboard.writeText(shareData.url)
      setMessage('Link da rota copiado.')
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') return
      setMessage('Não foi possível compartilhar esta rota.')
    }
  }

  return (
    <>
      <button
        aria-label="Compartilhar rota"
        className="route-app-bar__action"
        onClick={() => void shareRoute()}
        type="button"
      >
        <Share2 aria-hidden="true" />
      </button>
      <span aria-live="polite" className="sr-only">
        {message}
      </span>
    </>
  )
}

function RouteAppBar({
  regionSlug,
  route,
}: {
  regionSlug: string
  route: RouteDetail
}) {
  return (
    <div className="route-app-bar">
      <Link
        aria-label="Voltar para todas as rotas"
        className="route-app-bar__action"
        href={`/${regionSlug}/rotas`}
      >
        <ArrowLeft aria-hidden="true" />
      </Link>
      <strong className="route-app-bar__title">{route.public_name}</strong>
      <RouteShareButton routeName={route.public_name} />
      <RouteFavoriteButton
        className="route-app-bar__action"
        compact
        route={route}
      />
    </div>
  )
}

function RouteTabs({
  activeTab,
  regionSlug,
  routeSlug,
}: {
  activeTab: RouteTab
  regionSlug: string
  routeSlug: string
}) {
  const basePath = `/${regionSlug}/rotas/${routeSlug}`
  const tabs = [
    { href: basePath, id: 'overview' as const, label: 'Visão geral' },
    { href: `${basePath}/mapa`, id: 'map' as const, label: 'Mapa' },
    { href: `${basePath}/catalogo`, id: 'catalog' as const, label: 'Catálogo' },
  ]

  return (
    <nav aria-label="Conteúdo da rota" className="route-tabs">
      {tabs.map((tab) => (
        <Link
          aria-current={activeTab === tab.id ? 'page' : undefined}
          href={tab.href}
          key={tab.id}
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  )
}

function RouteOverview({ route }: { route: RouteDetail }) {
  const criticalAlerts = route.alerts.filter(
    (alert) => alert.severity === 'critical',
  )
  const nonCriticalAlerts = route.alerts.filter(
    (alert) => alert.severity !== 'critical',
  )
  const hasPreparation = Boolean(
    route.preparation_content || route.accessibility_content,
  )

  return (
    <div className="route-overview">
      {hasPreparation ? (
        <section
          aria-labelledby="preparation-title"
          className="route-section route-section--preparation"
        >
          <p className="eyebrow">Preparação</p>
          <h2 id="preparation-title">Prepare-se para visitar</h2>
          <div className="preparation-list">
            {route.preparation_content ? (
              <article className="preparation-item">
                <span aria-hidden="true" className="preparation-item__icon">
                  <Compass aria-hidden="true" />
                </span>
                <div>
                  <h3>Orientações essenciais</h3>
                  <p>{route.preparation_content}</p>
                </div>
              </article>
            ) : null}
            {route.accessibility_content ? (
              <article className="preparation-item">
                <span aria-hidden="true" className="preparation-item__icon">
                  <Accessibility aria-hidden="true" />
                </span>
                <div>
                  <h3>Acessibilidade</h3>
                  <p>{route.accessibility_content}</p>
                </div>
              </article>
            ) : null}
          </div>
        </section>
      ) : null}

      {criticalAlerts.length > 0 ? (
        <section
          aria-labelledby="critical-alerts-title"
          className="route-section"
        >
          <div className="section-heading">
            <div>
              <p className="eyebrow">Atenção prioritária</p>
              <h2 id="critical-alerts-title">Alertas de segurança</h2>
            </div>
          </div>
          <div className="alert-list">
            {criticalAlerts.map((alert) => (
              <article
                className="route-alert route-alert--critical"
                key={alert.id}
              >
                <div className="route-alert__header">
                  <span aria-hidden="true" className="route-alert__icon">
                    <ShieldAlert aria-hidden="true" />
                  </span>
                  <div>
                    <strong>{alert.title}</strong>
                    {alert.description ? <p>{alert.description}</p> : null}
                    {alert.alternative ? (
                      <p className="route-alert__alternative">
                        Alternativa: {alert.alternative}
                      </p>
                    ) : null}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {nonCriticalAlerts.length > 0 ? (
        <section
          aria-labelledby="non-critical-alerts-title"
          className="route-section route-section--warning"
        >
          <div className="section-heading">
            <div>
              <p className="eyebrow">Antes de sair</p>
              <h2 id="non-critical-alerts-title">Faixa de atenção</h2>
            </div>
          </div>
          <div className="alert-list">
            {nonCriticalAlerts.map((alert) => (
              <article
                className="route-alert route-alert--warning-banner"
                key={alert.id}
              >
                <div className="route-alert__header">
                  <span aria-hidden="true" className="route-alert__icon">
                    {alert.severity === 'warning' ? (
                      <AlertTriangle aria-hidden="true" />
                    ) : (
                      <Info aria-hidden="true" />
                    )}
                  </span>
                  <div>
                    <strong>{alert.title}</strong>
                    {alert.description ? <p>{alert.description}</p> : null}
                    {alert.alternative ? (
                      <p className="route-alert__alternative">
                        Alternativa: {alert.alternative}
                      </p>
                    ) : null}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {route.description ? (
        <section
          aria-labelledby="about-title"
          className="route-section route-copy"
        >
          <p className="eyebrow">Sobre a experiência</p>
          <h2 id="about-title">O que esperar</h2>
          <p>{route.description}</p>
        </section>
      ) : null}

      {route.stages.length > 0 ? (
        <section
          aria-labelledby="stages-title"
          className="route-section route-section--stages"
        >
          <div className="section-heading">
            <div>
              <p className="eyebrow">Passo a passo</p>
              <h2 id="stages-title">Etapas da rota</h2>
            </div>
            <Link
              className="stage-map-link"
              href={`/${route.region_slug}/rotas/${route.slug}/mapa`}
            >
              <MapPin aria-hidden="true" />
              <span>Ver mapa</span>
            </Link>
          </div>
          <ol className="stage-list">
            {route.stages.map((stage, index) => {
              const isLast = index === route.stages.length - 1
              return (
                <li
                  className={`stage-item${isLast ? ' stage-item--last' : ''}`}
                  key={stage.id}
                >
                  <div className="stage-item__timeline">
                    <span className="stage-item__number" aria-hidden="true">
                      {stage.position}
                    </span>
                    {!isLast ? (
                      <span
                        className="stage-item__connector"
                        aria-hidden="true"
                      />
                    ) : null}
                  </div>
                  <div className="stage-item__body">
                    <div className="stage-item__header">
                      <h3>{stage.public_name}</h3>
                      {stage.duration_minutes ? (
                        <span className="stage-item__duration">
                          <Clock3 aria-hidden="true" />
                          <span>{formatDuration(stage.duration_minutes)}</span>
                        </span>
                      ) : null}
                    </div>
                    {stage.description ? <p>{stage.description}</p> : null}
                    {stage.arrival_guidance ? (
                      <p className="muted-text">{stage.arrival_guidance}</p>
                    ) : null}
                  </div>
                </li>
              )
            })}
          </ol>
        </section>
      ) : null}
    </div>
  )
}

function RouteCatalog({
  catalog,
  initialActorSlug,
  route,
}: {
  catalog: RouteCatalogItem[]
  initialActorSlug?: string
  route: RouteDetail
}) {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')
  const [activeActorSlug, setActiveActorSlug] = useState(initialActorSlug ?? '')
  const categories = Array.from(
    new Map(
      catalog.map((item) => [
        item.actor.category_slug,
        item.actor.category_name,
      ]),
    ),
  )
  const normalizedQuery = query.trim().toLocaleLowerCase('pt-BR')
  const visibleItems = catalog.filter((item) => {
    const matchesCategory = !category || item.actor.category_slug === category
    const matchesQuery =
      !normalizedQuery ||
      `${item.actor.public_name} ${item.actor.short_description}`
        .toLocaleLowerCase('pt-BR')
        .includes(normalizedQuery)
    return matchesCategory && matchesQuery
  })

  function showActor(slug: string) {
    const nextSlug = activeActorSlug === slug ? '' : slug
    setActiveActorSlug(nextSlug)
    const url = new URL(window.location.href)
    if (nextSlug) url.searchParams.set('ator', nextSlug)
    else url.searchParams.delete('ator')
    window.history.replaceState(null, '', `${url.pathname}${url.search}`)
  }

  return (
    <section aria-labelledby="catalog-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Conexões locais</p>
          <h2 id="catalog-title">Catálogo da rota</h2>
        </div>
        <span aria-live="polite">
          {visibleItems.length}{' '}
          {visibleItems.length === 1 ? 'resultado' : 'resultados'}
        </span>
      </div>
      <div className="catalog-filters">
        <label>
          <span>Buscar no catálogo</span>
          <input
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Nome ou serviço"
            type="search"
            value={query}
          />
        </label>
        <label>
          <span>Categoria</span>
          <select
            onChange={(event) => setCategory(event.target.value)}
            value={category}
          >
            <option value="">Todas as categorias</option>
            {categories.map(([slug, name]) => (
              <option key={slug} value={slug}>
                {name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {visibleItems.length === 0 ? (
        <FeedbackState
          action={
            <Button
              onClick={() => {
                setQuery('')
                setCategory('')
              }}
              variant="secondary"
            >
              Limpar filtros
            </Button>
          }
          message="A rota continua selecionada. Ajuste a busca ou a categoria."
          title="Nenhum item encontrado"
          variant="empty"
        />
      ) : (
        <ul className="catalog-grid">
          {visibleItems.map((item) => {
            const actor = item.actor
            const isOpen = activeActorSlug === actor.slug
            const primaryLocation =
              actor.locations.find((location) => location.is_primary) ??
              actor.locations[0]
            const address = primaryLocation
              ? formatPublicAddress(primaryLocation.address_fields)
              : ''
            const directions = primaryLocation
              ? directionsHref(primaryLocation)
              : null
            return (
              <li className="catalog-card" key={actor.id}>
                <div>
                  <div className="catalog-card__meta">
                    <span>{actor.category_name}</span>
                    {item.sponsorship_label ? (
                      <span>Patrocinado: {item.sponsorship_label}</span>
                    ) : null}
                  </div>
                  <h3>{actor.public_name}</h3>
                  <p>{actor.short_description}</p>
                  {address ? <p className="muted-text">{address}</p> : null}
                </div>
                <Button
                  aria-expanded={isOpen}
                  onClick={() => showActor(actor.slug)}
                  type="button"
                  variant="secondary"
                >
                  {isOpen ? 'Ocultar detalhes' : 'Ver detalhes'}
                </Button>
                {isOpen ? (
                  <div className="actor-detail">
                    <p>{actor.full_description || actor.short_description}</p>
                    {Array.isArray(actor.services) &&
                    actor.services.length > 0 ? (
                      <>
                        <strong>Serviços</strong>
                        <ul>
                          {actor.services
                            .filter(
                              (service): service is string =>
                                typeof service === 'string',
                            )
                            .map((service) => (
                              <li key={service}>{service}</li>
                            ))}
                        </ul>
                      </>
                    ) : null}
                    <div className="contact-actions">
                      {actor.contact_channels.map((contact) => {
                        const href = contactHref(contact)
                        if (!href) return null
                        const opensNewTab = href.startsWith('http')
                        return (
                          <a
                            className="ui-button"
                            href={href}
                            key={`${contact.channel_type}-${contact.public_value}`}
                            rel={opensNewTab ? 'noreferrer' : undefined}
                            target={opensNewTab ? '_blank' : undefined}
                            onClick={() =>
                              void trackEvent('contact_opened', {
                                region_id: route.region_slug,
                                route_id: route.slug,
                                actor_id: actor.id,
                              })
                            }
                          >
                            {contactLabels[contact.channel_type]}
                          </a>
                        )
                      })}
                      {directions ? (
                        <a
                          className="ui-button ui-button--secondary"
                          href={directions}
                          rel="noreferrer"
                          target="_blank"
                          onClick={() =>
                            void trackEvent('contact_opened', {
                              region_id: route.region_slug,
                              route_id: route.slug,
                              actor_id: actor.id,
                            })
                          }
                        >
                          Como chegar
                        </a>
                      ) : null}
                    </div>
                    <p className="verification-note">
                      Atualizado em {formatDate(actor.updated_at)}. Confirme as
                      informações diretamente antes da visita.
                    </p>
                  </div>
                ) : null}
              </li>
            )
          })}
        </ul>
      )}

      <p className="verification-note">
        Catálogo contextual de {route.public_name}. Contatos exibidos são os
        autorizados para publicação.
      </p>
    </section>
  )
}
export function RouteExperience({
  initialActorSlug,
  regionSlug,
  routeSlug,
  tab: initialTab,
}: RouteExperienceProps) {
  const [route, setRoute] = useState<RouteDetail | null>(null)
  const [catalog, setCatalog] = useState<RouteCatalogItem[]>([])
  const [tab] = useState<RouteTab>(initialTab)

  const [failed, setFailed] = useState(false)
  const [showReportModal, setShowReportModal] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    const requests =
      tab === 'catalog' || tab === 'map'
        ? Promise.all([
            getPublishedRoute(regionSlug, routeSlug, controller.signal),
            getPublishedRouteCatalog(regionSlug, routeSlug, controller.signal),
          ])
        : getPublishedRoute(regionSlug, routeSlug, controller.signal).then(
            (routeDetail) =>
              [routeDetail, []] as [RouteDetail, RouteCatalogItem[]],
          )

    requests
      .then(([routeDetail, routeCatalog]) => {
        setRoute(routeDetail)
        setCatalog(routeCatalog)
        void trackEvent('route_opened', {
          region_id: regionSlug,
          route_id: routeSlug,
        })
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setFailed(true)
      })

    return () => controller.abort()
  }, [regionSlug, routeSlug, tab])

  if (failed) {
    return (
      <FeedbackState
        action={
          <Link className="ui-button" href={`/${regionSlug}/rotas`}>
            Voltar às rotas
          </Link>
        }
        message="A rota pode estar indisponível ou o link pode ter mudado."
        title="Não foi possível abrir esta rota"
        variant="error"
      />
    )
  }

  if (!route) {
    return (
      <FeedbackState
        message="Estamos buscando as informações publicadas."
        title="Carregando rota"
        variant="loading"
      />
    )
  }

  const criticalAlerts = route.alerts.filter(
    (alert) => alert.severity === 'critical',
  )

  return (
    <article className="route-experience">
      <RouteAppBar regionSlug={regionSlug} route={route} />
      <Link className="route-back-link" href={`/${regionSlug}/rotas`}>
        <ArrowLeft aria-hidden="true" /> Todas as rotas
      </Link>
      <header className="route-hero route-hero--fallback">
        <div className="route-hero__visual">
          <span aria-hidden="true" className="route-hero__fallback-mark" />
          <div className="route-hero__copy">
            <p className="route-hero__region">{route.region_name}</p>
            <h1>{route.short_promise}</h1>
          </div>
          <dl className="route-facts">
            <div>
              <Clock3 aria-hidden="true" />
              <dt>Duração</dt>
              <dd>{formatDuration(route.duration_minutes)}</dd>
            </div>
            <div>
              <Gauge aria-hidden="true" />
              <dt>Dificuldade</dt>
              <dd>{difficultyLabels[route.difficulty]}</dd>
            </div>
            <div>
              <BadgeDollarSign aria-hidden="true" />
              <dt>Custo</dt>
              <dd>
                {formatCost(route.estimated_cost_min, route.estimated_cost_max)}
              </dd>
            </div>
          </dl>
        </div>
        <div className="route-hero__summary-panel">
          <div className="route-hero__identity">
            <p className="eyebrow">Rota publicada</p>
            <p>{route.public_name}</p>
          </div>
          {criticalAlerts.length > 0 ? (
            <div className="route-critical-summary" role="alert">
              <strong>Alerta crítico antes de iniciar</strong>
              <span>
                {criticalAlerts[0]?.title}. Leia os alertas ativos abaixo.
              </span>
            </div>
          ) : null}
          <Link
            className="ui-button route-primary-action"
            href={`/${regionSlug}/rotas/${routeSlug}/mapa`}
          >
            <Play aria-hidden="true" fill="currentColor" />
            Iniciar rota
          </Link>
          <RouteLocalActions route={route} />
          <Button
            className="route-report-button"
            onClick={() => setShowReportModal(true)}
            type="button"
            variant="secondary"
          >
            <AlertTriangle aria-hidden="true" />
            Relatar problema
          </Button>
          <p className="verification-note route-hero__verification">
            Conteúdo atualizado em {formatDate(route.updated_at)}.
          </p>
        </div>
      </header>

      <RouteTabs
        activeTab={tab}
        regionSlug={regionSlug}
        routeSlug={routeSlug}
      />

      <div className="route-tab-content">
        {tab === 'overview' ? <RouteOverview route={route} /> : null}
        {tab === 'map' ? <RouteMap catalog={catalog} route={route} /> : null}
        {tab === 'catalog' ? (
          <RouteCatalog
            catalog={catalog}
            initialActorSlug={initialActorSlug}
            route={route}
          />
        ) : null}
      </div>

      <ReportIssueModal
        isOpen={showReportModal}
        onClose={() => setShowReportModal(false)}
        regionSlug={regionSlug}
        targetName={route.public_name}
        targetSlug={routeSlug}
        targetType="route"
      />
    </article>
  )
}
