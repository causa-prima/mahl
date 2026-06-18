# Dev Workflow: Build, Run, Test, Migrate

<!--
wann-lesen: Bei jedem Ausführen von Befehlen (Build, Test, Run, Migration, Stryker) und beim Entwickeln von Hooks
kritische-regeln:
  - Toolchain ist WSL-nativ (.NET + Node) – dotnet/npm/npx direkt aufrufen
  - Test- und Stryker-Aufrufe: immer Python-Wrapper aus .claude/scripts/ verwenden – Hook erzwingt das und zeigt den richtigen Befehl
  - .NET-Tools (dotnet-ef, dotnet-stryker) sind lokal gepinnt (.config/dotnet-tools.json) – nach Clone: dotnet tool restore
  - Timeouts immer setzen – Richtwerte in der Tabelle unten
  - Stryker --mutate: Pfad ist projektrelativ (ohne Server/-Präfix für Backend, ohne Client/-Präfix für Frontend)
-->

## Inhalt

| Abschnitt | Inhalt | Wann lesen |
|-----------|--------|------------|
| Befehlsauswahl & Timeouts | Auto-deny/allow-once-Mechanismus, Timeout-Richtwerte für alle relevanten Kommandos | Vor jedem lang laufenden Befehl |
| Tool-Call-Failure-Analyse | Root Cause → korrektes Muster ableiten → dokumentieren → wiederholen | Bei fehlgeschlagenen Befehlen |
| WSL-native Toolchain | .NET + Node nativ; lokale Tool-Manifest; Test/Stryker via Wrapper | Beim Aufrufen von dotnet/npm |
| Datenbank starten | Docker Compose, Connection String | Beim Starten der lokalen Umgebung |
| Backend | Build, Run, Seed-Daten | Beim Starten / Bauen des Backends |
| Frontend | npm install, dev-Server, Produktions-Build, Vite-Proxy | Beim Starten / Bauen des Frontends |
| Tests | Alle Tests / einzelnes Projekt / einzelner Test / Frontend-Tests | Beim Ausführen von Tests |
| Datenbank-Workflow | Drop+Recreate (Entwicklung) vs. Migrations (ab V1), Seed-Daten | Bei Schema-Änderungen |
| Mutation Testing | Stryker gezielt (eine Datei) und vollständig, --mutate-Pfad-Konvention | Nach jeder Phase oder gezielt nach Änderungen |
| Hook-Entwicklung | Exit-Code-Semantik, $CLAUDE_PROJECT_DIR in settings.json | Beim Schreiben oder Debuggen von Hooks |
| Hook-Tests | pytest-Aufruf, Subshell-Pflicht, Edit-vs-Write-Delta-Verhalten | Nach Änderungen an Hook-Dateien |

> **Wann lesen:** Bei Build/Run-Problemen, Datenbankänderungen, Test-Ausführung, Mutation Testing.

---

## Befehlsauswahl & Timeouts (für Agenten)

**Befehlsauswahl:** Der Bash-Permission-Hook (`check-bash-permission.py`) entscheidet automatisch:
- **Allow-Liste**: Befehle werden ohne Nachfrage ausgeführt.
- **Wrong-Approach** (z.B. `dotnet test` direkt, `python3 /abs/path`): Immer blockiert – es gibt eine bessere Alternative. Kein Override möglich.
- **Destruktiv** (z.B. `rm -rf`, `git reset --hard`): Auto-deny, aber per `# --allow-once` freigabefähig.
- **Auto-deny**: Alle anderen Befehle werden automatisch abgelehnt.
- **`# --allow-once`**: Marker an den Befehl hängen → Hook fragt den User. Wird geloggt in `.claude/tmp/denied-commands.log`.

**Vollständige Liste:** `python3 .claude/hooks/check-bash-permission.py --list` zeigt alle erlaubten Befehle, die Projekt-Task-Wrapper (Tests/Lint/Mutation) und die Deny-Mechanik. Wird am Session-Start automatisch in den Kontext geladen.

**Timeouts:** Vor jedem lang laufenden Prozess überlegen: *Wann sollte ich abbrechen?* Das Bash-Tool akzeptiert einen `timeout`-Parameter (Millisekunden). Richtwerte:

