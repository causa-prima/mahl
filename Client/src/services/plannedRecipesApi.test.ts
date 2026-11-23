import { describe, it, expect } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import type { RecipeId } from '../domain/recipe'
import { planRecipe } from './plannedRecipesApi'

const id = '3f2b8c1e-0000-4000-8000-000000000401' as RecipeId

describe('planRecipe', () => {
  // ADR-S084-3
  // Transportmechanik, im DOM nicht beobachtbar: ohne Status-Check würde die Komponente nur unnötig neu laden,
  // das GET brächte denselben Stand (ADR-S084-3-Addendum). Deshalb hier gegen die HTTP-Grenze.
  it('PlanRecipe_Status500_ReturnsUnexpectedError', async () => {
    // Given: der Server antwortet 500
    server.use(http.put(`/api/planned-recipes/${id}`, () => new HttpResponse(null, { status: 500 })))

    // When: ich vormerke
    const result = await planRecipe(id)

    // Then: Err(Unexpected) mit dem Status in der Meldung
    expect(result.isErr()).toBe(true)
    expect(result._unsafeUnwrapErr()).toEqual({ kind: 'Unexpected', message: expect.stringContaining('500') as unknown })
  })
})
