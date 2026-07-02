import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  // workers: 1 – harte Serialisierung. Die E2E-DB-Isolation (ADR-S084-4 Addendum) teilt sich EINE
  // mahl_e2e-DB und leert sie per-Test; parallele Worker (Playwright-Default über Dateien hinweg) würden
  // sich gegenseitig die Daten wegtrunken. Bis eine per-Worker-DB existiert, bleibt der Lauf single-worker.
  workers: 1,
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
      // --no-launch-profile: launchSettings.json würde sonst ASPNETCORE_ENVIRONMENT=Development erzwingen
      // und die hier gesetzte E2E-Umgebung überschreiben. Ohne Profil greift die inherited env unten.
      command: 'dotnet run --project ../Server --no-launch-profile',
      url: 'http://localhost:5059/api/ingredients',
      // ASPNETCORE_ENVIRONMENT=E2E (ADR-S084-4 Addendum): eigene DB mahl_e2e (appsettings.E2E.json), Schema-Migrate
      // + Reset-Endpoint beim Start (Program.cs-Guard) -> per-Test-DB-Isolation, dev/prod unberührt.
      env: { ASPNETCORE_URLS: 'http://localhost:5059', ASPNETCORE_ENVIRONMENT: 'E2E' },
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
