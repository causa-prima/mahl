import type { APIRequestContext } from '@playwright/test'
import { E2E_API_BASE, expect } from '../fixtures'
import { seedIngredientViaApi } from './ingredientsApi'

// Gültig aufgebaute Kennung (UUIDv7-Form), zu der es kein Rezept gibt – Ziel eines Direktlinks ins Leere.
export const UNKNOWN_RECIPE_ID = '01900000-0000-7000-8000-000000000000'

type RecipeSeed = { readonly title: string; readonly ingredients: string; readonly instruction: string }

// Low-Level-Seed über den API-Port: legt ein Rezept mit einem Schritt an und gibt seine Id zurück
// (Ziel eines Direktlinks). Die Zutaten der Zeilen müssen bereits existieren.
export async function createRecipeViaApi(request: Readonly<APIRequestContext>, recipe: RecipeSeed): Promise<string> {
  const response = await request.post(`${E2E_API_BASE}/api/recipes`, {
    data: { title: recipe.title, ingredients: recipe.ingredients, steps: [{ instruction: recipe.instruction }] },
  })
  expect(response.status(), 'Seed-Rezept muss angelegt werden (201)').toBe(201)
  const { id } = await response.json() as { id: string }
  return id
}

// Legt Rezepte direkt über die API an (Vorbedingung "das Rezept X existiert"), vor dem Laden der
// Seite. Ein Rezept braucht mindestens eine Zutat und einen Schritt; beides ist für die Vorbedingung
// beiläufig, deshalb teilen sich alle Rezepte eine Zutat, die einmal angelegt wird. Folge: höchstens
// einmal je Test aufrufen und nicht zusammen mit einem eigenen Seed der Zutat "Salz" – ein zweiter POST
// derselben Zutat käme als Duplikat nicht durch. Nacheinander statt parallel: Die Anlege-Reihenfolge
// ist Teil der Vorbedingung, wenn ein Test sie bewusst von der erwarteten Listen-Reihenfolge abweichen lässt.
// Die Promise-Kette per reduce ersetzt eine for…of-Schleife, die `functional/no-loop-statements` verbietet.
export async function seedRecipesWithSaltViaApi(request: Readonly<APIRequestContext>, ...titles: readonly string[]): Promise<void> {
  await seedIngredientViaApi(request, 'Salz', 'g')
  await titles.reduce(async (previous, title) => {
    await previous
    await createRecipeViaApi(request, { title, ingredients: 'Salz', instruction: 'Zubereiten.' })
  }, Promise.resolve())
}
