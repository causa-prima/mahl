import type { ListPageDefinition } from './listPage'
import { ingredientsPage } from './ingredientsPage'

// Alle Listen-Seiten der Querschnitts-Suiten (ADR-S112-5, Nachweis-Schicht). Eine neue Seite trägt sich
// hier ein und liefert ihr Page Object (listPage.ts) – interaction.spec.ts läuft dann auch gegen sie,
// statt nachgebaut zu werden. Die Touch-Target-Suite hat eine eigene Registry (touchTargetPages.ts).
export const LIST_PAGES: readonly ListPageDefinition[] = [ingredientsPage]
