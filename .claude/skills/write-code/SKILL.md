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

**PFLICHT-OUTPUT nach dem Lesen** – beantworte aufgabenspezifisch:
- **YAGNI:** Was implementiere ich explizit NICHT? (Nennung konkreter Nicht-Ziele)
- **KISS:** Wie halte ich die Lösung minimal? (keine vorzeitigen Abstraktionen)
- **Fehlerbehandlung:** Welches Pattern nutze ich? (ROP/OneOf/Result – kein `throw` für Business-Fehler)

### 2. Implementieren via TDD

→ `docs/TDD_PROCESS.md` (RED → GREEN → REFACTOR)

### 3. Selbst-Review vor Review-Agenten

→ `docs/REVIEW_CHECKLIST.md` Punkt für Punkt durchgehen und Findings sofort fixen.

---

## Kurzcheck: Was niemals erlaubt ist

| Verboten (C#) | Verboten (TypeScript) |
|---|---|
| `.IsT0`, `.IsT1`, `.AsT0` | `try/catch` für Validierungsfehler |
| `throw` für Business-Fehler | `any` statt `unknown` |
| `new` für Domain-Entities ohne Factory | Rohe `string`-IDs ohne Branded Type |
| `public set;` (außer EF-Entities) | Mutable State (`let` + Mutation) |

Vollständige Regeln immer in den Guidelines – nicht hier.