| Befehl | Erwartete Dauer | Empfohlener Timeout |
|--------|----------------|---------------------|
| `dotnet build` | 15–45 s | 90 000 ms |
| `dotnet test` (alle, mit Coverage) | 8–25 s | 50 000 ms |
| `dotnet test` (einzeln) | 5–20 s | 40 000 ms |
| `dotnet stryker` (eine Datei) | ~1 min | 120 000 ms |
| `dotnet stryker` (vollständig) | ~2–3 min | 360 000 ms |
| `npm install` | 30–120 s | 180 000 ms |
| `npm run build` | 10–30 s | 60 000 ms |
| `npm run lint` | 5–15 s | 30 000 ms |
| `npm run lint:duplicates` | 5–15 s | 30 000 ms |
| `vitest-run.py` | 5–15 s | 30 000 ms |
| `playwright-test.py` | 10–30 s | 60 000 ms |
| `stryker-frontend.py` (eine Datei) | 1–3 min | 180 000 ms |
| `stryker-frontend.py` (vollständig) | 2–5 min | 360 000 ms |
| `docker compose up -d` | 5–30 s | 60 000 ms |

Wenn ein Prozess den Timeout überschreitet:
- Warum könnte das sein? Falsches Kommando? Hängender Prozess?
- Waren Annahmen über die Umgebung falsch?
- Abbrechen oder noch warten? Begründung kommunizieren.

**Unerwartet langsame Befehle** → Zeile in `docs/process/slow-commands.md` aktualisieren (keine neuen Zeilen anlegen – bestehende Einträge updaten).

---

## Tool-Call-Failure-Analyse (Pflicht)

Schlägt ein Tool-Call fehl:
1. **Root Cause analysieren:** Was genau ist fehlgeschlagen und warum? Nicht nur die Fehlermeldung lesen, sondern die Ursache verstehen.
2. **Korrektes Muster ableiten:** Welcher Aufruf hätte funktioniert?
3. **Hier dokumentieren:** Das korrekte Muster in `docs/process/dev-workflow.md` eintragen (verhindert Wiederholung).
4. **Erst dann wiederholen** – mit dem korrekten Befehl.

Parameter einfach weglassen oder "blind" variieren ist kein Debugging.

---

## WSL-native Toolchain

.NET (SDK via `dotnet-install.sh` nach `~/.dotnet`) und Node (via `fnm`, Version in `Client/.nvmrc`)
laufen **nativ in WSL** auf einem ext4-Repo. `dotnet`/`npm`/`npx` werden direkt aufgerufen.

> **Warum WSL-nativ:** .NET und Node sind auf Linux erstklassig, die DB läuft im Container
> (kein Windows-Zwang), und das ext4-Repo vermeidet die `/mnt/c`-Mount-Latenz – alle Tool-Aufrufe
> laufen damit direkt.

**.NET-Tools sind lokal gepinnt** (`.config/dotnet-tools.json`: `dotnet-ef`, `dotnet-stryker`):
nach einem frischen Clone einmalig `dotnet tool restore`. `dotnet ef`/`dotnet stryker` lösen die
lokalen Tools dann automatisch auf.

Test- und Stryker-Aufrufe immer via Projekt-Scripts:
```bash
# Backend
python3 .claude/scripts/dotnet-test.py [--filter ...] [--verbose]
python3 .claude/scripts/dotnet-stryker.py [--mutate ...] [--verbose]

# Frontend
python3 .claude/scripts/vitest-run.py [--filter ...] [--verbose]
python3 .claude/scripts/playwright-test.py [--filter ...] [--verbose]
python3 .claude/scripts/stryker-frontend.py [--mutate src/...] [--verbose]
```

> **Einheitliche CLI:** Alle Wrapper-Scripts (auch `eslint-run.py`, `jscpd-run.py`) nutzen
> `--verbose` für „mehr als die kuratierte Default-Ausgabe" und bieten `--help` mit
> Verwendung, Beispielen und Parametern. Default-Output ist bereits gefiltert – **nicht**
> zusätzlich durch `tail`/`grep`/`head` leiten.

Alle anderen dotnet-Befehle direkt:
```bash
dotnet build
dotnet ef migrations add InitialCreate
dotnet run --project Server          # Dev-Server (Port via Server/Properties/launchSettings.json: :5059)
```

> **Parallele Builds:** Kein `dotnet watch` gleichzeitig mit `build`/`test`/`stryker` auf
> demselben Projekt laufen lassen (Race auf `bin`/`obj`). Sonst sind parallele dotnet-Prozesse unkritisch.

---

## Projekt-Struktur (Infrastructure-Referenz)

