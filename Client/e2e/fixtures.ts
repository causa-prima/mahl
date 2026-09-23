import { test as base, expect } from '@playwright/test'

// E2E-Backend (ASPNETCORE_URLS in playwright.config.ts). An einer Stelle statt je Spec hartkodiert.
export const E2E_API_BASE = 'http://localhost:5059'

// ADR-S084-4 Addendum: per-Test-DB-Isolation. Vor JEDEM Test die E2E-DB leeren (E2E-only Reset-Endpoint,
// nur bei ASPNETCORE_ENVIRONMENT=E2E gemappt) -> jeder Test startet gegen eine leere DB, keine
// Residual-Akkumulation über Läufe/Tests hinweg. Als Auto-Fixture statt beforeEach je Spec, damit keine
// Spec den Reset vergessen kann; Auto-Fixtures werden vor den beforeEach-Hooks aufgebaut, der Reset
// läuft also VOR dem initialen GET eines `page.goto` im beforeEach.
export const test = base.extend<{ resetDatabase: undefined }>({
  resetDatabase: [async ({ request }, use) => {
    const res = await request.post(`${E2E_API_BASE}/api/test/reset`)
    // Laut scheitern, falls der Reset-Endpoint nicht existiert (falsche Umgebung) statt still zu no-op'en.
    expect(res.status(), 'Reset-Endpoint muss in der E2E-Umgebung 204 liefern').toBe(204)
    await use(undefined)
  }, { auto: true }],
})

export { expect }
