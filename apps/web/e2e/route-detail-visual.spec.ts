import { expect, test } from '@playwright/test'

const routeDetail = {
  accessibility_content:
    'Alguns trechos exigem apoio. Confirme as condições antes da visita.',
  alerts: [
    {
      alternative: 'Consulte a equipe local antes de iniciar.',
      description: 'O acesso depende das condições verificadas no território.',
      ends_at: '2030-01-01T00:00:00Z',
      id: 'alert-critical',
      severity: 'critical',
      starts_at: '2026-01-01T00:00:00Z',
      title: 'Acesso sujeito a confirmação',
      updated_at: '2026-07-31T12:00:00Z',
    },
    {
      alternative: '',
      description: 'Leve água e proteção para mudanças de tempo.',
      ends_at: '2030-01-01T00:00:00Z',
      id: 'alert-warning',
      severity: 'warning',
      starts_at: '2026-01-01T00:00:00Z',
      title: 'Prepare-se para o clima',
      updated_at: '2026-07-31T12:00:00Z',
    },
  ],
  description:
    'Uma rota publicada com conteúdo longo para verificar leitura, densidade e recomposição sem depender de fotografias não aprovadas.',
  difficulty: 'moderate',
  duration_minutes: 330,
  estimated_cost_max: null,
  estimated_cost_min: null,
  id: 'route-visual',
  offline_enabled: true,
  preparation_content:
    'Planeje o deslocamento, leve água, proteção solar e confirme os horários diretamente com as referências publicadas.',
  public_name: 'Caminho publicado entre águas, floresta e comunidades',
  region_name: 'Território das Águas e Florestas',
  region_slug: 'territorio-publicado',
  segments: [],
  short_promise:
    'Uma jornada cuidadosa por paisagens, saberes e encontros do território.',
  slug: 'caminho-publicado',
  stages: [
    {
      arrival_guidance: 'Confirme o ponto de encontro antes de sair.',
      description: 'Acolhimento e orientação para a experiência.',
      duration_minutes: 30,
      id: 'stage-1',
      is_optional: false,
      point: { coordinates: [-54.97, -2.55], type: 'Point' },
      position: 1,
      public_name: 'Chegada e orientação local',
      stage_type: 'start',
      updated_at: '2026-07-31T12:00:00Z',
    },
    {
      arrival_guidance: 'Siga somente pelas orientações publicadas.',
      description: 'Trecho principal da experiência no território.',
      duration_minutes: 180,
      id: 'stage-2',
      is_optional: false,
      point: { coordinates: [-54.96, -2.56], type: 'Point' },
      position: 2,
      public_name: 'Vivência no território',
      stage_type: 'experience',
      updated_at: '2026-07-31T12:00:00Z',
    },
  ],
  transport_modes: ['walk'],
  updated_at: '2026-07-31T12:00:00Z',
}

const viewports = [
  { height: 568, name: '320x568', width: 320 },
  { height: 844, name: '390x844', width: 390 },
  { height: 932, name: '430x932', width: 430 },
  { height: 1024, name: 'tablet-768', width: 768 },
  { height: 800, name: '1280', width: 1280 },
  { height: 900, name: '1440', width: 1440 },
  { height: 1080, name: '1920', width: 1920 },
  { height: 1440, name: '2560', width: 2560 },
]

test('recompõe o detalhe longo sem hero editorial em claro e escuro', async ({
  page,
}) => {
  const consoleErrors: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text())
  })
  await page.route(
    '**/api/public/regions/territorio-publicado/routes/caminho-publicado',
    (route) =>
      route.fulfill({
        body: JSON.stringify(routeDetail),
        contentType: 'application/json',
      }),
  )

  await page.goto('/territorio-publicado/rotas/caminho-publicado')
  await expect(
    page.getByRole('heading', { name: routeDetail.short_promise }),
  ).toBeVisible()
  await expect(page.getByText('Consulte localmente')).toBeVisible()
  await expect(page.locator('.route-critical-summary')).toContainText(
    'Acesso sujeito a confirmação',
  )
  await expect(
    page.getByRole('link', { name: 'Iniciar rota' }),
  ).toHaveAttribute(
    'href',
    '/territorio-publicado/rotas/caminho-publicado/mapa',
  )

  for (const theme of ['light', 'dark'] as const) {
    if (theme === 'dark') {
      await page
        .getByRole('button', {
          name: 'Tema atual: claro. Ativar tema escuro.',
        })
        .click()
    }

    for (const viewport of viewports) {
      await page.setViewportSize(viewport)
      expect(
        await page.evaluate(
          () => document.body.scrollWidth <= document.body.clientWidth + 1,
        ),
      ).toBe(true)
      expect(
        await page.evaluate(
          () =>
            document.querySelector(
              '[data-nextjs-dialog], .vite-error-overlay, #webpack-dev-server-client-overlay',
            ) === null,
        ),
      ).toBe(true)

      if (process.env.CAPTURE_VISUAL_EVIDENCE === 'true') {
        await page.screenshot({
          fullPage: true,
          path: `../../docs/visual-evidence/detail-${theme}-${viewport.name}.png`,
        })
      }
    }
  }

  await page.setViewportSize({ height: 844, width: 390 })
  const devtools = await page.context().newCDPSession(page)
  await devtools.send('Emulation.setPageScaleFactor', { pageScaleFactor: 2 })
  await expect(page.getByRole('link', { name: 'Iniciar rota' })).toBeVisible()
  await expect(
    page.getByRole('button', { exact: true, name: 'Favoritar rota' }),
  ).toBeVisible()
  await devtools.send('Emulation.setPageScaleFactor', { pageScaleFactor: 1 })

  expect(consoleErrors).toEqual([])
})

test('captura o detalhe com conteúdo publicado pela API local', async ({
  page,
}) => {
  test.skip(
    process.env.CAPTURE_REAL_VISUAL_EVIDENCE !== 'true',
    'Executado somente com a API editorial local disponível.',
  )

  await page.setViewportSize({ height: 844, width: 390 })
  await page.goto('/santarem-alter-do-chao/rotas/pindobal')
  await expect(page.locator('.route-experience')).toBeVisible()
  await expect(page.locator('.route-facts')).toBeVisible()
  await page.screenshot({
    fullPage: true,
    path: '../../docs/visual-evidence/detail-real-light-390x844.png',
  })

  await page.setViewportSize({ height: 900, width: 1440 })
  await page
    .getByRole('button', {
      name: 'Tema atual: claro. Ativar tema escuro.',
    })
    .click()
  await page.screenshot({
    fullPage: true,
    path: '../../docs/visual-evidence/detail-real-dark-1440.png',
  })

  await page.setViewportSize({ height: 844, width: 390 })
  await page.screenshot({
    fullPage: true,
    path: '../../docs/visual-evidence/detail-real-dark-390x844.png',
  })
})
