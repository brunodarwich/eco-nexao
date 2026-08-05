import assert from 'node:assert/strict'
import { randomUUID } from 'node:crypto'
import { spawn, spawnSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '../..')
const apiUrl = 'http://127.0.0.1:18100'
const webUrl = 'http://127.0.0.1:13100'
const adminUrl = 'http://127.0.0.1:13101'
const pnpm = process.platform === 'win32' ? 'pnpm.cmd' : 'pnpm'
const uv = process.platform === 'win32' ? 'uv.exe' : 'uv'
const processes = []
const logs = new Map()
const analyticsEventIds = []

const apiEnv = {
  ...process.env,
  ANALYTICS_BATCH_RATE: '3/minute',
  DATABASE_ENGINE: 'postgresql',
  DJANGO_ALLOWED_HOSTS: 'localhost,127.0.0.1',
  DJANGO_CSRF_TRUSTED_ORIGINS: adminUrl,
  DJANGO_DEBUG: 'false',
  DJANGO_INTEGRATION_TEST_FAULTS: 'true',
  DJANGO_SECURE_COOKIES: 'false',
  PUBLIC_REPORTS_RATE: '20/minute',
}

function command(
  command,
  args,
  { allowFailure = false, env = process.env } = {},
) {
  const result = spawnSync(command, args, {
    cwd: root,
    encoding: 'utf8',
    env,
    windowsHide: true,
  })
  if (!allowFailure && result.status !== 0)
    throw new Error(
      `${command} ${args.join(' ')} falhou:\n${result.stdout}\n${result.stderr}`,
    )
  return result
}

function start(name, commandName, args, env) {
  const shim = process.platform === 'win32' && commandName.endsWith('.cmd')
  const child = spawn(
    shim ? (process.env.ComSpec ?? 'cmd.exe') : commandName,
    shim ? ['/d', '/s', '/c', commandName, ...args] : args,
    {
      cwd: root,
      env,
      windowsHide: true,
    },
  )
  let output = ''
  child.stdout.on('data', (chunk) => (output += chunk.toString()))
  child.stderr.on('data', (chunk) => (output += chunk.toString()))
  logs.set(name, () =>
    output.slice(-6000).replaceAll(/integration-only-password/gi, '[REDACTED]'),
  )
  processes.push({ child, name })
  return child
}

async function waitFor(url, name, accepted = (status) => status < 500) {
  const deadline = Date.now() + 120_000
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url)
      if (accepted(response.status)) return response
    } catch {}
    await new Promise((resolveWait) => setTimeout(resolveWait, 500))
  }
  throw new Error(`${name} não ficou pronto.\n${logs.get(name)?.() ?? ''}`)
}

function absorbCookies(response, jar) {
  const values =
    response.headers.getSetCookie?.() ??
    [response.headers.get('set-cookie')].filter(Boolean)
  for (const value of values) {
    const [pair] = value.split(';', 1)
    const separator = pair.indexOf('=')
    jar.set(pair.slice(0, separator), pair.slice(separator + 1))
  }
}

const cookieHeader = (jar) =>
  [...jar].map(([name, value]) => `${name}=${value}`).join('; ')

async function json(url, options = {}) {
  const response = await fetch(url, options)
  const payload = await response.json().catch(() => null)
  return { payload, response }
}

async function stopProcess(entry) {
  const { child } = entry
  if (child.exitCode !== null) return
  const exited = new Promise((resolveExit) => child.once('exit', resolveExit))
  if (process.platform === 'win32')
    command('taskkill.exe', ['/pid', String(child.pid), '/t'], {
      allowFailure: true,
    })
  else child.kill('SIGTERM')
  const graceful = await Promise.race([
    exited.then(() => true),
    new Promise((resolveWait) => setTimeout(() => resolveWait(false), 5000)),
  ])
  if (!graceful && child.exitCode === null) {
    if (process.platform === 'win32')
      command('taskkill.exe', ['/pid', String(child.pid), '/t', '/f'], {
        allowFailure: true,
      })
    else child.kill('SIGKILL')
    await Promise.race([
      exited,
      new Promise((resolveWait) => setTimeout(resolveWait, 5000)),
    ])
  }
}

