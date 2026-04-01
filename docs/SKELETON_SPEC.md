# SKELETON-Spezifikation

<!--
wann-lesen: Bei Referenz-Fragen zum DB-Schema, zu API-Endpoints oder zur Frontend-Seitenstruktur
kritische-regeln:
  - Kein produktiver Code – nur Referenz/Spezifikation
  - Status beachten: Backend wird nach Spec-Audit verworfen und neu implementiert (BDD/Gherkin + Outside-In ATDD)
-->

## Inhalt

| Abschnitt | Inhalt | Wann lesen |
|-----------|--------|------------|
| Implementierte User Stories | Welche US-Nummern im SKELETON enthalten sind | Als Überblick |
| Datenbank-Schema | 5 Tabellen: Ingredient, Recipe, RecipeIngredient, Step, WeeklyPoolEntry, ShoppingListItem – Felder, Typen, Constraints | Bei Schema-Änderungen oder neuen Migrations |
| API-Endpoints | Alle Routen mit HTTP-Methode, Pfad, kurzer Beschreibung und Request-Body | Beim Implementieren oder Aufrufen von Endpoints |
| Frontend-Seiten | Navigation, 6 Seiten mit UI-Details und API-Aufrufen | Beim Implementieren von Frontend-Komponenten |
| Akzeptanzkriterium | End-to-End-Szenario (5 Schritte) als Definition of Done für SKELETON | Zur Verifikation der Gesamtfunktionalität |

> **Status:** 🔄 Neustart beschlossen (Session 042, 2026-03-26) – Backend wird nach Spec-Audit verworfen und neu implementiert mit BDD/Gherkin + Outside-In ATDD. Frontend noch nicht implementiert.

---

## Ziel

Minimaler technischer Durchstich (End-to-End), der alle Schichten verbindet:
**Zutat anlegen → Rezept anlegen → Rezept in Pool → Einkaufsliste generiert & abhakbar**

---

## Implementierte User Stories

| Story | Beschreibung |
|-------|-------------|
| US-904 | Zutaten-Verwaltung (CRUD) |
| US-602 | Manuelle Rezepterfassung (Titel + Zutaten + Schritte + Foto-Upload) |
| US-803 | Rezept dem Wochen-Pool hinzufügen (flache Liste, keine Datumslogik) |
| US-201 | Einkaufsliste anzeigen (generiert aus Pool) |
| US-303 | Artikel abhaken (BoughtAt-Timestamp, verschiebt in "Zuletzt gekauft") |

---

## Datenbank-Schema

> **IDs:** Alle Primärschlüssel sind `Guid` (UUIDv7, serverseitig generiert). Fremdschlüssel-Typen entsprechend.

### Ingredient
| Feld | Typ | Constraints |
|------|-----|-------------|
| `Id` | Guid | PK, UUIDv7 |
| `Name` | string(200) | NOT NULL, UNIQUE |
| `DefaultUnit` | string(50) | NOT NULL (z.B. "g", "ml", "Stück") |
| `AlwaysInStock` | bool | NOT NULL, DEFAULT false. Im SKELETON ohne Wirkung – Filterung erst ab MVP. |
| `DeletedAt` | timestamptz? | NULL = aktiv, NOT NULL = soft-deleted |

### Recipe
| Feld | Typ | Constraints |
|------|-----|-------------|
| `Id` | Guid | PK, UUIDv7 |
| `Title` | string(300) | NOT NULL |
| `SourceUrl` | string(2000)? | NULLABLE |
| `HasSourceImage` | bool | NOT NULL, DEFAULT false |
| `DeletedAt` | timestamptz? | NULL = aktiv, NOT NULL = soft-deleted |

**Constraint:** ENTWEDER `SourceUrl` ODER `HasSourceImage = true`, nie beides.
**Bildpfad-Konvention:** `/uploads/recipe-sources/{id}/original.webp` – deterministisch aus der Recipe-ID ableitbar. Server konvertiert jedes hochgeladene Bild serverseitig zu WEBP (Format-Erkennung via Magic Bytes, kein expliziter Typ im Request nötig).

### RecipeIngredient
| Feld | Typ | Constraints |
|------|-----|-------------|
| `Id` | Guid | PK, UUIDv7 |
| `RecipeId` | Guid | FK → Recipe.Id, ON DELETE CASCADE |
| `IngredientId` | Guid | FK → Ingredient.Id, ON DELETE RESTRICT |
| `Quantity` | decimal(7,3)? | NULL = "nach Geschmack" (Unspecified), sonst > 0 |
| `Unit` | string(50)? | NULL wenn Quantity NULL, sonst NOT NULL |

**Index:** UNIQUE (RecipeId, IngredientId)

