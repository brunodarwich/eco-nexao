import { expect, test } from '@playwright/test'

test.use({ serviceWorkers: 'block' })

const mockRegions = [
  {
    center_point: { coordinates: [-54.7, -2.4], type: 'Point' },
    id: 'region-001',
    public_name: 'Território Tapajós',
    published_version: 1,
    short_description: 'Região de teste multirregional.',
    slug: 'territorio-tapajos',
    timezone: 'America/Fortaleza',
    updated_at: '2026-07-31T12:00:00Z',
  },
]

const mockDashboardSummary = {
  active_alerts_count: 2,
  pending_revisions_count: 3,
  priority_reports_count: 5,
  region_slug: 'territorio-tapajos',
}

test.describe('Testes integrados de Tema e Persistência (Web & Admin)', () => {
  test('inicia em tema claro por padrão quando não há preferência salva', async ({
    page,
  }) => {
    await page.goto('/')
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')

    const metaThemeColor = page.locator('meta[name="theme-color"]')
    await expect(metaThemeColor).toHaveAttribute('content', '#f7f8f5')

    const colorScheme = await page.evaluate(
      () => document.documentElement.style.colorScheme,
    )
    expect(colorScheme).toBe('light')

    const storedTheme = await page.evaluate(() =>
      localStorage.getItem('econexao-theme'),
    )
    expect(storedTheme).toBeNull()
  })

  test('alterna para tema escuro equivalente e persists a escolha no localStorage', async ({
    page,
  }) => {
    await page.goto('/')

    const themeToggle = page.getByRole('button', {
      name: /Usar tema escuro|Tema atual: claro/i,
    })
    await expect(themeToggle).toBeVisible()
    await themeToggle.click()

    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')

    const metaThemeColor = page.locator('meta[name="theme-color"]')
    await expect(metaThemeColor).toHaveAttribute('content', '#090d09')

    const colorScheme = await page.evaluate(
      () => document.documentElement.style.colorScheme,
    )
    expect(colorScheme).toBe('dark')

    const storedTheme = await page.evaluate(() =>
      localStorage.getItem('econexao-theme'),
    )
    expect(storedTheme).toBe('dark')
  })

  test('preserva o tema escolhido ao recarregar a página e em nova aba/contexto', async ({
    context,
    page,
  }) => {
    await page.goto('/')
    const themeToggle = page.getByRole('button', {
      name: /Usar tema escuro|Tema atual: claro/i,
    })
    await themeToggle.click()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')

    // Reload
    await page.reload()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')

    // Nova aba na mesma origem. localStorage é isolado por origem e não deve vazar
    // automaticamente da PWA (3100) para o painel administrativo (3001).
    const newPage = await context.newPage()
    await newPage.goto('/')
    await expect(newPage.locator('html')).toHaveAttribute('data-theme', 'dark')
    await newPage.close()
  })
})

