import type { APIRequestContext } from '@playwright/test'
import { E2E_API_BASE, expect } from '../fixtures'

// Merkt ein Rezept direkt über den API-Port vor (ADR-S153-1: PUT auf die Rezept-ID, 204) – für Vorbedingungen,
// die nicht über die Oberfläche entstehen, etwa „wird auf einem anderen Gerät vorgemerkt“.
export async function planRecipeViaApi(request: Readonly<APIRequestContext>, recipeId: string): Promise<void> {
  const response = await request.put(`${E2E_API_BASE}/api/planned-recipes/${recipeId}`)
  expect(response.status(), 'Vormerken über die API muss gelingen (204)').toBe(204)
}

// Hebt eine Vormerkung direkt über den API-Port auf (ADR-S153-1: DELETE auf die Rezept-ID, 204) – etwa „wird auf
// einem anderen Gerät aufgehoben“.
export async function unplanRecipeViaApi(request: Readonly<APIRequestContext>, recipeId: string): Promise<void> {
  const response = await request.delete(`${E2E_API_BASE}/api/planned-recipes/${recipeId}`)
  expect(response.status(), 'Aufheben über die API muss gelingen (204)').toBe(204)
}