**Einheiten-Konvention:** Metrische Einheiten werden vor dem Speichern auf ihre Basiseinheit normalisiert (Gewicht → g, Volumen → ml). Das Frontend übernimmt die Konversion; das Backend empfängt und speichert immer die Basiseinheit. Nicht-metrische Einheiten (EL, TL, Stück, Prise etc.) werden als Freitext gespeichert.

### Step
| Feld | Typ | Constraints |
|------|-----|-------------|
| `Id` | Guid | PK, UUIDv7 |
| `RecipeId` | Guid | FK → Recipe.Id, ON DELETE CASCADE |
| `StepNumber` | int | NOT NULL; serverseitig vergeben als Index + 1 (1-basiert, Reihenfolge = Reihenfolge im Request) |
| `Instruction` | text(4000) | NOT NULL |

**Index + Constraint:** UNIQUE (RecipeId, StepNumber)

### WeeklyPoolEntry
| Feld | Typ | Constraints |
|------|-----|-------------|
| `Id` | Guid | PK, UUIDv7 |
| `RecipeId` | Guid | FK → Recipe.Id |
| `AddedAt` | timestamptz | NOT NULL, DEFAULT NOW() |

**Index:** UNIQUE (RecipeId) — ein Rezept kann nur einmal gleichzeitig im Pool sein.

Keine Datumslogik in SKELETON (kein `PlannedDate`).

### ShoppingListItem
| Feld | Typ | Constraints |
|------|-----|-------------|
| `Id` | Guid | PK, UUIDv7 |
| `IngredientId` | Guid | FK → Ingredient.Id |
| `Quantity` | decimal(7,3)? | NULL = Menge nicht angegeben (aus Rezept mit "nach Geschmack"), sonst > 0 |
| `Unit` | string(50)? | NULL wenn Quantity NULL, sonst NOT NULL |
| `BoughtAt` | timestamptz? | NULL = offen, NOT NULL = gekauft |
| `GeneratedAt` | timestamptz | NOT NULL, DEFAULT NOW() |

**Generierungslogik (SKELETON):** Alte Items löschen, alle Pool-Rezepte neu berechnen. Gleiche Zutat + Einheit = Mengen summieren. Kein Tracking welche Zutat aus welchem Rezept kommt.

---

## API-Konventionen

### Validierung
- Alle unabhängigen Felder werden vollständig validiert; alle Fehler werden gesammelt zurückgegeben (kein Fail-Fast).
- Abhängige Validierungen (z.B. `unit` nur prüfen wenn `quantity` gesetzt) bleiben kurzschließend.
- `422 Unprocessable Entity`, Body: Array von Fehlermeldungen `["Fehler 1", "Fehler 2"]`
- Alle String-Felder werden vor der Validierung getrimmt; gespeichert wird der getrimte Wert.

### DB-Inkonsistenz
GET-Endpoints rekonstruieren Domain-Objekte über `Create()`. Verhalten bei inkonsistenten DB-Daten hängt vom Endpoint-Typ ab:

- **Listen-Endpoints** (z.B. GET `/api/recipes`, GET `/api/ingredients`): Korrupte Einträge werden übersprungen und der Fehler geloggt. Die Liste enthält nur konsistente Einträge — kein 500.
- **Einzeln-Endpoints** (z.B. GET `/api/recipes/{id}`, GET `/api/ingredients/{id}`): `500 Internal Server Error`, `Content-Type: application/problem+json`, Body: `{ "detail": "DB inconsistency in {Entity} #{id}: {Fehlermeldung}", "traceId": "..." }`. Die `traceId` ermöglicht Korrelation mit dem Server-Log-Eintrag.

### IDs
- Alle `{id}`-Parameter und Felder in Request/Response sind `Guid` (UUIDv7).

---

## API-Endpoints

### Zutaten (`/api/ingredients`)

**`IngredientDto`:** `{ id: Guid, name: string, defaultUnit: string, alwaysInStock: bool }`

| Methode | Pfad | Status | Response | Fehler |
|---------|------|--------|----------|--------|
| GET | `/api/ingredients` | 200 | `IngredientDto[]`, alphabetisch nach Name (korrupte Records werden übersprungen, Fehler geloggt) | – |
| POST | `/api/ingredients` | 201 | `IngredientDto`, `Location: /api/ingredients/{id}` | 409 Duplikat, 422 Validierung |
| GET | `/api/ingredients/{id}` | 200 | `IngredientDto` | 404, 500 DB-Inkonsistenz |
| PUT | `/api/ingredients/{id}` | 200 | `IngredientDto` | 404, 409 Duplikat/Soft-deleted, 422 Validierung |
| DELETE | `/api/ingredients/{id}` | 204 | – | 404 (auch bei bereits soft-deleted) |
| POST | `/api/ingredients/{id}/restore` | 200 | `IngredientDto` | 404, 409 bereits aktiv |

