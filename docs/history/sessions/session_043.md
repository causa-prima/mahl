# Session 043 – 2026-04-01

## Phase
SKELETON – Neustart-Vorbereitung

## Ziel der Session
Sauberer Neustart: gesamten Anwendungscode löschen, Infrastruktur bereinigen, Dependency-Hook einrichten, dann mit BDD/Gherkin + Outside-In ATDD neu beginnen.

## Was wurde gemacht

### Neustart-Diskussion & Strategie
- Vorgehensplan besprochen: Aufräumen → Commit → dann US-904 mit Gherkin starten
- Entschieden: Gherkin **nicht** vorab für alle Stories schreiben, sondern jeweils vor dem Feature

### Git-Setup
- `git config --global user.name/email` eingerichtet (war nicht konfiguriert)
- SSH-Authentifizierung für GitHub eingerichtet (Passwort-Auth seit 2021 abgeschafft)
- Upstream-Tracking für `main` gesetzt (`git push --set-upstream origin main`)

### Erster Commit: Akkumulierter Stand
- Alle seit dem letzten Commit angesammelten Änderungen committet und gepusht
- `.gitignore` erweitert: `Server/wwwroot/` und `.claude/tmp/` ignorieren

### Lösch-Entscheidung
- Entschieden: **gesamten Anwendungscode löschen**, nur Qualitäts-Configs behalten
- Behalten: `stryker-config.json`, `coverlet.runsettings`, `.editorconfig`, `Directory.Build.props`, `Client/tsconfig*.json`, `Client/eslint.config.js`, `docker-compose.yml`, `docs/`, `.claude/`
- Gelöscht: `Server/`, `Server.Tests/`, `mahl.sln`, `Client/src/`, `Client/package.json` etc.

### Dependency-Hook
- `check-dependency-allowlist.py`: PreToolUse-Hook blockiert Agent-Edits auf `package.json`, `*.csproj` und `DEPENDENCIES.md`
- Hook sofort beim Test an `DEPENDENCIES.md` verifiziert (Edit wurde korrekt geblockt)
- `test_dependency_allowlist.py`: 10 Tests, alle grün
- `settings.json` aktualisiert: Hook vor `check-code-quality-blocking` eingehängt
- `DEPENDENCIES.md` Enforcement-Sektion manuell vom User aktualisiert

### Commit
- Alles in einem Commit (diskutiert: 1 vs 2, entschieden für 1 da sachlich zusammengehörend)

## Ergebnisse
- Repo ist sauber – kein Anwendungscode mehr vorhanden
- Dependency-Hook aktiv und getestet
- Bereit für US-904 (Zutaten CRUD) mit Gherkin + Outside-In ATDD

## Offene Punkte / Nächste Session
- US-904: `features/ingredients.feature` schreiben → E2E-Test (rot) → Backend-Test (rot) → Implementierung (grün)
- Solution-Datei, `.csproj`-Dateien, `Program.cs` neu anlegen (vom User, da durch Hook geschützt)

## Probleme / Hindernisse
- `git add -A` / `git commit` zweimal durch stale `index.lock` blockiert → manuell gelöscht
- `git rm -r` durch Bash-Hook geblockt (matched `rm -r`-Pattern) → User musste direkt ausführen
- `!`-Präfix im Claude Code Chat nicht copy-pasteable → User musste manuell tippen
- Hook-Import via Bindestrich-Dateiname (`check-dependency-allowlist.py`) nicht direkt importierbar → `importlib.util` verwendet
