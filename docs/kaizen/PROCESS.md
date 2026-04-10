# Kaizen-Prozess

<!--
wann-lesen: Beim Schreiben eines lessons_learned-Eintrags (Schwere/Kategorie/Kontext bestimmen),
            beim Starten einer Retro, beim Bewerten einer Maßnahme.
-->

## Eintrag-Format (lessons_learned.md)

Einträge werden pro Session gruppiert:

```markdown
## Session NNN – YYYY-MM-DD

- **[SCHWERE] [KATEGORIE] [KONTEXT] Kurztitel**
  Was: Ein Satz – was ist passiert?
  Warum: Ein Satz – Ursache.
  Regel: Die destillierte Erkenntnis (imperative Form).
```

Alle drei Tags sind Pflicht. Definitionen: Abschnitte unten.

---

## Schwere-Kategorien

| Schwere | Definition | Sofortreaktion | Maßnahmen-Anspruch |
|---------|-----------|----------------|-------------------|
| **KRITISCH** | Verursacht signifikanten Rework oder Qualitätsverlust; darf unter keinen Umständen wiederholt werden | **Andon-Cord:** Arbeit sofort stoppen, Ursache analysieren, Gegenmaßnahme definieren – erst dann weitermachen | Poka-yoke **Pflicht** – schwächere Maßnahmen reichen nicht |
| **HOCH** | Verzögert die Arbeit spürbar oder gefährdet Qualität | In derselben Session: Eintrag in `lessons_learned.md` + `countermeasures.md` | Poka-yoke anstreben wenn verhältnismäßig; sonst expliziter Schritt in Guideline oder Skill |
| **MITTEL** | Kleine Prozessabweichung, schnell bemerkt | Eintrag in `lessons_learned.md` | Poka-yoke anstreben wenn einfach umsetzbar; sonst Eintrag in `principles.md` wenn wiederholt |
| **GERING** | Stilistisch oder präferenzbedingt | Eintrag in `lessons_learned.md` | Keine Maßnahme nötig |

---

## Bereichs-Kategorien

Entscheidungskriterium: **Wo liegt der Fix?**

| Kategorie | Beschreibung | Beispiele |
|-----------|-------------|---------|
| **PROZESS** | Fix liegt im Workflow, in einem Skill-Schritt oder in der Session-Struktur | TDD-Verstoß, Skill-Schritt übersprungen, Evaluation+Implementierung kombiniert |
| **AGENT** | Fix liegt in der Art wie Sub-Agenten instruiert werden | Reviewer mit Iterations-Vorwissen, unklarer Prompt, falscher Kontext an Agent |
| **QUALITÄT** | Fix liegt im Code oder in der Test-Qualität (kein Prozess-Muster) | Primitive Typen statt Domain-Typen (isolierter Fall), fehlender Test |
| **TOOLING** | Fix liegt in Build, Infrastruktur, IDE oder Konfiguration | WSL/npm-Problem, CI-Konfiguration, Build-Pipeline |

> Wenn ein QUALITÄT-Problem wiederholt auftritt → Ursache ist meist PROZESS (Skill/Hook fehlt).

---

## Kontext-Tags

Beschreibt *was* konkret betroffen war – feiner als die Kategorie.

| Tag | Bedeutung |
|-----|-----------|
| `TDD` | Test-first-Disziplin, Red-Green-Refactor-Loop |
| `C#-Code` | C#-Implementierung, .NET-Guidelines |
| `TS-Code` | TypeScript/React-Implementierung, Frontend-Guidelines |
| `Review` | Code- oder Dokument-Review-Prozess |
| `Agent-Prompt` | Formulierung von Sub-Agenten-Instruktionen |
| `Skill-Nutzung` | Anwendung oder Aufrufen von Skills |
| `Session-Struktur` | Session-Planung, Kontext-Management, Scope |
| `Tooling` | Build, IDE, WSL, Infrastruktur |
| `Gherkin` | Feature-Files, Szenario-Formulierung |
| `Doku` | Guidelines, Docs, Entscheidungen pflegen |
| `Sonstiges` | Passt in keinen anderen Tag |