**POST/PUT Request-Body:** `{ name: string, defaultUnit: string }`

**409-Varianten POST/PUT:**
- Aktiver Name: `"Eine Zutat mit dem Namen '{name}' existiert bereits."`
- Soft-deleted Name: `{ "code": "ingredient_soft_deleted", "id": Guid }`
- Bereits aktiv (restore): `"Zutat ist bereits aktiv."`

**Check-Reihenfolge POST:** Soft-deleted-Check läuft vor Active-Duplicate-Check. Durch den 409-Mechanismus ist es über die API nicht möglich, eine aktive Zutat mit demselben Namen wie eine soft-deleted Zutat anzulegen.

**422-Fehlermeldungen:**
- `name` leer: `"Name darf nicht leer sein."`
- `defaultUnit` leer: `"Einheit darf nicht leer sein."`

---

### Rezepte (`/api/recipes`)

**`RecipeSummaryDto`** (Liste): `{ id: Guid, title: string }` — bewusst minimal; Erweiterung in MVP (siehe MVP_SPEC)
**`RecipeDto`** (Detail): `{ id: Guid, title: string, sourceUrl: string?, sourceImageUrl: string?, ingredients: RecipeIngredientDto[], steps: StepDto[] }`

`sourceUrl` und `sourceImageUrl` sind gegenseitig exklusiv (nie beide gesetzt). `sourceImageUrl` = `/uploads/recipe-sources/{id}/original.webp` wenn ein Bild vorhanden ist.
**`RecipeIngredientDto`**: `{ id: Guid, ingredientId: Guid, ingredientName: string, quantity: decimal?, unit: string? }`
**`StepDto`**: `{ id: Guid, instruction: string }` — Steps werden nach `StepNumber` aufsteigend sortiert zurückgegeben; die Listenposition entspricht der Schrittreihenfolge.

| Methode | Pfad | Status | Response | Fehler |
|---------|------|--------|----------|--------|
| GET | `/api/recipes` | 200 | `RecipeSummaryDto[]`, alphabetisch nach Title (korrupte Records werden übersprungen, Fehler geloggt) | – |
| POST | `/api/recipes` | 201 | `RecipeDto`, `Location: /api/recipes/{id}` | 422 Validierung |
| GET | `/api/recipes/{id}` | 200 | `RecipeDto` | 404, 500 DB-Inkonsistenz |
| DELETE | `/api/recipes/{id}` | 204 | – | 404 (auch bei bereits soft-deleted) |

**POST Request-Body:** `{ title: string, sourceUrl?: string, sourceImageBase64?: string, ingredients: [{ ingredientId: Guid, quantity: decimal?, unit: string? }], steps: [{ instruction: string }] }`

**Validierungsregeln POST:**
- `title`: nicht-leer nach Trimming
- `sourceUrl`: wenn angegeben, muss absolute URI sein; ENTWEDER `sourceUrl` ODER `sourceImageBase64`, nie beides
- `ingredients`: mind. 1 Eintrag; alle `ingredientId` müssen existieren und nicht soft-deleted sein
- `steps`: mind. 1 Eintrag; jede `instruction` nicht-leer nach Trimming
- `quantity`: wenn angegeben > 0; `unit` erforderlich wenn `quantity` gesetzt
- `stepNumber` wird serverseitig vergeben (Position im Array + 1) und für die DB-Sortierung verwendet; es erscheint nur im DB-Objekt – nicht im Domain-Objekt und nicht im DTO

**422-Fehlermeldungen:**
- `title` leer: `"Titel darf nicht leer sein."`
- `ingredients` leer: `"Rezept muss mindestens eine Zutat haben."`
- `steps` leer: `"Rezept muss mindestens einen Schritt haben."`
- `sourceUrl` nicht absolut: `"Quell-URL muss eine absolute URI sein."`
- `quantity` ≤ 0: `"Menge muss größer als 0 sein."`
- `unit` leer wenn `quantity` gesetzt: `"Einheit darf nicht leer sein."`
- `instruction` leer: `"Schritt-Anweisung darf nicht leer sein."`
- `ingredientId` nicht gefunden oder soft-deleted: `"Eine oder mehrere Zutaten wurden nicht gefunden."` (beide Fälle liefern dieselbe Meldung)

---

### Wochen-Pool (`/api/weekly-pool`)

**`WeeklyPoolEntryDto`:** `{ id: Guid, recipeId: Guid, recipeTitle: string, addedAt: timestamptz }`

