import { defineConfig } from '@playwright/test';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
const python =
  process.env.ENGINE_PYTHON ||
  (existsSync('engine/.venv/bin/python') ? resolve('engine/.venv/bin/python') : 'python3');
export default defineConfig({
  testDir: './tests/e2e',
  outputDir: '.local/playwright-results',
  workers: 1,
  timeout: 30000,
  use: {
    baseURL: 'http://127.0.0.1:3100',
    channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome',
    headless: true,
  },
  webServer: [
    {
      command: `"${python}" -B -m riogineer_engine.server --port 8101`,
      url: 'http://127.0.0.1:8101/health',
      env: { PYTHONPATH: 'engine' },
      reuseExistingServer: false,
      timeout: 30000,
    },
    {
      command: 'npm run dev -- --port 3100',
      url: 'http://127.0.0.1:3100/digital-engineer',
      env: {
        RIOGINEER_ENGINE_URL: 'http://127.0.0.1:8101',
        NEXT_TELEMETRY_DISABLED: '1',
        RIOGINEER_REVIEW_SECRET: 'test-only-review-key',
        RIOGINEER_E2E: '1',
        RIOGINEER_LLM_PROVIDER: '',
      },
      reuseExistingServer: false,
      timeout: 60000,
    },
  ],
});
