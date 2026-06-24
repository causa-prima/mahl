# Observations – Beobachtungs-Backlog

<!--
Zweck: Vorausschauende System-Design-Beobachtungen / Optimierungen (proaktiver Track).
       Ergänzt das reaktive lessons_learned.md. Speist Jenga NICHT (kein Script liest diese Datei).

Eintrag-Format:
  ## OBS-S<NNN>-<n> – Kurztitel
  - Quelle: User | Orchestrator | Subagent   (bei Agent-Quelle möglichst präzise: Subagent vs. Orchestrator)
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

## OBS-S090-1 – Vitest ist typ-blind; Typfehler erst im Stryker-Dry-Run sichtbar
- Quelle: Agent
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: frontend-tdd
- Beobachtung: `vitest` (esbuild, transpile-only) prüft **keine** Typen. Echte TS-Fehler (z.B. `ResultAsync` ≠ `Promise`; `errAsync`-`kind`-Widening) blieben bis zum Stryker-typescript-checker-Dry-Run unsichtbar (~1 Zyklus Verzögerung). Kein `tsc --noEmit`-Wrapper auf der Bash-Allow-Liste → der Layer-Implementer konnte Typen nicht isoliert **vor** dem teuren Stryker-Lauf prüfen.
- Kandidaten: A) `tsc --noEmit`-Wrapper-Script (analog `eslint-run.py`) auf die Allow-Liste (gering) | B) Status quo (Stryker fängt es, aber spät)
- Entscheidung/Maßnahme: aufgeschoben (NEU) – vor Bewertung sammeln; Kandidat A wahrscheinlich.

---

## OBS-S090-2 – qa-check-Übergabe-Hash erzwingt Extra-Stryker-Lauf bei Re-Stage
- Quelle: Agent (Orchestrator-Beobachtung)
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: implementing-scenario / qa-check
- Beobachtung: Der `qa-check.py`-Übergabe-Hash rechnet über den **gestageten** Zustand. Stagt der Orchestrator nach der Subagent-Hash-Berechnung noch eine freigegebene Test-Änderung, mismatcht `--verify` → ein **erneuter** (teurer) Stryker-Lauf nur, um einen frischen Hash über den finalen Index zu erzeugen. In dieser Session 2× passiert (Frontend Option-A-Restage; variant-c).
- Kandidaten: A) Stage-vor-Hash als feste Reihenfolge-Konvention | B) Hash über Working-Tree statt Index | C) Subagent stagt final selbst + Hash zuletzt
- Entscheidung/Maßnahme: aufgeschoben (NEU) – Reihenfolge-Konvention im implementing-scenario-Flow klären; vor Bewertung sammeln.

---

## OBS-S090-3 – Alt-Hooks überprüfen/entschlacken
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Hook/Script
- Beobachtung: Die Hook-Scripte (`check-memory.sh`, `pre-compact.sh`, `session-start.sh`, `session-end.sh`, `task-completed.sh`) stammen aus einer frühen Projektphase mit noch geringem Claude-Code-Verständnis. Mehrere tragen evtl. veraltete Annahmen (z.B. der jetzt korrigierte `/mnt/c`-Hardcode, S090). Ungeprüft, ob einzelne Hooks heute noch ihren Zweck erfüllen, redundant sind oder angepasst/entfernt gehören.
- Kandidaten: A) Hook-für-Hook-Audit (Zweck, Trigger, Mehrwert, Redundanz) | B) gegen aktuelle CC-Hook-Mechanik (Events/Matcher) gegenchecken | C) Status quo
- Entscheidung/Maßnahme: aufgeschoben (NEU) – in der nächsten Retro evaluieren; verwandt mit OBS-S088-1 (Hook-Dispatcher/Reload-Friktion).
- Bezug: OBS-S088-1

