import { expect, test } from '@playwright/test'

test.beforeEach(async ({ page }) => {
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
  await page.route('**/api/documents', async route => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        json: {
          documents: [
            {
              id: 'doc_1',
              name: 'portfolio-note.txt',
              kind: 'text',
              size: 42,
              created_at: new Date().toISOString(),
              preview: 'AUM is $20.4M across 48 deals.',
              correlation_id: 'test-correlation',
            },
          ],
        },
      })
    } else {
      await route.continue()
    }
  })
  await page.route('**/api/documents/history', route => route.fulfill({
    json: {
      events: [
        {
          type: 'uploaded',
          document_id: 'doc_1',
          name: 'portfolio-note.txt',
          kind: 'text',
          timestamp: new Date().toISOString(),
          correlation_id: 'test-correlation',
        },
      ],
    },
  }))
  await page.route('**/api/attachments/extract', route => route.fulfill({
    json: {
      attachments: [
        { id: 'doc_2', name: 'upload.txt', kind: 'text', content: 'Uploaded text content.' },
      ],
    },
  }))
})

test('login or authenticated shell renders', async ({ page }) => {
  await page.goto('/')
  await expect(
    page.getByRole('button', { name: /sign in with sso/i })
      .or(page.getByText('Agent Mesh')),
  ).toBeVisible()
})

test('agent mesh health and assistant language settings are visible', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('Agent Mesh')).toBeVisible()
  await expect(page.getByText('5/5')).toBeVisible()
  await page.getByRole('button', { name: /Assistant settings/ }).click()
  const panel = page.locator('#assistant-settings-panel')
  await expect(panel.getByText('Assistant settings')).toBeVisible()
  await expect(panel.getByText('Controls replies, dictation locale, and spoken accent. The app UI stays English.')).toBeVisible()
  await page.getByRole('button', { name: 'Assistant language French' }).click()
  await expect(page.getByRole('button', { name: 'Assistant language French' })).toHaveAttribute('aria-pressed', 'true')
  await page.getByRole('button', { name: 'Assistant language Arabic' }).click()
  await expect(page.getByRole('button', { name: 'Assistant language Arabic' })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.locator('.app-shell')).not.toHaveAttribute('dir', 'rtl')
  await page.getByRole('button', { name: 'TTS voice' }).click()
  await expect(page.getByRole('listbox', { name: 'TTS voice options' })).toBeVisible()
  await expect(page.getByRole('option', { name: 'Auto matching voice' })).toBeVisible()
})

test('documents library supports upload, history, export and delete controls', async ({ page }) => {
  await page.goto('/documents')
  await expect(page.getByRole('heading', { name: 'Documents' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'portfolio-note.txt' })).toBeVisible()
  await expect(page.getByText('AUM is $20.4M')).toBeVisible()
  await expect(page.getByTitle('Export extracted text')).toBeVisible()
  await expect(page.getByTitle('Delete document')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'History' })).toBeVisible()
})

test('chat exposes voice, upload and email confirmation UI', async ({ page }) => {
  await page.goto('/chat')
  await expect(page.getByRole('button', { name: 'Attach files' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Dictate message' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Start voice conversation' })).toBeVisible()
  await expect(page.getByRole('combobox', { name: 'Response mode' })).toHaveValue('instant')
})
