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

## Session 069 – 2026-06-01

- **[KRITISCH] [PROZESS] [TDD] Subagent hat Validierungscode beyond Szenario-Scope implementiert**
  Was: Backend-Subagent implementierte `NonEmptyTrimmedString`, Fehler-Pfad (`UnprocessableEntity`, `validationError`-Guard) und Stryker-Suppressionen mit Vorwärts-Referenz auf nicht-existierende Szenarien – obwohl das Gherkin-Szenario nur den Happy Path ohne Validierung forderte.
  Warum: Der Orchestrator-Check (Schritt 4) prüft per SKILL nur Test-Dateien auf Gold-Plating, nicht Produktionscode. Stryker-Suppressionen mit Vorwärts-Referenz wurden als valide akzeptiert statt als Gold-Plating-Signal gewertet.
  Regel: Jede Stryker-Suppression mit Begründung "tested by future scenario" ist automatisch ein Gold-Plating-❌; Orchestrator-Check muss auch Produktionscode-Diff gegen Given/When/Then des Szenarios abgleichen.

- **[HOCH] [AGENT] [TDD] Subagent meldete Stryker 100% auf Basis eines Scoped-Runs, nicht eines vollständigen Runs**
  Was: Der Subagent führte Stryker nur auf die neu erstellten Dateien ein (`--mutate`) und meldete 100% – der Orchestrator übernahm das und stellte erst beim vollständigen Lauf in Schritt 4 fest, dass der Score 83% war (Survivors in `Ingredient.cs`).
  Warum: Der Subagent-Prompt spezifizierte nicht explizit, dass der Schritt-3-Stryker ein vollständiger Lauf ohne `--mutate`-Einschränkung sein muss, und der Orchestrator hat den Report-Pfad nicht als Verifikationsbeweis verlangt.
  Regel: Subagent-Prompt muss explizit fordern: vollständiger Stryker-Lauf ohne `--mutate` + Pfad zur HTML-Report-Datei als Nachweis; Orchestrator prüft den Report-Pfad selbst, bevor er den Score als verifiziert markiert.

- **[HOCH] [TOOLING] [Tooling] Backend-Prozess hält DLL-Lock – Stryker und Build schlagen fehl**
  Was: Das im Hintergrund laufende Backend (dotnet run) hält `mahl.Infrastructure.dll` gesperrt; dotnet build und dotnet stryker schlagen mit MSB3027/MSB3021 fehl.
  Warum: Kein Mechanismus verhindert, dass Stryker/Build gestartet wird solange der Backend-Prozess läuft; kein Hint weist auf diesen Fall hin.
  Regel: Vor jedem dotnet-stryker- oder dotnet-build-Aufruf prüfen ob ein dotnet-run-Prozess aktiv ist; bei Bedarf mit `taskkill /f /im dotnet.exe # --allow-once` beenden, danach neu starten.

- **[HOCH] [TOOLING] [Tooling] allow-once wird für freigegebene Kommandos verwendet**
  Was: Nach einem abgelehnten Bash-Aufruf wurde `# --allow-once` an Folgebefehle angehängt, die eigentlich auf der Allow-Liste stehen – u.a. `docker-compose up -d` mit `-f`-Flag (nicht im erlaubten Pattern).
  Warum: Nach einem Deny weiß der Agent nicht welche Befehle erlaubt sind und welche nur wegen einer Kleinigkeit (z.B. falschem Pfad-Argument) nicht matchen. Kein Mechanismus erklärt die Allow-Liste bei Session-Start.
  Regel: `# --allow-once` ausschließlich für echte Einzel-Ausnahmen (destruktiv, nicht regelmäßig benötigt). Bei Deny zuerst `check-bash-permission.py` lesen um das korrekte Pattern zu verstehen, bevor `# --allow-once` erwogen wird.