Das `Infrastructure`-Projekt ist eine separate Assembly:
- **`Infrastructure/`** – `public` (EF Core Entities, `MahlDbContext`)
- **`Server/`** – vollständig `internal` (referenziert `Infrastructure`)
- **`Server.Tests/`** – referenziert `Infrastructure` direkt (für `MahlDbContext` in Tests)

Beim Hinzufügen einer neuen Projektreferenz: `Infrastructure` → `Server` und `Infrastructure` → `Server.Tests`, aber **nicht** `Server` → `Server.Tests`. Vollständige Begründung: `docs/reference/architecture.md` Sektion 0c.

---

## Datenbank starten (Docker)

```bash
docker compose up -d
```

**Connection String** (`Server/appsettings.json`):
```
Host=localhost;Port=5432;Database=mahl;Username=mahl_user;Password=mahl_dev_password
```

---

## Backend

```bash
# Build
dotnet build

# Run (Backend API – Dev-Server)
dotnet run --project Server
# → http://localhost:5059 (Port via Server/Properties/launchSettings.json; HTTP-only; OpenAPI JSON unter /openapi/v1.json)

# Seed-Daten laden (10 Rezepte + 45 Zutaten)
dotnet run --project Server -- --seed-data
```

---

## Frontend

Node wird von `fnm` verwaltet (Version in `Client/.nvmrc`); npm/npx laufen nativ. npm-Befehle im `Client/`-Verzeichnis ausführen:

```bash
# Dependencies installieren (reproduzierbar aus package-lock.json)
cd Client && npm ci

# Dev-Server
cd Client && npm run dev
# → http://localhost:5173

# Produktions-Build (Output → Server/wwwroot/)
cd Client && npm run build

# Update / Audit
cd Client && npm update
cd Client && npm audit fix
```

> **Playwright-Browser** (einmalig nach `npm ci` bzw. nach einem Playwright-Bump):
> `cd Client && npx playwright install chromium`; die System-Libs brauchen Root und werden
> **vom User** ausgeführt: `sudo env "PATH=$PATH" npx playwright install-deps`
> (plain `sudo npx …` schlägt fehl – `npx` liegt im fnm-User-PATH, nicht in sudos `secure_path`).
> (Neue Dependency hinzufügen statt nur installieren: `docs/reference/dependencies.md`-Prozess, dann `npm install <pkg>`.)

**Vite-Proxy:** Entwicklung proxied `/api/*` auf `http://localhost:5059` (Backend).

### Nach Dependency-Updates: Pflicht-Verifikation

Updates – auch reine In-Range-Bumps via `npm update` – können Regressionen einführen (z.B. brach ein MUI-Minor-Bump den Vitest-Lauf über einen nicht unterstützten ESM-Directory-Import). Nach jedem `npm install`/`npm update` daher die volle Kette prüfen:

```bash
python3 .claude/scripts/vitest-run.py      # Laufzeit
python3 .claude/scripts/eslint-run.py      # Typ-Auflösung + Lint
python3 .claude/scripts/jscpd-run.py       # Config-Kompatibilität (v.a. nach Major-Bumps)
cd Client && npm run build                 # tsc + Vite-Build
```

Bei Major-Bumps zusätzlich auf **Config-Warnungen** achten (nicht nur Exit-Code) – Tools ändern still ihr Config-Schema (z.B. jscpd 5: Feld `languages` → `format`).

Wurde **Playwright** gebumpt, zusätzlich das passende Browser-Binary neu installieren – sonst bricht der E2E-Lauf mit „Executable doesn't exist" ab:

```bash
cd Client && npx playwright install chromium
python3 .claude/scripts/playwright-test.py   # E2E-Kette nach dem Bump verifizieren
```

---

## Tests

```bash
# Backend Tests
python3 .claude/scripts/dotnet-test.py
python3 .claude/scripts/dotnet-test.py --filter TestMethodName
python3 .claude/scripts/dotnet-test.py --verbose

# Frontend Unit-Tests (vitest)
python3 .claude/scripts/vitest-run.py
python3 .claude/scripts/vitest-run.py --filter Pattern   # Substring-Match gegen Testname
python3 .claude/scripts/vitest-run.py --file Pattern     # Filter nach Dateiname (kombinierbar mit --filter)
python3 .claude/scripts/vitest-run.py --verbose

# E2E-Tests (Playwright)
python3 .claude/scripts/playwright-test.py
python3 .claude/scripts/playwright-test.py --filter ingredients  # Datei- oder Testname-Filter
python3 .claude/scripts/playwright-test.py --verbose
```