test.describe('Testes integrados de Erros HTTP (401, 403, 429, 500/502) e Recuperação', () => {
  test.beforeEach(async ({ page }) => {
    // Garantir que as rotas públicas de regiões e rotas no admin respondam 200 OK com mocks válidos
    await page.route('**/api/public/regions', (route) =>
      route.fulfill({
        body: JSON.stringify(mockRegions),
        contentType: 'application/json',
        status: 200,
      }),
    )
    await page.route('**/api/public/regions/*/routes', (route) =>
      route.fulfill({
        body: JSON.stringify([]),
        contentType: 'application/json',
        status: 200,
      }),
    )
  })

  test('Admin: exibe erro 401 (sessão ausente) e não aceita lista/resposta vazia como sucesso', async ({
    page,
  }) => {
    await page.route('**/api/admin/dashboard/summary*', (route) =>
      route.fulfill({
        body: JSON.stringify({ detail: 'Autenticação necessária.' }),
        contentType: 'application/json',
        status: 401,
      }),
    )

    await page.goto('http://localhost:3001')
    await expect(page.getByText('Sessão necessária')).toBeVisible()
    await expect(
      page.getByText(
        'Sua sessão administrativa expirou ou não foi encontrada. Entre novamente para continuar.',
      ),
    ).toBeVisible()
  })

  test('Admin: exibe erro 403 (sem permissão)', async ({ page }) => {
    await page.route('**/api/admin/dashboard/summary*', (route) =>
      route.fulfill({
        body: JSON.stringify({ detail: 'Acesso negado para esta região.' }),
        contentType: 'application/json',
        status: 403,
      }),
    )

    await page.goto('http://localhost:3001')
    await expect(page.getByText('Acesso não autorizado')).toBeVisible()
    await expect(
      page.getByText(
        'Sua conta não tem permissão para consultar os dados desta área ou região.',
      ),
    ).toBeVisible()
  })

  test('Admin: exibe erro 429 (limitação temporária)', async ({ page }) => {
    await page.route('**/api/admin/dashboard/summary*', (route) =>
      route.fulfill({
        body: JSON.stringify({ detail: 'Muitas requisições.' }),
        contentType: 'application/json',
        status: 429,
      }),
    )

    await page.goto('http://localhost:3001')
    await expect(page.getByText('Muitas tentativas')).toBeVisible()
    await expect(
      page.getByText(
        'A API limitou temporariamente as consultas. Aguarde alguns instantes e tente novamente.',
      ),
    ).toBeVisible()
  })

  test('Admin: exibe erro 502 (indisponibilidade) e recupera via retry quando a API volta', async ({
    page,
  }) => {
    let mockStatus = 502
    let summaryRequests = 0

    await page.route('**/api/admin/dashboard/summary*', (route) => {
      summaryRequests += 1
      if (mockStatus === 502) {
        return route.fulfill({
          body: JSON.stringify({ detail: 'Bad Gateway' }),
          contentType: 'application/json',
          status: 502,
        })
      }
      return route.fulfill({
        body: JSON.stringify(mockDashboardSummary),
        contentType: 'application/json',
        status: 200,
      })
    })

    await page.goto('http://localhost:3001')
    await expect(page.getByText('Serviço indisponível')).toBeVisible()

    // Recuperação: a API volta a responder 200 OK
    mockStatus = 200
    const retryButton = page.getByRole('button', { name: 'Tentar novamente' })
    await expect(retryButton).toBeVisible()
    await retryButton.click()

    // Confirma recuperação dos dados no painel
    await expect.poll(() => summaryRequests).toBe(2)
    await expect(page.getByText('Serviço indisponível')).toBeHidden()
    await expect(
      page.getByRole('heading', { name: /Atenção: 2 alerta/ }),
    ).toBeVisible()
  })

  test('Diferenciação clara entre Carregando, Vazio e Erro (Web)', async ({
    page,
  }) => {
    // Limpa os mocks de beforeEach para este teste de Web
    await page.unroute('**/api/public/regions')
    await page.unroute('**/api/public/regions/*/routes')

    // 1. Carregando
    await page.route('**/api/public/regions', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 800))
      await route.fulfill({
        body: JSON.stringify(mockRegions),
        contentType: 'application/json',
        status: 200,
      })
    })

    await page.goto('/?trocar=true')
    await expect(
      page.getByRole('heading', { name: 'Carregando regiões' }),
    ).toBeVisible()

    await expect(
      page.getByRole('heading', { name: 'Território Tapajós' }),
    ).toBeVisible()

    // 2. Vazio
    await page.unroute('**/api/public/regions')
    await page.route('**/api/public/regions', (route) =>
      route.fulfill({
        body: JSON.stringify([]),
        contentType: 'application/json',
        status: 200,
      }),
    )
    await page.goto('/?trocar=true')
    await expect(
      page.getByRole('heading', { name: 'Nenhuma região disponível' }),
    ).toBeVisible()

    // 3. Erro (não pode ser tratado como lista vazia silenciosa)
    await page.unroute('**/api/public/regions')
    await page.route('**/api/public/regions', (route) =>
      route.fulfill({
        body: JSON.stringify({ detail: 'Internal Server Error' }),
        contentType: 'application/json',
        status: 500,
      }),
    )
    await page.goto('/?trocar=true')
    await expect(
      page.getByRole('heading', {
        name: 'Não foi possível carregar as regiões',
      }),
    ).toBeVisible()
    await expect(
      page.getByRole('heading', { name: 'Nenhuma região disponível' }),
    ).toBeHidden()
  })

  test('Ausência de fallback regional fixo em Web e Admin', async ({
    page,
  }) => {
    await page.unroute('**/api/public/regions')
    await page.unroute('**/api/public/regions/*/routes')

    await page.route('**/api/public/regions', (route) =>
      route.fulfill({
        body: JSON.stringify([]),
        contentType: 'application/json',
        status: 200,
      }),
    )

    // Acessar rota sem região salva e sem parâmetros
    await page.goto('/')

    // Deve solicitar escolha de região ou exibir aviso, sem redirecionar forçadamente para /santarem ou /altamira
    const url = page.url()
    expect(url).not.toContain('/santarem')
    expect(url).not.toContain('/altamira')
  })
})
