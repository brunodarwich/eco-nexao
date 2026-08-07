import path from 'path'
import { defineConfig, devices } from '@playwright/test'

const useExternalServer = process.env.PLAYWRIGHT_EXTERNAL_SERVER === 'true'
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3100'

export default defineConfig({
  expect: { timeout: 20_000 },
  testDir: './e2e',
  timeout: 60_000,
  fullyParallel: true,
  retries: 0,
  reporter: 'list',
  use: {
    baseURL,
    channel: 'chrome',
    trace: 'retain-on-failure',
  },
  webServer: useExternalServer
    ? undefined
    : [
        {
          command: 'pnpm exec next build && pnpm exec next start --port 3100',
          env: {
            ...process.env,
            NEXT_DIST_DIR: '.next-e2e',
            NEXT_E2E_BUILD: 'true',
          },
          reuseExistingServer: !process.env.CI,
          timeout: 180_000,
          url: 'http://localhost:3100',
        },
        {
          command:
            'pnpm exec next build --webpack && pnpm exec next start --port 3001',
          cwd: path.resolve(__dirname, '../admin'),
          env: {
            ...process.env,
            NEXT_DIST_DIR: '.next-e2e',
            NEXT_E2E_BUILD: 'true',
          },
          reuseExistingServer: !process.env.CI,
          timeout: 180_000,
          url: 'http://localhost:3001',
        },
      ],
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'mobile-chromium',
      use: { ...devices['Pixel 5'] },
    },
  ],
})
