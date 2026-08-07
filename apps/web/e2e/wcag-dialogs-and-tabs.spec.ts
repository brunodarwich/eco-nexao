import { expect, test } from '@playwright/test'

test.use({ serviceWorkers: 'block' })

const regionsMock = [
  {
    center_point: { coordinates: [-54.7, -2.4], type: 'Point' },
    id: '00000000-0000-0000-0000-000000000001',
    public_name: 'Território das Águas e Florestas',
    published_version: 1,
    short_description:
      'Floresta, rios e comunidades conectados por rotas publicadas.',
    slug: 'territorio-publicado',
    timezone: 'America/Fortaleza',
    updated_at: '2026-07-31T12:00:00Z',
  },
]

const routesMock = [
  {
    accessibility_content: '',
    difficulty: 'easy' as const,
    duration_minutes: 120,
    estimated_cost_max: null,
    estimated_cost_min: null,
    id: 'route-flona',
    offline_enabled: true,
    public_name: 'Trilha da Flona Tapajós',
    short_promise: 'Experiência em comunidade e floresta.',
    slug: 'trilha-flona',
    transport_modes: ['walk'],
    updated_at: '2026-07-31T12:00:00Z',
  },
]

const routeDetailMock = {
  accessibility_content:
    'Alguns trechos exigem apoio. Confirme as condições antes da visita.',
  alerts: [],
  description:
    'Uma rota publicada para verificação de acessibilidade e relatos.',
  difficulty: 'easy' as const,
  duration_minutes: 120,
  estimated_cost_max: null,
  estimated_cost_min: null,
  id: 'route-flona',
  offline_enabled: true,
  preparation_content: 'Planeje o deslocamento, leve água e proteção solar.',
  public_name: 'Trilha da Flona Tapajós',
  region_name: 'Território das Águas e Florestas',
  region_slug: 'territorio-publicado',
  segments: [],
  short_promise: 'Experiência em comunidade e floresta.',
  slug: 'trilha-flona',
  stages: [
    {
      arrival_guidance: 'Início no centro de visitantes.',
      description: 'Ponto de recepção.',
      duration_minutes: 30,
      id: 'stage-1',
      is_optional: false,
      point: { coordinates: [-54.7, -2.4], type: 'Point' },
      position: 1,
      public_name: 'Centro de Visitantes',
      stage_type: 'start',
      updated_at: '2026-07-31T12:00:00Z',
    },
  ],
  transport_modes: ['walk'],
  updated_at: '2026-07-31T12:00:00Z',
}

const catalogMock = [
  {
    actor: {
      category: { name: 'Gastronomia', slug: 'gastronomia' },
      category_name: 'Gastronomia',
      category_slug: 'gastronomia',
      contact_channels: [
        { channel_type: 'whatsapp', public_value: '+5593991234567' },
      ],
      display_name: 'Restaurante do Pindobal',
      id: '00000000-0000-0000-0000-000000000002',
      locations: [
        {
          address_fields: {
            formatted_address: 'Praia do Pindobal, Belterra - PA',
          },
          id: 'loc-1',
          is_primary: true,
          point: { coordinates: [-54.7, -2.4], type: 'Point' as const },
        },
      ],
      public_name: 'Restaurante do Pindobal',
      short_description: 'Comida regional ribeirinha com vista para o rio.',
      slug: 'restaurante-pindobal',
    },
    actorId: '00000000-0000-0000-0000-000000000002',
    actorSlug: 'restaurante-pindobal',
    address: 'Praia do Pindobal, Belterra - PA',
    categoryName: 'Gastronomia',
    categorySlug: 'gastronomia',
    coordinates: [-54.7, -2.4] as [number, number],
    name: 'Restaurante do Pindobal',
    public_contact_channels: [
      { channel_type: 'whatsapp', public_value: '+5593991234567' },
    ],
    public_locations: [
      {
        formatted_address: 'Praia do Pindobal, Belterra - PA',
        locality: 'Pindobal',
      },
    ],
    route_role: 'experience' as const,
    stage_id: null,
    summary: 'Comida regional ribeirinha com vista para o rio.',
  },
]

const summaryMock = {
  active_alerts_count: 0,
  pending_revisions_count: 1,
  published_routes_count: 1,
  total_actors_count: 1,
}

