# Observations – Beobachtungs-Backlog

<!--
Zweck: Vorausschauende System-Design-Beobachtungen / Optimierungen (proaktiver Track).
       Ergänzt das reaktive lessons_learned.md. Speist Jenga NICHT (kein Script liest diese Datei).

Eintrag-Format:
  ## OBS-S<NNN>-<n> – Kurztitel
  - Quelle: User | Agent
  - Status: NEU | IN BEOBACHTUNG | UMGESETZT (S<NNN>) | VERWORFEN (Grund)
  - Impact: KRITISCH | HOCH | MITTEL | GERING    Häufigkeit: gelegentlich | häufig
  - Kategorie: PROZESS | AGENT | QUALITÄT | TOOLING    Kontext: <Kontext-Tag wie in lessons_learned>
  - Beobachtung: <was ist nicht ideal / was fiel auf>
  - Kandidaten: (nur bei nicht-trivial) A … (Gefahr/Aufwand) | B … | C …
  - Entscheidung/Maßnahme: <gewählter Kandidat + warum statt Alternativen>; → CM-… falls stehende Leitplanke
  - Bezug: (optional) LL-S<NNN>-<n> / CM-XX

  ID: OBS-S<NNN>-<n> – 3-stellige Session, laufende Nummer innerhalb der Session.
  Impact = dieselben vier Werte wie die LL-Schwere (geteiltes Vokabular).
  Häufigkeit: faktisch gelegentlich/häufig. Impact × Häufigkeit = Prioritäts-Matrix.
  Erfassungs-Regel: sofort & problemlos umsetzbare Einmal-Optimierung → einfach machen, kein Eintrag;
                    aufgeschoben → Eintrag.

Zwei-Brillen-Modell, Erfassungs-Tests, Gefahr/Kandidaten-Bewertung, Evaluierungs-Gate,
Grooming/Eskalation, Quer-Bewegung LL↔OBS: docs/kaizen/process.md
-->

> **Format-Referenz:** `docs/kaizen/process.md`
> **Archiv (aufgelöste Einträge):** `docs/kaizen/archive/observations_archive.md`

---

## OBS-S085-1 – Absolute-Pfad-Retries bei Bash verschwenden Token
- Quelle: User
- Status: UMGESETZT (S087) – `normalize_repo_paths` in `check-bash-permission.py`; `updatedInput`+`additionalContext` live verifiziert.
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Bash/Permission
- Beobachtung: Agenten versuchen wiederholt Bash mit absoluten Pfaden, laufen in den Permission-Deny und verschwenden Token (Deny-Log S086: 113/295 Zeilen mit `/mnt/c/...`, steigender Trend).
- Kandidaten: A) Hook schreibt Befehl auf relativen Pfad um | B) Deny mit gezieltem Hinweis | C) Doku/Allow-Liste schärfen
- Entscheidung/Maßnahme: **Kandidat A** (bei sauberem Scoping geringe Gefahr; spart den Retry-Round-Trip, den B kostet). `check-bash-permission.py` normalisiert als erster Schritt jeden Repo-Root-Präfix `/mnt/c/Users/kieritz/source/repos/mahl/` → relativ (**breit**, da Einheitlichkeit der Regel der Hauptnutzen ist), **außer** Inneres von `cmd.exe /c "…"` (Windows-`C:\…`); `# --allow-once`-Befehle unangetastet (ONE_TIME-Check zuerst). Bei Änderung `updatedInput` (umgeschriebener Befehl) + `additionalContext` (Hinweis an Agent). `defer` verworfen – würde die Hook-eigene Analyse umgehen.

## OBS-S085-2 – Zu verbose Kommunikation (Orchestrator↔Subagenten) verschwendet Token
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Kommunikation im implementing-scenario (und ggf. allen Prozessen) ist unnötig verbose.
- Kandidaten: A) „Caveman-like" Denken/Kommunizieren für Subagenten (Gefahr: Qualitätsrisiko prüfen) | B) knappere Prompt-/Output-Vorgaben ohne Stil-Verarmung (geringe Gefahr)
- Entscheidung/Maßnahme: Aus der S086-Evaluierung **ausgenommen** (hohe Gefahr/Qualitätsrisiko) → eigener Spike, bevor entschieden wird.