> **E2E startet das Backend selbst** (`playwright.config.ts`, `reuseExistingServer:false` auf 5059) – vorher **keinen eigenen Backend auf 5059** laufen lassen (sonst Port-Konflikt), Postgres muss aber laufen. Begründung im Config-Kommentar.

---

## Datenbank-Workflow

### Während Entwicklung (vor Production-Release): Drop + Recreate

**KEINE Migrations-Hölle** – bei Schema-Änderungen einfach neu aufbauen:

```bash
dotnet ef database drop --force --project Server   # drop ist deny → # --allow-once anhängen
dotnet ef migrations remove --project Server
dotnet ef migrations add InitialCreate --project Server
dotnet ef database update --project Server

# Danach Seed-Daten laden:
dotnet run --project Server -- --seed-data
```

**Seed-Daten:** `Server/Data/SeedDataExtensions.cs` – implementiert als C# Extension Method `app.SeedDatabase()`.

### Ab Production-Release (V1/V2): Normale Migrations

```bash
# Neue Migration hinzufügen
dotnet ef migrations add MigrationName --project Server

# Migrations anwenden
dotnet ef database update --project Server
```

---

## Mutation Testing (Stryker.NET)

**Konfiguration:** `stryker-config.json` im Repository-Root (für Server-Projekt).

```bash
# Gezielt: Nur eine Datei (~1 min)
# Pfad ist PROJEKTRELATIV (relativ zu Server/mahl.Server.csproj), nicht solution-relativ
python3 .claude/scripts/dotnet-stryker.py --mutate Domain/Quantity.cs

# Vollständiger Lauf Server (~2–3 min, am Ende jeder Phase – PFLICHT)
python3 .claude/scripts/dotnet-stryker.py

# Mit allen nicht-getöteten Mutanten (Status, StatusReason, Zeile, Spalte)
python3 .claude/scripts/dotnet-stryker.py --verbose
```

> **Ausgabe:** `dotnet-stryker.py` zeigt die letzten 30 Zeilen des Stryker-Outputs, dann eine kompakte
> Zusammenfassung (Score + Survivors mit Datei/Zeile).
>
> **`--verbose`-Flag:** Zeigt alle nicht-getöteten Mutanten (Survived, Ignored, Timeout, NoCoverage)
> mit Status, StatusReason, Zeile und Spalte – nützlich für gezielte Analyse ohne Ad-hoc-Python.
>
> **Auswertungs-Script standalone** – nützlich für manuelle Analyse älterer Reports:
> `python3 .claude/scripts/stryker-summary.py [path/to/report.json] [--verbose]`
> `--verbose` zeigt alle nicht-getöteten Mutanten (Survived, Ignored, Timeout, NoCoverage) mit Status, StatusReason, Zeile und Spalte.
> Bei expliziter Pfad-Angabe wird der Timestamp-Check übersprungen.

> **Wichtig:** `--mutate` ersetzt die `mutate`-Liste aus `stryker-config.json`. Die Excludes
> (Migrations, DbTypes etc.) entfallen. Das ist in Ordnung, weil nur die eine Zieldatei
> getestet wird – die anderen Dateien werden als "Removed by mutate filter" ignoriert.
> Der Pfad muss **projektrelativ** angegeben werden (ohne `Server/`-Präfix).

**Ziel:** 100% Mutation Score. Ausnahmen (äquivalente Mutanten) dokumentieren in `docs/history/adr.md`.

**Äquivalente Mutanten supprimieren** – Syntax und Kategorienamen: siehe `docs/guidelines/csharp-stryker.md`. Kurzform:
```csharp
// Stryker disable once String : <Begründung>   // Doppelpunkt vor Beschreibung ist Pflicht
```

> **⚠️ Scope von `disable once`:** Der Kommentar deaktiviert **alle Mutations des angegebenen Typs im nächsten syntaktischen Statement** – nicht nur die nächste Zeile.
> Bei Lambda-Aufrufen wie `group.MapPost("/", async (...) => { ... })` ist das gesamte `MapPost(...)`-Statement das Ziel, nicht nur `"/"`.
> Das bedeutet: ein `// Stryker disable once String` vor `MapPost(` deaktiviert auch alle String-Mutations im Lambda-Body (Fehlermeldungen, Location-URLs etc.).
>
> **Korrekte Platzierung:** Kommentar auf einer eigenen Zeile **direkt vor dem Ziel-String-Literal** innerhalb der Argumentliste, und kein weiterer Disable-Kommentar auf äußerer Statement-Ebene:
> ```csharp
> group.MapPost(
>     // Stryker disable once String : Route patterns "/" and "" are treated equivalently
>     "/",                         // ← nur diese Mutation wird deaktiviert
>     async (dto, db) => { ... }  // ← String-Mutations hier bleiben aktiv
> );
> ```
> Wenn der Lambda-Body keine eigenen String-Literals enthält (z.B. `MapGet`), ist die Platzierung vor dem gesamten Aufruf unproblematisch.

