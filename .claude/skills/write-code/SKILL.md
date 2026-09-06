---
name: write-code
description: >
  Pflicht-Vorbereitung vor dem Schreiben von C#, TypeScript/React oder Python:
  Guidelines lesen, TDD-Workflow starten, Selbst-Review. Verwende diesen Skill
  automatisch bevor du neuen Produktionscode in C# oder TypeScript schreibst –
  und ebenso vor Python unter prozesscode/ (Werkzeuge, Hooks, Checks), für das
  eigene Maßgaben gelten.
user-invocable: false
---

# Skill: write-code

<a id="WRC-wann-aktiv"></a>
## Wann dieser Skill aktiv wird

Immer wenn du C#- oder TypeScript/React-Code schreibst – egal ob im Rahmen von `/feature` oder ad hoc.

**Auch bei Python unter `prozesscode/`** (Werkzeuge, Hooks, Checks). Dort gilt allerdings ein
eigener, kurzer Pfad: [Prozess-Code](#WRC-prozess-code) statt der Produktcode-Pflichten.

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
- Python (`prozesscode/`) → `docs/guidelines/coding-guideline-python.md`, dann [Prozess-Code](#WRC-prozess-code)

<a id="WRC-prozess-code"></a>
### Prozess-Code: der kurze Pfad

Für Python unter `prozesscode/` gelten **eigene Maßgaben**, nicht die abgeschwächten
Produktcode-Regeln – der Grund (ein anderes Fehlerprofil) steht in
`coding-guideline-python.md`. Konkret entfällt hier alles, was den Produktcode-Pfad
ausmacht: kein PFLICHT-OUTPUT, kein Stryker, keine Coverage-Schwelle, keine
Szenario-Bindung.

Was stattdessen gilt – vier Dinge:

1. **Tests, und sie laufen von selbst.** Jede Änderung fährt die Werkzeug-Suite; rot bleiben
   ist keine Option. Red-Green-Refactor gilt unverändert.
2. **Gegenprobe bei jedem Guard.** Wer einen Hook, ein Gate oder einen Wrapper baut oder
   ändert, bricht ihn einmal absichtlich und sieht ihn anspringen. Ohne diesen Schritt ist
   nicht belegt, dass er überhaupt prüft.
   **Bei Hooks und Checks zusätzlich maschinell**, im Anschluss:
   `python3 -m prozesscode.mutmut-run --mutate prozesscode.hooks.<name> --ratchet`.
   Die Handprobe belegt, dass **ein** Fall anspringt; die Sperrklinke fragt, ob **jede**
   Bedingung des Guards von einem Test gehalten wird – und ob das schlechter geworden ist
   als beim letzten Mal. Grün heißt fertig, rot nennt die Stellen. Rechne mit ein bis zwei
   Minuten je Modul; nur für Guards, nicht für jedes Werkzeug.
3. **Verdikt statt Rohausgabe.** Werkzeuge laufen über ihre Wrapper in `prozesscode`, und
   eine Meldung nennt den Ausweg, nicht nur den Befund.
4. **Review nach eigenen Stufen.** Selbstcheck gegen
   [`RCL-prozess-code`](../../../docs/process/review-checklist.md#RCL-prozess-code) – **statt**
   der übrigen Abschnitte jener Checkliste. Ein Auditor kommt nur bei Guards und geteilten
   Modulen dazu; Auslöser und Verzichtsgrund stehen in
   [`RVC-prozess-code`](../review-code/SKILL.md#RVC-prozess-code).

Damit ist der Pfad zu Ende – die Produktcode-Schritte und der allgemeine
[Selbst-Review](#WRC-selbst-review) entfallen.

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
