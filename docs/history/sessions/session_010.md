# Session 10 – 2026-02-27

## Phase
SKELETON 🔄 (Backend vollständig, Frontend ausstehend)

## Thema
Skills & Guidelines-Architektur – keine Produktionscode-Änderungen.

## Implementiertes

### Neue Datei: `docs/CODING_GUIDELINE_GENERAL.md`
Sprachunabhängige Prinzipien extrahiert und zentralisiert:
- KISS (Keep It Simple)
- Naming (GLOSSARY, selbsterklärende Namen)
- Komplexitätsgrenzen (~20 Zeilen, Verschachtelung ≤3)
- Paradigmen-Übersichtstabelle (C# vs. TypeScript für Immutability, ROP, etc.)

### Angepasst: `docs/CODING_GUIDELINE_CSHARP.md`
Verweis auf `CODING_GUIDELINE_GENERAL.md` am Anfang ergänzt.

### Angepasst: `docs/CODING_GUIDELINE_TYPESCRIPT.md`
Verweis auf `CODING_GUIDELINE_GENERAL.md` am Anfang ergänzt. Veralteter Verweis auf C#-Guideline als "Referenz" entfernt.

### Angepasst: `docs/REVIEW_CHECKLIST.md`
- Einführungshinweis: Checkliste ist der retrospektive Review-Modus zu den Guidelines.
- Neuer Block "Allgemeine Prinzipien": KISS- und Naming-Checkpoint.
- Alter "Naming & Sprache"-Block in neuen Block integriert (kein separater Block mehr).

### Neu: `.claude/skills/write-code/SKILL.md`
Triggert bei Code-Schreiben. Orchestriert: General-Guideline lesen → Sprach-Guideline lesen → TDD (tdd-workflow Skill) → Selbst-Review (REVIEW_CHECKLIST.md). Kein duplizierter Guideline-Inhalt.

### Neu: `.claude/skills/review-code/SKILL.md`
Triggert bei Code-Reviews. Orchestriert: REVIEW_CHECKLIST.md durchgehen → Review-Agents spawnen (scope-basiert per LLM_PROMPT_TEMPLATE.md).

### Angepasst: `CLAUDE.md`
Navigation-Tabelle: General-Guideline als Einstiegspunkt für Code-Schreiben, eigene Zeile für allgemeine Coding-Prinzipien.

## Architektur-Entscheidungen

- **Guidelines = präskriptiv, Checklist = retrospektiv**: Beide Dokumente behalten ihre Rolle. Die Checklist ist kein Duplikat, sondern der Review-Modus zu den Guidelines.
- **Kein Inhalt in Skills, nur Verweise**: Skills orchestrieren – Guideline-Inhalte gehören in die Guideline-Dateien.
- **CODING_GUIDELINE_GENERAL.md** verhindert strukturell Drift zwischen C# und TS.

## Offene Punkte
- Prioritäten aus Session 9 bleiben unverändert (Frontend-Neuimplementierung, Hook-Umstellungen).
