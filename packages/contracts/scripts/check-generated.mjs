import { spawnSync } from 'node:child_process'
import { mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'

const root = resolve(import.meta.dirname, '../../..')
const temporaryDirectory = mkdtempSync(join(tmpdir(), 'econexao-contracts-'))
const generatedSchema = join(temporaryDirectory, 'schema.yaml')
const generatedTypes = join(temporaryDirectory, 'api.ts')
const uv = process.platform === 'win32' ? 'uv.exe' : 'uv'
const pnpmExecutable = process.env.npm_execpath ? process.execPath : 'pnpm'
const pnpmPrefix = process.env.npm_execpath ? [process.env.npm_execpath] : []

function run(command, args) {
  const result = spawnSync(command, args, {
    cwd: root,
    encoding: 'utf8',
    stdio: 'pipe',
  })

  if (result.status !== 0) {
    process.stderr.write(result.stdout ?? '')
    process.stderr.write(result.stderr ?? '')
    process.stderr.write(result.error ? `${result.error.message}\n` : '')
    process.exit(result.status ?? 1)
  }
}

function normalized(path) {
  return readFileSync(path, 'utf8').replaceAll('\r\n', '\n')
}

try {
  run(uv, [
    '--cache-dir',
    '.uv-cache',
    'run',
    '--project',
    'services/api',
    'python',
    'services/api/manage.py',
    'spectacular',
    '--file',
    generatedSchema,
    '--validate',
  ])
  run(pnpmExecutable, [
    ...pnpmPrefix,
    'exec',
    'prettier',
    '--config',
    resolve(root, '.prettierrc.json'),
    '--write',
    generatedSchema,
  ])
  run(pnpmExecutable, [
    ...pnpmPrefix,
    '--filter',
    '@econexao/contracts',
    'exec',
    'openapi-typescript',
    generatedSchema,
    '-o',
    generatedTypes,
  ])
  run(pnpmExecutable, [
    ...pnpmPrefix,
    'exec',
    'prettier',
    '--config',
    resolve(root, '.prettierrc.json'),
    '--write',
    generatedTypes,
  ])

  const comparisons = [
    [
      'OpenAPI',
      resolve(root, 'packages/contracts/openapi/schema.yaml'),
      generatedSchema,
    ],
    [
      'tipos TypeScript',
      resolve(root, 'packages/contracts/src/api.ts'),
      generatedTypes,
    ],
  ]
  const stale = comparisons
    .filter(
      ([, expected, generated]) =>
        normalized(expected) !== normalized(generated),
    )
    .map(([label]) => label)

  if (stale.length > 0) {
    process.stderr.write(
      `Contrato desatualizado (${stale.join(', ')}). Execute: pnpm contracts:generate\n`,
    )
    process.exit(1)
  }

  process.stdout.write('OpenAPI e tipos TypeScript estão sincronizados.\n')
} finally {
  rmSync(temporaryDirectory, { recursive: true, force: true })
}
