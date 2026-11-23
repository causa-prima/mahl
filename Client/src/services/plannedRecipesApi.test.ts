import { describe, it, expect } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import type { RecipeId } from '../domain/recipe'
import { planRecipe, unplanRecipe } from './plannedRecipesApi'

const id = '3f2b8c1e-0000-4000-8000-000000000401' as RecipeId

describe('Vormerkung senden (planRecipe, unplanRecipe)', () => {
  // ADR-S084-3
  // Transportmechanik, im DOM nicht beobachtbar: ohne Status-Check würde die Komponente nur unnötig neu laden,
  // das GET brächte denselben Stand (ADR-S084-3-Addendum). Deshalb hier gegen die HTTP-Grenze.
  it.each([
    ['planRecipe', http.put, planRecipe],
    ['unplanRecipe', http.delete, unplanRecipe],
  ] as const)('%s_Status500_ReturnsUnexpectedError', async (_name, handler, send) => {
    // Given: der Server antwortet 500
    server.use(handler(`/api/planned-recipes/${id}`, () => new HttpResponse(null, { status: 500 })))

    // When: ich die Operation ausführe
    const result = await send(id)

    // Then: Err(Unexpected), die Meldung nennt den Status (am Ende verankert: die URL mit der ID könnte "500" enthalten)
    expect(result.isErr()).toBe(true)
    expect(result._unsafeUnwrapErr()).toEqual({ kind: 'Unexpected', message: expect.stringMatching(/: 500$/) as unknown })
  })
})
