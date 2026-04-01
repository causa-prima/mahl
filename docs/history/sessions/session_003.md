# Session 003 – 2026-02-24

## Ziel der Session

Coding-Richtlinien (fDDD, ROP, Type-Driven Development) formal einführen und in die gesamte Agenten-Dokumentation integrieren.

## Implementiertes

### Neu erstellt
- `docs/CODING_GUIDELINE_TYPESCRIPT.md` – TypeScript/React-spezifische Coding-Guideline mit Äquivalenten zu den C#-Prinzipien:
  - Immutability (`const`, `readonly`, kein direktes Mutieren)
  - Branded Types statt Primitive Obsession
  - Discriminated Unions ("Make Illegal States Unrepresentable")
  - `neverthrow` für Railway-Oriented Programming
  - Pure Functions / Separation of Concerns (domain/ / services/ / Komponenten)
  - Pragmatische Test-Code-Regeln

### Geändert
- `CLAUDE.md` – Zwei neue Zeilen in der Navigationstabelle:
  - `C#-Code schreiben` → `docs/CODING_GUIDELINE_CSHARP.md`
  - `TypeScript/React-Code schreiben` → `docs/CODING_GUIDELINE_TYPESCRIPT.md`

- `docs/ARCHITECTURE.md` – Neue Sektion 0 "Design Philosophy" (vor der alten Sektion 0):
  - Überblick der drei Kernprinzipien (Type-Driven, ROP, Immutability)
  - Verweis auf beide Guideline-Dateien
  - Test-Code-Ausnahmen dokumentiert
  - Alte Sektion 0 umbenannt zu "0b"

- `docs/LLM_PROMPT_TEMPLATE.md` – Hinweis-Box am Anfang:
  - Jeder Code-schreibende/reviewende Agent liest zuerst die passende Richtlinie

- `.claude/agents/code-quality.md` – Kontext-Abschnitt am Ende um beide Guideline-Dateien erweitert

- `.claude/agents/test-quality.md` – Neuer Prüfpunkt 5 (Einhaltung Coding-Richtlinien im Test-Code) + Kontext-Abschnitt

- `.claude/commands/feature.md` – Coding-Richtlinien als Pflichtlektüre vor dem Start ergänzt

## Diskutierte Konzepte (keine Implementierung)

**Frage 1:** Sind fDDD/ROP/Type-Driven auf TypeScript anwendbar?
→ Ja, mit Anpassungen. TypeScript ist bei Sum Types sogar ausdrucksstärker (native Discriminated Unions). Branded Types ersetzen `readonly record struct`. `neverthrow` ersetzt `OneOf`.

**Frage 2:** Gelten Richtlinien auch für Test-Code?
→ Ja, mit pragmatischen Abschwächungen. Immutability und Branded Types: ✅ anwenden. ROP-Verkettung: `._unsafeUnwrap()` in Tests erlaubt. `try/catch`: in Tests erlaubt.

**Frage 3:** Wie in die Dokumentation integrieren?
→ Drei Ebenen: (A) neue Guideline-Dateien, (B) CLAUDE.md-Navigation, (C) Agent-Prompts.

## Probleme / Offene Punkte

- Keine technischen Probleme.
- Offen: `docs/REVIEW_CHECKLIST.md` könnte einen Punkt zu "Branded Types in TypeScript" bekommen – wurde zurückgestellt.

## Ergebnis

Alle Agenten lesen ab sofort die sprachspezifischen Coding-Richtlinien als Pflicht vor dem Schreiben oder Reviewen von Code.