**Pflege der Kontext-Tags:**
- Alle `Sonstiges`-Einträge werden in jeder Retro explizit gesichtet – Ziel: fehlende Tags ableiten
- Sehr häufige Tags (>30% aller Einträge) werden auf sinnvolle Aufteilung untersucht
- Neue oder geänderte Tags werden in dieser Datei dokumentiert

---

## Wann gehört etwas wohin?

| Ziel | Kriterium |
|------|-----------|
| `lessons_learned.md` | Jedes Finding, immer |
| `principles.md` | Verhaltensregel die in jeder Session gilt; zu querschnittlich für eine Guideline/Skill |
| `countermeasures.md` | Jedes KRITISCH- oder HOCH-Finding sofort; MITTEL/GERING wenn Retro ein Muster aufdeckt |
| Guideline / Skill | Das Problem liegt an einem fehlenden oder falschen Schritt in einem konkreten Arbeitsablauf. Die Änderung ist direkt als Regel/Schritt in einem bestehenden Dokument formulierbar. (Meist wird zusätzlich ein `countermeasures.md`-Eintrag angelegt, der auf diese Änderung verweist.) |

---

## Retro-Trigger: Jenga-Score

Der Jenga-Score misst akkumulierten Problemdruck seit der letzten Retro.
Script `jenga_score.py` berechnet ihn aus der aktuellen `lessons_learned.md`.

**Start-Wert:** 100 Punkte

| Ereignis | Abzug |
|---------|-------|
| Session (immer) | -5 |
| KRITISCH-Finding | -25 |
| HOCH-Finding | -10 |
| MITTEL-Finding | -3 |
| GERING-Finding | -1 |

**Bei Jenga-Score ≤ 0:** Nächste Session beginnt mit einer Retro (Skill `kaizen`).

Scripts: `.claude/scripts/jenga_score.py` (nach jeder Session) und `.claude/scripts/retro_report.py` (zur Retro).
Nach einer Retro wird `lessons_learned.md` archiviert → Jenga-Score startet neu bei 100.

---

## Scripts

### jenga_score.py
Läuft nach jeder Session (im `closing-session`-Skill).
Input: `docs/kaizen/lessons_learned.md`
Output: Jenga-Score + Zähltabelle (Schwere × Kategorie × Kontext)

### retro_report.py
Läuft zu Beginn jeder Retro (im `kaizen`-Skill).
Input: aktuelle `lessons_learned.md` + alle Archiv-Dateien in `docs/kaizen/archive/`
Output: Aggregation, Zeitreihen-Charts, Pattern-Kandidaten (Muster ≥2× im Fenster, gefiltert gegen `countermeasures.md`),
semantisches Clustering (ab 50 Einträgen), Trendanalyse je Kategorie.
Details: Kommentar-Header in `.claude/scripts/retro_report.py`.

---

## Archivierung (nach Retro)

Die aktuelle `lessons_learned.md` wird nach `docs/kaizen/archive/` verschoben.
Ablauf: Skill `kaizen`, Schritt 5.
Der Jenga-Score startet automatisch neu – `jenga_score.py` liest immer nur die aktuelle Datei.

---

## BEWÄHRT-Kriterium für Countermeasures

Eine Maßnahme gilt als BEWÄHRT wenn:
- Die relevante Situation nach Einführung der Maßnahme mindestens 3× aufgetreten ist
- Kein Rückfall beobachtet wurde
- "Aufgetreten" = die Art der Arbeit, bei der das Problem hätte entstehen können, hat stattgefunden

Nachweis: Session-Dateien in `docs/history/sessions/` lesen und beurteilen, ob die relevante Arbeit stattfand.

## Obsolet-Kriterien für Countermeasures

Ein Eintrag ist obsolet wenn:
- Das betroffene Tool oder die Technologie nicht mehr genutzt wird
- Der zugrundeliegende Prozess so fundamental umgebaut wurde, dass das Problem strukturell nicht mehr entstehen kann
- Es sich um eine einmalige Situation handelte, die grundsätzlich nicht wiederkehren kann