| Methode | Pfad | Status | Response | Fehler |
|---------|------|--------|----------|--------|
| GET | `/api/weekly-pool` | 200 | `WeeklyPoolEntryDto[]` | – |
| POST | `/api/weekly-pool/recipes/{recipeId}` | 201 | `WeeklyPoolEntryDto` | 409 Duplikat, 422 Rezept nicht gefunden oder soft-deleted |
| DELETE | `/api/weekly-pool/recipes/{recipeId}` | 204 | – (idempotent) | – |

**GET-Verhalten bei soft-gelöschten Rezepten:** Einträge, deren Rezept soft-gelöscht ist, werden ausgefiltert und erscheinen nicht in der Liste. Wird ein Pool-Rezept nach Aufnahme soft-gelöscht und später wiederhergestellt, bleibt der Pool-Eintrag erhalten und erscheint nach Wiederherstellung wieder.

---

### Einkaufsliste (`/api/shopping-list`)

**`ShoppingListResponseDto`:** `{ openItems: ShoppingListItemDto[], boughtItems: ShoppingListItemDto[] }`
**`ShoppingListItemDto`:** `{ id: Guid, ingredientId: Guid, ingredientName: string, quantity: decimal?, unit: string?, boughtAt: timestamptz? }`

| Methode | Pfad | Status | Response | Fehler |
|---------|------|--------|----------|--------|
| POST | `/api/shopping-list/generate` | 200 | `ShoppingListResponseDto` (`openItems` gefüllt, `boughtItems` leer) | – |
| GET | `/api/shopping-list` | 200 | `ShoppingListResponseDto` | – |
| PUT | `/api/shopping-list/items/{id}/check` | 204 | – | 404 |
| PUT | `/api/shopping-list/items/{id}/uncheck` | 204 | – | 404 |

**Generierungsverhalten:** Löscht alle bestehenden Items (auch bei leerem Pool → leere Listen). `AlwaysInStock`-Filter im SKELETON nicht aktiv.

---

## Frontend-Seiten

### Navigation
- **Mobile (< 768px):** Burger-Menü (MUI Drawer)
- **Desktop (≥ 768px):** Horizontale Tabs

Menü-Punkte: Zutaten | Rezepte | Wochen-Pool | Einkaufsliste

### /ingredients – Zutaten-Seite
- Liste (Name, Einheit)
- FAB "Neue Zutat" → Dialog (Name required, Einheit required)
- Löschen-Button pro Zeile mit Bestätigungsdialog

### /recipes – Rezepte-Seite
- Liste aller Rezepte (nur Titel)
- FAB "Neues Rezept" → `/recipes/new`
- Klick auf Rezept → Detailansicht (in-page expand oder `/recipes/{id}`)

### /recipes/{id} – Rezept-Detailansicht
- Titel, Quelle (URL als Link ODER Bild als Vorschau), Zutaten-Liste, Schritte (nummeriert)
- Button "Zum Pool hinzufügen"

### /recipes/new – Rezept-Formular
- Titel (required)
- Quelle: Radio "URL" oder "Foto" → entsprechendes Eingabefeld
- Zutaten: Autocomplete-Dropdown (sucht in `/api/ingredients`) + Menge + Einheit + Hinzufügen; "Neue Zutat anlegen"-Option bei fehlendem Eintrag
- Schritte: Textfeld + "Schritt hinzufügen"
- Validierung: mind. 1 Zutat, mind. 1 Schritt
- Speichern → POST /api/recipes

### /weekly-pool – Wochen-Pool
- Liste der Pool-Rezepte mit "Entfernen"-Button
- Button "Einkaufsliste generieren" (prominent) → POST /api/shopping-list/generate → navigiert zur Einkaufsliste

### /shopping-list – Einkaufsliste
- **Zwei Bereiche:** "Noch kaufen" (BoughtAt == null) | "Zuletzt gekauft" (BoughtAt != null)
- **Kachel-Layout** (min. 80×80px Touch-Target): Generic Icon, Zutat-Name, Menge + Einheit
- Klick togglet zwischen offen ↔ gekauft (Optimistic UI)
- Offen: volle Farbe; Gekauft: grau, reduzierte Opacity
- Leer: "Pool ist leer. Füge Rezepte zum Pool hinzu und generiere die Liste."

---

## Akzeptanzkriterium (Walking Skeleton)

1. Zutat anlegen (z.B. "Tomaten, Stück")
2. Rezept anlegen (Titel + mind. 1 Zutat + 1 Schritt)
3. Rezept dem Pool hinzufügen
4. Einkaufsliste generieren → zeigt "Tomaten Xg"
5. Artikel abhaken → verschiebt in "Zuletzt gekauft"
