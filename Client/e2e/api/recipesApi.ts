import type { APIRequestContext, APIResponse } from '@playwright/test'
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

type RecipeCommand = {
  readonly title: string
  readonly ingredients: string
  readonly steps: readonly { readonly instruction: string }[]
}

// Der Speicher-Befehl direkt über den API-Port, ohne Statusprüfung – für Szenarien, deren Gegenstand die
// Antwort des Servers ist (z.B. eine Ablehnung, die das Formular nie auslöst).
export async function postRecipeViaApi(request: Readonly<APIRequestContext>, recipe: RecipeCommand): Promise<APIResponse> {
  return request.post(`${E2E_API_BASE}/api/recipes`, { data: recipe })
}

// Die Titel der Rezept-Liste, gelesen über den API-Port – für „ist die Rezept-Liste unverändert" aus dem
// Formular heraus, das eine andere Seite ist als die Liste.
export async function fetchRecipeTitlesViaApi(request: Readonly<APIRequestContext>): Promise<readonly string[]> {
  const response = await request.get(`${E2E_API_BASE}/api/recipes`)
  expect(response.status(), 'Rezept-Liste muss lesbar sein (200)').toBe(200)
  const recipes = await response.json() as readonly { readonly title: string }[]
  return recipes.map(({ title }) => title)
}

// Legt Rezepte direkt über die API an (Vorbedingung "das Rezept X existiert"), vor dem Laden der
// Seite. Ein Rezept braucht mindestens eine Zutat und einen Schritt; beides ist für die Vorbedingung
// beiläufig, deshalb teilen sich alle Rezepte eine Zutat, die einmal angelegt wird. Folge: höchstens
// einmal je Test aufrufen und nicht zusammen mit einem eigenen Seed der Zutat "Salz" – ein zweiter POST
// derselben Zutat käme als Duplikat nicht durch. Nacheinander statt parallel: Die Anlege-Reihenfolge
// ist Teil der Vorbedingung, wenn ein Test sie bewusst von der erwarteten Listen-Reihenfolge abweichen lässt.
// Die Promise-Kette per reduce ersetzt eine for…of-Schleife, die `functional/no-loop-statements` verbietet.
// Gibt die Ids in der Reihenfolge der Titel zurück (Ziel eines Direktlinks oder einer Vormerkung).
export async function seedRecipesWithSaltViaApi(request: Readonly<APIRequestContext>, ...titles: readonly string[]): Promise<readonly string[]> {
  await seedIngredientViaApi(request, 'Salz', 'g')
  return titles.reduce<Promise<readonly string[]>>(async (previous, title) => {
    const ids = await previous
    return [...ids, await createRecipeViaApi(request, { title, ingredients: 'Salz', instruction: 'Zubereiten.' })]
  }, Promise.resolve([]))
}
