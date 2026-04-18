# Dev Workflow: Build, Run, Test, Migrate

<!--
wann-lesen: Bei jedem Ausführen von Befehlen (Build, Test, Run, Migration, Stryker) und beim Entwickeln von Hooks
kritische-regeln:
  - Test- und Stryker-Aufrufe: immer Python-Wrapper aus .claude/scripts/ verwenden – Hook erzwingt das und zeigt den richtigen Befehl
  - Alle anderen dotnet-Befehle: cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && dotnet ..." (WSL hat kein .NET)
  - Pipes nach cmd.exe funktionieren nicht in WSL – Variable capturen oder Script verwenden
  - Timeouts immer setzen – Richtwerte in der Tabelle unten
  - Stryker --mutate: Pfad ist projektrelativ (ohne Server/-Präfix für Backend, ohne Client/-Präfix für Frontend)
  - Shell-Scripts nach Write sofort: sed -i 's/\r//' datei.sh (NTFS-Zeilenenden)
-->

## Inhalt

| Abschnitt | Inhalt | Wann lesen |
|-----------|--------|------------|
| Befehlsauswahl & Timeouts | Auto-deny/allow-once-Mechanismus, Timeout-Richtwerte für alle relevanten Kommandos | Vor jedem lang laufenden Befehl |
| Bash-Befehle in WSL/cmd.exe | Pipe-Regeln, Varianten (Script / Variable / Datei / direkt) | Bei cmd.exe + Unix-Pipe-Problemen |
| Tool-Call-Failure-Analyse | Root Cause → korrektes Muster ableiten → dokumentieren → wiederholen | Bei fehlgeschlagenen Befehlen |
| KRITISCH: dotnet in WSL | `cmd.exe /c "..."` Wrapper-Pflicht, Beispiele | Immer wenn dotnet aufgerufen wird |
| Datenbank starten | Docker Compose, Connection String | Beim Starten der lokalen Umgebung |
| Backend | Build, Run, Seed-Daten | Beim Starten / Bauen des Backends |
| Frontend | npm install, dev-Server, Produktions-Build, Vite-Proxy | Beim Starten / Bauen des Frontends |
| Tests | Alle Tests / einzelnes Projekt / einzelner Test / Frontend-Tests | Beim Ausführen von Tests |
| Datenbank-Workflow | Drop+Recreate (Entwicklung) vs. Migrations (ab V1), Seed-Daten | Bei Schema-Änderungen |
| Mutation Testing | Stryker gezielt (eine Datei) und vollständig, --mutate-Pfad-Konvention | Nach jeder Phase oder gezielt nach Änderungen |
| Hook-Entwicklung | Exit-Code-Semantik, $CLAUDE_PROJECT_DIR in settings.json, NTFS-Zeilenenden, NTFS-Löschen | Beim Schreiben oder Debuggen von Hooks |
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
| `vitest-run.py` | 5–15 s | 30 000 ms |
| `playwright-test.py` | 10–30 s | 60 000 ms |
| `stryker-frontend.py` (eine Datei) | 1–3 min | 180 000 ms |
| `stryker-frontend.py` (vollständig) | 2–5 min | 360 000 ms |
| `docker-compose up -d` | 5–30 s | 60 000 ms |

Wenn ein Prozess den Timeout überschreitet:
- Warum könnte das sein? Falsches Kommando? Hängender Prozess?
- Waren Annahmen über die Umgebung falsch?
- Abbrechen oder noch warten? Begründung kommunizieren.

**Unerwartet langsame Befehle** → Zeile in `docs/slow-commands.md` aktualisieren (keine neuen Zeilen anlegen – bestehende Einträge updaten).

---

## Bash-Befehle in WSL/cmd.exe: Pipe-Regeln

Pipes nach `cmd.exe` funktionieren nicht in WSL (`cmd.exe ... | grep ...` schlägt fehl).
Außerdem: Unix-Befehle (`tail`, `grep`, `head`) **innerhalb** der `cmd.exe /c "..."` Quotes sind cmd.exe unbekannt.

### Varianten – wann welche?

**A) Standard für dotnet test / dotnet stryker: Projekt-Scripts verwenden**

```bash
python3 .claude/scripts/dotnet-test.py [--filter TestName] [--verbose]
python3 .claude/scripts/dotnet-stryker.py [--mutate Domain/Foo.cs] [--detail]
```

**B) Für andere cmd.exe-Aufrufe: Output in Variable capturen, dann filtern**
Wenn Output in den Context passt.

```bash
output=$(cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && dotnet build")
echo "$output" | grep -E "(error|warning CS|Build succeeded|Build FAILED)"
```

**C) Sehr große Outputs: Redirect in Datei**
Nur wenn der Output zu groß für den Context wäre. Datei danach löschen.

```bash
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && <befehl> > .claude\tmp\out.txt 2>&1"
cat /mnt/c/Users/kieritz/source/repos/mahl/.claude/tmp/out.txt
```

