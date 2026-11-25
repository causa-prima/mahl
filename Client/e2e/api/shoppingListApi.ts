import type { APIRequestContext } from '@playwright/test'
import { E2E_API_BASE, expect } from '../fixtures'

// Übernimmt die Zutaten der vorgemerkten Rezepte direkt über den API-Port (ADR-S154-3: POST /generate, 204) – für
// die Vorbedingung „die Zutaten der vorgemerkten Rezepte sind auf die Einkaufsliste übernommen“.
export async function generateShoppingListViaApi(request: Readonly<APIRequestContext>): Promise<void> {
  const response = await request.post(`${E2E_API_BASE}/api/shopping-list/generate`)
  expect(response.status(), 'Übernehmen über die API muss gelingen (204)').toBe(204)
}
