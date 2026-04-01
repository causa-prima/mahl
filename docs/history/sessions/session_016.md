# Session 16 – 2026-03-03

**Phase:** SKELETON (Dokumentations-Qualität)

## Ziel

Dokumentations-Scanbarkeit verbessern: Alle Docs-Dateien erhalten einen HTML-Kommentar-Header
(`wann-lesen`/`wann-schreiben`, `kritische-regeln`) und eine Inhalt-Tabelle, damit Agenten beim
initialen Scan (~100 Zeilen) Relevanz und Struktur sofort erfassen und gezielt navigieren können.

## Durchgeführt

### Neue Header + Inhalt-Tabellen
- `docs/CODING_GUIDELINE_GENERAL.md` ✅
- `docs/CODING_GUIDELINE_CSHARP.md` ✅
- `docs/CODING_GUIDELINE_TYPESCRIPT.md` ✅ (+ Verbotene-Muster-Tabelle nach vorne verschoben)
- `docs/ARCHITECTURE.md` ✅
- `docs/TDD_PROCESS.md` ✅ (neu angelegt – Section 5 aus ARCHITECTURE.md ausgelagert)
- `docs/DEV_WORKFLOW.md` ✅
- `docs/SKELETON_SPEC.md` ✅
- `docs/GLOSSARY.md` ✅
- `docs/NFR.md` ✅
- `docs/REVIEW_CHECKLIST.md` ✅
- `docs/LLM_PROMPT_TEMPLATE.md` ✅ (+ Commands-Sektion auf Skills aktualisiert)
- `docs/history/decisions.md` ✅
- `docs/history/lessons_learned.md` ✅ (`wann-schreiben` vs. `wann-lesen` getrennt)

### Nebenbei behoben
- `CODING_GUIDELINE_CSHARP.md`: Tabelle und kanonisches Beispiel auf `readonly record struct`
  korrigiert (war inkonsistent mit tatsächlichem Code)
- `MEMORY.md`: Falsche `readonly struct`-Notiz korrigiert
- `tdd-workflow/skill.md`: `ExcludingMissingMembers`-Beschreibung korrigiert (verboten, nicht
  "nur für anonyme Assertions"); Vollständige-Referenz-Verweis an Anfang verschoben
- `security.md`: Falsche Sektionsnummer (5 → 8) korrigiert, NFR.md als Referenz ergänzt
- `LLM_PROMPT_TEMPLATE.md`: Nicht-existente `.claude/commands/`-Einträge durch korrekte Skills ersetzt

### Split-Entscheidungen
- **TDD_PROCESS.md**: Section 5 aus ARCHITECTURE.md ausgelagert (175 Zeilen, eigenständig, hat
  eigenen Skill) → ARCHITECTURE.md jetzt ~270 Zeilen kürzer
- Alle anderen Dateien: Kein Split (zu kurz oder inhaltlich zu eng verknüpft)

### CLAUDE.md
- Neue Zeile "Code schreiben (jede Art)" → `docs/TDD_PROCESS.md` + `docs/DEV_WORKFLOW.md`
- "Tests / Mutation Testing" → `docs/TDD_PROCESS.md`

## Ergebnis

Alle 13 Dokumentationsdateien haben scanbare Header. Ein Agent sieht beim Öffnen einer Datei
sofort: wann er sie lesen soll, welche Regeln kritisch sind, und welcher Abschnitt für seine
aktuelle Aufgabe relevant ist.

## Offene Punkte

Keine neuen – die offenen Punkte aus Session 15 (Stryker Mittel-Prio, NoSource, Frontend) bleiben
unverändert die nächsten Prioritäten.
