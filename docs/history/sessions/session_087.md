# Session 087 – 2026-06-18

**Phase:** SKELETON
**Fokus:** Offenen OBS-Backlog (S085/086) abarbeiten + AGENT_MEMORY-Restruktur

## Implementiert

### OBS-1 – Bash-Hook: Repo-Pfad-Normalisierung
`check-bash-permission.py` normalisiert absolute WSL-Repo-Pfade → relativ (außer in `cmd.exe`-Regionen), `# --allow-once` unberührt. Bei Änderung `updatedInput` (umgeschriebener Befehl) + `additionalContext`. PreToolUse-Output-Vertrag vorab gegen offizielle Doku verifiziert; Hook live verifiziert (Script-Inhalt ist sofort aktiv, nur Hook-*Registrierung* braucht Restart). 280 PASS.

### OBS-3 – Script-Output / Tooling-Nutzung
A: Audit – alle 7 Wrapper geben bereits nur Relevantes aus (kein Change). C: `--list`/SessionStart-Hinweis „ohne tail/grep nutzen". D: erlaubte Befehle → `.claude/tmp/allowed-commands.log` (live verifiziert). B (tail-Deny) zurückgestellt.

### CLI-Vereinheitlichung (Anstoß User, aus OBS-3)
`--detail` → `--verbose` in allen Wrappern; `--help` selbst-dokumentierend via `description=__doc__` + `RawDescriptionHelpFormatter`; `eslint-run`/`jscpd-run` auf argparse; `parse_args()` vor `check_dotnet_dll_lock()`. ADR **verworfen** (Harness-Ergonomie gehört nicht in `adr.md`, nur App/Code/Tests).

### OBS-7 – ESLint-Metriken + Guideline
`max-depth` 4 / `max-params` 4 (warn) ergänzt; `max-lines-per-function` error→warn 50, für Test/Spec aus. `coding-guideline-general.md`: Aspiration-vs-Lint-Backstop (Verweis auf Config, keine Zahlen-Kopie). ESLint grün.

### OBS-8 – Modell-Defaults
6 read-only-Auditoren `model: sonnet`, beide Layer-Implementer `inherit`; `review-code`/`implementing-scenario`/`review-workflow` um „Modellwahl vor Spawn" ergänzt.

### OBS-14 – countermeasures.md: Fließtext + CM-IDs
Tabelle → Fließtext-Blöcke mit `CM-S<NNN>-<n>`; `retro_report.py` `load_cm` parst Header/Metadaten/Problem (am LL-Parser orientiert), `cm_id` im Datenmodell + Escalated-Report; 5 neue Tests (14 grün). `process.md` „Tabelle"→„Datei" nachgezogen.

### OBS-16-A – AGENT_MEMORY-Restruktur
Physischer Split: `docs/tech-debt.md` (IDs `TD-S…`, Fließtext, Priorität/Problem/Behebung-Trigger, ID-sortiert) + `docs/open-questions.md` (`OQ-S…`). AGENT_MEMORY auf schlanken Auto-Inject (27 Zeilen / 2,2 KB; war ~7 KB): Phase / Aktuelle Story / **Nächstes Szenario** / Prioritäten. Pflege-Konvention in `closing-session` Schritt 8; ~8 Referenzen nachgezogen.

## Probleme / Findings
- **LL-S087-1 (MITTEL):** Neue Tracker-Datei ohne vorherige Spiegelung der Sibling-Konventionen → ~4 Überarbeitungsrunden.
- **LL-S087-2 (MITTEL):** V1-vs-V2-Analyse übersah Lese-/Schreib-Token-Redundanz (nur Injektion betrachtet) → Empfehlung auf unvollständiger Basis, vom User korrigiert.

## Entscheidungen
- **O3b statt W5/Ableitung** für „Nächstes Szenario": Feature-File-Reihenfolge ≠ Umsetzungsreihenfolge (Priorität überschreibt) → explizit hingeschriebenes Feld, nicht abgeleitet.
- **Generator (B) verworfen** für Szenario-Tracking; DONE-aus-Tests scheitert am fehlenden maschinellen Mapping (CamelCase-Testnamen ≠ Szenario-Titel) → OBS-S087-1.

## Offene Punkte
- **OBS-4** (TS-LSP-Pilot) bleibt – einziges verbliebenes Element des S085/086-Backlogs.
- Neue Beobachtungen: **OBS-S087-1** (tech-debt Keyword/Relevanz-Script), **OBS-S087-2** (gemeinsame Tracker-Datei-Konvention dokumentieren).
- UMGESETZT-OBS (1/3/7/8/14/16) wandern bei der nächsten Retro ins Archiv (Retro-Trigger, nicht Session-Abschluss).
- Nicht committet vor diesem Abschluss-Commit.