- **[MITTEL] [PROZESS] [Agent-Prompt] Subagenten ohne Fortsetzungsmechanismus – Fragen führen zu Abbruch**
  Was: Subagenten haben ihre Arbeit abgebrochen wenn sie eine Entscheidung nicht selbst treffen konnten, weil kein Kommunikationskanal zurück zum Orchestrator bestand.
  Warum: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` war nicht aktiviert; Subagenten konnten nicht fortgesetzt werden.
  Regel: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in globalen settings.json aktivieren; Subagenten-Prompts explizit anweisen, Fragen gesammelt am Ende zu stellen statt mid-task abzubrechen.

- **[MITTEL] [PROZESS] [Agent-Prompt] Subagenten-Zwischenarbeit für Orchestrator nicht sichtbar**
  Was: Der Orchestrator sieht nur die finale Return-Message von Subagenten – keine Zwischenschritte, keine Tool-Calls, keine Probleme die unterwegs aufgetreten sind.
  Warum: Strukturelle Grenze des Agent-Tools; es gibt keine Möglichkeit, Subagenten-Protokolle aus dem Haupt-Thread zu lesen.
  Regel: Subagenten-Prompts müssen am Ende einen strukturierten Prozessverbesserungs-Abschnitt fordern: „Was hat nicht funktioniert, was hätte besser tooling-seitig unterstützt werden sollen?" – der Orchestrator wertet diesen Abschnitt aus und trägt Findings in lessons_learned ein.

- **[MITTEL] [QUALITÄT] [Doku] #pragma-Kommentar referenziert nicht-existierende Entscheidung in decisions.md**
  Was: `IngredientsEndpoints.cs` enthält `#pragma warning disable CA1308 // lowercase hex is required per ETag spec decision (docs/history/decisions.md)` – die referenzierte Entscheidung existiert nicht in decisions.md.
  Warum: Subagent hat die Querverweispflicht nicht geprüft; Orchestrator-Check hat den Kommentar nicht verifiziert.
  Regel: Jede `#pragma`/`// Stryker disable`-Begründung die auf `decisions.md` verweist muss vom Orchestrator verifiziert werden – grep auf das verlinkte Stichwort, nicht nur auf Vollständigkeit prüfen.

- **[GERING] [TOOLING] [Tooling] sed-Aufruf ohne Hint für Alternativen**
  Was: Ein `sed`-Aufruf wurde vom Hook geblockt ohne Hinweis auf Alternativen (Read-Tool mit offset/limit, oder head + tail).
  Warum: `WRONG_APPROACH_PATTERNS` für sed hat keinen Hint-Text.
  Regel: Im `check-bash-permission.py` einen Hint für sed eintragen: „Zum Lesen von Zeilenbereichen: Read-Tool mit offset/limit-Parametern verwenden."

## Session 068 – 2026-05-29

- **[HOCH] [PROZESS] [Agent-Prompt] Orchestrator hat Coding-Guidelines im Haupt-Thread gelesen**
  Was: Im Schritt 0 (Architektur-Check) und zur Vorbereitung des Subagenten-Prompts wurden CODING_GUIDELINE_TYPESCRIPT.md und verwandte HOW-Dokumente im Haupt-Thread gelesen.
  Warum: Der Impuls war, den Subagenten-Prompt präziser zu machen – aber der Workflow sieht vor, dass der Subagent diese Docs selbst liest.
  Regel: Haupt-Thread liest ausschließlich WHAT-Dokumente (Feature-File, ARCHITECTURE.md, SKELETON_SPEC.md, decisions.md). HOW-Dokumente (Coding-Guidelines, TDD_PROCESS.md) liest ausschließlich der Subagent.

- **[HOCH] [PROZESS] [Skill-Nutzung] Orchestrator hat Code direkt geschrieben statt Subagenten zu beauftragen**
  Was: `aria-labelledby`-Fix, Test-Refactoring und Stryker-Suppressionen wurden im Haupt-Thread implementiert.
  Warum: Die Fixes erschienen "klein genug" – der Effizienz-Impuls überwog die Workflow-Disziplin.
  Regel: Implementierungsarbeit (auch einzelne Bugfixes) gehört in Subagenten. Ausnahme nur bei trivialen Tippfehler-Korrekturen in Dokumenten.

- **[HOCH] [PROZESS] [Agent-Prompt] User-Interaktion kann Subagenten vorzeitig beenden**
  Was: Subagenten wurden durch Ablehnen von Tool-Calls (Edit/Write) unterbrochen und hinterließen unvollständige Arbeit; ein neuer Subagent kann den Kontext des alten nicht übernehmen.
  Warum: Annahme, dass der User mitten in der Subagenten-Ausführung steuern kann.
  Regel: Vor dem Spawnen eines Subagenten kommunizieren: "Bitte alle Tool-Calls ohne Kommentar freigeben." Erst steuernde Fragen nach Abschluss des Subagenten stellen.

