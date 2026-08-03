import { describe, expect, it } from 'vitest'
import {
  contactHref,
  directionsHref,
  formatPublicAddress,
} from '../lib/contact-links'
import type { RegionSummary, RouteSummary } from '../lib/public-api'
import type { RouteCatalogItem } from '../lib/public-api'
import { resolvePreferredRegion } from '../lib/region-preference'
import {
  filterRouteMapPoints,
  getRouteMapPoints,
} from '../lib/route-map-points'
import { filterRoutes, filtersFromSearchParams } from '../lib/route-filters'

const regions: RegionSummary[] = [
  {
    center_point: { coordinates: [-54.7, -2.4], type: 'Point' },
    id: 'region-1',
    public_name: 'Tapajós',
    published_version: 1,
    short_description: 'Floresta e rios.',
    slug: 'tapajos',
    timezone: 'America/Fortaleza',
    updated_at: '2026-07-29T12:00:00Z',
  },
]

const routes: RouteSummary[] = [
  {
    accessibility_content: '',
    difficulty: 'easy',
    duration_minutes: 90,
    estimated_cost_max: '80.00',
    estimated_cost_min: '20.00',
    id: 'route-1',
    offline_enabled: false,
    public_name: 'Caminho das águas',
    short_promise: 'Uma experiência tranquila entre praias.',
    slug: 'caminho-das-aguas',
    transport_modes: ['boat'],
    updated_at: '2026-07-29T12:00:00Z',
  },
  {
    accessibility_content: '',
    difficulty: 'hard',
    duration_minutes: 300,
    estimated_cost_max: null,
    estimated_cost_min: null,
    id: 'route-2',
    offline_enabled: false,
    public_name: 'Trilha da mata',
    short_promise: 'Imersão de dia inteiro na floresta.',
    slug: 'trilha-da-mata',
    transport_modes: ['walk'],
    updated_at: '2026-07-29T12:00:00Z',
  },
]

describe('region resolution and route discovery', () => {
  it('uses only a persisted region that is still published', () => {
    expect(resolvePreferredRegion(regions, 'tapajos')?.slug).toBe('tapajos')
    expect(resolvePreferredRegion(regions, 'regiao-arquivada')).toBeNull()
    expect(resolvePreferredRegion(regions, null)).toBeNull()
  })

  it('normalizes URL filters and combines them', () => {
    const filters = filtersFromSearchParams({
      difficulty: 'hard',
      duration: 'long',
      q: 'mata',
    })

    expect(filterRoutes(routes, filters).map((route) => route.slug)).toEqual([
      'trilha-da-mata',
    ])
  })

  it('ignores unsupported URL filter values', () => {
    expect(
      filtersFromSearchParams({
        difficulty: 'impossible',
        duration: ['short', 'long'],
      }),
    ).toEqual({ difficulty: '', duration: '', query: '' })
  })
})

describe('public contact links', () => {
  it('allows only expected contact formats and safe web protocols', () => {
    expect(
      contactHref({ channel_type: 'whatsapp', public_value: '+5593000000000' }),
    ).toBe('https://wa.me/5593000000000')
    expect(
      contactHref({
        channel_type: 'website',
        public_value: 'javascript:alert(1)',
      }),
    ).toBeNull()
    expect(
      contactHref({ channel_type: 'phone', public_value: '93 9999-0000' }),
    ).toBeNull()
  })

  it('builds directions only from valid public coordinates', () => {
    expect(
      directionsHref({
        address_fields: {},
        is_primary: true,
        label: 'Praia',
        operating_hours: [],
        point: { coordinates: [-54.97478, -2.55997], type: 'Point' },
        updated_at: '2026-07-29T12:00:00Z',
      }),
    ).toContain('destination=-2.55997,-54.97478')
  })

  it('renders only allowlisted public address fields', () => {
    expect(
      formatPublicAddress({
        city: 'Belterra',
        private_note: 'não exibir',
        state: 'PA',
      }),
    ).toBe('Belterra, PA')
  })
})

describe('published route map points', () => {
  const catalog = [
    {
      actor: {
        actor_kind: 'business',
        category_name: 'Alimentação',
        category_slug: 'alimentacao',
        contact_channels: [],
        id: 'actor-1',
        locations: [
          {
            address_fields: { city: 'Belterra', state: 'PA' },
            is_primary: true,
            label: 'Sede',
            operating_hours: [],
            point: { coordinates: [-54.978, -2.558], type: 'Point' },
            updated_at: '2026-07-31T12:00:00Z',
          },
        ],
        partnership_type: 'editorial',
        public_name: 'Cozinha do Tapajós',
        short_description: 'Comida regional.',
        slug: 'cozinha-do-tapajos',
        updated_at: '2026-07-31T12:00:00Z',
      },
      editorial_position: 1,
      is_featured: false,
      route_role: 'service',
      sponsorship_label: '',
      stage_id: null,
    },
    {
      actor: {
        actor_kind: 'support',
        category_name: 'Apoio',
        category_slug: 'apoio',
        contact_channels: [],
        id: 'actor-without-point',
        locations: [],
        partnership_type: 'editorial',
        public_name: 'Apoio sem localização',
        short_description: 'Não deve virar pin.',
        slug: 'apoio-sem-localizacao',
        updated_at: '2026-07-31T12:00:00Z',
      },
      editorial_position: 2,
      is_featured: false,
      route_role: 'support',
      sponsorship_label: '',
      stage_id: null,
    },
  ] satisfies RouteCatalogItem[]

  it('derives pins only from actors with valid public locations', () => {
    const points = getRouteMapPoints(catalog)

    expect(points).toHaveLength(1)
    expect(points[0]).toMatchObject({
      address: 'Belterra, PA',
      categorySlug: 'alimentacao',
      coordinates: [-54.978, -2.558],
      name: 'Cozinha do Tapajós',
    })
  })

  it('uses the same category filter for map and textual list', () => {
    const points = getRouteMapPoints(catalog)

    expect(filterRouteMapPoints(points, 'alimentacao')).toHaveLength(1)
    expect(filterRouteMapPoints(points, 'apoio')).toHaveLength(0)
    expect(filterRouteMapPoints(points, '')).toEqual(points)
  })
})

describe('route overview preparation and timeline', () => {
  it('separates critical alerts from non-critical warning alerts', () => {
    const alerts = [
      {
        id: '1',
        severity: 'critical' as const,
        title: 'Trilha bloqueada',
        description: '',
        alternative: '',
      },
      {
        id: '2',
        severity: 'warning' as const,
        title: 'Marea alta',
        description: '',
        alternative: '',
      },
      {
        id: '3',
        severity: 'info' as const,
        title: 'Horário de funcionamento',
        description: '',
        alternative: '',
      },
    ]

    const critical = alerts.filter((a) => a.severity === 'critical')
    const nonCritical = alerts.filter((a) => a.severity !== 'critical')

    expect(critical).toHaveLength(1)
    expect(nonCritical).toHaveLength(2)
  })
})
