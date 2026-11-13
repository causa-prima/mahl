import type { APIRequestContext } from '@playwright/test'
import { E2E_API_BASE, expect } from '../fixtures'

// Low-Level-Seed über den API-Port: legt eine Zutat an und gibt Id + xmin-ETag zurück (der ETag
// wird für ein nachfolgendes If-Match beim DELETE gebraucht, ADR-S058-3). Gemeinsame Basis für
// alle Seed-Varianten und den Löschen·Konflikt-Test – so lebt der POST-201-Block an einer Stelle.
export async function createIngredientViaApi(request: Readonly<APIRequestContext>, name: string, baseUnit: string): Promise<{ id: string; etag: string }> {
  const response = await request.post(`${E2E_API_BASE}/api/ingredients`, { data: { name, baseUnit } })
  expect(response.status(), 'Seed-Zutat muss angelegt werden (201)').toBe(201)
  const { id } = await response.json() as { id: string }
  return { id, etag: response.headers()['etag'] }
}

// Legt eine Zutat direkt über die API an (Vorbedingung "die Zutat X existiert"), vor dem Laden der
// Seite. Ein zweiter POST käme als Duplikat nicht durch – der direkte API-Seed ist der saubere Weg,
// den Ausgangszustand über den ausgehenden Port herzustellen. Id/ETag werden hier nicht gebraucht.
export async function seedIngredientViaApi(request: Readonly<APIRequestContext>, name: string, baseUnit: string): Promise<void> {
  await createIngredientViaApi(request, name, baseUnit)
}

// Legt eine Zutat an und löscht sie direkt wieder (soft-delete) – Vorbedingung "die Zutat X
// existiert und wurde gelöscht". Der ETag aus dem POST-Response geht als If-Match ins DELETE
// (Plumbing: DELETE verlangt als mutierender Single-Resource-Endpoint einen If-Match, ADR-S058-1).
export async function seedDeletedIngredientViaApi(request: Readonly<APIRequestContext>, name: string, baseUnit: string): Promise<{ id: string }> {
  const { id, etag } = await createIngredientViaApi(request, name, baseUnit)
  const deleteResponse = await request.delete(`${E2E_API_BASE}/api/ingredients/${id}`, { headers: { 'If-Match': etag } })
  expect(deleteResponse.status(), 'Seed-Löschen muss gelingen (204)').toBe(204)
  return { id }
}
