import { expect, test } from '@playwright/test'

const regions = [
  {
    center_point: { coordinates: [-54.7, -2.4], type: 'Point' },
    id: 'region-1',
    public_name: 'Tapajós',
    published_version: 1,
    short_description: 'Floresta, rios e comunidades.',
    slug: 'tapajos',
    timezone: 'America/Fortaleza',
    updated_at: '2026-07-29T12:00:00Z',
  },
]

const routes = [
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

const routeDetail = {
  ...routes[1],
  offline_enabled: true,
  alerts: [
    {
      description: 'Dados ainda precisam de confirmação humana.',
      ends_at: '2030-01-01T00:00:00Z',
      id: 'alert-1',
      severity: 'warning',
      starts_at: '2026-01-01T00:00:00Z',
      title: 'Informações demonstrativas',
      updated_at: '2026-07-29T12:00:00Z',
    },
  ],
  description: 'Trilha publicada para demonstração.',
  preparation_content: 'Leve água e confirme as condições locais.',
  region_name: 'Tapajós',
  region_slug: 'tapajos',
  segments: [
    {
      distance_meters: 1000,
      duration_minutes: 20,
      from_stage_id: 'stage-1',
      geometry: {
        coordinates: [
          [-54.97478, -2.55997],
          [-54.96111, -2.55833],
        ],
        type: 'LineString',
      },
      id: 'segment-1',
      instructions: 'Trecho demonstrativo.',
      to_stage_id: 'stage-2',
      transport_mode: 'walk',
      updated_at: '2026-07-29T12:00:00Z',
    },
  ],
  stages: [
    {
      arrival_guidance: 'Confirme a orientação local.',
      description: 'Ponto inicial demonstrativo.',
      duration_minutes: 20,
      id: 'stage-1',
      is_optional: false,
      point: { coordinates: [-54.97478, -2.55997], type: 'Point' },
      position: 1,
      public_name: 'Chegada e orientação',
      stage_type: 'start',
      updated_at: '2026-07-29T12:00:00Z',
    },
    {
      arrival_guidance: 'Siga somente após confirmar as condições.',
      description: 'Área final demonstrativa.',
      duration_minutes: 180,
      id: 'stage-2',
      is_optional: false,
      point: { coordinates: [-54.96111, -2.55833], type: 'Point' },
      position: 2,
      public_name: 'Praia de Pindobal',
      stage_type: 'experience',
      updated_at: '2026-07-29T12:00:00Z',
    },
  ],
}

const catalog = [
  {
    actor: {
      actor_kind: 'support',
      category_name: 'Apoio',
      category_slug: 'apoio',
      contact_channels: [
        {
          channel_type: 'website',
          public_value: 'https://example.com/econexao-apoio',
        },
      ],
      full_description: 'Referência fictícia para testar o detalhe.',
      id: 'actor-1',
      locations: [
        {
          address_fields: {
            city: 'Belterra',
            neighborhood: 'Pindobal',
            state: 'PA',
          },
          is_primary: true,
          label: 'Local demonstrativo',
          operating_hours: [],
          point: { coordinates: [-54.97478, -2.55997], type: 'Point' },
          updated_at: '2026-07-29T12:00:00Z',
        },
      ],
      partnership_type: 'editorial',
      public_name: 'Ponto de apoio demonstrativo',
      services: ['orientação'],
      short_description: 'Referência fictícia de apoio.',
      slug: 'ponto-de-apoio-demonstrativo',
      updated_at: '2026-07-29T12:00:00Z',
    },
    editorial_position: 1,
    is_featured: true,
    route_role: 'support',
    sponsorship_label: '',
    stage_id: 'stage-1',
  },
]

test('seleciona região, filtra rotas e abre uma URL compartilhável', async ({
  page,
}, testInfo) => {
  test.setTimeout(120_000)
  await page.route('**/api/public/regions', (route) =>
    route.fulfill({
      body: JSON.stringify(regions),
      contentType: 'application/json',
    }),
  )
  await page.route('**/api/public/regions/tapajos/routes', (route) =>
    route.fulfill({
      body: JSON.stringify(routes),
      contentType: 'application/json',
    }),
  )
  await page.route(
    '**/api/public/regions/tapajos/routes/trilha-da-mata',
    (route) =>
      route.fulfill({
        body: JSON.stringify(routeDetail),
        contentType: 'application/json',
      }),
  )
  await page.route(
    '**/api/public/regions/tapajos/routes/trilha-da-mata/catalog',
    (route) =>
      route.fulfill({
        body: JSON.stringify(catalog),
        contentType: 'application/json',
      }),
  )
  await page.route('https://demotiles.maplibre.org/style.json', (route) =>
    route.fulfill({
      body: JSON.stringify({ layers: [], sources: {}, version: 8 }),
      contentType: 'application/json',
    }),
  )

  await page.emulateMedia({ colorScheme: 'light' })
  await page.goto('/')
  await page.getByRole('button', { name: 'Usar apenas necessários' }).click()
  await page
    .getByRole('button', {
      name: 'Tema atual: claro. Ativar tema escuro.',
    })
    .click()
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
  await page.getByRole('link', { name: 'Explorar esta região' }).click()

  await expect(page).toHaveURL(/\/tapajos\/rotas$/)
  await expect(
    page.getByRole('heading', { name: 'Explore o território' }),
  ).toBeVisible()
  await expect(page.locator('.region-context-chip')).toContainText('Tapajós')
  const discoveryFavorite = page.getByRole('button', {
    name: 'Favoritar Caminho das águas',
  })
  await discoveryFavorite.click()
  const selectedDiscoveryFavorite = page.getByRole('button', {
    name: 'Remover Caminho das águas dos favoritos',
  })
  await expect(selectedDiscoveryFavorite).toHaveAttribute(
    'aria-pressed',
    'true',
  )
  await selectedDiscoveryFavorite.click()
  if (process.env.CAPTURE_VISUAL_EVIDENCE === 'true') {
    await page.screenshot({
      fullPage: true,
      path: `../../docs/visual-evidence/discovery-${testInfo.project.name}.png`,
    })
  }
  expect(
    await page.evaluate(
      () => document.body.scrollWidth <= document.body.clientWidth + 1,
    ),
  ).toBe(true)

  const filtersToggle = page.getByRole('button', { name: 'Filtros' })
  if (await filtersToggle.isVisible()) await filtersToggle.click()
  await page.getByLabel('Dificuldade').selectOption('hard')
  await expect(page).toHaveURL(/difficulty=hard/)
  await expect(
    page.getByRole('heading', { name: 'Trilha da mata' }),
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Caminho das águas' }),
  ).toHaveCount(0)

  await page
    .getByRole('link', { name: 'Conhecer a rota Trilha da mata' })
    .click()
  await expect(page).toHaveURL(/\/tapajos\/rotas\/trilha-da-mata$/)
  await expect(
    page.getByRole('heading', {
      name: 'Imersão de dia inteiro na floresta.',
    }),
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Faixa de atenção' }),
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Prepare-se para visitar' }),
  ).toBeVisible()
  await expect(
    page.getByRole('link', { name: 'Iniciar rota' }),
  ).toHaveAttribute('href', '/tapajos/rotas/trilha-da-mata/mapa')
  expect(
    await page.evaluate(() => {
      const preparation = document.querySelector('#preparation-title')
      const alerts = document.querySelector('#non-critical-alerts-title')
      return Boolean(
        preparation &&
        alerts &&
        preparation.compareDocumentPosition(alerts) &
          Node.DOCUMENT_POSITION_FOLLOWING,
      )
    }),
  ).toBe(true)
  await page
    .getByRole('button', { exact: true, name: 'Favoritar rota' })
    .click()
  await page.reload()
  await expect(
    page.getByRole('button', {
      exact: true,
      name: 'Remover dos favoritos',
    }),
  ).toBeVisible()

  await page.getByRole('link', { exact: true, name: 'Mapa' }).click()
  await expect(
    page.getByRole('heading', { name: 'Lista equivalente ao mapa' }),
  ).toBeVisible()
  await expect(page.getByText('1 ponto publicado')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Todos 1' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )
  await expect(
    page.getByRole('heading', { name: 'Pontos locais publicados' }),
  ).toBeVisible()
  await expect(page.getByText('Ponto de apoio demonstrativo')).toBeVisible()
  expect(
    await page.evaluate(
      () => document.body.scrollWidth <= document.body.clientWidth + 1,
    ),
  ).toBe(true)
  await page
    .getByRole('button', { exact: true, name: 'Usar minha localização' })
    .click()
  await expect(
    page.getByRole('heading', {
      name: 'Usar sua posição somente neste aparelho?',
    }),
  ).toBeVisible()
  await page.getByRole('button', { name: 'Agora não' }).click()

  await page.getByRole('link', { name: 'Catálogo' }).click()
  await expect(
    page.getByRole('heading', { name: 'Ponto de apoio demonstrativo' }),
  ).toBeVisible()
  await page.getByRole('button', { name: 'Ver detalhes' }).click()
  await expect(page).toHaveURL(/ator=ponto-de-apoio-demonstrativo/)
  await expect(
    page.getByRole('link', { name: 'Visitar site' }),
  ).toHaveAttribute('href', 'https://example.com/econexao-apoio')

  await page.goto('/tapajos/rotas/trilha-da-mata')
  await page.getByRole('button', { name: 'Salvar offline' }).click()
  await expect(
    page.getByText(
      'Inclui resumo, preparação, etapas, alertas e catálogo essencial.',
    ),
  ).toBeVisible()
  await page.getByRole('button', { name: 'Confirmar download' }).click()
  await expect(page.getByText(/Disponível offline/)).toBeVisible({
    timeout: 60_000,
  })
  await expect
    .poll(() =>
      page.evaluate(
        async () =>
          Boolean(navigator.serviceWorker.controller) &&
          Boolean(
            await caches.match(
              '/api/public/regions/tapajos/routes/trilha-da-mata',
            ),
          ),
      ),
    )
    .toBe(true)

  await page.context().setOffline(true)
  await page.goto('/tapajos/rotas/trilha-da-mata')
  await expect(
    page.getByRole('heading', { name: 'Faixa de atenção' }),
  ).toBeVisible()
  await page.goto('/tapajos/rotas/trilha-da-mata/catalogo')
  await expect(
    page.getByRole('heading', { name: 'Ponto de apoio demonstrativo' }),
  ).toBeVisible()
  await page.context().setOffline(false)
})
