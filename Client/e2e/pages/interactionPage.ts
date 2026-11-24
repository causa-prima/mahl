import type { APIRequestContext, Locator, Page } from '@playwright/test'

// Page-Object-Fähigkeiten der Querschnitts-Suite (ADR-S112-5, Nachweis-Schicht und Geltungsbereich). Nicht
// jede Seite zeigt jedes Querschnittsverhalten: Eine Seite liefert je Fähigkeit, die für sie gilt, eine
// Implementierung und trägt sich in deren Registry ein (interactionPages.ts); `interaction.spec.ts` läuft je
// Fähigkeit gegen jede eingetragene Seite. Muster wie touchTargetPage.ts.
//
// Die Interfaces enthalten nur, was sich von Seite zu Seite UNTERSCHEIDET (Pfade, Beschriftungen,
// Testdaten). Was überall gleich sein soll, spricht die Suite direkt an – genau das ist der Vertrag, den
// sie prüft. Erfüllt eine Seite einen Punkt nicht, scheitert die Suite nicht beim Kompilieren, sondern als
// Playwright-Timeout – dann zuerst hier nachsehen.

// Fähigkeit „Anlegen im Dialog“. Vertrag:
//   - Anlegen läuft über einen MUI-Dialog (role=dialog, Backdrop-Klick über `.MuiDialog-container`),
//     dessen erstes Eingabefeld ein Textfeld ist (Escape-Test drückt dort).
//   - Die Dialog-Buttons heißen "Speichern" und "Abbrechen".
export interface CreateDialogPage {
  // URL-Glob der Anlege-Anfrage, damit die Suite sie verzögern kann (Pending-Fenster).
  readonly createRoute: string
  goto(): Promise<void>
  openCreateDialog(): Promise<void>
  fillCreateDialogWithValidEntry(): Promise<void>
}

export interface CreateDialogPageDefinition {
  // Seitenname für den describe-Titel.
  readonly name: string
  create(page: Readonly<Page>, request: Readonly<APIRequestContext>): CreateDialogPage
}

// Ein Beispiel-Eintrag samt seiner Darstellung auf der Seite. Die Seite besitzt die Testdaten, weil
// nur sie weiß, was einen gültigen Eintrag ausmacht und wie er in der Liste erscheint.
export interface ListEntry {
  // Die Listenzeile mit ALLEN angezeigten Werten, nicht nur dem Namen: "erscheint wieder" heißt
  // vollständig wieder, nicht nur dem Namen nach.
  readonly row: Locator
  // Die Aktion, die den Eintrag aus der Liste nimmt – "Löschen" bzw. auf der Vorgemerkt-Seite "Entfernen".
  readonly deleteButton: Locator
  // Text des Toasts nach dem Löschen: Name samt Verb der Seite ("Mehl gelöscht", "Pfannkuchen entfernt").
  readonly deletedToast: string
  seed(): Promise<void>
}

// Fähigkeit „Löschen mit Rückgängig-Toast“. Vertrag: Die Aktion zeigt den Toast `deletedToast` mit der
// Aktion "Rückgängig"; ist der letzte Eintrag weg, steht der Leerzustand statt der Liste.
export interface DeleteWithUndoPage {
  // Zwei unterscheidbare Einträge – kein Szenario der Suite braucht mehr.
  readonly entries: readonly [ListEntry, ListEntry]
  readonly list: Locator
  // Hinweis bei leerer Liste; zugleich neutrales, nicht interaktives Klickziel.
  readonly emptyState: Locator
  // URL-Glob der Lösch-Anfrage, damit die Suite sie verzögern kann (Pending-Fenster).
  readonly deleteRoute: string
  goto(): Promise<void>
}

export interface DeleteWithUndoPageDefinition {
  // Seitenname für den describe-Titel.
  readonly name: string
  create(page: Readonly<Page>, request: Readonly<APIRequestContext>): DeleteWithUndoPage
}
