import type { APIRequestContext, Page } from '@playwright/test'

// Fähigkeit „Bedienbarkeit per Finger" (@NFR-accessibility-touch) für `accessibility.spec.ts`
// (ADR-S112-5, Ebene Geltungsbereich). Anders als Anlege-Dialog und Undo-Toast (listPage.ts) hat jede
// Seite Bedienelemente – die Fähigkeit liefert deshalb jede Seite, auch eine ohne Listen-Verhalten.
// Die Seite kennt ihre Zustände; die Suite misst in jedem davon alle sichtbaren Bedienelemente.

export interface TouchTargetState {
  // Zustandsname für die Fehlermeldung der Suite.
  readonly name: string
  // Nur für einen Zustand ohne jedes eigene Bedienelement (die Navigationsleiste zählt nicht): Sonst verlangt
  // die Suite mindestens eines, damit ein Zustand, in dem die Messung nichts findet, auffällt statt still grün
  // zu bleiben. Mit der Angabe
  // verlangt sie genau keines – bekommt der Zustand eines, wird es gemessen und die Angabe als überholt gemeldet.
  readonly withoutControls?: true
  // Führt vom vorigen Zustand in diesen und wartet, bis er sichtbar ist: Gemessen wird sofort danach,
  // und ein noch nicht gerendertes Element fiele nicht als Verstoß auf, sondern gar nicht.
  reach(): Promise<void>
}

export interface TouchTargetPageDefinition {
  // Seitenname für den describe-Titel.
  readonly name: string
  // Zustände in Durchlauf-Reihenfolge – jeder baut auf dem vorigen auf.
  states(page: Readonly<Page>, request: Readonly<APIRequestContext>): readonly TouchTargetState[]
}
