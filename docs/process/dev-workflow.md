# Dev Workflow: Build, Run, Test, Migrate

<!--
wann-lesen: Bei jedem Ausführen von Befehlen (Build, Test, Run, Migration, Stryker) und beim Entwickeln von Hooks
kritische-regeln:
  - Toolchain ist WSL-nativ (.NET + Node) – dotnet/npm/npx direkt aufrufen
  - Test- und Stryker-Aufrufe: immer Python-Wrapper aus prozesscode/ verwenden – Hook erzwingt das und zeigt den richtigen Befehl
  - .NET-Tools (dotnet-ef, dotnet-stryker) sind lokal gepinnt (.config/dotnet-tools.json) – nach Clone: dotnet tool restore
  - Stryker --mutate: Pfad ist projektrelativ (ohne Server/-Präfix für Backend, ohne Client/-Präfix für Frontend); mehrere Ziele als Kommaliste, keine Brace-Globs; ein Muster ohne Treffer bricht ab
-->

<a id="DEV-inhalt"></a>
## Inhalt

| Abschnitt | Inhalt | Wann lesen |
|-----------|--------|------------|
| [Befehlsauswahl](#DEV-befehlsauswahl) | Auto-deny/allow-once-Mechanismus, Scratchpad, zusammengesetzte Befehle | Wenn ein Befehl geblockt wird |
| [Tool-Call-Failure-Analyse](#DEV-failure-analyse) | Root Cause → korrektes Muster ableiten → dokumentieren → wiederholen | Bei fehlgeschlagenen Befehlen |
| [Rückgaben abhaken](#DEV-rueckgaben) | Knoten für Agenten- und Hintergrund-Ergebnisse, Stop-Erinnerung, `rueckgaben erledigt` | Wenn der Stop-Hook an eine Rückgabe erinnert |
| [WSL-native Toolchain](#DEV-wsl-toolchain) | .NET + Node nativ; lokale Tool-Manifest; Test/Stryker via Wrapper | Beim Aufrufen von dotnet/npm |
| [Datenbank starten](#DEV-datenbank-starten) | Docker Compose, Connection String | Beim Starten der lokalen Umgebung |
| [Backend](#DEV-backend) | Build, Run | Beim Starten / Bauen des Backends |
| [Frontend](#DEV-frontend) | npm install, dev-Server, Produktions-Build, Vite-Proxy | Beim Starten / Bauen des Frontends |
| [Abhängigkeits-Durchsicht](#DEV-abhaengigkeiten-durchsicht) | Monatliche Update-Abfrage, Vorlage, Trailer | Wenn die Agenda sie fällig meldet |
| [Tests](#DEV-tests) | Alle Tests / einzelnes Projekt / einzelner Test / Frontend-Tests | Beim Ausführen von Tests |
| [Datenbank-Workflow](#DEV-datenbank-workflow) | Drop+Recreate (Entwicklung) vs. Migrations (ab V1) | Bei Schema-Änderungen |
| [Mutation Testing](#DEV-mutation-testing) | Stryker gezielt (eine Datei) und vollständig, --mutate-Pfad-Konvention | Nach jeder Phase oder gezielt nach Änderungen |
| [Hook-Entwicklung](#DEV-hook-entwicklung) | Exit-Code-Semantik, $CLAUDE_PROJECT_DIR in settings.json | Beim Schreiben oder Debuggen von Hooks |
| [Hook-Tests](#DEV-hook-tests) | pytest-Aufruf, Subshell-Pflicht, Edit-vs-Write-Delta-Verhalten | Nach Änderungen an Hook-Dateien |

> **Wann lesen:** Bei Build/Run-Problemen, Datenbankänderungen, Test-Ausführung, Mutation Testing.

---

<a id="DEV-befehlsauswahl"></a>
## Befehlsauswahl (für Agenten)

**Befehlsauswahl:** Der Bash-Permission-Hook (`check-bash-permission.py`) entscheidet automatisch:
- **Allow-Liste**: Befehle werden ohne Nachfrage ausgeführt.
- **Wrong-Approach** (z.B. `dotnet test` direkt, `python3 /abs/path`): Immer blockiert – es gibt eine bessere Alternative. Kein Override möglich.
- **Destruktiv** (z.B. `rm -rf`, `git reset --hard`): Auto-deny, aber per `# --allow-once` freigabefähig.
- **Auto-deny**: Alle anderen Befehle werden automatisch abgelehnt.
- **`# --allow-once`**: Marker an den Befehl hängen → Hook fragt den User. Wird geloggt in `.claude/tmp/denied-commands.log`.
- **Auditoren** (die Review-Agenten, erkannt am Feld `agent_type` der Hook-Eingabe): nur lesend. Zusätzlich zur Allow-Liste muss ein Befehl eine engere Auditor-Liste treffen (`AUDITOR_PATTERNS` im Hook): Lesebefehle ohne schreibende Optionen (also kein `awk`, kein `sort -o`, `sed` nur als Zeilenbereich), git lesend, `pytest`, die Test-Runner und die Lese-, Test- und Lint-Werkzeuge aus `prozesscode` (ohne `--fix`). Rückfragen werden für sie zum Deny, auch `# --allow-once`: Reviewt wird vor dem Commit, und was ein Auditor ändert, träfe ungesicherte Arbeit. Grenze: Wer ohne bekannten `agent_type` kommt, hat die vollen Rechte. Deshalb gleicht ein Test `AUDITOREN` mit `.claude/agents/*-auditor.md` ab, und **Auditoren starten ohne `name`**: Bei einem benannten Agenten steht in `agent_type` der Name statt des Typs (live gemessen), deshalb lehnt `check-agent-start` einen solchen Start ab. `pytest` führt Testcode aus, dessen Schreibzugriffe gehen nach `tmp_path`.

**Wegwerf-Artefakte gehören ins Session-Scratchpad**, nicht ins Repo: Analyse-Scripte, Zwischenergebnisse, Diffs, Redirect-Ziele. Es liegt außerhalb des Repos, wird nicht committet und muss nicht aufgeräumt werden – es liegt unter `/tmp`, und das leert systemd beim Booten, auch mitten in einer Session. Was eine Unterbrechung überstehen muss, gehört nicht hinein. Redirects dorthin sind erlaubt; den konkreten Pfad zeigt `check-bash-permission.py --list`. In `.claude/tmp/` (gitignored) leben nur die Protokolle der Hooks und die [Rückgaben-Ablage](#DEV-rueckgaben) – kein Schreibziel für Bash.

Das **Ausführen** eines dort liegenden Scripts ist dagegen freigabepflichtig (`python3 <scratchpad>/<name>.py # --allow-once`): Ein Script führt beliebigen Code aus und umginge sonst genau die Prüfung, für die der Hook existiert – der Ablageort ändert daran nichts. Davor steht ohnehin die Werkzeugfrage: Edit, Read, `grep`/`find` und die `prozesscode`-Werkzeuge zuerst; ein eigenes Script lohnt nur, wenn es effizienter oder weniger fehleranfällig ist als diese – nicht deshalb, weil Bash gerade geblockt hat.

**Zusammengesetzte Befehle** sind erlaubt, solange jedes Teilstück erlaubt ist – Verkettung, Zeilenumbruch, Variablenzuweisung, Substitution, Heredoc, Schleifen (im Rumpf nur lesende Befehle) und Sub-Befehle aus `find -exec`/`xargs`. Nicht erlaubt ist indirekte Ausführung (`$CMD`, `eval`, `bash -c`), weil sie jede Prüfung aushebelt.

**Vollständige Liste:** `python3 -m prozesscode.hooks.check-bash-permission --list` zeigt alle erlaubten Befehle, die Projekt-Task-Wrapper (Tests/Lint/Mutation) und die Deny-Mechanik. Wird am Session-Start automatisch in den Kontext geladen.

---

<a id="DEV-failure-analyse"></a>
## Tool-Call-Failure-Analyse (Pflicht)

Schlägt ein Tool-Call fehl:
1. **Root Cause analysieren:** Was genau ist fehlgeschlagen und warum? Nicht nur die Fehlermeldung lesen, sondern die Ursache verstehen.
2. **Korrektes Muster ableiten:** Welcher Aufruf hätte funktioniert?
3. **Hier dokumentieren:** Das korrekte Muster in `docs/process/dev-workflow.md` eintragen (verhindert Wiederholung).
4. **Erst dann wiederholen** – mit dem korrekten Befehl.

Parameter einfach weglassen oder "blind" variieren ist kein Debugging.

---

<a id="DEV-rueckgaben"></a>
## Rückgaben aus dem Hintergrund abhaken

Agenten und Bash-Befehle mit `run_in_background` liefern zeitversetzt. Damit ein Ergebnis nicht
untergeht, während weitergearbeitet wird, gilt ein **Knoten im Taschentuch**:

- **Knüpfen passiert von selbst:** Jeder solche Start der Hauptsession landet als Eintrag in
  `.claude/tmp/rueckgaben/<session-id>/<id>.json` (Hook `merke-rueckgaben`, PostToolUse).
  Derselbe Hook nennt dabei als Kontext den Abhak-Befehl mit der ID – damit er beim Verarbeiten
  bekannt ist, nicht erst beim Stop. Was ein Subagent startet, verarbeitet er selbst.
- **Lösen ist deine Aufgabe:** Ist alles aus einer Rückgabe verarbeitet (jedes Finding
  umgesetzt, verworfen oder dem User vorgelegt), abhaken:
  `python3 -m prozesscode.rueckgaben erledigt <id> --ausgang '3 umgesetzt, 1 verworfen'`.
  Der Ausgang wird nicht gespeichert – er zwingt dazu, das Ergebnis zu benennen, und steht
  danach im Transkript. Offenes zeigt `python3 -m prozesscode.rueckgaben liste`.
- **Erinnert wird an zwei Stellen:** Willst du den Turn beenden, während eine fertige Rückgabe
  offen ist, blockt der Stop-Hook **einmal** und nennt sie. Wartest du bewusst oder fragst den
  User, beendest du einfach erneut. Nach `compact` oder `resume` zeigt der Session-Start die
  offenen Einträge.

Fertig oder laufend entscheidet der Harness (`background_tasks` der Stop-Eingabe), nicht die
Ablage. Sie trägt nur Offenes, mit dem letzten Eintrag verschwindet der Ordner. Verwaiste
Ordner fremder Sessions löscht der Session-Start nach 14 Tagen. Eine unlesbare Eintragsdatei
erscheint als Eintrag der Art „unlesbar“ und lässt sich ebenso abhaken. Hintergrund:
`prozesscode/rueckgaben.py`.

---

<a id="DEV-wsl-toolchain"></a>
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
python3 -m prozesscode.dotnet-test [--filter ...] [--verbose]
python3 -m prozesscode.dotnet-stryker [--mutate ...] [--verbose]

# Frontend
python3 -m prozesscode.vitest-run [--filter ...] [--verbose]
python3 -m prozesscode.playwright-test [--filter ...] [--verbose]
python3 -m prozesscode.stryker-frontend [--mutate src/...] [--verbose]
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

<a id="DEV-python-werkzeuge"></a>
### Python-Werkzeuge für den Prozess-Code (`.venv`)

Die Werkzeuge für den Prozess-Code unter `prozesscode/` (ruff, mutmut, pytest) liegen in einem
venv im Repo-Root. Das Verzeichnis ist nicht versioniert; hergestellt wird es aus
`requirements-dev.txt`:

```bash
sudo apt install python3.12-venv          # einmalig, sonst fehlt ensurepip
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

**Warum ein venv und kein `pip install --user`:** Das System-Python ist Debian-verwaltet und
weist Installationen nach PEP 668 ab (`externally-managed-environment`).

**Aufgerufen werden die Werkzeuge über ihre Wrapper**, nie direkt – `.venv/bin/ruff` steht
nicht auf der Bash-Allow-Liste:

```bash
python3 -m prozesscode.ruff-run            # Linter über prozesscode + tests
python3 -m prozesscode.ruff-run --fix      # sichere Fixes anwenden (ändert Dateien)
python3 -m prozesscode.coverage-run        # Testabdeckung (Metrik, kein Gate)
python3 -m prozesscode.mutmut-run --mutate prozesscode.anchors   # Mutationstest, Ausschnitt
```

`mutmut-run` nimmt einen **Modulpfad**, keinen Dateipfad: mutmut adressiert Mutanten über den
Modulnamen (`prozesscode.anchors.x_lies__mutmut_7`). Ohne `--mutate` läuft es über den
gesamten Prozess-Code – Stunden, also eine Sichtung für die Retro, kein Gate.

Mit `--ratchet` hält es den Score je Modul in `prozesscode/mutation-baseline.json` fest und
meldet einen Rückschritt als `✗`; Gleichstand geht durch, eine Verbesserung zieht die
Baseline nach. Kommt mutmut in einem Modul nicht durch alle Mutanten, wird es nicht verglichen,
und das Verdikt lautet `⚠ Sperrklinke ohne Aussage` (Exit 1) – kein Beleg für die Tests.
**Pflicht vor jedem Commit, der Prozess-Code ändert** – je geändertem Modul, im Skill
[`committing`](../../.claude/skills/committing/SKILL.md#CMT-gesamtpruefung). Bewusst einmal je
Commit und nicht je Edit: Ein Hook-Modul braucht Sekunden bis gut eine Minute, der Bash-Guard
gemessen siebeneinhalb Minuten – je Edit erzeugte das den Druck, unter dem ein Zwang umgangen
wird. Den Großteil kosten Mutanten, die eine echte Endlosschleife erzeugen: Sie laufen bis an das
Zeitlimit (`timeout_constant` in `setup.cfg`, dort auch, warum es nicht knapper sein darf). Ohne
jeden Zwang dagegen lagen die zwölf Dispatcher-Checks bei 37–70 %, und erst das Schließen
dieser Lücken fand neun echte Fehler in Guards und Wrappern. `--frisch` wirft `mutants/` weg;
nötig nach geänderten **Tests**, weil mutmut die Test-zu-Funktion-Zuordnung nur ergänzt und
nie bereinigt.

Zusätzlich läuft ruff **automatisch** über jede geänderte Python-Datei des Prozess-Codes
(PostToolUse, `checks/ruff_lint.py`, nicht-blockierend). Fehlt das venv, sagt der Check das –
ein Linter, der stumm ausfällt, wäre von „alles sauber" nicht zu unterscheiden.
Regelauswahl und ihre Begründung: `ruff.toml` im Root.

---

<a id="DEV-projekt-struktur"></a>
## Projekt-Struktur (Infrastructure-Referenz)

Das `Infrastructure`-Projekt ist eine separate Assembly:
- **`Infrastructure/`** – `public` (EF Core Entities, `MahlDbContext`)
- **`Server/`** – vollständig `internal` (referenziert `Infrastructure`)
- **`Server.Tests/`** – referenziert `Infrastructure` direkt (für `MahlDbContext` in Tests)

Beim Hinzufügen einer neuen Projektreferenz: `Infrastructure` → `Server` und `Infrastructure` → `Server.Tests`, aber **nicht** `Server` → `Server.Tests`. Vollständige Begründung: `docs/reference/architecture.md` [Hexagonal Architecture](../reference/architecture.md#ARC-hexagonal).

---

<a id="DEV-datenbank-starten"></a>
## Datenbank starten (Docker)

```bash
docker compose up -d
```

**Connection String** (`Server/appsettings.json`):
```
Host=localhost;Port=5432;Database=mahl;Username=mahl_user;Password=mahl_dev_password
```

---

<a id="DEV-backend"></a>
## Backend

```bash
# Build
dotnet build

# Run (Backend API – Dev-Server)
dotnet run --project Server
# → http://localhost:5059 (Port via Server/Properties/launchSettings.json; HTTP-only; OpenAPI JSON unter /openapi/v1.json)
```

---

<a id="DEV-frontend"></a>
## Frontend

Node wird von `fnm` verwaltet (Version in `Client/.nvmrc`); npm/npx laufen nativ. npm-Befehle **mit `--prefix Client` aus dem Repo-Root** ausführen, nicht per `cd Client` – ein Verzeichniswechsel überlebt den Befehl, und die folgenden Wrapper-Aufrufe scheitern dann an ihrem repo-root-relativen Pfad (`prozesscode/…`). Der Hook blockt `cd … && npm …` deshalb:

```bash
# Dependencies installieren (reproduzierbar aus package-lock.json)
npm --prefix Client ci

# Dev-Server
npm --prefix Client run dev
# → http://localhost:5173

# Produktions-Build (Output → Server/wwwroot/)
npm --prefix Client run build

# Update / Audit
npm --prefix Client update
npm --prefix Client audit fix
```

> **Playwright-Browser** (einmalig nach `npm ci` bzw. nach einem Playwright-Bump):
> `cd Client && npx playwright install chromium`; die System-Libs brauchen Root und werden
> **vom User** ausgeführt: `sudo env "PATH=$PATH" npx playwright install-deps`
> (plain `sudo npx …` schlägt fehl – `npx` liegt im fnm-User-PATH, nicht in sudos `secure_path`).
> (Neue Dependency hinzufügen statt nur installieren: `docs/reference/dependencies.md`-Prozess, dann `npm install <pkg>`.)

**Vite-Proxy:** Entwicklung proxied `/api/*` auf `http://localhost:5059` (Backend).

<a id="DEV-dependency-updates"></a>
### Nach Dependency-Updates: Pflicht-Verifikation

Updates – auch reine In-Range-Bumps via `npm update` – können Regressionen einführen (z.B. brach ein MUI-Minor-Bump den Vitest-Lauf über einen nicht unterstützten ESM-Directory-Import). Nach jedem `npm install`/`npm update` daher die volle Kette prüfen:

```bash
python3 -m prozesscode.vitest-run      # Laufzeit
python3 -m prozesscode.eslint-run      # Typ-Auflösung + Lint
python3 -m prozesscode.jscpd-run       # Config-Kompatibilität (v.a. nach Major-Bumps)
npm --prefix Client run build              # tsc + Vite-Build
```

Bei Major-Bumps zusätzlich auf **Config-Warnungen** achten (nicht nur Exit-Code) – Tools ändern still ihr Config-Schema (z.B. jscpd 5: Feld `languages` → `format`).

Wurde **Playwright** gebumpt, zusätzlich das passende Browser-Binary neu installieren – sonst bricht der E2E-Lauf mit „Executable doesn't exist" ab:

```bash
cd Client && npx playwright install chromium
python3 -m prozesscode.playwright-test   # E2E-Kette nach dem Bump verifizieren
```

---

<a id="DEV-abhaengigkeiten-durchsicht"></a>
## Abhängigkeits-Durchsicht (monatlich)

Die Session-Agenda legt sie vor, solange im laufenden Monat kein Commit die Zeile
`Dependency-Check: JJJJ-MM` trägt. Gegenstand ist **alles, womit gearbeitet wird**: die
Pakete des Produkts, die Prozess-Werkzeuge, die Toolchain darunter und Claude Code selbst – ein
veraltetes Werkzeug kostet sonst Umwege um Fehler, die oben längst behoben sind. Abgelehnte Updates
erscheinen im Folgemonat wieder; ihre Gründe stehen im Rumpf des letzten Durchsicht-Commits.

1. Updates abfragen:
   ```bash
   git log -1 --grep='^Dependency-Check:'                     # Gründe der Vormonats-Durchsicht
   dotnet list mahl.slnx package --outdated                   # NuGet (Directory.Packages.props)
   dotnet list mahl.slnx package --vulnerable --include-transitive
   dotnet tool search <id>   # je Werkzeug aus .config/dotnet-tools.json – sucht unscharf, Zeile mit exakter ID lesen
   npm --prefix Client outdated                               # Exit 1 heißt „etwas ist veraltet", kein Fehler
   npm --prefix Client audit
   .venv/bin/pip list --outdated                              # Python-Werkzeuge (requirements-dev.txt); listet auch deren Abhängigkeiten
   dotnet --version; node --version; docker --version         # Toolchain (Installation: DEV-wsl-toolchain)
   ```
   Die Toolchain-Stände gegen die offiziellen Release-Listen halten: .NET
   (`release-metadata/<major>/releases.json`, Sicherheits-Releases beachten), Node (`nodejs.org/dist/index.json`,
   LTS-Linie aus `Client/.nvmrc`), PostgreSQL (`postgresql.org/support/versioning`, Image in
   `docker-compose.yml`). Python und Docker kommen aus Ubuntu und laufen mit dessen Updates.
   Aktualisiert wird auf demselben Weg wie installiert – .NET:
   `curl -fsSL -o /tmp/dotnet-install.sh https://dot.net/v1/dotnet-install.sh && bash /tmp/dotnet-install.sh --channel <major> --install-dir ~/.dotnet`,
   Node: `fnm install <LTS-Linie> && fnm default <LTS-Linie>`.
   **Claude Code:** Abgleich nach [Anknüpfung an Claude Code](claude-code-anknuepfung.md#CCA-abgleich).
2. Dem User vorlegen: je Paket aktuell → neu, Majors und Lücken hervorgehoben, bei Majors die
   Breaking Changes aus dem Changelog; beim Claude-Code-Abgleich die berührten Anknüpfungen mit
   Befund. Er entscheidet je Update und führt es selbst aus – Edit auf die geschützten
   Abhängigkeitsdateien und `dotnet add package` / `dotnet tool update` sind gesperrt.
3. Nach den Updates verifizieren: Frontend per [Pflicht-Verifikation](#DEV-dependency-updates),
   Backend per `python3 -m prozesscode.dotnet-test`, Python-Werkzeuge per `python3 -m prozesscode.coverage-run`
   (läuft mit pytest und pytest-cov aus dem venv; `python3 -m pytest` nimmt das pytest des
   System-Pythons und prüft ein Update nicht) und `python3 -m prozesscode.ruff-run`. Nach einem mutmut-Update setzt die Sperrklinke ihre
   Baselines je Modul selbst neu (Messkennung in `mutation-baseline.json`).
   **Wertet ein Wrapper die Ausgabe eines aktualisierten Werkzeugs aus** (mutmut, Stryker,
   Playwright …), den Wrapper einmal echt laufen lassen und die gespeicherte echte Ausgabe in
   seinen Tests durch die der neuen Version ersetzen. Sie altert mit der Version: Unter mutmut
   3.8 änderte sich ein Meldungstext, `mutmut-run` meldete falsch grün, und die Tests gegen die
   alte gespeicherte Ausgabe blieben grün (S139).
4. Den abschließenden Commit mit `Dependency-Check: JJJJ-MM` im Trailer-Absatz
   versehen – auch wenn nichts aktualisiert wurde. Fehlt die Zeile, legt die Agenda die
   Durchsicht erneut vor. Der Rumpf nennt die abgelehnten Updates mit Grund – Schritt 1 des
   Folgemonats liest sie dort.

---

<a id="DEV-tests"></a>
## Tests

```bash
# Backend Tests
python3 -m prozesscode.dotnet-test
python3 -m prozesscode.dotnet-test --filter TestMethodName
python3 -m prozesscode.dotnet-test --verbose

# Frontend Unit-Tests (vitest)
python3 -m prozesscode.vitest-run
python3 -m prozesscode.vitest-run --filter Pattern   # Substring-Match gegen Testname
python3 -m prozesscode.vitest-run --file Pattern     # Filter nach Dateiname (kombinierbar mit --filter)
python3 -m prozesscode.vitest-run --verbose

# E2E-Tests (Playwright)
python3 -m prozesscode.playwright-test
python3 -m prozesscode.playwright-test --filter ingredients  # Datei- oder Testname-Filter
python3 -m prozesscode.playwright-test --verbose
```

> **E2E startet das Backend selbst** (`playwright.config.ts`, `reuseExistingServer:false` auf 5059) – vorher **keinen eigenen Backend auf 5059** laufen lassen (sonst Port-Konflikt), Postgres muss aber laufen. Begründung im Config-Kommentar.

<a id="DEV-test-container"></a>
### Test-Container zurücksetzen

Die Backend-Tests verwenden einen Postgres-Container, der Testläufe überdauert (ADR-S137-2): Er läuft
nach dem Testlauf weiter und wird nicht automatisch entfernt. Zurücksetzen – etwa bei kaputtem Zustand
oder um Ressourcen freizugeben; der nächste Testlauf legt ihn neu an:

```bash
docker rm -f -v $(docker ps -aq --filter label=reuse-id=mahl-server-tests)
```

`-v` entfernt auch das anonyme Datenvolume des Postgres-Image.

---

<a id="DEV-datenbank-workflow"></a>
## Datenbank-Workflow

<a id="DEV-drop-recreate"></a>
### Während Entwicklung (vor Production-Release): Drop + Recreate

**KEINE Migrations-Hölle** – bei Schema-Änderungen einfach neu aufbauen:

> ⚠️ **Vor `migrations remove`: handgepflegtes SQL sichern.** Die Migrationsdatei ist der
> Aufbaumechanismus für **alle** Umgebungen – Integrationstests (`PostgresContainerFixture`) und
> E2E (`E2ETestSupport`) provisionieren das Schema beide via `MigrateAsync()`, nicht via
> `EnsureCreated()`. `migrations add` erzeugt die Datei aber **ausschließlich aus dem EF-Modell**:
> Von Hand ergänzte `migrationBuilder.Sql(...)`-Blöcke kennt EF nicht und schreibt sie nicht zurück.
> Betroffen ist heute der funktionale Unique-Index `IX_Ingredients_Name_Lower`
> (`LOWER("Name")`, ADR-S105-2).
>
> Also: `grep -n "migrationBuilder.Sql" Infrastructure/Migrations/*.cs` **vor** dem Remove, und die
> Blöcke danach in `Up` **und** `Down` der neuen Datei zurückschreiben.
>
> **Der Verlust ist still.** Der Build bleibt grün, `dotnet ef` meldet nichts – erst die
> Integrationstests zeigen ihn (S120: sechs fehlschlagende Duplikat-Tests). Ohne vollständigen
> Testlauf nach dem Neu-Generieren fällt er gar nicht auf.

> **`--project` = `Infrastructure`, `--startup-project` = `Server`:** DbContext und Migrationen liegen
> im `Infrastructure`-Projekt (ADR-S041-2), die DI-/Host-Konfiguration in `Server`. `dotnet ef` braucht
> beide Angaben – nur `--project Server` scheitert mit „target project doesn't match migrations assembly".

```bash
dotnet ef database drop --force --project Infrastructure --startup-project Server   # drop ist deny → # --allow-once anhängen
dotnet ef migrations remove --project Infrastructure --startup-project Server
dotnet ef migrations add InitialCreate --project Infrastructure --startup-project Server
dotnet ef database update --project Infrastructure --startup-project Server
```

<a id="DEV-migrations"></a>
### Ab Production-Release (V1/V2): Normale Migrations

```bash
# Neue Migration hinzufügen
dotnet ef migrations add MigrationName --project Infrastructure --startup-project Server

# Migrations anwenden
dotnet ef database update --project Infrastructure --startup-project Server
```

---

<a id="DEV-mutation-testing"></a>
## Mutation Testing (Stryker.NET)

**Konfiguration:** `stryker-config.json` im Repository-Root (für Server-Projekt).

```bash
# Gezielt: Nur eine Datei (~1 min)
# Pfad ist PROJEKTRELATIV (relativ zu Server/mahl.Server.csproj), nicht solution-relativ
python3 -m prozesscode.dotnet-stryker --mutate Domain/Quantity.cs

# Vollständiger Lauf Server (~2–3 min, am Ende jeder Phase – PFLICHT)
python3 -m prozesscode.dotnet-stryker

# Mit allen nicht-getöteten Mutanten (Status, StatusReason, Zeile, Spalte)
python3 -m prozesscode.dotnet-stryker --verbose
```

> **Ausgabe:** `dotnet-stryker.py` zeigt die letzten 30 Zeilen des Stryker-Outputs, dann eine kompakte
> Zusammenfassung (Score + Survivors mit Datei/Zeile).
>
> **`--verbose`-Flag:** Zeigt alle nicht-getöteten Mutanten (Survived, Ignored, Timeout, NoCoverage)
> mit Status, StatusReason, Zeile und Spalte – nützlich für gezielte Analyse ohne Ad-hoc-Python.
>
> **Auswertungs-Script standalone** – nützlich für manuelle Analyse älterer Reports:
> `python3 -m prozesscode.stryker-summary [path/to/report.json] [--verbose]`
> `--verbose` zeigt alle nicht-getöteten Mutanten (Survived, Ignored, Timeout, NoCoverage) mit Status, StatusReason, Zeile und Spalte.
> Bei expliziter Pfad-Angabe wird der Timestamp-Check übersprungen.

> **Wichtig:** `--mutate` ersetzt die `mutate`-Liste aus `stryker-config.json`. Die Excludes
> (Migrations, DbTypes etc.) entfallen. Das ist in Ordnung, weil nur die eine Zieldatei
> getestet wird – die anderen Dateien werden als "Removed by mutate filter" ignoriert.
> Der Pfad muss **projektrelativ** angegeben werden (ohne `Server/`-Präfix).
>
> **Mehrere Ziele** als Kommaliste: `--mutate Domain/Foo.cs,Endpoints/Bar.cs`. Die Wrapper
> übersetzen das in die jeweils passende CLI-Form (Stryker.NET: mehrere `--mutate`-Flags,
> StrykerJS: eine Kommaliste – beides in S109 empirisch verifiziert). **Keine Brace-Globs**
> (`{a,b}`): beide Stryker splitten am Komma und zerreißen sie.
>
> **Ein Muster ohne Treffer bricht den Lauf ab** (Exit 2, mit Korrekturvorschlag), und ein
> Report ohne einen einzigen validen Mutanten gilt als Fehler statt als 100 %: „nichts gemessen"
> ist kein „alles getötet". Jede Auswertung nennt darum auch den **Umfang** (Dateien / valide
> Mutanten), nicht nur den Score – der Übergabe-Hash bindet den Report-*Inhalt*, nicht dessen
> Umfang, ein zu eng gelaufener Report muss also am Umfang auffallen.

**Ziel:** 100% Mutation Score. Umgang mit Survivors und Suppressionen: [Welcher Survivor bekommt welche Reaktion?](tdd-process.md#TDD-survivor-entscheidung).

**Äquivalente Mutanten supprimieren** – Syntax, Kategorienamen und Pflichtangabe (ADR oder Einzelfall-Freigabe): [Stryker-Inline-Suppressions](../guidelines/csharp-stryker.md#STK-suppressions).

> **⚠️ Scope von `disable once`:** Der Kommentar deaktiviert **alle Mutations des angegebenen Typs im nächsten syntaktischen Statement** – nicht nur die nächste Zeile.
> Bei Lambda-Aufrufen wie `group.MapPost("", async (...) => { ... })` ist das gesamte `MapPost(...)`-Statement das Ziel, nicht nur das erste Argument.
> Das bedeutet: ein `// Stryker disable once String` vor `MapPost(` deaktiviert auch alle String-Mutations im Lambda-Body (Fehlermeldungen, Location-URLs etc.).
>
> **Korrekte Platzierung:** Kommentar auf einer eigenen Zeile **direkt vor dem Ziel-String-Literal** innerhalb der Argumentliste, und kein weiterer Disable-Kommentar auf äußerer Statement-Ebene:
> ```csharp
> SomeCall(
>     // Stryker disable once String : <Begründung> (<erlaubende ADR>)
>     "<literal>",                 // ← nur diese Mutation wird deaktiviert
>     async (dto, db) => { ... }  // ← String-Mutations hier bleiben aktiv
> );
> ```
> (Die Route des Gruppen-Stamms braucht keine Suppression: sie wird als `""` geschrieben, ADR-S136-1.)
>
> Wenn der Lambda-Body keine eigenen String-Literals enthält (z.B. `MapGet`), ist die Platzierung vor dem gesamten Aufruf unproblematisch.

**Frontend (Stryker-JS):**
```bash
# Alle Dateien (~variabel)
python3 -m prozesscode.stryker-frontend

# Gezielt: eine Datei (Pfad relativ zu Client/)
python3 -m prozesscode.stryker-frontend --mutate src/pages/IngredientsPage.tsx

# Mit allen nicht-getöteten Mutanten (analog zu Backend)
python3 -m prozesscode.stryker-frontend --verbose
```

> **Ausgabe:** `stryker-frontend.py` zeigt die letzten 30 Zeilen des Stryker-Outputs, dann eine kompakte
> Zusammenfassung (Score + Survivors mit Datei/Zeile). Reports werden unter
> `StrykerOutput/Frontend/<timestamp>/reports/` abgelegt (Backend analog: `StrykerOutput/Backend/<timestamp>/`).

---

<a id="DEV-hook-entwicklung"></a>
## Hook-Entwicklung

**Aktive Hooks:** Pre/PostToolUse-Hooks in `.claude/settings.json` prüfen Bash-Berechtigungen und Code-Qualitätsregeln automatisch. Bei unerwartetem Block → Hook-Feedback in der Fehlermeldung lesen (exit 2 + stderr). Hooks-Verzeichnis: `prozesscode/hooks/` – im Python-Paket, damit mutmut sie über den Modulpfad erreicht (`.claude` ist wegen des führenden Punkts kein gültiger Paketname).

<a id="DEV-exit-codes"></a>
### Exit-Code-Semantik

| Exit-Code | Bedeutung | Claude sieht Meldung? |
|-----------|-----------|----------------------|
| `0` | OK – kein Problem | Nein |
| `1` | Fehler – Terminal-Ausgabe | Nein |
| `2` + stderr | Feedback an Claude | **Ja** (system-reminder) |

- **PreToolUse + exit 2**: blockiert die Tool-Ausführung und zeigt Claude das Feedback
- **PostToolUse + exit 2**: Tool hat bereits ausgeführt, Claude sieht Feedback (advisory)

→ Immer `exit 2` + stderr verwenden, wenn Claude die Meldung sehen und darauf reagieren soll.

<a id="DEV-project-dir"></a>
### `$CLAUDE_PROJECT_DIR` in settings.json

Hook-Commands müssen **`$CLAUDE_PROJECT_DIR`** statt `$PWD` verwenden:

```json
{ "command": "cd \"$CLAUDE_PROJECT_DIR\" && python3 -m prozesscode.hooks.mein-hook" }
```

Die Hooks laufen als **Paketmodule** (`-m`), nicht als Dateipfad: Sie nutzen relative Importe
und laden ohne Paketkontext nicht. Das `cd` davor setzt den Repo-Root als Arbeitsverzeichnis,
damit `prozesscode` auf dem Importpfad liegt; es läuft in der Hook-eigenen Shell und
persistiert nirgends.

**Warum nicht `$PWD`?** `$PWD` ist fragil: wenn Claude `cd` in einem Bash-Tool-Call ausführt, persistiert der neue CWD für alle folgenden Bash-Calls in dieser Session. Hooks erben dieses CWD – alle `$PWD`-basierten Pfade zeigen dann auf das falsche Verzeichnis. `$CLAUDE_PROJECT_DIR` zeigt immer auf den Projekt-Root, unabhängig vom CWD.

**KRITISCH:** `cd` in ein Unterverzeichnis bricht im *Bash-Tool* die Hook-Chain bis zum
nächsten Neustart – das Verzeichnis bleibt für alle folgenden Aufrufe gesetzt:
```bash
# FALSCH – persistiert CWD, bricht Hooks:
cd Client && npm run build

# RICHTIG – ohne Verzeichniswechsel:
npm --prefix Client run build
```
Ebenso `git -C <pfad>` oder der Pfad als Argument. Eine Subshell `(cd Client && …)` hielte das
Verzeichnis zwar fest, lässt die Allow-Liste aber nicht zu. Zurück zum Root führt
`cd <absoluter Repo-Pfad>`; der Bash-Guard lässt diesen Pfad absolut stehen.

<a id="DEV-hooks-dynamisch"></a>
### Hooks werden dynamisch geladen

Änderungen an `settings.json` werden **sofort** wirksam – kein Neustart von Claude Code nötig. Claude Code liest die Hook-Konfiguration bei jeder Hook-Invocation neu.

<a id="DEV-hook-tests"></a>
## Tests: Code-Quality-Hooks

Nach Änderungen an Hook-Dateien automatisierte Tests ausführen:

```bash
python3 -m pytest tests/ -q
```

> Vom Repo-Root aus aufrufen: `tests/conftest.py` legt den Root auf den Importpfad, damit
> `prozesscode` als Paket auflöst.

> **Edit vs. Write:** `tdd_one_test` und `test_patterns` berechnen bei Edit ein **Delta**
> (new − old). Bei Write wird das Delta gegen die aktuelle Datei auf Disk berechnet
> (existiert sie nicht: gegen leer). Alle anderen Checks prüfen nur `new_content` –
> kein Unterschied zwischen Edit und Write.

Die Testfälle liegen in `tests/test_<checkname>.py`.