## OBS-S090-4 – Subagent-`git add` umgeht den Test-Review-Gate
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: TDD
- Beobachtung: Die Layer-Implementer haben das `Bash`-Tool und die Allow-Liste erlaubt `git add <datei>` → ein Subagent kann (und tat es in S090) Dateien selbst stagen. Der `qa-check`-Übergabe-Hash rechnet über den **gestageten** Zustand, weshalb der Subagent sogar stagen *muss*. Damit ist der dokumentierte Gate „Haupt-Thread reviewt Tests, *dann* staged er" faktisch nicht erzwungen: Ein Subagent könnte ungeprüfte Assertions stagen und trotzdem einen grünen 100%-Hash erzeugen. **Mutation-Score + Hash beweisen „getestet+gemutet", nicht „vom Orchestrator inhaltlich freigegeben".** Kein konkreter Schaden in S090 (Review fand statt) — Integritäts-Risiko, kein Fehlausgang.
- Kandidaten: A) Hash über die Test-/alle gestageten Dateien berechnen, sodass nachträgliches Subagent-Staging den Hash bricht (User-Hinweis: vermutlich leicht umsetzbar) | B) `git add` aus dem Layer-Implementer-Bash entfernen, Staging komplett beim Haupt-Thread | C) Status quo + explizite Prozess-Warnung
- Entscheidung/Maßnahme: aufgeschoben (NEU) – Kandidat A wirkt am günstigsten; in der nächsten Retro entscheiden.
- Bezug: OBS-S090-2 (qa-check-Hash/Staging-Reihenfolge)

## OBS-S090-5 – TD-Grooming-Lücke: Infra-Schuld fällt durchs Raster
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Sonstiges
- Beobachtung: Technische Schuld wird heute nur **opportunistisch** gegroomt (Architektur-Check in `implementing-scenario`: passende TD zum aktuellen Szenario mitnehmen). Schuld ohne Szenario-Bezug — typisch Infrastruktur, z.B. **TD-S083-5** (dirty-Postgres, kein Reset zwischen E2E-Läufen) — mappt auf kein Szenario und wird so **nie** angefasst. Zusätzlich fehlt am Session-Ende ein Check, ob TD unbewusst miterledigt wurde (dann Eintrag schließen).
- Kandidaten: A) periodisches/retro-gebundenes TD-Grooming für szenario-fremde Schuld | B) Session-End-Check „wurde TD unbewusst behoben?" | C) Infra-TD eigene Behandlung/Trigger geben
- Entscheidung/Maßnahme: aufgeschoben (NEU) – Lösung in der nächsten Retro finden (User: „dazu müssen wir eine Lösung finden").
- Bezug: OBS-S087-1 (TD relevanz-filterbar machen)

---

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
- Status: IN BEOBACHTUNG – S087: A (Wrapper-Audit, kein Change) + C (`--list`/SessionStart-Hinweis „ohne tail/grep") + D (`allowed-commands.log`) umgesetzt, B (tail-Deny) zurückgestellt; **S095 wiederaufgegriffen** nach D-Analyse.
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Mutation-Testing
- Beobachtung: Agenten greppen/`tail`-en Stryker-&-Co-Output, obwohl unsere Scripte gezielt nur das Relevante ausgeben sollen (Deny-Log S086: 81 head/tail-Zeilen).
- Kandidaten: A) prüfen ob alle Scripte nur Relevantes ausgeben | B) `tail`/Filter auf unsere CMDs per Deny unterbinden | C) `--help` + Session-Hinweis | D) erlaubte Befehle loggen, um Misuse-Patterns zu finden
- Entscheidung/Maßnahme: **A + C + D**; **B zurückgestellt** bis mehr Daten (mittlere Gefahr, könnte legitime Nutzung blocken). C über `--list` + SessionStart-Injection: knappe Script-Anwendungsfälle + Hinweis „normal **ohne** `tail`/Filter nutzen (Output ist optimal); wo nicht → als Beobachtung sammeln". D = erlaubte Befehle loggen.
- **Rezidiv (S090, Quelle: User):** Trotz Gegenmaßnahme C erneut aufgetreten — `grep` mehrfach auf qa-check-Output, `tail` auf playwright-test. Der Session-Hinweis (C) allein verhindert das Verhalten nicht zuverlässig.
- **D-Analyse durchgeführt + Neubewertung (S095):** `allowed-commands.log` ausgewertet (~15+ Filter-Instanzen S90–93). Befund: das Filtern ist **nicht** einheitlich Misuse, sondern zerfällt in drei Klassen — (1) **reines Kürzen** auf bereits kuratiertem Output (`vitest-run|tail`, `eslint-run|tail`) → Disziplin-Thema; (2) **gezieltes Feld-Extrahieren**, weil der Wrapper das Verdikt vergräbt (`qa-check --verify | grep | tail`, `stryker | grep Score/Survived`) → Wrapper sollte das Verdikt klar ausgeben; (3) **legitimer Workaround**, weil der Wrapper die relevante Info gar nicht liefert (`dotnet-test` bei RED ohne Assertion-Details → **OBS-S091-1**). Konsequenz (User-Entscheid): **kein pauschales Deny (B)** — es würde Klasse 2+3 bestrafen. Stattdessen **zuerst die Wrapper fixen** (Klasse 2+3, s. OBS-S091-1/-3), *dann* neu bewerten, ob für Restklasse 1 überhaupt noch eine Maßnahme nötig ist.

