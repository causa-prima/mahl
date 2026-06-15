import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://localhost:5173',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  // Poka-Yoke (ADR-S084-4) gegen "E2E testet gegen veraltetes Backend": Playwright besitzt den
  // Backend-Lebenszyklus. reuseExistingServer:false erzwingt einen FRISCHEN Build/Start
  // aus dem Quellcode pro Lauf -> es kann kein stale Prozess (mit altem Code) still
  // mitgetestet werden. Die url (/api/ingredients) ist nur Readiness-Probe: Playwright
  // wartet bis sie 200 liefert -> verifiziert DB-Verbindung und waermt EF/JIT (mindert
  // zugleich das Cold-Start-Race). Laeuft bereits ein Backend auf 5059, schlaegt der
  // Start mit Port-Konflikt fehl (lauter Abbruch statt stillem Reuse) - gewollt.
  // Vite darf reused werden (wird nie stale: Hot-Reload).
  webServer: [
    {
      command: 'dotnet run --project ../Server',
      url: 'http://localhost:5059/api/ingredients',
      env: { ASPNETCORE_URLS: 'http://localhost:5059' },
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
    },
  ],
})
