# Session 28 – 2026-03-16

## Thema
Hook-Architektur: Wrapper-Scripts statt wachsender Regex-Patterns im Bash-Permission-Hook

## Kontext / Ausgangspunkt
Der `check-bash-permission.py`-Hook hatte zuletzt ein neues `output=$(cmd.exe ...)` Allow-Pattern bekommen, weil Agenten die Pipe-nach-cmd.exe-Einschränkung mit Variable-Capture umgingen. Das führte zur Frage: Sollen wir immer komplexere Patterns hinzufügen, oder gibt es eine bessere Architektur?

## Diskussion & Entscheidungen

### Hook-Meldungen verbessert
- Pipe-nach-cmd.exe-Meldung: Varianten A/B/C mit konkreten Beispielen
- Unsafe-Redirect-Meldung: Hinweis auf Scripts ergänzt
- Stryker-DENY-Meldung: auf neues Script-Interface aktualisiert

### Analyse: Patterns vs. Scripts
Ausführliche Pro/Contra-Analyse ergab: Patterns sind gut für Sicherheitsregeln (stabil, klar), Scripts besser für Anwendungsfälle (WSL-Komplexität, erweiterbar).

Bewertung aller Kandidaten → 2 Scripts sinnvoll (test, stryker), Rest via Pattern oder trivial:
- `dotnet-test.py` ✅ – häufigster Anwendungsfall, komplexes 2-Zeilen-Pattern
- `dotnet-stryker.py` ✅ – fragiles PRIORITY_ALLOW-Regex
- `dotnet-build.py` ❌ – einfaches Pattern, kein Mehrwert
- `dotnet-run.py` ❌ – Agenten starten keine Server
- `dotnet-ef.py` ❌ – einfache Hook-Patterns reichen
- `npm.py` ❌ – Pattern deckt es ab
- `run-hook-tests.py` ❌ – Pattern `python3 -m pytest .claude/` reicht
- `npm install` ❌ ALLOW – führt externen Code aus, bleibt `ask`

## Implementiertes

### Neue Scripts
- `.claude/scripts/_util.py`: `_win_path()` + `run_dotnet()` Helper
- `.claude/scripts/dotnet-test.py`: `--project`, `--filter`, `--verbose`
- `.claude/scripts/dotnet-stryker.py`: dünner Wrapper, ruft stryker + `stryker-summary.py` auf

### Hook-Änderungen (`check-bash-permission.py`)
- `PRIORITY_ALLOW_PATTERNS` vollständig entfernt (Variable, Kommentar, Schritt 0)
- `dotnet test` → neues DENY-Pattern (Script verwenden)
- `dotnet stryker` DENY-Meldung auf Script-Interface aktualisiert
- Stryker-PRIORITY_ALLOW entfernt (ersetzt durch Script)
- `output=$(cmd.exe ... dotnet test)` ALLOW entfernt (jetzt DENY)
- `output=$(cmd.exe ... dotnet build)` ALLOW bleibt (für build noch sinnvoll)
- Neu ALLOW: `dotnet ef migrations add/remove/list`, `database update`
- Neu ALLOW: `python3 -m pytest .claude/`
- npm run: ALLOW bleibt; npm install: bleibt `ask`

### Tests
- RED-Tests für `dotnet test` direkt, Variable-Capture für test
- Tests für alle neuen ALLOW-Patterns (ef, pytest, Scripts)
- 57 pytest-Tests ✅, Hook-Tests alle grün

### Dokumentation aktualisiert
- `DEV_WORKFLOW.md`: Scripts als primäre Beispiele, Varianten A–D, Stryker-Sektion
- `TDD_PROCESS.md`: `--files` (falscher Flag) → `--mutate` + Script
- `.claude/skills/tdd-workflow/skill.md`: cmd.exe → Script
- `.claude/skills/review-code/SKILL.md`: "via cmd.exe-Wrapper" → Script
- `docs/slow-commands.md`: alle Einträge auf Scripts umgestellt

## Ergebnisse
- Hook deutlich schlanker: kein PRIORITY_ALLOW mehr, 2 weniger ALLOW-Patterns
- Agenten haben klare, direkte Befehle statt WSL-Workarounds
- Fehlermeldungen enthalten jetzt immer konkrete Alternativen

## Offene Punkte
- Stryker-Findings (Mittel-Priorität) aus Session 25 noch offen (Layer-Isolation RecipesEndpoints etc.)
- Frontend-Implementierung steht noch aus