## OBS-S085-4 – Kein Language-Server für die Agenten-Programmierung im Einsatz
- Quelle: User
- Status: IN BEOBACHTUNG – **Pilot durchgeführt & technisch validiert (2026-06-20):** `typescript-lsp`@claude-plugins-official läuft auf **nativem** Claude-Install 2.1.183 (anthropics/claude-code #20050 hier **nicht** relevant – galt für ältere Versionen); `ENABLE_LSP_TOOL` nicht nötig; `/reload-plugins` statt Neustart genügt. Alle Ops ok (hover, documentSymbol, goToDefinition cross-file, workspaceSymbol, findReferences); **semantisch präziser als grep** (Kommentar-/String-Treffer korrekt ausgeschlossen). **CAVEAT:** erster `findReferences` direkt nach Plugin-Load = kalter/unvollständiger Index → erst nach Warmlauf vollständig (bei verdächtig wenigen Treffern wiederholen). Offene Bewertung: realer Nutzen über laufende Arbeit. C# weiter zurückgestellt (#1359).
- Impact: MITTEL–HOCH (von GERING revidiert)    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Sonstiges
- Beobachtung: Wir nutzen aktuell **keinen** Language-Server, der Claude Code Code-Intelligence bereitstellt. Recherche (S086): Claude Code v2.1.172 unterstützt LSP (`ENABLE_LSP_TOOL` + Marketplace-Plugin pro Sprache). Nutzen potenziell **hoch** (Auto-Typfehler nach jedem Edit, find-refs, Symbole, Call-Hierarchie → kürzere Edit-Fix-Schleifen) → Impact GERING→MITTEL/HOCH revidiert.
- Entscheidung/Maßnahme: **(a) TS-LSP-Pilot** (`typescript-lsp`-Plugin); **(b) C# zurückgestellt** — offene Showstopper im Claude-Code-LSP-*Client* (claude-plugins-official#1359: 3 server→client-Requests unbeantwortet → csharp-ls-Solution-Loading bricht; claude-code#38683 Roslyn-Kompat). Trigger zum Wiederaufgreifen = #1359 geschlossen.
- **Pilot-Bound & Abschluss-Kriterien:** Bewertung beim **nächsten Kaizen/Retro** (bewertet OBS ohnehin). Mindest-Evidenz: LSP in **≥ ~3 Sessions mit echter TS-Arbeit** verfügbar; sonst Ergebnis = „eine Runde verlängern" (kein Urteil auf Null-Daten).
  - **Erfolg → adoptieren** (alle drei): (1) tatsächlich genutzt (Frequenz, s. Messung); (2) materieller Mehrwert nachweisbar (konkrete HELP-Vorfälle, wo grep+Read schlechter gewesen wäre); (3) keine Zuverlässigkeits-Blocker über die umgehbare Kalt-Index-Caveat hinaus. → permanente Ein-Zeilen-Regel in `coding-guideline-typescript.md`, Pilot-Notiz raus, Status = UMGESETZT.
  - **Fehlschlag → verwerfen/parken** (eines): kaum genutzt / kein Vorteil ggü. grep+Read; oder Kosten > Nutzen (stale/Flakiness/Setup-Fragilität). → Plugin + Pilot-Notiz entfernen, Status = VERWORFEN (Grund).
- **Messung:** (a) **Frequenz objektiv** = beim Retro Session-Transkripte des Pilot-Zeitraums nach LSP-Tool-Calls grepen (Invocations / distinkte Sessions / Operationen; kein neues Tooling). (b) **Nutzen/Zuverlässigkeit qualitativ** = Pilot-Lauf-Log unten. Bewusst keine Pseudo-Metrik für „Nutzen". Bias bekannt: stille Erfolge unterberichtet, Reibung überzeichnet → HELP-Einträge sind eine **Untergrenze** des Nutzens, FAIL-Volumen nicht überbewerten.
- **Pilot-Lauf-Log** (Format `[S<NNN> | Datum] op — HELP|FAIL — Beschreibung`; bei Nicht-Session-Ereignissen Kontext-Label statt Session-Nr.; **Beschreibung ≤ ~100 Zeichen**, länger nur wenn für spätere Nachvollziehbarkeit wirklich nötig; **FAILs immer, HELPs nur bei klarem Counterfactual**; Routine-Calls nicht loggen):
  - [Aktivierungs-Test 2026-06-20] findReferences — FAIL — direkt nach Plugin-Load kalter Index (1 statt 3 Refs); nach Warmlauf korrekt.
  - [Aktivierungs-Test 2026-06-20] findReferences — HELP — schloss Kommentar-/String-Treffer aus, die grep mitzählte (3 statt 4, 12 statt 15).

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

## OBS-S091-1 – `dotnet-test.py` zeigt bei RED keine Assertion-Details (MTP-Runner)
- Quelle: Agent
- Status: NEU
- Impact: MITTEL    Häufigkeit: jeder Backend-RED
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: `dotnet-test.py` gibt bei Fehlschlag (Default **und** `--verbose`) nur `Failed: N, Passed: M` + einen Verweis auf eine UTF-16-`.log` aus — **keine** Assertion-Message/Expected-Actual. Empirisch verifiziert (S091, gezielt gebrochene Assertion, voller ungefilterter Output): der MTP-Runner (xunit.v3, TD-S089-1) schreibt Fehlerdetails nur in `TestResults/*.log`, nicht auf stdout im Format, das das `_RELEVANT`-Regex (`Error Message`/`at mahl.`) erwartet. Beim RED-Debugging fehlt damit genau die Info, die man braucht (der Backend-Subagent musste die UTF-16-Datei manuell lesen).
- Kandidaten: — (Retro; u.a.: Wrapper extrahiert die fehlgeschlagene Assertion aus der `.log` vs. MTP auf stdout-Ausgabe konfigurieren)
- Entscheidung/Maßnahme: **Direkt fixen vor dem nächsten Szenario (S095-Entscheid):** wiederkehrendes Problem, Beobachten lohnt nicht — `dotnet-test.py` muss bei RED die fehlgeschlagene Assertion (Expected/Actual) auf stdout zeigen. Teil des Wrapper-Output-Fix-Batches (mit OBS-S091-3). Verschärft den OBS-S085-3-Workaround.
- Bezug: TD-S089-1 (MTP-Migration); OBS-S085-3 (Wrapper-Output-Filtern)

## OBS-S091-2 – Wrapper-Aufrufpfad cwd-relativ, kollidiert mit Projekt-Tooling-cwd
- Quelle: Agent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Die Wrapper liegen im Repo-Root (`.claude/scripts/`) und lösen ihren Root intern via `_util.REPO_ROOT` auf — aber der **Aufrufpfad** `python3 .claude/scripts/foo.py` ist cwd-relativ. Projekt-Tooling (`npm`/`dotnet`/`vite`) zieht die Shell in `Client/`/`Server/`-Subdirs; der nächste Wrapper-Aufruf scheitert dann mit „No such file" (S091: beide Subagenten + Orchestrator betroffen).
- Kandidaten: — (Retro; u.a.: grep-bare Regel „Wrapper nie nach einem `cd` aufrufen" vs. Wrapper per absolutem Pfad/Alias aufrufbar machen)
- Entscheidung/Maßnahme: offen (Retro)
- Bezug: —

## OBS-S091-3 – `vitest-run.py --filter` Substring-Semantik nicht offensichtlich
- Quelle: Agent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: `vitest-run.py --filter X` matcht X als Substring über den **voll-qualifizierten** Testnamen (inkl. `describe`-Block). Ein neuer describe-Block „…(leere Einheit)" wurde dadurch zunächst übersprungen → irreführendes „N passed" statt der erwarteten Gesamtzahl (der FE-Subagent zog ungefiltert nach). Verbesserung: Filter-Semantik dokumentieren oder die Zahl gematchter/übersprungener Tests ausweisen.
- Kandidaten: — (Retro)
- Entscheidung/Maßnahme: **Direkt fixen vor dem nächsten Szenario (S095-Entscheid):** Teil des Wrapper-Output-Fix-Batches (mit OBS-S091-1) — `vitest-run.py` weist die Zahl gematchter/übersprungener Tests aus (und/oder dokumentiert die Substring-Semantik).
- Bezug: OBS-S085-3 (Filter-/Output-Familie); OBS-S091-1

## OBS-S091-4 – Suppressions systematisch tracken (Script)
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Suppressions (Stryker + Analyzer/`.editorconfig`) systematisch tracken, vermutlich per Script. Zwei Ziele: **(1)** Suppressions, die ein nachfolgendes Szenario beheben soll, nicht aus den Augen verlieren — S091 hing das an manueller Erinnerung (die FE-`:53`-Suppression wurde planmäßig im „leere Einheit"-Szenario aufgelöst; ADR-S000-4 war eine solche Vertagung, die obsolet wurde und lingerte). **(2)** Suppressions ohne Szenario-Bezug periodisch, **nach Klasse gruppiert** reviewen — ändert sich etwas, das eine Klasse überflüssig macht (z.B. löste `noUncheckedIndexedAccess` den `Partial<…>`-Workaround), will man wissen, wo diese Suppressions sitzen.
- Kandidaten: — (Retro; u.a.: Script sammelt Stryker-/`.editorconfig`-Suppressions + gruppiert nach Klasse/Begründung; optionales Feld „behoben-durch-Szenario" pro Suppression)
- Entscheidung/Maßnahme: offen (Retro)
- Bezug: ADR-S000-4 (gelöschte Suppression-Vertagung), OBS-S090-5 (TD-Grooming-Lücke)

---

## OBS-S092-1 – Doppelte LL/OBS-Erfassung: implementing-scenario Schritt 6.1 vs. closing-session
- Quelle: User
- Status: NEU
- Impact: GERING    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: implementing-scenario / closing-session
- Beobachtung: `implementing-scenario` Schritt 6.1 („Offene Punkte triagieren") erfasst LLs/OBSs/Tech-Debt, und `closing-session` (Schritt 2/3/5) erfasst dieselbe Klasse von Punkten erneut. Bei direktem Übergang Szenario → Abschluss ist die Vorab-Triage in 6.1 redundant – sie ist nur nötig, wenn die Session **nicht** abgeschlossen wird (Szenario fertig, Session läuft weiter). In dieser Session führte das zu doppeltem Abfragen.
- Kandidaten: A) 6.1 erfasst nur, wenn KEIN Abschluss folgt; bei Abschluss an closing-session delegieren (gering) | B) 6.1 sammelt nur (kein Schreiben), closing-session schreibt einmalig | C) Status quo (Doppel-Prompt akzeptieren)
- Entscheidung/Maßnahme: offen (Retro) – Kandidat A/B wahrscheinlich.

---

## OBS-S092-2 – Dokumentiertes Kommando zum Header-Lesen (statt eigenes Script)
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Doku/Hook/Script
- Beobachtung: Viele Doku-Dateien tragen im Header die Meta-Infos inkl. Schema/Format (z.B. lessons_learned, observations, adr, tech-debt). Agenten lesen sie ad-hoc (sed/Read), teils unvollständig. Es genügt ein **dokumentiertes Kommando-Pattern** mit bestehenden Tools (z.B. `sed -n '1,/^-->/p' <datei>` o.ä.), aufgenommen in den Startup-Hinweis bzw. die `--list`-Referenz – **kein eigenes Script** (Wartung) und **nicht** alle Header im Startup injizieren (zu teuer). Ggf. zweigeteilt (Metadaten vs. Schema), aber evtl. besser immer beides gemeinsam, da Schema ohne Metadaten selten nützt.
- Kandidaten: A) Kommando-Pattern (bestehende Tools, z.B. `sed`-Range bis `-->`/erstes `---`) im Startup-Hinweis / auf der `--list`-Referenz dokumentieren (gering) | B) doch eigenes Script (mehr Wartung) | C) Status quo
- Entscheidung/Maßnahme: offen (Retro) – Kandidat A wahrscheinlich; Header-Endmarker-Konvention (`-->` vs. `---`) projektweit klären, damit ein einzelnes Pattern alle Docs trifft.

