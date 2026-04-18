---
name: write-code
description: >
  Pflicht-Vorbereitung vor dem Schreiben von C# oder TypeScript/React-Code:
  Guidelines lesen, TDD-Workflow starten, Selbst-Review. Verwende diesen Skill
  automatisch bevor du neuen Produktionscode in C# oder TypeScript schreibst.
user-invocable: false
---

# Skill: write-code

## Wann dieser Skill aktiv wird

Immer wenn du C#- oder TypeScript/React-Code schreibst – egal ob im Rahmen von `/feature` oder ad hoc.

---

## Pflicht-Schritte vor dem ersten Code

### 1. Richtigen Guidelines lesen

**Immer lesen (sprachunabhängige Grundprinzipien):**
→ `docs/CODING_GUIDELINE_GENERAL.md`

**Zusätzlich je nach Sprache:**
- C# (Backend, Tests) → `docs/CODING_GUIDELINE_CSHARP.md`
  - Endpoint oder Validierungskette → zusätzlich `docs/CSharp-ROP.md`
  - Neuer Domain-Typ mit Zustandsvarianten → zusätzlich `docs/CSharp-SumTypes.md`
  - Stryker-Survivors behandeln (Phase 3) → zusätzlich `docs/CSharp-Stryker.md`
- TypeScript/React (Frontend) → `docs/CODING_GUIDELINE_TYPESCRIPT.md`
  - React-Komponenten (`src/components/`, `src/pages/`) → zusätzlich `docs/CODING_GUIDELINE_UX.md`

**PFLICHT-OUTPUT nach dem Lesen** – beantworte aufgabenspezifisch:
- **YAGNI:** Was implementiere ich explizit NICHT? (Nennung konkreter Nicht-Ziele)
  Für jede neue Property und jede neue Methode: „Welcher aktuell rote Test fordert genau das?"
  Kein Test → nicht schreiben – auch wenn die Property „offensichtlich bald gebraucht wird".
- **KISS:** Wie halte ich die Lösung minimal? (keine vorzeitigen Abstraktionen)
- **Fehlerbehandlung:** Welches Pattern nutze ich? (ROP/OneOf/Result – kein `throw` für Business-Fehler)

### 2. Implementieren via TDD

→ `docs/TDD_PROCESS.md` (RED → GREEN → REFACTOR)

### 3. Selbst-Review vor Review-Agenten

→ `docs/REVIEW_CHECKLIST.md` Punkt für Punkt durchgehen und Findings sofort fixen.

---

## Kurzcheck: Pflicht-Alternativen

**C#**

| Statt | Verwende |
|---|---|
| `.IsT0`, `.IsT1`, `.AsT0` | `.Match()` |
| `throw` für Business-Fehler | `OneOf`/`Error<string>` |
| `new` für Domain-Entities | Factory Method |
| `public set;` (außer EF-Entities) | `init;` |

**TypeScript**

| Statt | Verwende |
|---|---|
| `try/catch` für Validierungsfehler | `neverthrow` Result |
| `any` | `unknown` + Type Guard |
| Rohe `string`/`number`/`uuid` als Domain-Konzept | Branded Type |
| `let` + Mutation | `const` + neues Objekt |

Vollständige Regeln immer in den Guidelines – nicht hier.