## OBS-S085-3 – Agenten durchsuchen Tool-Outputs selbst statt unsere gezielten Scripte zu nutzen
- Quelle: User
- Status: UMGESETZT (S087) – A: Audit bestätigt alle 7 Wrapper geben bereits nur Relevantes aus (kein Change). C: `--list`/SessionStart-Hinweis „ohne tail/grep nutzen". D: erlaubte Befehle → `allowed-commands.log` (live verifiziert). B (tail-Deny) bleibt zurückgestellt. Zusatz: Wrapper-CLI vereinheitlicht (`--detail`→`--verbose`, `--help` überall, s. Session-Log S087).
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Mutation-Testing
- Beobachtung: Agenten greppen/`tail`-en Stryker-&-Co-Output, obwohl unsere Scripte gezielt nur das Relevante ausgeben sollen (Deny-Log S086: 81 head/tail-Zeilen).
- Kandidaten: A) prüfen ob alle Scripte nur Relevantes ausgeben | B) `tail`/Filter auf unsere CMDs per Deny unterbinden | C) `--help` + Session-Hinweis | D) erlaubte Befehle loggen, um Misuse-Patterns zu finden
- Entscheidung/Maßnahme: **A + C + D**; **B zurückgestellt** bis mehr Daten (mittlere Gefahr, könnte legitime Nutzung blocken). C über `--list` + SessionStart-Injection: knappe Script-Anwendungsfälle + Hinweis „normal **ohne** `tail`/Filter nutzen (Output ist optimal); wo nicht → als Beobachtung sammeln". D = erlaubte Befehle loggen.

## OBS-S085-4 – Kein Language-Server für die Agenten-Programmierung im Einsatz
- Quelle: User
- Status: IN BEOBACHTUNG
- Impact: MITTEL–HOCH (von GERING revidiert)    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Sonstiges
- Beobachtung: Wir nutzen aktuell **keinen** Language-Server, der Claude Code Code-Intelligence bereitstellt. Recherche (S086): Claude Code v2.1.172 unterstützt LSP (`ENABLE_LSP_TOOL` + Marketplace-Plugin pro Sprache). Nutzen potenziell **hoch** (Auto-Typfehler nach jedem Edit, find-refs, Symbole, Call-Hierarchie → kürzere Edit-Fix-Schleifen) → Impact GERING→MITTEL/HOCH revidiert.
- Entscheidung/Maßnahme: **(a) TS-LSP-Pilot** (eine Session testweise, `typescript-lsp`-Plugin); **(b) C# zurückgestellt** — offene Showstopper im Claude-Code-LSP-*Client* (claude-plugins-official#1359: 3 server→client-Requests unbeantwortet → csharp-ls-Solution-Loading bricht; claude-code#38683 Roslyn-Kompat). Trigger zum Wiederaufgreifen = #1359 geschlossen.