**D) Kein Filter nötig: cmd.exe direkt**
Wenn der vollständige Output erwünscht ist.

```bash
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && dotnet build"
```

### Was NICHT funktioniert

```bash
# FALSCH – Pipe nach cmd.exe funktioniert nicht in WSL:
cmd.exe /c "cd /d C:\...\mahl && dotnet build" 2>&1 | tail -20

# FALSCH – Unix-Befehle innerhalb der cmd.exe-Quotes:
cmd.exe /c "cd /d C:\...\mahl && dotnet build 2>&1 | tail -20"
```

## Tool-Call-Failure-Analyse (Pflicht)

Schlägt ein Tool-Call fehl:
1. **Root Cause analysieren:** Was genau ist fehlgeschlagen und warum? Nicht nur die Fehlermeldung lesen, sondern die Ursache verstehen.
2. **Korrektes Muster ableiten:** Welcher Aufruf hätte funktioniert?
3. **Hier dokumentieren:** Das korrekte Muster in `docs/DEV_WORKFLOW.md` eintragen (verhindert Wiederholung).
4. **Erst dann wiederholen** – mit dem korrekten Befehl.

Parameter einfach weglassen oder "blind" variieren ist kein Debugging.

---

## KRITISCH: dotnet in WSL

.NET ist **nur auf dem Windows-Host** installiert – nicht in WSL.

Test- und Stryker-Aufrufe immer via Projekt-Scripts (kapseln cmd.exe intern):
```bash
# Backend
python3 .claude/scripts/dotnet-test.py [--filter ...] [--verbose]
python3 .claude/scripts/dotnet-stryker.py [--mutate ...] [--detail]

# Frontend
python3 .claude/scripts/vitest-run.py [--filter ...] [--verbose]
python3 .claude/scripts/playwright-test.py [--filter ...] [--verbose]
python3 .claude/scripts/stryker-frontend.py [--mutate src/...] [--detail]
```

Alle anderen dotnet-Befehle via cmd.exe-Wrapper:
```bash
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && dotnet <command>"

# Beispiele:
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && dotnet build"
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && dotnet run --project Server"
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && dotnet ef migrations add InitialCreate"
```

---

## Projekt-Struktur (Infrastructure-Referenz)

Das `Infrastructure`-Projekt ist eine separate Assembly:
- **`Infrastructure/`** – `public` (EF Core Entities, `MahlDbContext`)
- **`Server/`** – vollständig `internal` (referenziert `Infrastructure`)
- **`Server.Tests/`** – referenziert `Infrastructure` direkt (für `MahlDbContext` in Tests)

Beim Hinzufügen einer neuen Projektreferenz: `Infrastructure` → `Server` und `Infrastructure` → `Server.Tests`, aber **nicht** `Server` → `Server.Tests`. Vollständige Begründung: `docs/ARCHITECTURE.md` Sektion 0c.

---

## Datenbank starten (Docker)

```bash
docker-compose up -d
```

**Connection String** (`Server/appsettings.json`):
```
Host=localhost;Port=5432;Database=mahl;Username=mahl_user;Password=mahl_dev_password
```

---

## Backend

```bash
# Build
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && dotnet build"

# Run (Backend API)
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && dotnet run --project Server"
# → läuft auf https://localhost:7xxx / http://localhost:5059 (OpenAPI JSON unter /openapi/v1.json)

# Seed-Daten laden (10 Rezepte + 45 Zutaten)
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && dotnet run --project Server -- --seed-data"
```

---

## Frontend

> **WSL-Hinweis:** `npm` in WSL zeigt auf die Windows-nvm-Installation mit defekten Pfaden. Alle npm-Befehle via `cmd.exe /c` ausführen (analog zu dotnet):

```bash
# npm install (einmalig)
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl\Client && npm install"

# Playwright-Browser installieren (einmalig nach npm install)
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl\Client && npx playwright install chromium"

# Dev-Server
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl\Client && npm run dev"
# → http://localhost:5173

# Produktions-Build (Output → Server/wwwroot/)
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl\Client && npm run build"

# npm update / audit
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl\Client && npm update"
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl\Client && npm audit fix"
```

**Vite-Proxy:** Entwicklung proxied `/api/*` auf `http://localhost:5059` (Backend).

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
python3 .claude/scripts/vitest-run.py --verbose

# E2E-Tests (Playwright)
python3 .claude/scripts/playwright-test.py
python3 .claude/scripts/playwright-test.py --filter ingredients  # Datei- oder Testname-Filter
python3 .claude/scripts/playwright-test.py --verbose
```

---

## Datenbank-Workflow

### Während Entwicklung (vor Production-Release): Drop + Recreate

**KEINE Migrations-Hölle** – bei Schema-Änderungen einfach neu aufbauen:

```bash
# Im Server-Verzeichnis (via cmd.exe wrapper):
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl\Server && dotnet ef database drop --force"
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl\Server && dotnet ef migrations remove"
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl\Server && dotnet ef migrations add InitialCreate"
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl\Server && dotnet ef database update"

