import { test, expect } from './fixtures'
import { seedRecipesWithSaltViaApi } from './api/recipesApi'

// @US-803-happy-path
test.describe('US803_HappyPath: Vorgemerkt-Seite', () => {
  // Szenario: Ohne Vormerkungen zeigt die Vorgemerkt-Seite einen Hinweis
  test('US803_HappyPath_GetPlannedRecipes_NonePlanned_ShowsHintAndLinkToRecipeList', async ({ page, request }) => {
    // Given: das Rezept "Pfannkuchen" existiert, und kein Rezept ist vorgemerkt (DB-Reset der Auto-Fixture)
    await seedRecipesWithSaltViaApi(request, 'Pfannkuchen')

    // When: ich zur Vorgemerkt-Seite navigiere
    await page.goto('/planned')

    // Then: ich sehe den Hinweis "Noch keine Rezepte vorgemerkt." und den Link "Zur Rezept-Liste"
    await expect(page.getByRole('heading', { level: 1, name: 'Vorgemerkt' })).toBeVisible()
    await expect(page.getByText('Noch keine Rezepte vorgemerkt.')).toBeVisible()
    const toRecipeList = page.getByRole('link', { name: 'Zur Rezept-Liste' })
    await expect(toRecipeList).toBeVisible()

    // When: ich auf "Zur Rezept-Liste" klicke
    await toRecipeList.click()

    // Then: ich sehe die Rezept-Liste mit "Pfannkuchen"
    await expect(page).toHaveURL(/\/recipes$/)
    await expect(page.getByRole('heading', { level: 1, name: 'Rezepte' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Pfannkuchen' })).toBeVisible()
  })
})
