# Spec-Audit Baseline

<!--
wann-lesen: Vor oder während einer erneuten Spec-Review, um bekannte Findings herauszufiltern.
-->

Dokumentiert alle Findings aus allen bisherigen Spec-Audits.
Bei künftigen Reviews: Findings die hier als "bekannt / erledigt" oder "bekannt / Code-Bug" gelistet sind, können übersprungen werden.

---

## Methode

Zwei parallele Explore-Agenten:
- **Agent A:** Alle Spec-Dokumente → strukturierte Behavior-Liste
- **Agent B:** Gesamter Backend-Code inkl. Tests → strukturierte Behavior-Liste

Danach manueller Diff im Hauptkontext, kategorisiert in:
- **A – Im Code, nicht in Specs** → Spec ergänzt
- **B – Code widerspricht Spec** → Entscheidung getroffen, Spec ggf. angepasst

---

## Änderungen an der Spec (Session 043, 2026-03-31)

| # | Datei | Änderung |
|---|-------|----------|
| A3 | SKELETON_SPEC.md | TraceId-Feld zum 500-Problem-Response-Body ergänzt + Hinweis auf Log-Korrelation |
| A4 | SKELETON_SPEC.md | Check-Reihenfolge bei POST `/api/ingredients` dokumentiert (Soft-deleted vor Active-Duplicate) + Erklärung warum simultanes Auftreten über API verhindert wird |
| A5 | SKELETON_SPEC.md | Restore-409-Meldung (`"Zutat ist bereits aktiv."`) in 409-Varianten aufgenommen |
| A6/PUT | SKELETON_SPEC.md | PUT `/api/ingredients/{id}`: 409 für Soft-deleted-Ziel dokumentiert (gleicher Body wie POST) |
| A8 | SKELETON_SPEC.md | 422-Fehlermeldungen (Deutsch) für Ingredients und Recipes ergänzt |
| B4 | SKELETON_SPEC.md | `StepDto`: `stepNumber` entfernt; Sortiernotiz und Klarstellung (nur im DB-Objekt) ergänzt |

## Änderungen an der Spec (Session 044, 2026-03-31)

| # | Datei | Änderung |
|---|-------|----------|
| A-N1 | SKELETON_SPEC.md | `RecipeIngredientDto` um `ingredientName: string` ergänzt |
| A-N2 | SKELETON_SPEC.md | WeeklyPoolEntry DB-Schema: `**Index:** UNIQUE (RecipeId)` ergänzt |
| A-N4 | SKELETON_SPEC.md | 422-Fehlermeldungen Recipes: soft-deleted `ingredientId` liefert dieselbe Message wie nicht gefunden: `"Eine oder mehrere Zutaten wurden nicht gefunden."` |
| A-N5 | SKELETON_SPEC.md | GET `/api/weekly-pool`: Einträge mit soft-gelöschtem Rezept werden ausgefiltert; bei Restore bleibt Pool-Eintrag erhalten |
| B-N2/N3 | SKELETON_SPEC.md | DB-Inkonsistenz-Konvention präzisiert: Listen-Endpoints = überspringen + loggen (kein 500), Einzel-Endpoints = 500. GET `/api/ingredients` (Liste) korrigiert: kein 500 mehr in Fehler-Spalte |

---

## Bekannte Diskrepanzen: Spec korrekt, Code falsch

Der alte Backend-Code wird verworfen (Neustart mit ATDD). Die folgenden Diskrepanzen sind **erwartete Abweichungen** – kein Handlungsbedarf beim Review, nur beim Neustart.

| # | Endpoint / Bereich | Spec | Code (alt, wird verworfen) |
|---|-------------------|------|---------------------------|
| A7 | `RecipeSummaryDto` | `{ id, title }` | Hat zusätzliches `SourceUrl?`-Feld |
| A6 | POST `/api/weekly-pool` | Route: `/api/weekly-pool/recipes/{recipeId}` (kein Body) | Route: `/api/weekly-pool`, Body: `AddToPoolDto { RecipeId }` |
| B5 | POST `/api/shopping-list/generate` | Gleiche Zutat + Einheit → Mengen summieren | Kein Summieren – Items 1:1 kopiert |
| B6 | POST `/api/weekly-pool` Response | `recipeTitle` korrekt befüllt | `recipeTitle` ist immer `""` |
| PUT soft-deleted | PUT `/api/ingredients/{id}` | 409 `ingredient_soft_deleted` | 404 |
| B-N1 | Alle 422-Responses | Body: Array von Fehlermeldungen `["Fehler 1", ...]` | Body: einzelner String |
| B-N4 | PUT `/api/ingredients/{id}` | Endpoint vollständig beschrieben | Endpoint nicht implementiert |
| B-N5 | `Recipe` DB-Schema | `HasSourceImage: bool`; Bildpfad per Konvention | `SourceImagePath: string[500]?` direkt gespeichert; kein Image-Upload implementiert |
| B-N6 | Validierungsstrategie | Alle unabhängigen Felder prüfen, alle Fehler sammeln | `Sequence()` stoppt beim ersten Fehler (Fail-fast) |
| B-N2 | GET `/api/recipes` (Liste) | Korrupte Records überspringen, Fehler loggen | Gibt 500 bei erstem korrupten Record zurück |
| B-N2 | GET `/api/ingredients` (Liste) | Korrupte Records überspringen, Fehler loggen | Gibt 500 bei erstem korrupten Record zurück |
| A-N5 | GET `/api/weekly-pool` | Einträge mit soft-gelöschtem Rezept werden ausgefiltert | Kein DeletedAt-Filter im JOIN → `recipeTitle` wäre null |

---

## Bewusst nicht in die Spec aufgenommen

| Punkt | Begründung |
|-------|------------|
| CORS-Origins (`localhost:5173`, `localhost:3000`) | Dev-Konfiguration, kein API-Verhalten; gehört in ARCHITECTURE.md / DEV_WORKFLOW.md |
| `--seed-data` CLI-Flag | Dev-only, kein produktives Verhalten |
| `OneOfExtensions.Sequence()` schlägt beim ersten Fehler fehl | Bewusste Design-Entscheidung, bereits in Spec (abhängige Validierungen bleiben kurzschließend) |
| Logging-Anforderung als NFR | Für Solo-Projekt ausreichend in ARCHITECTURE.md dokumentiert; kein separater NFR-Eintrag nötig |
| Decimal Precision `decimal(10,3)` im Code | Code falsch; Spec mit `decimal(7,3)` ist die Entscheidung |
| RESTRICT FK Ingredient → RecipeIngredient | Soft-Delete umgeht physisches Löschen; RESTRICT feuert nie und ist nur defensive Absicherung |
| `RecipeDbType.SourceImagePath` (Code) | Code falsch; Spec mit `HasSourceImage: bool` + Konventionspfad ist die Entscheidung |
| Validierungsreihenfolge in `Recipe.Create()` (Title vor Zutaten) | Implementierungsdetail; Spec beschreibt nur dass abhängige Validierungen kurzschließend sind |