## OBS-S085-7 – Zeilenlimits für Tests/Frontend sinnvoll?
- Quelle: User
- Status: UMGESETZT (S087) – `eslint.config.js`: `complexity`/`max-depth` error (auch Tests), `max-params` warn, `max-lines-per-function` warn 50 / aus für Test+Spec; general-Guideline „Komplexität & Refactoring" um Aspiration-vs-Backstop-Hinweis + Param-Richtwert ergänzt (Schwellen via Config-Verweis, keine Kopie). ESLint grün, kein Bestands-Verstoß.
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: QUALITÄT    Kontext: TS-Code
- Beobachtung: ESLint erzwingt `max-lines-per-function: 50` hart für **alle** `**/*.{ts,tsx}` inkl. Tests; Guideline nennt parallel „~20 Zeilen" (Mismatch). Für Tests/JSX nie evaluiert.
- Entscheidung/Maßnahme: **Differenzieren**, begründet über „was proxyt die Metrik": `complexity: error 10` überall inkl. Tests (hohe Komplexität im Test ist selbst ein Smell); `max-depth: error 4`; `max-params: warn 4` (Konstruktoren/Domänenobjekte nicht sauber per Glob ausschließbar → warn statt error; C#-Param-Limit ist separater SonarAnalyzer/`.editorconfig`-Layer); `max-lines-per-function: warn 50` (Prod) / **aus** für Tests (`**/*.{test,spec}.{ts,tsx}`). Zwei-Stufen = Guideline-Aspiration vs. Lint-Deckel (Lint ≥ Guideline), zweistufig nur bei der verrauschten Zeilen-Metrik; JSX nicht per Glob sondern über Komplexität + Review.

## OBS-S085-8 – (Sub-)Agenten nutzen nicht das aufgaben-passende Modell
- Quelle: User
- Status: UMGESETZT (S087) – 6 read-only-Auditoren `model: sonnet`, beide Layer-Implementer `model: inherit`; `review-code`/`implementing-scenario`/`review-workflow` um „Modellwahl vor Spawn"-Hinweis ergänzt. `kaizen` spawnt keine Subagenten → entfällt.
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Alle 8 Agenten sind `model: inherit`; Token werden verschwendet, wenn nicht das passende Modell genutzt wird.
- Kandidaten: A) Orchestrator wählt Modell nach Schwierigkeit | B) Cap pro Agent via Frontmatter | C) Status quo
- Entscheidung/Maßnahme: **A+B kombiniert** (Tool-Vertrag bestätigt: `Agent`-`model`-Param übersteuert Frontmatter → Frontmatter = Default, kein Deckel). Defaults: 6 read-only-Auditoren `model: sonnet`, beide Layer-Implementer `inherit`. Skills (`implementing-scenario`, `review-code`, `kaizen`/`review-workflow`) weisen an: Modell vor jedem Spawn nach Schwierigkeit wählen.

## OBS-S085-10 – „Schwere" → „Impact" umbenennen (deferred Meta-Änderung)
- Quelle: Agent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: „Impact" ist treffender als „Schwere" und schlägt die Brücke zu observations.md.
- Kandidaten: A) nur Docs/Skills umbenennen | B) Docs + Script-Output-Strings + Tests | C) gar nicht
- Entscheidung/Maßnahme: Aus der S086-Evaluierung **ausgenommen** (deferred Meta-Änderung) – getrennt entscheiden, ggf. gekoppelt an OBS-S085-14 (gemeinsamer Script/History-Touch).

## OBS-S085-12 – Noise-Review skaliert nicht: Archive jede Retro neu zu filtern wird teuer
- Quelle: Agent
- Status: IN BEOBACHTUNG
- Impact: GERING    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: kaizen-Schritt 0 sah vor, alle Archiv-Dateien jede Retro neu gegen den Filter zu prüfen → Token-Kosten steigen, Grenznutzen gering.
- Entscheidung/Maßnahme: **B gewählt** — Staffel B (nur zuletzt archivierte Periode doppelprüfen) → (kein Rückfall) → A (Archiv-Scan weglassen). Umsetzung: kaizen Schritt 0 (bereits angewandt). Gekoppelt an CM „Noise als LL" (AKTIV + beobachten).