async function login(username) {
  const jar = new Map()
  const csrf = await json(`${adminUrl}/api/admin/auth/csrf`)
  assert.equal(csrf.response.status, 200)
  absorbCookies(csrf.response, jar)
  const headers = {
    'Content-Type': 'application/json',
    Cookie: cookieHeader(jar),
    Origin: adminUrl,
    'X-CSRFToken': csrf.payload.csrf_token,
  }
  const result = await json(`${adminUrl}/api/admin/auth/login`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ username, password: 'integration-only-password' }),
  })
  absorbCookies(result.response, jar)
  return { ...result, csrfToken: csrf.payload.csrf_token, jar }
}

try {
  if (!process.env.TASK_7_4_SUPABASE_PROJECT_REF)
    throw new Error(
      'Defina TASK_7_4_SUPABASE_PROJECT_REF para autorizar explicitamente o projeto Supabase de teste.',
    )
  command(
    uv,
    [
      '--cache-dir',
      '.uv-cache',
      'run',
      '--project',
      'services/api',
      'python',
      'services/api/manage.py',
      'migrate',
      '--noinput',
    ],
    { env: apiEnv },
  )
  command(
    uv,
    [
      '--cache-dir',
      '.uv-cache',
      'run',
      '--project',
      'services/api',
      'python',
      'services/api/manage.py',
      'shell',
      '-c',
      "exec(open('tests/integration/task_7_4_fixtures.py', encoding='utf-8').read())",
    ],
    { env: apiEnv },
  )

  const api = start(
    'api',
    uv,
    [
      '--cache-dir',
      '.uv-cache',
      'run',
      '--project',
      'services/api',
      'python',
      'services/api/manage.py',
      'runserver',
      '127.0.0.1:18100',
      '--noreload',
    ],
    apiEnv,
  )
  start(
    'web',
    pnpm,
    ['--filter', '@econexao/web', 'exec', 'next', 'dev', '--port', '13100'],
    {
      ...process.env,
      NEXT_DIST_DIR: '.next-integration',
      NEXT_PUBLIC_API_URL: `${apiUrl}/api/v1`,
    },
  )
  start(
    'admin',
    pnpm,
    ['--filter', '@econexao/admin', 'exec', 'next', 'dev', '--port', '13101'],
    {
      ...process.env,
      ECONEXAO_API_INTERNAL_URL: `${apiUrl}/api/v1`,
      NEXT_DIST_DIR: '.next-integration',
    },
  )
  await Promise.all([
    waitFor(`${apiUrl}/api/v1/health`, 'api'),
    waitFor(`${webUrl}/api/public/health`, 'web'),
    waitFor(`${adminUrl}/api/admin/auth/session`, 'admin'),
  ])

  let result = await json(`${webUrl}/api/public/regions`)
  assert.equal(result.response.status, 200)
  assert.deepEqual(
    result.payload.map((item) => item.slug),
    ['integration-norte', 'integration-sul'],
  )
  result = await json(`${webUrl}/api/public/regions/integration-norte/routes`)
  assert.equal(result.response.status, 200)
  assert.equal(result.payload[0].slug, 'rota-integrada')

  const invalidCsrf = await fetch(`${adminUrl}/api/admin/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: adminUrl },
    body: '{}',
  })
  assert.equal(invalidCsrf.status, 403)
  const invalidLogin = await login('integration_staff')
  assert.equal(invalidLogin.response.status, 200)
  result = await json(`${adminUrl}/api/admin/reports`, {
    headers: { Cookie: cookieHeader(invalidLogin.jar) },
  })
  assert.equal(result.response.status, 403)

  const admin = await login('integration_admin')
  assert.equal(admin.response.status, 200)
  result = await json(`${adminUrl}/api/admin/auth/session`, {
    headers: { Cookie: cookieHeader(admin.jar) },
  })
  assert.equal(result.payload.authenticated, true)

  const report = await json(`${webUrl}/api/public/public/reports/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      report_type: 'incorrect_information',
      target_type: 'route',
      target_slug: 'rota-integrada',
      region_slug: 'integration-norte',
      description: 'Informação fictícia incorreta para o teste integrado.',
    }),
  })
  assert.equal(report.response.status, 201)
  result = await json(
    `${adminUrl}/api/admin/reports?region_slug=integration-sul`,
    { headers: { Cookie: cookieHeader(admin.jar) } },
  )
  assert.equal(result.response.status, 200)
  assert.equal(result.payload.length, 0)
  result = await json(`${adminUrl}/api/admin/reports/${report.payload.id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Cookie: cookieHeader(admin.jar),
      Origin: adminUrl,
      'X-CSRFToken': admin.csrfToken,
    },
    body: JSON.stringify({
      status: 'reviewed',
      moderation_note: 'Validado no teste integrado.',
    }),
  })
  assert.equal(result.response.status, 200)
  assert.equal(result.payload.status, 'reviewed')

  for (let attempt = 1; attempt <= 4; attempt += 1) {
    const eventId = randomUUID()
    analyticsEventIds.push(eventId)
    const analytics = await fetch(`${webUrl}/api/public/events/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        consent_granted: true,
        events: [
          {
            event_id: eventId,
            event_name: 'app_opened',
            occurred_at: new Date().toISOString(),
            properties: { entry_type: 'direct' },
          },
        ],
      }),
    })
    assert.equal(analytics.status, attempt <= 3 ? 201 : 429)
  }

  const csv = readFileSync(resolve(root, 'spec/schemas/catalogo-template.csv'))
  const validateForm = new FormData()
  validateForm.set('file', new Blob([csv], { type: 'text/csv' }), 'catalog.csv')
  result = await json(`${adminUrl}/api/admin/imports/validate`, {
    method: 'POST',
    headers: {
      Cookie: cookieHeader(admin.jar),
      Origin: adminUrl,
      'X-CSRFToken': admin.csrfToken,
    },
    body: validateForm,
  })
  assert.equal(result.response.status, 200)
  assert.equal(
    result.payload.valid,
    false,
    'template fora do escopo regional deve ser rejeitado sem persistência',
  )

  const categories = command(
    uv,
    [
      '--cache-dir',
      '.uv-cache',
      'run',
      '--project',
      'services/api',
      'python',
      'services/api/manage.py',
      'shell',
      '-c',
      "from modules.catalog.models import Category; from modules.routes.models import Route; print(Category.objects.get(slug='apoio-integrado').id, Route.objects.get(region__slug='integration-norte').id)",
    ],
    { env: apiEnv },
  )
    .stdout.trim()
    .split(/\s+/)
  const support = await json(`${adminUrl}/api/admin/catalog/support-points`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Cookie: cookieHeader(admin.jar),
      Origin: adminUrl,
      'X-CSRFToken': admin.csrfToken,
      'Idempotency-Key': randomUUID(),
    },
    body: JSON.stringify({
      actor: {
        category_id: categories.at(-2),
        public_name: 'Apoio HTTP Integrado',
        short_description: 'Ponto fictício criado pelo teste integrado.',
        services: ['água'],
      },
      location: {
        label: 'Principal',
        address_fields: { locality: 'Cidade de teste', country_code: 'BR' },
        latitude: -2.41,
        longitude: -54.69,
        public_visibility: true,
      },
      contacts: [],
      route_links: [
        {
          route_id: categories.at(-1),
          stage_id: null,
          route_role: 'support',
          editorial_position: 1,
          is_featured: false,
          sponsorship_label: '',
        },
      ],
    }),
  })
  assert.equal(support.response.status, 201)

  const upstream500 = await fetch(`${webUrl}/api/public/regions`, {
    headers: { 'X-Integration-Fault': 'database_500' },
  })
  assert.equal(upstream500.status, 500)
  const recovered = await waitFor(
    `${webUrl}/api/public/regions`,
    'recuperação da API',
    (status) => status === 200,
  )
  assert.equal(recovered.status, 200)
  await stopProcess({ child: api, name: 'api' })
  result = await json(`${adminUrl}/api/admin/auth/session`)
  assert.equal(result.response.status, 502)

  console.log(
    'task 7.4 aprovada: PostGIS + API + web + admin separados; HTTP real, auth, CSRF, escopo, relatos, moderação, analytics, CSV, cadastro, 401/403/429/500/502 e recuperação.',
  )
} catch (error) {
  for (const [name, readLog] of logs)
    console.error(`\n--- ${name} (sanitizado) ---\n${readLog()}`)
  throw error
} finally {
  for (const entry of processes.reverse()) await stopProcess(entry)
  command(
    uv,
    [
      '--cache-dir',
      '.uv-cache',
      'run',
      '--project',
      'services/api',
      'python',
      'services/api/manage.py',
      'shell',
      '-c',
      "exec(open('tests/integration/task_7_4_cleanup.py', encoding='utf-8').read())",
    ],
    {
      allowFailure: true,
      env: { ...apiEnv, TASK_7_4_EVENT_IDS: analyticsEventIds.join(',') },
    },
  )
}