**Frontend (Stryker-JS):**
```bash
# Alle Dateien (~variabel)
python3 .claude/scripts/stryker-frontend.py

# Gezielt: eine Datei (Pfad relativ zu Client/)
python3 .claude/scripts/stryker-frontend.py --mutate src/pages/IngredientsPage.tsx

# Mit allen nicht-getöteten Mutanten (analog zu Backend)
python3 .claude/scripts/stryker-frontend.py --verbose
```

> **Ausgabe:** `stryker-frontend.py` zeigt die letzten 30 Zeilen des Stryker-Outputs, dann eine kompakte
> Zusammenfassung (Score + Survivors mit Datei/Zeile). Reports werden unter
> `StrykerOutput/Frontend/<timestamp>/reports/` abgelegt (Backend analog: `StrykerOutput/Backend/<timestamp>/`).

---

## Hook-Entwicklung

**Aktive Hooks:** Pre/PostToolUse-Hooks in `.claude/settings.json` prüfen Bash-Berechtigungen und Code-Qualitätsregeln automatisch. Bei unerwartetem Block → Hook-Feedback in der Fehlermeldung lesen (exit 2 + stderr). Hooks-Verzeichnis: `.claude/hooks/`.

### Exit-Code-Semantik

| Exit-Code | Bedeutung | Claude sieht Meldung? |
|-----------|-----------|----------------------|
| `0` | OK – kein Problem | Nein |
| `1` | Fehler – Terminal-Ausgabe | Nein |
| `2` + stderr | Feedback an Claude | **Ja** (system-reminder) |

- **PreToolUse + exit 2**: blockiert die Tool-Ausführung und zeigt Claude das Feedback
- **PostToolUse + exit 2**: Tool hat bereits ausgeführt, Claude sieht Feedback (advisory)

→ Immer `exit 2` + stderr verwenden, wenn Claude die Meldung sehen und darauf reagieren soll.

### `$CLAUDE_PROJECT_DIR` in settings.json

Hook-Commands müssen **`$CLAUDE_PROJECT_DIR`** statt `$PWD` verwenden:

```json
{ "command": "python3 $CLAUDE_PROJECT_DIR/.claude/hooks/mein-hook.py" }
```

**Warum nicht `$PWD`?** `$PWD` ist fragil: wenn Claude `cd` in einem Bash-Tool-Call ausführt, persistiert der neue CWD für alle folgenden Bash-Calls in dieser Session. Hooks erben dieses CWD – alle `$PWD`-basierten Pfade zeigen dann auf das falsche Verzeichnis. `$CLAUDE_PROJECT_DIR` zeigt immer auf den Projekt-Root, unabhängig vom CWD.

**KRITISCH:** `cd` in ein Unterverzeichnis **ohne Subshell** bricht die Hook-Chain bis zum nächsten Neustart:
```bash
# FALSCH – persistiert CWD, bricht Hooks:
cd .claude/hooks && python3 -m pytest tests/ -q

# RICHTIG – Subshell, CWD bleibt erhalten:
(cd .claude/hooks && python3 -m pytest tests/ -q)
```

### Hooks werden dynamisch geladen

Änderungen an `settings.json` werden **sofort** wirksam – kein Neustart von Claude Code nötig. Claude Code liest die Hook-Konfiguration bei jeder Hook-Invocation neu.

## Tests: Code-Quality-Hooks

Nach Änderungen an Hook-Dateien automatisierte Tests ausführen:

```bash
python3 -m pytest .claude/hooks/tests/ -q
```

> pytest mit `.claude/hooks/tests/` als Pfad aufrufen (nicht `.claude/hooks/`), damit das
> `checks`-Package korrekt importiert wird.

> **Edit vs. Write:** `tdd_one_test` und `test_patterns` berechnen bei Edit ein **Delta**
> (new − old). Bei Write wird das Delta gegen die aktuelle Datei auf Disk berechnet
> (existiert sie nicht: gegen leer). Alle anderen Checks prüfen nur `new_content` –
> kein Unterschied zwischen Edit und Write.

Die Testfälle liegen in `.claude/hooks/tests/test_<checkname>.py`.