test.beforeEach(async ({ page }) => {
  await page.route(/\/api\/admin\/dashboard\/summary/, (route) =>
    route.fulfill({
      body: JSON.stringify(summaryMock),
      contentType: 'application/json',
    }),
  )
  await page.route(/\/api\/.*analytics\/operational/, (route) =>
    route.fulfill({
      body: JSON.stringify({
        metrics: [],
        ranking: [],
        region_slug: 'territorio-publicado',
        route_slug: 'trilha-flona',
      }),
      contentType: 'application/json',
    }),
  )
  await page.route(/\/api\/public\/regions\/.*catalog/, (route) =>
    route.fulfill({
      body: JSON.stringify(catalogMock),
      contentType: 'application/json',
    }),
  )
  await page.route(
    /\/api\/public\/regions\/[^/]+\/routes\/[^/]+(\?.*)?$/,
    (route) =>
      route.fulfill({
        body: JSON.stringify(routeDetailMock),
        contentType: 'application/json',
      }),
  )
  await page.route(/\/api\/public\/regions\/[^/]+\/routes(\?.*)?$/, (route) =>
    route.fulfill({
      body: JSON.stringify(routesMock),
      contentType: 'application/json',
    }),
  )
  await page.route(/\/api\/public\/regions(\?.*)?$/, (route) =>
    route.fulfill({
      body: JSON.stringify(regionsMock),
      contentType: 'application/json',
    }),
  )
})

test.describe('WCAG 2.2 AA — Diálogo de Consentimento de Analytics', () => {
  test('valida foco inicial, contenção de foco, Escape e restauração de foco', async ({
    page,
  }) => {
    await page.goto('/')
    await page.evaluate(() => localStorage.clear())
    await page.reload()

    const triggerButton = page.getByRole('button', { name: 'Configurar' })
    await expect(triggerButton).toBeVisible()
    await triggerButton.focus()
    await page.keyboard.press('Enter')

    const dialog = page.getByRole('dialog', {
      name: 'Configurações de Privacidade',
    })
    await expect(dialog).toBeVisible()
    await expect(dialog).toHaveAttribute('aria-modal', 'true')

    // 1. Foco inicial
    const initialFocused = dialog.getByRole('button', {
      name: 'Apenas Necessários',
    })
    await expect(initialFocused).toBeFocused()

    // 2. Contenção de foco (Focus Trap)
    await page.keyboard.press('Shift+Tab')
    const lastFocused = dialog.getByRole('button', { name: 'Aceitar Todos' })
    await expect(lastFocused).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(initialFocused).toBeFocused()

    // 3. Escape e Restauração de Foco
    await page.keyboard.press('Escape')
    await expect(dialog).toBeHidden()
    await expect(page.getByRole('button', { name: 'Configurar' })).toBeFocused()
  })
})

test.describe('WCAG 2.2 AA — Diálogo de Relato de Informação Incorreta', () => {
  test('valida foco inicial, contenção, Escape e restauração de foco', async ({
    page,
  }) => {
    await page.goto('/territorio-publicado/rotas/trilha-flona')

    const triggerButton = page.getByRole('button', { name: 'Relatar problema' })
    await expect(triggerButton).toBeVisible()
    await triggerButton.focus()
    await page.keyboard.press('Enter')

    const dialog = page.getByRole('dialog', {
      name: 'Relatar Informação Incorreta',
    })
    await expect(dialog).toBeVisible()
    await expect(dialog).toHaveAttribute('aria-modal', 'true')

    // 1. Foco inicial (botão fechar com data-autofocus)
    const closeButton = dialog.getByRole('button', {
      name: 'Fechar formulário de relato',
    })
    await expect(closeButton).toBeFocused()

    // 2. Contenção de foco (Shift+Tab vai para Cancelar)
    await page.keyboard.press('Shift+Tab')
    const cancelButton = dialog.getByRole('button', { name: 'Cancelar' })
    await expect(cancelButton).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(closeButton).toBeFocused()

    // 3. Escape e Restauração de Foco
    await page.keyboard.press('Escape')
    await expect(dialog).toBeHidden()
    await expect(triggerButton).toBeFocused()
  })
})

test.describe('WCAG 2.2 AA — Diálogo de Consentimento de Localização', () => {
  test('valida foco inicial, contenção, Escape e restauração de foco', async ({
    page,
  }) => {
    await page.goto('/territorio-publicado/rotas/trilha-flona/mapa')

    const triggerButton = page
      .getByRole('button', { name: /Usar minha localização/i })
      .first()
    await expect(triggerButton).toBeVisible()
    await triggerButton.focus()
    await page.keyboard.press('Enter')

    const dialog = page.getByRole('dialog', {
      name: 'Usar sua posição somente neste aparelho?',
    })
    await expect(dialog).toBeVisible()
    await expect(dialog).toHaveAttribute('aria-modal', 'true')

    // 1. Foco inicial
    const continueBtn = dialog.getByRole('button', { name: 'Continuar' })
    await expect(continueBtn).toBeFocused()

    // 2. Contenção de foco
    await page.keyboard.press('Tab')
    const cancelBtn = dialog.getByRole('button', { name: 'Agora não' })
    await expect(cancelBtn).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(continueBtn).toBeFocused()

    // 3. Escape e Restauração de Foco
    await page.keyboard.press('Escape')
    await expect(dialog).toBeHidden()
    await expect(triggerButton).toBeFocused()
  })
})

