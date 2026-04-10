# Session 051 – 2026-04-10

## Phase
SKELETON – gherkin-workshop US-904

## Ziel
Fehlende Szenarien für US-904 (Zutaten verwalten) identifizieren, ausarbeiten und freigeben.

## Durchgeführt

### gherkin-workshop US-904 (vollständiger Durchlauf)
- **Schritt 0:** Kontext geladen (USER_STORIES.md, GLOSSARY.md, E2E_TESTING.md, decisions.md, bestehendes Feature-File mit 6 Szenarien + 6 TODOs)
- **Schritt 1 (Dialog, 3 Runden):** Geklärt:
  - Case-insensitiver Duplikat-Check, kein Auto-Capitalize, gespeichert wird getippter Wert nach Trimming
  - Max. Länge: Name 30 Zeichen / Einheit 20 Zeichen; Fehlermeldungstexte vereinbart
  - Restore via POST: übernimmt neue Einheit + neuen Namen
  - Parallelfall Restore-409: transparent (Zutat erscheint aktiv)
  - Restore-UI nicht in SKELETON-Scope (V1)
  - Update + Tags: V1-Scope (nicht SKELETON)
- **Schritt 2 (Parallele Entdeckung):** 3 Agents (Example Mapping, State-Transition, Input-Partition) – Ergebnis: 16 neue Szenarien identifiziert, 2 offene Fragen zu Restore-Semantik
- **Schritt 3 (Synthese):** Deduplizierung, vollständige Gherkin-Formulierung
- **Schritt 4 (Review-Loop, 3 Iterationen):**
  - Iteration 1: 2 HIGH (Full State fehlend in Duplikat-Szenarien, `{name}`-Semantik ungeklärt) + 4 MEDIUM + 3 LOW → alle behoben
  - Iteration 2: 2 HIGH (Full State "Neue Zutat anlegen", Update+Tags-Scope) + 4 MEDIUM → HIGH behoben; Scope als V1 dokumentiert
  - Iteration 3: 0 CRITICAL, 2 HIGH (Zutat löschen Given/Then, Sort-Assertion trivial) → behoben nach User-Dialog
- **Schritt 5 (Feature-File & Freigabe):** Implizit freigegeben

### decisions.md – neue Einträge
- Name max 30 Zeichen / Einheit max 20 Zeichen + Fehlermeldungstexte
- Case-insensitiver Duplikat-Check, kein Auto-Capitalize
- `{name}` in Duplikat-Fehlermeldung = Request-Wert (getrimmt)
- Restore via POST: übernimmt neue Einheit + neuen Namen
- Restore Parallelfall (409): Client zeigt Zutat als aktiv, Einheit nicht kontrollierbar
- DELETE 404 UI-Fehlermeldung: `"Zutat wurde nicht gefunden."`

## Ergebnis
`features/ingredients.feature`: 6 → 23 Szenarien (4 HP / 10 Error / 9 EC)

## Offene Punkte
- V1: gherkin-workshop für US-904 Update (Bearbeiten) + Tags → in AGENT_MEMORY Prio 2