---

## OBS-S092-3 – kaizen-Workshop prüft LL-Metadaten (v.a. Impact) vor dem Retro-Skript
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Review
- Beobachtung: LL-Metadaten (insb. Impact) könnten falsch/inkonsistent gesetzt sein und damit Jenga-/Prioritäts-Matrix verzerren. Idee: Der kaizen-Workshop listet vor dem Retro-Skript potentielle Metadaten-Fehler auf. Nutzen ist empirisch prüfbar: mehrere Subagenten bewerten bestehende Einträge (oder ein Sample) **blind** neu; viele Abweichungen → analysieren und Schlüsse ziehen (echte Fehlklassifikation vs. bloßer Drift / subjektive Streuung).
- Kandidaten: — (Retro; erster Schritt = Validierungs-Experiment mit blinden Subagenten-Neubewertungen eines Samples, dann Abweichungs-Analyse)
- Entscheidung/Maßnahme: offen (Retro) – erst Nutzen via Blind-Rebewertung verifizieren, bevor ein Workshop-Schritt eingebaut wird.
- Bezug: OBS-S085-10 (Impact-Vokabular geteilt mit LL-Schwere)

---

## OBS-S093-1 – SonarAnalyzer S125 feuert auf deutsche Kommentare mit Satz-Ende „;"
- Quelle: Agent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Build/Analyzer
- Beobachtung: SonarAnalyzer S125 („Sections of code should not be commented out") interpretiert deutschsprachige Kommentare, die mit „…;" enden, als auskommentierten Code und bricht den Build. In dieser Session musste ein korrekter Erklär-Kommentar nur umformuliert werden, um S125 zu beruhigen – inhaltlich unnötiger Eingriff.
- Kandidaten: A) Kommentar-Stil-Hinweis in coding-guideline-csharp.md (dt. Kommentare nicht auf „;" enden) (gering, kaschiert Symptom) | B) S125 gezielt feinjustieren/dämpfen (mittel, Analyzer-Config) | C) Status quo (Einzelfall umformulieren)
- Entscheidung/Maßnahme: offen (Retro) – Impact gering; vor Config-Änderung Häufigkeit beobachten.

---

## OBS-S093-3 – „Nächste Prioritäten" brauchen pro Vorzieh-Item Scope + Begründung + Done-Zustand
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: In `AGENT_MEMORY.md` → „Nächste Prioritäten" wurde ein vorgezogenes Item zu weit gefasst notiert („`@US-904-error`-Block vorziehen") und ohne dauerhaft sichtbare Begründung. Folge: Der Vorzieh-Grund (S091 feld-keyed-422-Bug) wurde inertial weitergeschleppt, obwohl er längst erledigt war; ein Agent konnte weder erkennen, woraus das Vorgezogene besteht, noch wann es fertig ist. „Error-Szenarien vorziehen" ist zu weit; „Error-Szenario leerer Name + leere Einheit vorziehen, weil <Grund>" ist eng genug. Gilt auch für andere Vorzieh-Items (z.B. „Erst-Formular-UX-Baseline vor dem Feature-Fluss" braucht ebenfalls einen notierten Grund).
- Kandidaten: A) Konvention für Vorzieh-Einträge: konkretes Szenario(-Set) + Begründung + Done-Kriterium, beim Erledigen entfernen (gering) | B) frei wie bisher (driftet) | C) Vorzieh-Items ganz verbieten, immer Feature-Reihenfolge (zu rigide)
- Entscheidung/Maßnahme: offen (Retro) – Kandidat A wahrscheinlich; ggf. als Schreib-Hinweis in closing-session Schritt 8 / AGENT_MEMORY-Header.