## OBS-S085-14 – countermeasures.md: IDs + Fließtext-Format (wie ADR/LL/OBS)
- Quelle: User
- Status: UMGESETZT (S087) – `countermeasures.md` auf Fließtext + CM-IDs (`CM-S<NNN>-<n>`) umgebaut (21 Einträge); `retro_report.py` `load_cm` parst Header/Metadaten/Problem-Zeile (am LL-Parser orientiert), `cm_id` im Datenmodell + Escalated-Report; 5 neue Tests in `test_retro_report.py` (14 grün). Format-Doku in process.md („Tabelle"→„Datei") nachgezogen. OBS-S085-10 (Schwere→Impact) NICHT gekoppelt – „Schwere" beibehalten (konsistent mit LL-Parser), bleibt deferred.
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Die CM-Tabelle ist schwer lesbar und CMs sind schwer referenzierbar (keine IDs).
- Kandidaten: A) CM-IDs einführen (`CM-S<NNN>-<n>`) | B) Tabelle → Fließtext (`retro_report.py` `load_cm` parst die `|`-Tabelle → Script muss mit)
- Entscheidung/Maßnahme: **A + B jetzt.** A = CM-IDs. B = Tabelle→Fließtext mit Header-Sektion; `load_cm` anpassen – am bestehenden LL-Fließtext/Header-Parser orientieren bzw. Code wiederverwenden, Test-Nachweis (mittlere Gefahr). Ggf. mit OBS-S085-10 koppeln.

