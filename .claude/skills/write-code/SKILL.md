---
name: write-code
description: >
  Pflicht-Vorbereitung vor dem Schreiben von C# oder TypeScript/React-Code:
  Guidelines lesen, TDD-Workflow starten, Selbst-Review. Verwende diesen Skill
  automatisch bevor du neuen Produktionscode in C# oder TypeScript schreibst.
user-invocable: false
---

# Skill: write-code

<a id="WRC-wann-aktiv"></a>
## Wann dieser Skill aktiv wird

Immer wenn du C#- oder TypeScript/React-Code schreibst – egal ob im Rahmen von `/feature` oder ad hoc.

---

<a id="WRC-pflicht-schritte"></a>
## Pflicht-Schritte vor dem ersten Code

<a id="WRC-guidelines-lesen"></a>
### Richtige Guidelines lesen

**Abschnittsweise lesen, nicht die ganze Datei** – soweit das Projekt einen Weg dafür anbietet
(Navigationstabelle in `CLAUDE.md`). Eine Coding-Guideline ist typischerweise um ein Vielfaches
größer als der Abschnitt, den eine konkrete Aufgabe braucht. Verschaff dir zuerst das
Inhaltsverzeichnis, dann hol gezielt. Im Zweifel die Datei ganz lesen: Zu eng zu schneiden ist
der teurere Fehler.

**Immer lesen (sprachunabhängige Grundprinzipien):**
→ `docs/guidelines/coding-guideline-general.md` – komplett, die Datei ist klein (~6 KB)

**Zusätzlich je nach Sprache:**
- C# (Backend, Tests) → `docs/guidelines/coding-guideline-csharp.md`
  - Endpoint oder Validierungskette → zusätzlich `docs/guidelines/csharp-rop.md`
  - Neuer Domain-Typ mit Zustandsvarianten → zusätzlich `docs/guidelines/csharp-sumtypes.md`
  - Stryker-Survivors behandeln ([REFACTOR](../../../docs/process/tdd-process.md#TDD-refactor)) → zusätzlich `docs/guidelines/csharp-stryker.md`
- TypeScript/React (Frontend) → `docs/guidelines/coding-guideline-typescript.md`
  - React-Komponenten (`src/components/`, `src/pages/`) → zusätzlich `docs/guidelines/coding-guideline-ux.md`

**PFLICHT-OUTPUT nach dem Lesen** – beantworte aufgabenspezifisch:
- **YAGNI:** Was implementiere ich explizit NICHT? (Nennung konkreter Nicht-Ziele)
  Für jede neue Property und jede neue Methode: „Welcher aktuell rote Test fordert genau das?"
  Kein Test → nicht schreiben – auch wenn die Property „offensichtlich bald gebraucht wird".
- **KISS:** Wie halte ich die Lösung minimal? (keine vorzeitigen Abstraktionen)
- **Fehlerbehandlung:** Welches Pattern nutze ich? (ROP/OneOf/Result – kein `throw` für Business-Fehler)

<a id="WRC-tdd"></a>
### Implementieren via TDD

→ `docs/process/tdd-process.md` (RED → GREEN → REFACTOR)

<a id="WRC-selbst-review"></a>
### Selbst-Review vor Review-Agenten

→ `docs/process/review-checklist.md` Punkt für Punkt durchgehen und Findings sofort fixen.

---

<a id="WRC-kurzcheck-alternativen"></a>
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
