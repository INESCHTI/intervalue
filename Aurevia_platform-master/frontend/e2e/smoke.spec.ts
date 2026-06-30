import { test, expect, type Page } from '@playwright/test'

/**
 * Smoke + content tests for the Aurevia web app.
 * Validates the four screens render and surfaces the data shown in the UI
 * so it can be compared against the canonical demo data.
 */

let consoleErrors: string[] = []

test.beforeEach(async ({ page }) => {
  consoleErrors = []
  page.on('console', (msg) => {
    const text = msg.text()
    if (msg.type() === 'error' && !text.includes('net::ERR_NETWORK_ACCESS_DENIED')) {
      consoleErrors.push(text)
    }
  })

  await page.route('**/api/**', async route => {
    const url = route.request().url()
    if (url.includes('/portfolio/summary')) {
      return route.fulfill({
        json: {
          aum_fmt: '$20.4M',
          twr_pct: 19.65,
          annualized_pct: 19.65,
          irr_pct: 22.8,
          sharpe: 0.58,
          volatility_pct: 14.2,
          profit_fmt: '$3.1M',
          num_deals: 8,
          num_active: 6,
        },
      })
    }
    if (url.includes('/portfolio/allocation')) {
      return route.fulfill({
        json: {
          geography: { 'North America': 42, Europe: 28, APAC: 18, MENA: 12 },
          sector: { Technology: 36, Healthcare: 24, Energy: 21, Consumer: 19 },
        },
      })
    }
    if (url.includes('/portfolio/deals')) {
      return route.fulfill({
        json: [
          { name: 'Aurora Brands', sector: 'Consumer', geo: 'Europe', status: 'Active', aum: 3.2, twr: 18.4 },
          { name: 'HelioGrid', sector: 'Energy', geo: 'MENA', status: 'Active', aum: 2.8, twr: 21.1 },
          { name: 'Northstar AI', sector: 'Technology', geo: 'North America', status: 'Active', aum: 4.1, twr: 26.7 },
          { name: 'Cobalt Health', sector: 'Healthcare', geo: 'Europe', status: 'Active', aum: 2.4, twr: 12.9 },
          { name: 'Atlas Renewables', sector: 'Energy', geo: 'APAC', status: 'Exited', aum: 1.6, twr: 31.2 },
          { name: 'Meridian Cloud', sector: 'Technology', geo: 'North America', status: 'Active', aum: 2.9, twr: 17.5 },
          { name: 'VitaCore Labs', sector: 'Healthcare', geo: 'APAC', status: 'Watch', aum: 1.7, twr: -3.4 },
          { name: 'Lumen Retail', sector: 'Consumer', geo: 'MENA', status: 'Active', aum: 1.7, twr: 8.6 },
        ],
      })
    }
    if (url.includes('/market')) {
      return route.fulfill({
        json: {
          quotes: [
            { symbol: 'S&P 500', name: 'US Large Cap Equity', price: 5512.38, change_pct: 0.42 },
            { symbol: 'NASDAQ', name: 'US Growth Equity', price: 17842.91, change_pct: 0.68 },
            { symbol: 'STOXX 600', name: 'Europe Broad Market', price: 514.22, change_pct: -0.14 },
          ],
          indicators: [
            { key: 'fed', name: 'Fed Funds Rate', value: 5.25, unit: '%', date: '2026-06-14' },
            { key: 'cpi', name: 'US CPI YoY', value: 3.1, unit: '%', date: '2026-06-14' },
            { key: 'oil', name: 'Brent Crude', value: 82.4, unit: 'USD', date: '2026-06-14' },
          ],
        },
      })
    }
    return route.continue()
  })

  await page.route('**/voice-api/status', route => route.fulfill({
    json: {
      status: 'ok',
      stt: { engine: 'mock', model: 'demo-stt', ready: true },
      tts: { engine: 'mock', voice: 'demo-voice', ready: true },
      voice_to_voice: true,
    },
  }))
})

async function goto(page: Page, path: string) {
  await page.goto(path)
  await page.waitForLoadState('networkidle')
}

test('dashboard renders the KPI cards', async ({ page }) => {
  await goto(page, '/')
  await expect(page.getByRole('heading', { name: 'Portfolio Overview' })).toBeVisible()
  await expect(page.getByText('$20.4M')).toBeVisible()
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
  const input = page.getByPlaceholder(/Ask Aurevia anything/i)
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