- **[MITTEL] [QUALITÄT] [TDD] Viele Stryker-Suppressionen als Gold-Plating-Signal**
  Was: Hooks (`useResultMutation`, `useResultQuery`) und `match.ts` zeigten viele NoCoverage/Survived-Mutanten die nur per Suppression zu bereinigen waren.
  Warum: Infrastruktur-Code wurde mit allen vier States implementiert, obwohl das Happy-Path-Szenario nur pending+success benötigt.
  Regel: Wenn Stryker viele Suppressionen erzwingt → erst klären ob der Code überhaupt gebraucht wird, bevor supprimiert wird.

- **[MITTEL] [TOOLING] [Tooling] `# --allow-once` nicht an Standard-Lesebefehle anhängen**
  Was: `# --allow-once` wurde an `find`- und `grep`-Befehle angehängt obwohl diese keine Ausnahme benötigen.
  Warum: Falsches Verständnis – `--allow-once` ist für destruktive Einzelfall-Ausnahmen (`git restore`, `rm -rf`), nicht für normale Lesebefehle.
  Regel: `# --allow-once` nur bei destruktiven oder ungewöhnlichen Befehlen verwenden. Standard-Lesebefehle (find, grep, ls) brauchen es nie.

## Session 067 – 2026-05-07

- **[MITTEL] [PROZESS] [Doku] Migrations-Kontext nicht vor dem Schreiben eines decisions.md-Eintrags verifiziert**
  Was: Für die DokuWiki-Migrationsstrategie wurde ein vollständiger decisions.md-Eintrag mit fünf Optionen formuliert und abgelehnt – der Kontext war falsch (Migration ist ein einmaliger Import bei MVP-Start mit DB-Reset, kein V1-Datenmigrations-Problem).
  Warum: Annahme übernommen ohne den Timing-Kontext (wann, welche Datenbasis) zu klären.
  Regel: Bei Migrationsstrategie-Einträgen zuerst klären: Wann passiert die Migration? Welcher Datenbankstand? Dann erst Optionen formulieren.

- **[GERING] [TOOLING] [Tooling] Parallel laufende npm-Kommandos modifizieren node_modules gleichzeitig**
  Was: `npm update` und `npm install @mui/...` liefen als parallele Background-Tasks und schrieben gleichzeitig in node_modules – kein Fehler aufgetreten, aber das Risiko war real.
  Warum: Effizienz-Optimierung ohne Berücksichtigung dass beide Befehle dieselbe Directory-Struktur mutieren.
  Regel: npm-Kommandos die node_modules modifizieren immer sequenziell ausführen, nie als parallele Background-Tasks.

## Session 066 – 2026-05-05

- **[MITTEL] [PROZESS] [Doku] AGENT_MEMORY.md mit Implementierungshistorie befüllt statt vorwärtsgerichteter Handlungsrelevanz**
  Was: In AGENT_MEMORY.md wurde ein "Tooling (Session 066)"-Block ergänzt, der auflistet was in der Session umgesetzt wurde – statt nur was für künftige Sessions handlungsrelevant ist.
  Warum: Session-Log und Working-Memory verwechselt; AGENT_MEMORY wirkt wie ein Statusbericht, verleitet daher zum Dokumentieren von Erledigtem.
  Regel: AGENT_MEMORY.md enthält ausschließlich Informationen die eine *zukünftige* Session braucht um effektiv zu handeln – was implementiert wurde gehört in die Session-Datei, nicht in die Memory.

- **[MITTEL] [QUALITÄT] [TS-Code] Breite ESLint-Suppression statt minimaler Fix in Betracht gezogen**
  Was: Bei `functional/prefer-immutable-types` im Test-Helper war der erste Impuls, die Regel für alle Test-Dateien zu deaktivieren, statt den konkreten Parameter mit `Readonly<>` zu typisieren.
  Warum: Der Fehler wurde als "Test-Code-spezifisch" eingestuft und eine globale Ausnahme als einfacher betrachtet.
  Regel: Vor jeder ESLint-Suppression den minimalen Fix suchen und die Ursache verstehen – eine globale Suppress ist nur gerechtfertigt wenn das Muster strukturell im gesamten Scope nicht erfüllbar ist.