---

## OBS-S094-1 – AGENT_MEMORY auf Skill-Scope eindampfen (Cruft dupliziert auto-geladene Quellen)
- Quelle: User
- Status: NEU
- Impact: GERING    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: `AGENT_MEMORY.md` wird bei jedem Session-Start voll injiziert (jede Zeile kostet Token), enthält aber Inhalte, die **andere ebenfalls auto-geladene Quellen** duplizieren: (a) die „Letzte Aktualisierung"-Zeile (Datum aus git/Index/Harness ableitbar, Änderungs-Summary ↔ Session-Index-Zeile); (b) der Navigations-Header (Session-Logs, adr via `decisions.py`, Kaizen, tech-debt, open-questions) ↔ CLAUDE.md-Navigationstabelle (die „Navigationszentrale", ebenfalls beim Start geladen). Der `closing-session`-Skill (Schritt 8) scoped die Datei ohnehin auf **Phase + Aktuelle Story + Nächste Prioritäten** – Header/Changelog stehen quer dazu.
- Kandidaten: A) „Letzte Aktualisierung"-Zeile + Navigations-Header streichen, AGENT_MEMORY auf Phase/Story/Prioritäten reduzieren, `closing-session` Schritt 8 klarstellen (gering; Datei + Skill gemeinsam, sonst Drift) | B) Status quo (redundant, Token-Kosten je Start)
- Entscheidung/Maßnahme: offen (Retro) – Kandidat A wahrscheinlich; Datei + Skill **zusammen** ändern (sonst driftet die Datei gegen den Skill, der die Zeilen implizit erwartet).

