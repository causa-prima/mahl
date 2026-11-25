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

type RecipeWithIngredients = { readonly title: string; readonly lines: readonly string[] }

// Die Zutat einer Rezeptzeile in der Grammatik von ADR-S135-2, beschränkt auf die Formen der Szenarien:
// „250 g Mehl“ (Menge, Einheit, Zutat) oder „Salz“ (ohne Menge).
function ingredientOfLine(line: string): { readonly name: string; readonly unit: string | null } {
  const [first = '', unit = '', ...name] = line.split(' ')
  return /^\d/.test(first) ? { name: name.join(' '), unit } : { name: line, unit: null }
}

// Die Zutaten aller Zeilen, je Name einmal. Die Einheit ist die Basiseinheit der Zutat (ADR-S135-2); steht eine
// Zutat in keiner Zeile mit Menge, ist ihre Einheit für die Szenarien beiläufig – dann "g".
// Zwei Zeilen mit verschiedenen Einheiten derselben Zutat brechen ab: Sie widersprächen der einen Basiseinheit, und
// der Test schlüge sonst erst mit einer Server-Meldung fehl statt an seinen Daten.
function ingredientsOf(recipes: readonly RecipeWithIngredients[]): ReadonlyMap<string, string> {
  const ingredients = recipes.flatMap(({ lines }) => lines.map(ingredientOfLine))
  const units = new Map(ingredients.flatMap(({ name, unit }) => (unit === null ? [] : [[name, unit] as const])))
  const conflict = ingredients.find(({ name, unit }) => unit !== null && unit !== units.get(name))
  if (conflict !== undefined) {
    throw new Error(`Testdaten: Zutat "${conflict.name}" mit zwei Einheiten (${conflict.unit ?? ''}, ${units.get(conflict.name) ?? ''})`)
  }
  return new Map(ingredients.map(({ name }) => [name, units.get(name) ?? 'g']))
}

// Legt die Zutaten und Rezepte der Vorbedingung „das Rezept X mit den Zutaten … existiert“ über die API an
// (Step-Hinweis in features/shopping-lists.feature: Zutaten bei Bedarf anlegen). Jede Zutat wird einmal angelegt,
// auch wenn sie in mehreren Rezepten steht – ein zweiter POST käme als Duplikat nicht durch. Nacheinander, weil
// Rezepte die Zutaten voraussetzen. Die Promise-Ketten per reduce ersetzen for…of-Schleifen, die
// `functional/no-loop-statements` verbietet. Gibt die Ids in der Reihenfolge der Rezepte zurück.
export async function seedRecipesWithIngredientsViaApi(request: Readonly<APIRequestContext>, ...recipes: readonly RecipeWithIngredients[]): Promise<readonly string[]> {
  await [...ingredientsOf(recipes)].reduce(async (previous, [name, unit]) => {
    await previous
    await seedIngredientViaApi(request, name, unit)
  }, Promise.resolve())
  return recipes.reduce<Promise<readonly string[]>>(async (previous, { title, lines }) => {
    const ids = await previous
    return [...ids, await createRecipeViaApi(request, { title, ingredients: lines.join('\n'), instruction: 'Zubereiten.' })]
  }, Promise.resolve([]))
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
