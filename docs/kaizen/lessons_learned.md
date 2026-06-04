# Lessons Learned

<!--
Format: Einträge pro Session gruppiert. Ein Bullet pro Erkenntnis.
Pflicht: Jede Session endet mit mindestens einem Eintrag – "Keine Learnings" nur mit expliziter Begründung.
Technische Schuld gehört in AGENT_MEMORY.md, nicht hierher.

Eintrag-Format:
  ## Session NNN – YYYY-MM-DD

  - **[SCHWERE] [KATEGORIE] [KONTEXT] Kurztitel**
    Was: Ein Satz – was ist passiert?
    Warum: Ein Satz – Ursache.
    Regel: Die destillierte Erkenntnis (imperative Form).

Schwere:    KRITISCH | HOCH | MITTEL | GERING
Kategorien: PROZESS | AGENT | QUALITÄT | TOOLING
Kontext:    TDD | C#-Code | TS-Code | Review | Agent-Prompt | Skill-Nutzung |
            Session-Struktur | Tooling | Gherkin | Doku | Sonstiges

Alle drei Tags sind Pflicht. Definitionen und Reaktionsregeln: docs/kaizen/PROCESS.md

Vor dem Eintrag prüfen: Gab es ein falsches Agenten-Verhalten das wieder auftreten kann? Nein → kein Eintrag (Infra-Wissen → DEV_WORKFLOW.md / Config). Details: docs/kaizen/PROCESS.md

Nach der Sitzung prüfen: Gehört ein Eintrag in principles.md oder countermeasures.md?
KRITISCH-Findings werden sofort behandelt (Andon-Cord) – hier trotzdem dokumentieren.
-->

> **Format-Referenz:** `docs/kaizen/PROCESS.md`
> **Archiv:** `docs/kaizen/archive/`

## Session 071 – 2026-06-04

- **[HOCH] [AGENT] [Doku] Dateiinhalt ohne Verifikation zitiert**
  Was: Die Zeichenfolge "Bei Löschen, Archivieren, Überschreiben" wurde zweimal als konkretes Zitat aus einer Datei präsentiert (erst CODING_GUIDELINE_UX.md, dann CLAUDE.md) — sie existiert in keiner der beiden.
  Warum: Schlussfolgerung aus dem Kontext als Zitat präsentiert, ohne Read-Tool-Verifikation.
  Regel: Vor dem Zitieren einer konkreten Zeichenfolge aus einer Datei immer mit Read-Tool verifizieren — Paraphrasen und Schlussfolgerungen sind kein Zitat.

- **[MITTEL] [PROZESS] [Gherkin] Szenarien-Reihenfolge im Workshop nicht korrekt angewandt**
  Was: Neue Szenarien ohne Backend-Interaktion (Feld-Init, Abbrechen) wurden nach dem bestehenden "Zutat anlegen"-Szenario eingefügt statt davor.
  Warum: Die Sortierregel "trivialster zuerst" wurde nicht auf Backend-Unabhängigkeit als Komplexitätskriterium angewandt.
  Regel: Szenarien ohne Backend-Interaktion kommen vor Szenarien mit mutierenden Server-Anfragen — gilt auch beim Einfügen in bestehende Feature-Files.

## Session 070 – 2026-06-04

- **[MITTEL] [TOOLING] [Agent-Prompt] Hintergrund-Subagenten scheitern an Edit/Write-Permissions**
  Was: A8- und E1-Subagenten wurden mit `run_in_background: true` gestartet und konnten keine Dateien editieren, obwohl der User mündlich Freigabe erteilt hatte.
  Warum: Hintergrund-Agenten haben keinen interaktiven Bestätigungskanal – Permission-Prompts für Edit/Write können nicht an den User weitergeleitet werden.
  Regel: Subagenten die Dateien editieren müssen als Vordergrund-Agenten starten (kein `run_in_background: true`); alternativ relevante Pfade vorab in `settings.json` unter `permissions.allow` eintragen.

---