---

## OBS-S095-1 – OBS speisen Jenga nicht → Retro droht mit OBS-Themen vollzulaufen und lang zu werden
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: Observations speisen den Jenga-Score bewusst nicht (kein Problemdruck) und werden nur in der Retro getrefiert. Folge: Das offene OBS-Backlog wächst monoton zwischen den Retros (aktuell ~25 offene Einträge), und Schritt 4 (Backlog-Grooming) bläht die Retro auf — viele Punkte auf einmal, kognitiv anstrengend (vgl. OBS-S086-3). Es fehlt ein Mechanismus, der das Backlog zwischen Retros abbaut oder die Grooming-Last begrenzt (z.B. Priorisierung/Stapelung, Sofort-Erledigung trivialer OBS außerhalb der Retro, OBS-Budget pro Retro).
- Kandidaten: — (gemeinsame Discovery in eigener Session)
- Entscheidung/Maßnahme: **Eigene Session (S095 vertagt – Design-Thema, braucht Platz).** Erarbeitete Diagnose als Startpunkt: Das Backlog wächst nicht wegen zu hoher *Erfassungs*-, sondern zu niedriger *Auflösungsrate* (Auflösung ist retro-gegated; früher wurden OBS zwischen Sessions erledigt – Gewohnheit ging beim Formalisieren verloren). Hebel = Auflösung aus der Retro herauslösen für alles ohne Diskussionsbedarf. Zentrale Spannung: Triage-beim-Erfassen vs. OBS-S086-1 (keine Vorab-Kandidaten) → Auflösungsidee: nur *leichte Triage-Klassifikation* beim Erfassen (trivial+risikolos / hoher Impact / braucht Diskussion), keine Kandidaten-Entwicklung. Zu betrachtende User-Punkte: (a) Wachstum bremsen; (b) was sofort erledigen (trivial-risikolos vs. hoher Impact); (c) Maßnahmen-Analyse beim Erfassen nötig zum Bewerten? grill-me zum Aufdecken von Ziel/Weg nutzen.
- Bezug: OBS-S086-3 (blockweise Findings), OBS-S086-1 (keine Vorab-Kandidaten), OBS-S085-12 (Noise-Review-Skalierung)

