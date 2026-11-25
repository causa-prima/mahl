import { test, expect } from './fixtures'
import { planRecipeViaApi } from './api/plannedRecipesApi'
import { seedRecipesWithSaltViaApi } from './api/recipesApi'
import { exactly } from './exactText'
import { noPlannedRecipesHint, plannedEntries } from './pages/plannedRecipesPage'
import { emptyShoppingListHint, toPlannedRecipesLink } from './pages/shoppingListPage'

// @US-201-happy-path
test.describe('US201_HappyPath: Einkaufsliste', () => {
  // Szenario: Eine noch nie gefüllte Einkaufsliste zeigt einen Hinweis
  test('US201_HappyPath_GetShoppingList_NeverFilled_ShowsHintAndLinkToPlannedRecipes', async ({ page, request }) => {
    // Given: das Rezept "Pfannkuchen" ist vorgemerkt
    const [pancakesId] = await seedRecipesWithSaltViaApi(request, 'Pfannkuchen')
    await planRecipeViaApi(request, pancakesId)

    // And: die Einkaufsliste ist leer (DB-Reset der Auto-Fixture)

    // When: ich zur Einkaufsliste navigiere
    await page.goto('/shopping-list')

    // Then: sehe ich den Hinweis "Die Einkaufsliste ist leer." und den Link "Zu den vorgemerkten Rezepten"
    await expect(page.getByRole('heading', { level: 1, name: 'Einkaufsliste' })).toBeVisible()
    await expect(emptyShoppingListHint(page)).toBeVisible()
    await expect(toPlannedRecipesLink(page)).toBeVisible()

    // When: ich auf "Zu den vorgemerkten Rezepten" klicke
    await toPlannedRecipesLink(page).click()

    // Then: zeigt die Vorgemerkt-Seite genau das Rezept "Pfannkuchen" – „genau“ schließt den Leerzustand-Hinweis aus
    await expect(page.getByRole('heading', { level: 1, name: 'Vorgemerkt' })).toBeVisible()
    await expect(plannedEntries(page)).toHaveText([exactly('Pfannkuchen')])
    await expect(noPlannedRecipesHint(page)).toBeHidden()
  })
})
