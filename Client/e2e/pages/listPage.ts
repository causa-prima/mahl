import type { APIRequestContext, Locator, Page } from '@playwright/test'

// Page-Object-Interface der Querschnitts-Suite (ADR-S112-5, Nachweis-Schicht). Jede Listen-Seite liefert
// eine Implementierung; `interaction.spec.ts` läuft gegen jede davon. Das Interface enthält nur, was sich
// von Seite zu Seite UNTERSCHEIDET (Pfade, Beschriftungen, Testdaten). Was überall gleich sein soll,
// spricht die Suite direkt an – genau das ist der Vertrag, den sie prüft. Eine Seite, die hier
// eingebunden wird, muss ihn erfüllen:
//   - Anlegen läuft über einen MUI-Dialog (role=dialog, Backdrop-Klick über `.MuiDialog-container`),
//     dessen erstes Eingabefeld ein Textfeld ist (Escape-Test drückt dort).
//   - Die Dialog-Buttons heißen "Speichern" und "Abbrechen".
//   - Löschen zeigt den Toast "<label> gelöscht" mit der Aktion "Rückgängig".
// Erfüllt eine Seite einen Punkt nicht, scheitert die Suite nicht beim Kompilieren, sondern als
// Playwright-Timeout – dann zuerst hier nachsehen.
//
// Abgeleitet aus einer einzigen Seite (Zutaten). Mit der zweiten Seite ist zu erwarten, dass sich der
// Zuschnitt verschiebt – das ist eingeplant, nicht ein Fehler des Interfaces.

// Ein Beispiel-Eintrag samt seiner Darstellung auf der Seite. Die Seite besitzt die Testdaten, weil
// nur sie weiß, was einen gültigen Eintrag ausmacht und wie er in der Liste erscheint.
export interface ListEntry {
  // Anzeigename – geht in den Toast "<label> gelöscht" ein.
  readonly label: string
  // Die Listenzeile mit ALLEN angezeigten Werten, nicht nur dem Namen: "erscheint wieder" heißt
  // vollständig wieder, nicht nur dem Namen nach.
  readonly row: Locator
  readonly deleteButton: Locator
  seed(): Promise<void>
}

export interface ListPage {
  // Zwei unterscheidbare Einträge – kein Szenario der Suite braucht mehr.
  readonly entries: readonly [ListEntry, ListEntry]
  readonly list: Locator
  // Hinweis bei leerer Liste; zugleich neutrales, nicht interaktives Klickziel.
  readonly emptyState: Locator
  // URL-Globs der Seiten-API, damit die Suite Anfragen verzögern kann (Pending-Fenster).
  readonly createRoute: string
  readonly deleteRoute: string
  goto(): Promise<void>
  openCreateDialog(): Promise<void>
  fillCreateDialogWithValidEntry(): Promise<void>
}

export interface ListPageDefinition {
  // Seitenname für den describe-Titel.
  readonly name: string
  create(page: Readonly<Page>, request: Readonly<APIRequestContext>): ListPage
}