---

## OBS-S095-2 – review-docs: Check auf „Low-Value-Content" (grenzwertiger Mehrwert, Kosten > Nutzen)
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Skills/Docs könnten Selbstverständlichkeiten enthalten — Regeln, gegen die ohnehin nie verstoßen würde, oder Inhalte mit grenzwertigem Mehrwert, deren Token-/Lesekosten den Nutzen nicht rechtfertigen. Offen, ob der `review-docs`-Skill dafür einen expliziten Check hat. Die Skill-Beschreibung nennt „Minimalität", aber das zielt eher auf Redundanz/Länge — „Low-Value-Content" (Regel ist korrekt, aber unnötig, weil der Fehler praktisch nie passiert) ist ein anderer, schärferer Winkel und evtl. nicht abgedeckt.
- Kandidaten: — (gemeinsame Discovery in der Retro; u.a.: erst prüfen, ob review-docs „Minimalität" das schon abdeckt, vs. eigenen Low-Value-Check ergänzen)
- Entscheidung/Maßnahme: offen (Retro)
- Bezug: —

---

## OBS-S095-3 – Poka-Yoke-Hook: stabile Datei darf keine volatile ID referenzieren (Referenz-Richtung)
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Das principles.md-Prinzip „Referenzen laufen volatil → stabil, nie umgekehrt" wird nur manuell durchgesetzt (S094: LL-S094-2; S095: 2 weitere Funde in Skills). Ein **syntaktischer** Check ist poka-yoke-bar (kein Ermessen): Beim Edit/Write einer **stabilen** Datei prüfen, ob neuer Inhalt ein **volatiles** ID-Schema (`OBS-`/`OQ-`/`LL-`/`TD-S…`) referenziert. Empirie S095: nur 5 Bestands-Treffer in 3 stabilen Dateien (FP-Risiko niedrig) — **sofern** die kaizen-internen Bookkeeping-Dateien (`observations.md`, `countermeasures.md`, `lessons_learned.md`, `process.md`) aus dem „stabilen" Set ausgeschlossen werden.
- Kandidaten: — (gemeinsame Discovery beim Bau; Designpunkte: (1) Klassifikation stabil-Set vs. volatil-/Bookkeeping-Set; (2) OBS/LL werden *archiviert* (Ref stale-aber-auffindbar) vs. OQ/TD werden *gelöscht* (Ref dangelt hart) → ggf. hart blocken bei OQ/TD, warnen bei OBS/LL; (3) **Ausnahme „temporäre Pilot-Notiz"**: eine bewusst zeitlich begrenzte Kopplung einer stabilen Datei an ein volatiles Pilot-OBS — aktuelles Beispiel: TS-Guideline-LSP-Pilot ↔ OBS-S085-4 (kann nicht abgeschlossen werden mangels Nutzungsdaten) → Marker-/Pfad-Ausnahme statt False-Positive; (4) Ort: Check-Modul in `check-code-quality-blocking.py` (In-Process-Dispatcher).
- Entscheidung/Maßnahme: offen — Hook gezielt bauen (wird dann CM); Bestand: 2 von 5 Refs in S095 bereinigt, die 3 TS-Guideline-Hits bleiben als dokumentierte Pilot-Ausnahme.
- Bezug: principles.md „Referenzen volatil→stabil"; CM-S086-1 (Referenz-Hygiene/stale Anchors); LL-S094-2

---

## OBS-S095-4 – „Lead-Developer"-Subagent als Eskalations-Instanz für Layer-Implementer
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: AGENT    Kontext: Agent-Prompt
- Beobachtung: Statt anspruchsvolle Schichten komplett auf Opus laufen zu lassen, könnte ein dedizierter „Lead-Developer"-Subagent (stark, z.B. Opus) als Eskalations-Instanz dienen, an den schwächere Implementer (sonnet/haiku) gezielt **Fragen** übergeben — wie in echten Teams, wo Juniors Hilfestellung von Seniors holen. So liefe nur der punktuelle Rat auf dem teuren Modell, nicht die ganze Schicht. Vorausschauende Optimierung der Modell-/Token-Ökonomie; baut auf der S095-Entscheidung „Implementer-Default = sonnet, Opus-Eskalation pro Schicht" auf.
- Kandidaten: — (gemeinsame Discovery; u.a.: Frage-Übergabe-Protokoll via SendMessage an einen Lead-Subagenten; wann eskalieren; ob haiku als Implementer-Floor tragfähig ist)
- Entscheidung/Maßnahme: offen (Retro) — eigene Anpassung, vor Umsetzung bewerten.
- Bezug: OBS-S085-8 / OBS-S093-2 (Modellwahl pro Schicht)
