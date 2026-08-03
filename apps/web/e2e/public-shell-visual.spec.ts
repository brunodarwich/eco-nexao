import { expect, test } from '@playwright/test'

test.use({ serviceWorkers: 'block' })

const regions = [
  {
    center_point: { coordinates: [-54.7, -2.4], type: 'Point' },
    id: 'region-visual',
    public_name: 'Território das Águas e Florestas',
    published_version: 1,
    short_description:
      'Floresta, rios e comunidades conectados por rotas publicadas.',
    slug: 'territorio-publicado',
    timezone: 'America/Fortaleza',
    updated_at: '2026-07-31T12:00:00Z',
  },
]

const routes = Array.from({ length: 8 }, (_, index) => ({
  accessibility_content: '',
  difficulty: (['easy', 'moderate', 'hard'] as const)[index % 3],
  duration_minutes: 90 + index * 30,
  estimated_cost_max: null,
  estimated_cost_min: null,
  id: `route-${index}`,
  offline_enabled: index % 2 === 0,
  public_name:
    index === 0
      ? 'Caminho das águas entre comunidades e floresta'
      : `Rota publicada ${index + 1}`,
  short_promise:
    'Uma experiência publicada para conhecer o território com cuidado.',
  slug: `rota-publicada-${index}`,
  transport_modes: ['walk'],
  updated_at: '2026-07-31T12:00:00Z',
}))

const viewports = [
  { height: 568, name: '320x568', width: 320 },
  { height: 844, name: '390x844', width: 390 },
  { height: 932, name: '430x932', width: 430 },
  { height: 800, name: '1280', width: 1280 },
  { height: 900, name: '1440', width: 1440 },
  { height: 1080, name: '1920', width: 1920 },
  { height: 1440, name: '2560', width: 2560 },
]

test('recompõe descoberta entre mobile e ultrawide sem overflow', async ({
  page,
}) => {
  await page.route('**/api/public/regions', (route) =>
    route.fulfill({
      body: JSON.stringify(regions),
      contentType: 'application/json',
    }),
  )
  await page.route(
    '**/api/public/regions/territorio-publicado/routes',
    (route) =>
      route.fulfill({
        body: JSON.stringify(routes),
        contentType: 'application/json',
      }),
  )

  await page.goto('/territorio-publicado/rotas')
  await expect(
    page.getByRole('heading', { name: 'Explore o território' }),
  ).toBeVisible()

  for (const viewport of viewports) {
    await page.setViewportSize(viewport)
    await expect(page.locator('body')).not.toHaveCSS('overflow-x', 'scroll')
    expect(
      await page.evaluate(
        () => document.body.scrollWidth <= document.body.clientWidth + 1,
      ),
    ).toBe(true)

    if (viewport.width >= 1200) {
      await expect(
        page.getByRole('navigation', { name: 'Navegação pública' }),
      ).toBeVisible()
    } else {
      await expect(
        page.getByRole('navigation', { name: 'Navegação pública' }),
      ).toBeHidden()
    }

    if (process.env.CAPTURE_VISUAL_EVIDENCE === 'true') {
      await page.screenshot({
        fullPage: true,
        path: `../../docs/visual-evidence/discovery-light-${viewport.name}.png`,
      })
    }
  }

  await page
    .getByRole('button', { name: 'Tema atual: claro. Ativar tema escuro.' })
    .click()
  for (const viewport of [viewports[1], viewports[4]]) {
    await page.setViewportSize(viewport)
    if (process.env.CAPTURE_VISUAL_EVIDENCE === 'true') {
      await page.screenshot({
        fullPage: true,
        path: `../../docs/visual-evidence/discovery-dark-${viewport.name}.png`,
      })
    }
  }
})

test('permanece operável por teclado em rede móvel limitada e movimento reduzido', async ({
  page,
}) => {
  await page.emulateMedia({
    colorScheme: 'light',
    forcedColors: 'active',
    reducedMotion: 'reduce',
  })
  await page.route('**/api/public/regions', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1_200))
    await route.fulfill({
      body: JSON.stringify(regions),
      contentType: 'application/json',
    })
  })
  await page.route(
    '**/api/public/regions/territorio-publicado/routes',
    async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1_200))
      await route.fulfill({
        body: JSON.stringify(routes),
        contentType: 'application/json',
      })
    },
  )

  await page.goto('/?trocar=true')
  await expect(
    page.getByRole('heading', { name: 'Carregando regiões' }),
  ).toBeVisible()

  const regionLink = page.getByRole('link', { name: 'Explorar esta região' })
  await expect(regionLink).toBeVisible()
  await regionLink.focus()
  await expect(regionLink).toBeFocused()
  await page.keyboard.press('Enter')

  await expect(page).toHaveURL(/\/territorio-publicado\/rotas$/)
  await expect(
    page.getByRole('heading', { name: 'Explore o território' }),
  ).toBeVisible()
  await expect(page.getByRole('search')).toBeVisible()
  await expect(
    page.getByRole('button', {
      name: 'Favoritar Caminho das águas entre comunidades e floresta',
    }),
  ).toBeVisible()
  expect(
    await page.evaluate(
      () => document.body.scrollWidth <= document.body.clientWidth + 1,
    ),
  ).toBe(true)
  expect(
    await page.evaluate(
      () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    ),
  ).toBe(true)
})