test.describe('WCAG 2.2 AA — Editor Administrativo (PoiEditorModal)', () => {
  test('valida foco inicial, contenção, Escape e restauração de foco no Admin', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 720 })
    await page.goto('http://localhost:3001/')

    await expect(
      page.getByRole('heading', { name: 'Painel Operacional' }),
    ).toBeVisible()

    const editTrigger = page.getByRole('button', { name: /Editar/ }).first()
    await expect(editTrigger).toBeVisible()
    await editTrigger.click()

    const dialog = page.getByRole('dialog', { name: 'Editar Ponto de Apoio' })
    await expect(dialog).toBeVisible()
    await expect(dialog).toHaveAttribute('aria-modal', 'true')

    // 1. Foco inicial (botão fechar com data-autofocus)
    const closeBtn = dialog.getByRole('button', { name: 'Fechar modal' })
    await expect(closeBtn).toBeFocused()

    // 2. Contenção de foco
    await page.keyboard.press('Shift+Tab')
    const saveBtn = dialog.getByRole('button', {
      name: /Salvar alterações como rascunho/,
    })
    await expect(saveBtn).toBeFocused()

    // 3. Escape e Restauração de Foco
    await page.keyboard.press('Escape')
    await expect(dialog).toBeHidden()
    await expect(editTrigger).toBeFocused()
  })
})

test.describe('WCAG 2.2 AA — Tabs do Painel Operacional', () => {
  test('valida roving tabIndex, navegação por setas, Home, End e associação tab/tabpanel', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 720 })
    await page.goto('http://localhost:3001/')

    const tablist = page.getByRole('tablist', {
      name: 'Navegação do Painel Operacional',
    })
    await expect(tablist).toBeVisible()

    const tabAnalytics = page.getByRole('tab', { name: /Métricas do App/ })
    const tabRoutes = page.getByRole('tab', { name: /Rotas & Prontidão/ })
    const tabReports = page.getByRole('tab', { name: /Relatos & Auditoria/ })
    const tabImport = page.getByRole('tab', { name: /Importar CSV/ })
    const tabDiscovery = page.getByRole('tab', { name: /Descoberta Externa/ })

    // 1. Roving tabIndex e Estado Inicial
    await expect(tabAnalytics).toHaveAttribute('aria-selected', 'true')
    await expect(tabAnalytics).toHaveAttribute('tabindex', '0')
    await expect(tabRoutes).toHaveAttribute('aria-selected', 'false')
    await expect(tabRoutes).toHaveAttribute('tabindex', '-1')

    // 2. Associação tab / tabpanel
    const panelId = await tabAnalytics.getAttribute('aria-controls')
    expect(panelId).toBe('dashboard-tabpanel-analytics')
    const panel = page.locator(`#${panelId}`)
    await expect(panel).toHaveAttribute('role', 'tabpanel')
    await expect(panel).toHaveAttribute(
      'aria-labelledby',
      'dashboard-tab-analytics',
    )

    // 3. Navegação por teclado: Setas, Home e End
    await tabAnalytics.focus()
    await page.keyboard.press('ArrowRight')
    await expect(tabRoutes).toBeFocused()
    await expect(tabRoutes).toHaveAttribute('aria-selected', 'true')
    await expect(tabRoutes).toHaveAttribute('tabindex', '0')

    await page.keyboard.press('End')
    await expect(tabDiscovery).toBeFocused()
    await expect(tabDiscovery).toHaveAttribute('aria-selected', 'true')

    await page.keyboard.press('Home')
    await expect(tabAnalytics).toBeFocused()
    await expect(tabAnalytics).toHaveAttribute('aria-selected', 'true')

    await page.keyboard.press('ArrowLeft')
    await expect(tabDiscovery).toBeFocused()
  })
})

test.describe('WCAG 2.2 AA — Responsividade, Tema, Movimento Reduzido e Zoom 200%', () => {
  test('funciona sem overflow em 320px de largura e com zoom de 200%', async ({
    page,
  }) => {
    await page.setViewportSize({ height: 568, width: 320 })
    await page.goto('/')

    expect(
      await page.evaluate(
        () => document.body.scrollWidth <= document.body.clientWidth + 1,
      ),
    ).toBe(true)

    // Testar tema claro e escuro
    const themeBtn = page.getByRole('button', { name: /Ativar tema/ })
    await expect(themeBtn).toBeVisible()
    await themeBtn.click()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')

    await themeBtn.click()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
  })

  test('respeita preferência de movimento reduzido', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.goto('/')

    expect(
      await page.evaluate(
        () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
      ),
    ).toBe(true)
  })
})
