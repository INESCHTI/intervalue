import { test, expect, type Page } from '@playwright/test'

/**
 * Smoke + content tests for the LaRuche web app.
 * Validates the four screens render and surfaces the data shown in the UI
 * so it can be compared against the canonical demo data.
 */

const consoleErrors: string[] = []

test.beforeEach(async ({ page }) => {
  consoleErrors.length = 0
  await page.route('**/api/mesh/health', route => route.fulfill({
    json: {
      status: 'ok',
      checked_at: new Date().toISOString(),
      services: [
        { id: 'orchestrator', name: 'orchestrator', status: 'ok', latency_ms: 0, url: 'local', detail: {} },
        { id: 'financial', name: 'agent-financial', status: 'ok', latency_ms: 12, url: ':8001', detail: {} },
        { id: 'docs', name: 'agent-docs', status: 'ok', latency_ms: 14, url: ':8003', detail: {} },
        { id: 'action', name: 'agent-action', status: 'ok', latency_ms: 9, url: ':8004', detail: {} },
        { id: 'voice', name: 'voice', status: 'ok', latency_ms: 10, url: ':8006', detail: {} },
      ],
    },
  }))
  await page.route('**/api/portfolio/summary', route => route.fulfill({
    json: {
      aum_fmt: '$20.4M',
      twr_pct: 178.65,
      annualized_pct: 7.13,
      irr_pct: 8.3,
      sharpe: 0.58,
      volatility_pct: 12.27,
      profit_fmt: '$7.85M',
      num_deals: 48,
      num_active: 32,
    },
  }))
  await page.route('**/api/portfolio/allocation', route => route.fulfill({
    json: {
      geography: { Asia: 37, 'North America': 35, Global: 16, Europe: 8, 'Middle East': 4 },
      sector: { 'Real Estate': 45, 'Private Equity': 35, Equities: 15, Credit: 5 },
    },
  }))
  await page.route('**/api/portfolio/deals', route => route.fulfill({
    json: Array.from({ length: 8 }, (_, index) => ({
      name: index === 0 ? 'Aurora Brands' : `Deal ${index + 1}`,
      sector: 'Private Equity',
      geo: 'Global',
      status: 'Active',
      aum: 1000000,
      twr: 12.3,
    })),
  }))
  await page.route('**/api/market', route => route.fulfill({
    json: {
      quotes: [
        { symbol: 'SPX', name: 'S&P 500', price: 5470, change_pct: 0.4 },
        { symbol: 'NDX', name: 'Nasdaq 100', price: 19500, change_pct: 0.7 },
      ],
      indicators: [
        { key: 'fed', name: 'Fed Funds Rate', value: 5.25, unit: '%', date: '2026-06-19' },
      ],
    },
  }))
  await page.route('**/voice-api/status', route => route.fulfill({
    json: {
      status: 'ok',
      stt: { engine: 'browser speech recognition', model: 'browser', ready: false },
      tts: { engine: 'browser speech fallback', voice: 'auto', ready: false },
      voice_to_voice: true,
    },
  }))
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
})

async function goto(page: Page, path: string) {
  await page.goto(path)
  await page.waitForLoadState('networkidle')
}

test('dashboard renders the KPI cards', async ({ page }) => {
  await goto(page, '/')
  await expect(page.getByRole('heading', { name: 'Portfolio Overview' })).toBeVisible()
  await expect(page.getByText('$20.4M')).toBeVisible()
  await expect(page.getByText('19.65%')).toBeVisible()
  await expect(page.getByText('0.58')).toBeVisible()
  await page.getByRole('button', { name: '1M' }).click()
  await expect(page.getByRole('button', { name: '1M' })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByText('Last 30 days')).toBeVisible()
  // Geographic + sector breakdowns present
  await expect(page.getByText('Geographic Allocation')).toBeVisible()
  await expect(page.getByText('Sector Mix')).toBeVisible()
  await page.screenshot({ path: 'e2e/__screens__/dashboard.png' })
})

test('portfolio deals table renders rows', async ({ page }) => {
  await goto(page, '/portfolio')
  await expect(page.getByRole('heading', { name: 'Portfolio Deals' })).toBeVisible()
  const rows = page.locator('tbody tr')
  await expect(rows).toHaveCount(8)
  await expect(page.getByText('Aurora Brands')).toBeVisible()
  await page.screenshot({ path: 'e2e/__screens__/portfolio.png' })
})

test('market page renders quotes and indicators', async ({ page }) => {
  await goto(page, '/market')
  await expect(page.getByRole('heading', { name: 'Market Data' })).toBeVisible()
  await expect(page.getByText('S&P 500')).toBeVisible()
  await expect(page.getByText('Fed Funds Rate')).toBeVisible()
  await page.screenshot({ path: 'e2e/__screens__/market.png' })
})

test('chat page renders and accepts input', async ({ page }) => {
  await goto(page, '/chat')
  await expect(page.getByRole('heading', { name: 'AI Assistant' })).toBeVisible()
  const input = page.getByPlaceholder(/Ask LaRuche anything/i)
  await expect(input).toBeVisible()
  await expect(page.getByRole('button', { name: 'Attach files' })).toBeVisible()
  const fileInput = page.locator('input[type="file"]')
  await expect(fileInput).toHaveAttribute('multiple', '')
  await expect(fileInput).toHaveAttribute('accept', /image\/\*.*audio\/\*/)
  await expect(page.getByRole('button', { name: 'Dictate message' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Start voice conversation' })).toBeVisible()
  await expect(page.getByRole('combobox', { name: 'Response mode' })).toHaveValue('instant')
  await page.getByRole('combobox', { name: 'Response mode' }).selectOption('deep')
  await expect(page.getByRole('combobox', { name: 'Response mode' })).toHaveValue('deep')
  await input.fill('What is my portfolio AUM?')
  await expect(page.getByRole('button', { name: 'Send message' })).toBeVisible()
  await page.screenshot({ path: 'e2e/__screens__/chat.png' })
})

test('voice studio exposes all three speech modes', async ({ page }) => {
  await goto(page, '/voice')
  await expect(page.getByRole('heading', { name: 'Voice Studio' })).toBeVisible()
  await expect(page.getByRole('button', { name: /Voice to voice/ })).toBeVisible()
  await expect(page.getByRole('button', { name: /Speech to text/ })).toBeVisible()
  await page.getByRole('button', { name: /Text to speech/ }).click()
  await expect(page.getByRole('heading', { name: 'Generate a briefing' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Play briefing' })).toBeVisible()
  await page.screenshot({ path: 'e2e/__screens__/voice.png' })
})

test('no console errors across navigation', async ({ page }) => {
  await goto(page, '/')
  await goto(page, '/portfolio')
  await goto(page, '/market')
  await goto(page, '/chat')
  await goto(page, '/voice')
  expect(consoleErrors, consoleErrors.join('\n')).toEqual([])
})
