import type { Locator, Page } from '@playwright/test'

// Ein Eintrag der Navigationsleiste (ADR-S103-1): Die Leiste ist ein Landmark „Hauptnavigation“, jeder Eintrag
// ein Link mit dem Namen der Seite.
export const navEntry = (page: Readonly<Page>, name: string): Locator =>
  page.getByRole('navigation', { name: 'Hauptnavigation' }).getByRole('link', { name, exact: true })
