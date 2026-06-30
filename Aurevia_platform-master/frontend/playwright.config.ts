import { defineConfig, devices } from '@playwright/test'

/**
 * E2E config â€” runs against the already-running Vite dev server on :5173.
 * Start the app first:  npm run dev   (in frontend/)
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never' }]],
  webServer: {
    command: 'node_modules\\.bin\\vite.cmd --host 127.0.0.1',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: true,
    timeout: 30_000,
    env: {
      VITE_DEV_AUTH: 'true',
    },
  },
  use: {
    baseURL: 'http://127.0.0.1:5173',
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})