## OBS-S085-16 – AGENT_MEMORY.md verschlanken / umstrukturieren
- Quelle: Agent (Analyse) + User (Anmerkungen)
- Status: UMGESETZT (Teil A S087, Teil B S088).
  - **Teil A (S087):** physischer Split (V2): `docs/tech-debt.md` + `docs/open-questions.md` ausgelagert (eigene Header/IDs: TD-S…, OQ-S…); AGENT_MEMORY auf schlanken Auto-Inject reduziert; Pflege-Konvention in `closing-session` Schritt 8; ~8 Referenzen nachgezogen. Keyword-/Relevanz-Script für tech-debt → eigene **OBS-S087-1**.
  - **Teil B (S088) – Generator doch umgesetzt:** Die S087-Ablehnung („kein maschinelles Mapping, CamelCase-Testname ≠ Szenario-Titel") wurde aufgelöst durch die **`// Szenario: <Titel>`-Kommentar-Konvention** über jedem E2E-Test (ADR-S041-7-Addendum). `next_scenario.py` leitet DONE daraus ab und löst den `{{NEXT_SCENARIO}}`-Platzhalter beim Session-Start auf (`session-start.sh --render`); Reihenfolge-Abweichungen via expliziten Anstrich über dem Platzhalter (Feature-File-Reihenfolge bleibt unangetastet). Das **separate Header-Feld „Nächstes Szenario" entfällt** (es konkurrierte mit der Prioritätenliste → Widerspruch, der diese Session auslöste). Mapping-Integrität als Poka-Yoke-Hook `check-e2e-scenario-ref.py` (bidirektional: Spec-Edit + Feature-Edit). Anschluss-Beobachtung Hook-Sprawl → **OBS-S088-1**.
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: AGENT_MEMORY.md wird per `session-start.sh` bei JEDEM Start voll injiziert → jede Zeile kostet Token. 4-KB-Limit ohne Enforcer (S083 aufgehoben); aktuell ~7 KB.
- Leitfrage (User): „Welche Info braucht *jeder* Agent beim Start, um den Projektstatus für *seine* Aufgabe zu verstehen?" Was das nicht erfüllt → read-on-demand, referenziert.
- Kandidaten: A) Doku-Restruktur (schlanker Auto-Inject-Index + ausgelagerte Details) | B) Inject-Mechanik via Script | C) besser beschreiben, was in die Datei gehört/nicht (via Leitfrage)
- Entscheidung/Maßnahme: **A zuerst** (Doku-Restruktur; „Prioritäten/Phase" bleiben **hand-geschrieben**, Rest ableitbar) → **dann B als Generator-Script** (zieht letzte Session aus `index.md`, offene CMs aus `countermeasures.md`, prüft Größenbudget). **C ergänzt:** beim Umsetzen die Leitfrage als Filter nutzen + explizit dokumentieren, was rein-/nicht reingehört. Dateiname nach Restruktur entscheiden. Begleitprinzip: Single Source of Truth (OBS-S085-15).
- Bezug: CM „AGENT_MEMORY 4-KB-Limit" (S083, OFFEN); OBS-S085-15

## OBS-S086-1 – OBS-Kandidaten gemeinsam erarbeiten statt eigenmächtig vorab festlegen
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: Kandidaten in OBS-Einträgen wurden bisher vom Agenten eigenmächtig vorformuliert → teils unpassende/unvollständige Vorschläge, gemeinsam-umzusetzende Optionen oder fehlende Möglichkeiten; das gemeinsame Nachdenken wird übersprungen. Erfassung sollte billig bleiben (nur Beobachtung + ggf. *als roh markierte* Idee); Kandidaten-Discovery + Bewertung gehören in den Retro-Evaluierungsschritt.
- Kandidaten: — (bewusst leer; gemeinsame Discovery in der Retro – dogfoodet diese Beobachtung selbst)
- Entscheidung/Maßnahme: offen (Retro)
- Bezug: OBS-S086-2, OBS-S086-3, OBS-S085-13

## OBS-S086-2 – Verständnis vor Erfassung sichern (ggf. grill-me)
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: OBS wurden teils falsch erfasst – Negativbeispiel OBS-S085-4 („languageServer buggy" meinte eigentlich „wir nutzen gar keinen Language-Server"). Vor dem Festhalten sicherstellen, dass Ziel/Problem richtig verstanden ist; bei Unklarheit `grill-me` nutzen.
- Kandidaten: — (gemeinsame Discovery in der Retro)
- Entscheidung/Maßnahme: offen (Retro)
- Bezug: OBS-S086-1; LL-S086-2

## OBS-S086-3 – Viele Findings nicht alle auf einmal – kategorie-/blockweise
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Kommunikation
- Beobachtung: Alle OBS in einem Rutsch zu besprechen ist token-effizient, aber kognitiv anstrengend (ständiges gedankliches Hin-/Herspringen). Bei vielen Punkten kategorieweise (wie A/B/C) und/oder blockweise (nur x Beobachtungen auf einmal, dann die nächsten).
- Kandidaten: — (gemeinsame Discovery in der Retro)
- Entscheidung/Maßnahme: offen (Retro)
- Bezug: OBS-S085-13

## OBS-S086-4 – `--allow-once`: Notwendigkeits- und Gefahr-Hinweise
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Bash/Permission
- Beobachtung: Drei Ideen für `check-bash-permission.py` bei `# --allow-once`-Befehlen: (a) prüfen, ob `--allow-once` überhaupt nötig ist (Befehl evtl. ohnehin allow-listed) → Hinweis zurückgeben; (b) den Deny-Grund / das Gefährliche aufbereitet bei der User-Freigabe mitgeben (highlighten, damit der User es nicht übersieht); (c) den Agenten anweisen, bei `--allow-once` zu beschreiben, was der Befehl Gefährliches tut und warum es nicht ohne geht (entfällt, wenn der User vorab manuell `--allow-once` angeordnet hat).
- Kandidaten: — (gemeinsame Discovery in der Retro)
- Entscheidung/Maßnahme: offen (Retro)
- Bezug: OBS-S085-1

## OBS-S086-5 – Session-Datei-Inhalt: Scope definieren
- Quelle: User
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Unklar/unausgewertet, was in `docs/history/sessions/session_NNN.md` gehört – ist es sinnvoll, alles festzuhalten? Welche Teile können/sollten weg, was fehlt? (Analog zu OBS-S085-9 für `index.md`, aber für die Session-Dateien.)
- Kandidaten: — (gemeinsame Discovery in der Retro)
- Entscheidung/Maßnahme: offen (Retro)

## OBS-S087-1 – Technische Schuld durchsuchbar/relevanz-gefiltert machen
- Quelle: User
- Status: NEU
- Impact: GERING–MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: `docs/tech-debt.md` wird heute per Volltext-grep durchsucht (bei 10 Einträgen ausreichend). Wächst die Datei, wäre es nützlich, wenn der Architektur-Check in `implementing-scenario` (oder ein eigenes Script) die zum bearbeiteten Code-Bereich **potentiell relevante** technische Schuld automatisch identifiziert/auflistet – z.B. über kuratierte Bereichs-Keywords pro Eintrag. Bewusst NICHT jetzt umgesetzt (YAGNI): Keyword-Vokabular sollte **gemeinsam mit dem konsumierenden Script** entworfen werden, sonst spekulative Tags ohne Abnehmer + Drift.
- Kandidaten: — (gemeinsame Discovery in der Retro; u.a.: Keyword-Feld pro TD-Eintrag vs. Ableitung aus Heading/Problem; eigenes Script vs. Erweiterung des implementing-scenario-Architektur-Checks)
- Entscheidung/Maßnahme: offen (Retro)
- Bezug: OBS-S085-16 (AGENT_MEMORY-Restruktur, in deren Zuge tech-debt.md ausgelagert wurde)

## OBS-S087-2 – Gemeinsame „Tracker-Datei-Konvention" einmal dokumentieren
- Quelle: Agent
- Status: NEU
- Impact: GERING–MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: `observations.md`, `countermeasures.md`, `tech-debt.md`, `open-questions.md` teilen inzwischen dasselbe Muster (Header `wann-lesen/wann-schreiben/Eintrag-Format`, Session-basierte IDs `XX-S<NNN>-<n>`, Fließtext statt Tabelle, `---`-Trenner zwischen Einträgen, Sortierung nach ID aufsteigend). Das Muster ist nirgends zentral beschrieben → beim Anlegen einer neuen Tracker-Datei wird es ad-hoc re-derived (S087: tech-debt.md ~4× überarbeitet, s. LL-S087-1). Eine einmalige Konventions-Beschreibung (z.B. in `process.md` oder einem kurzen Doku-Styleguide) würde das vermeiden.
- Kandidaten: — (gemeinsame Discovery in der Retro; u.a.: wo dokumentieren – process.md vs. eigener Styleguide; wie viel Verbindlichkeit)
- Entscheidung/Maßnahme: offen (Retro)
- Bezug: LL-S087-1

## OBS-S088-1 – Hook-Registrierung: ein Dispatcher je Matcher/Event statt Einzeleinträge
- Quelle: User
- Status: NEU
- Impact: GERING–MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Pro Tool-Matcher stehen mehrere Hook-Scripts einzeln in `settings.json` (PreToolUse `Edit|Write`: dependency-allowlist, code-quality-blocking, index-length, e2e-scenario-ref). Ein neuer/entfernter Check erfordert eine `settings.json`-Änderung → **Claude-Code-Reload** nötig, bevor er greift. `check-code-quality-blocking.py` ist bereits ein In-Process-Dispatcher (`CHECKS`-Liste + `checks/`-Package) – Checks dort sind reload-frei. Verallgemeinert man das (ein Dispatcher je Matcher *und* Event, der die Einzel-Checks aufruft), würde künftiges Hinzufügen/Entfernen eines Checks nur den Dispatcher-Inhalt ändern → sofort live, ohne Reload. Designpunkte: Pre (blocking, exit 2) vs. Post (non-blocking) getrennt; uneinheitlicher Input-Vertrag (Fragment-`HookInput` vs. voller Post-Edit-Inhalt + Datei-Reads bei e2e-scenario-ref → Dispatcher gibt rohes JSON, Checks adaptieren); Output-Stil je Dispatcher einheitlich (Bash nutzt JSON-`permissionDecision`); fail-open je Check.
- Kandidaten: — (gemeinsame Discovery in der Retro, OBS-S086-1; grobe Richtung: In-Process-Registry wie check-code-quality-blocking vs. Subprozess-Liste)
- Entscheidung/Maßnahme: offen (Retro) – als eigener fokussierter Refactor mit eigenen Tests, getrennt vom Szenario-Tracking-Commit
- Bezug: OBS-S085-16 (Reload-Friktion-Familie)
