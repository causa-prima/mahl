import { test, expect } from '@playwright/test'

// @US-904-happy-path
test.describe('US904_HappyPath: Zutaten verwalten', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/ingredients')
  })

  test('US904_HappyPath_CreateIngredient_ValidData_IngredientAppearsInList', async ({ page }) => {
    await page.getByRole('button', { name: 'Neue Zutat' }).click()
    await page.getByLabel('Name').fill('Tomaten')
    await page.getByLabel('Einheit').fill('Stück')
    await page.getByRole('button', { name: 'Speichern' }).click()

    await expect(page.getByTestId('ingredient-list').getByText('Tomaten')).toBeVisible()
  })
})