- **[MITTEL] [PROZESS] [TDD] Unit-Test-Ausnahme mit Performance-Schwelle statt semantischem Kriterium begründet**
  Was: Die erste Formulierung der Stryker-getriggerten Unit-Test-Ausnahme enthielt ">2 Minuten Laufzeit" als Kriterium – User hat das als unrealistisch und falsch zurückgewiesen.
  Warum: Performance-Argument war das erste Suchbild; das eigentliche Kriterium (strukturell nicht via HTTP beobachtbar) ist semantisch, nicht metrisch.
  Regel: Die Rechtfertigung für einen Unit Test ist immer semantisch (Verhalten nicht via HTTP beobachtbar), niemals eine Laufzeit-Schwelle.

## Session 065 – 2026-04-18

- **[MITTEL] [TOOLING] [TS-Code] test.fail() läuft durch und timeoutet statt sofort zu überspringen**
  Was: `test.fail('name', fn)` in Playwright führt den Test-Body aus und timeoutet (30s), wenn das Feature noch nicht implementiert ist – Exit-Code 1 wie bei echtem Fehler.
  Warum: `test.fail()` markiert einen erwarteten Assertion-Fehler, nicht einen erwarteten Nicht-Lauf; Timeouts zählen nicht als „erwarteter Fehler".
  Regel: Für „noch nicht implementiert"-Tests immer `test.skip` verwenden, nie `test.fail`.

- **[GERING] [TOOLING] [TS-Code] toBeInTheDocument() ohne jest-dom-Setup verwendet**
  Was: `expect(...).toBeInTheDocument()` scheitert mit "Invalid Chai property", weil `@testing-library/jest-dom` nicht eingebunden ist.
  Warum: Matcher aus der Testing-Library-Dokumentation sind nicht standardmäßig verfügbar.
  Regel: Vor `toBeInTheDocument()` prüfen ob jest-dom im Setup-File registriert ist; sonst `findByRole` oder `findByText` verwenden (werfen bei Nicht-Vorhandensein von sich aus).

- **[MITTEL] [QUALITÄT] [TS-Code] Stryker-Survivor auf useQuery-Default `= []` nicht testbar ohne Loading-State-Infrastruktur**
  Was: Die Mutation `= []` → `= ["Stryker was here"]` überlebte, weil MSW immer Daten liefert und der Default nie aktiv ist.
  Warum: Der Default-Wert dient als TypeScript-Null-Safety, ist aber erst nach Einführung eines Loading-State-Tests killbar.
  Regel: Solche Survivor bewusst mit Kommentar supprimieren (`-- Default [...] nie getestet: data ist während Tests nie undefined [...]. Entfällt wenn Loading-State-Szenario implementiert ist.`) – nicht stillschweigend belassen.

## Session 064 – 2026-04-18

- **[MITTEL] [AGENT] [Tooling] retro_report.py-Cluster vor CM-Vorschlag nicht einzeln geprüft**
  Was: `[MITTEL][PROZESS][Tooling] 2×` als Cluster gemeldet → CM "Hook-Tests nach Änderungen" vorgeschlagen, ohne zu prüfen dass die beiden Einträge (S048: Edit-ohne-Read; S060: Hook-Tests) semantisch verschieden sind.
  Warum: Cluster-Label als inhaltliche Aussage übernommen statt die Einzel-Einträge zu lesen.
  Regel: Retro-Script-Cluster sind Tag-Kombinationen, keine semantischen Gruppen – immer die Einzel-Einträge lesen bevor ein Maßnahmenvorschlag formuliert wird.

- **[MITTEL] [PROZESS] [Skill-Nutzung] BEWÄHRT-Prüfung ohne Session-File-Lektüre durchgeführt**
  Was: CM2 (Ad-hoc-Bash) als BEWÄHRT-Kandidat vorgeschlagen, obwohl die meisten Sessions keine Coding-Sessions mit Test-/Build-Befehlen waren – erst User-Nachfrage hat das aufgedeckt.
  Warum: INDEX.md-Kurzfassungen genutzt statt die relevanten Session-Dateien zu lesen, wie der Kaizen-Skill es vorschreibt.
  Regel: Bei BEWÄHRT-Prüfung immer die gefilterten Session-Dateien lesen (nicht nur INDEX) – nur so ist erkennbar ob die Maßnahme wirklich 3× in relevantem Kontext beobachtet wurde.

---