# Danach Seed-Daten laden:
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && dotnet run --project Server -- --seed-data"
```

**Seed-Daten:** `Server/Data/SeedDataExtensions.cs` – implementiert als C# Extension Method `app.SeedDatabase()`.

### Ab Production-Release (V1/V2): Normale Migrations

```bash
# Neue Migration hinzufügen
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && dotnet ef migrations add MigrationName --project Server"

# Migrations anwenden
cmd.exe /c "cd /d C:\Users\kieritz\source\repos\mahl && dotnet ef database update --project Server"
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
python3 .claude/scripts/dotnet-stryker.py --detail
```

> **Ausgabe:** `dotnet-stryker.py` zeigt die letzten 30 Zeilen des Stryker-Outputs, dann eine kompakte
> Zusammenfassung (Score + Survivors mit Datei/Zeile).
>
> **`--detail`-Flag:** Zeigt alle nicht-getöteten Mutanten (Survived, Ignored, Timeout, NoCoverage)
> mit Status, StatusReason, Zeile und Spalte – nützlich für gezielte Analyse ohne Ad-hoc-Python.
>
> **Auswertungs-Script standalone** – nützlich für manuelle Analyse älterer Reports:
> `python3 .claude/scripts/stryker-summary.py [path/to/report.json] [--detail]`
> `--detail` zeigt alle nicht-getöteten Mutanten (Survived, Ignored, Timeout, NoCoverage) mit Status, StatusReason, Zeile und Spalte.
> Bei expliziter Pfad-Angabe wird der Timestamp-Check übersprungen.

> **Wichtig:** `--mutate` ersetzt die `mutate`-Liste aus `stryker-config.json`. Die Excludes
> (Migrations, DbTypes etc.) entfallen. Das ist in Ordnung, weil nur die eine Zieldatei
> getestet wird – die anderen Dateien werden als "Removed by mutate filter" ignoriert.
> Der Pfad muss **projektrelativ** angegeben werden (ohne `Server/`-Präfix).

**Ziel:** 100% Mutation Score. Ausnahmen (äquivalente Mutanten) dokumentieren in `docs/history/decisions.md`.

**Äquivalente Mutanten supprimieren** – Syntax und Kategorienamen: siehe `docs/CSharp-Stryker.md`. Kurzform:
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

# Mit Survivor-Details (mehr Output-Zeilen)
python3 .claude/scripts/stryker-frontend.py --detail
```

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
(cd .claude/hooks && python3 -m pytest tests/ -p no:cacheprovider -s -q)
```

### Hooks werden dynamisch geladen

Änderungen an `settings.json` werden **sofort** wirksam – kein Neustart von Claude Code nötig. Claude Code liest die Hook-Konfiguration bei jeder Hook-Invocation neu.

### Shell-Scripts auf NTFS (WSL)

Das `Write`-Tool erzeugt auf NTFS `\r\n`-Zeilenenden. Nach jedem `Write` einer `.sh`-Datei:

```bash
sed -i 's/\r//' /pfad/zur/datei.sh
```

Alternativ: Script via `Bash`-Tool mit `cat > file << 'EOF' ... EOF` erstellen (schreibt Unix-Zeilenenden).

### Dateien auf NTFS löschen (WSL)

`rm` auf `/mnt/c/...`-Pfaden kann mit "Read-only file system" scheitern. Alternative:

```bash
cmd.exe /c "del /f C:\Users\kieritz\source\repos\mahl\pfad\zur\datei.txt"
```

Mehrere Dateien sequenziell:

```bash
cmd.exe /c "del /f C:\...\datei1.txt && del /f C:\...\datei2.txt && echo Done"
```

---

## Tests: Code-Quality-Hooks

Nach Änderungen an Hook-Dateien automatisierte Tests ausführen:

```bash
python3 -m pytest .claude/hooks/tests/ -p no:cacheprovider -s -q
```

> **`-p no:cacheprovider -s`** ist nötig wegen WSL/NTFS-Einschränkungen (pytest-Tempfiles).
> pytest muss mit `.claude/hooks/tests/` als Pfad aufgerufen werden (nicht `.claude/hooks/`),
> damit das `checks`-Package korrekt importiert wird.

> **Edit vs. Write:** `tdd_one_test` und `test_patterns` berechnen bei Edit ein **Delta**
> (new − old). Bei Write wird das Delta gegen die aktuelle Datei auf Disk berechnet
> (existiert sie nicht: gegen leer). Alle anderen Checks prüfen nur `new_content` –
> kein Unterschied zwischen Edit und Write.

Die Testfälle liegen in `.claude/hooks/tests/test_<checkname>.py`.
