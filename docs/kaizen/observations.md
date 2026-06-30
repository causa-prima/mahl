# Observations – Beobachtungs-Backlog

<!--
Zweck: Vorausschauende System-Design-Beobachtungen / Optimierungen (proaktiver Track).
       Ergänzt das reaktive lessons_learned.md. Speist den Jenga-Score NICHT.
       ABER: `obs-drain.py` parst diese Datei (via `obs_parse.py`) für den Drain-Vorschlag → das Eintrags-Format
       unten parse-stabil halten (Feld-Präfixe `- Status:` / `- Impact:` / `- Bezug:` nicht umformatieren).

Eintrag-Format:
  ## OBS-S<NNN>-<n> – Kurztitel
  - Quelle: User | Orchestrator | Subagent   (bei Agent-Quelle möglichst präzise: Subagent vs. Orchestrator)
  - Status: NEU | IN BEOBACHTUNG bis S<NNN> | UMGESETZT (S<NNN>) | VERWORFEN (Grund)
            (IN BEOBACHTUNG: `bis S<NNN>` = Pflicht-Wiedervorlage-Termin; Mechanik: process.md)
  - Impact: KRITISCH | HOCH | MITTEL | GERING    Häufigkeit: gelegentlich | häufig | dauerhaft
  - Kategorie: PROZESS | AGENT | QUALITÄT | TOOLING    Kontext: <Kontext-Tag wie in lessons_learned>
  - Beobachtung: <was ist nicht ideal / was fiel auf>
  - Entscheidung/Maßnahme: <bei Erfassung offen; beim Drain: gewählte Lösung + warum statt Alternativen / Verwerf-Grund / Aufschub-Grund + Re-Trigger>; → CM-… falls stehende Leitplanke
  - Bezug: (optional) LL-S<NNN>-<n> / OBS-S<NNN>-<n> / CM-S<NNN>-<n>

  Impact = dieselben vier Werte wie die LL-Schwere (geteiltes Vokabular); Impact × Häufigkeit = Prioritäts-Matrix.
  Erfassungs-Regel: sofort & problemlos umsetzbare Einmal-Optimierung → einfach machen, kein Eintrag;
                    aufgeschoben → Eintrag.

Zwei-Brillen-Modell, Erfassungs-Tests, Gefahr/Kandidaten-Bewertung, Evaluierungs-Gate,
Drain-Mechanismus (Wert-/Alters-/Wiedervorlage-Lane), Quer-Bewegung LL↔OBS: docs/kaizen/process.md
-->

> **Mechanismus & Prozess:** `docs/kaizen/process.md`
> **Archiv (aufgelöste Einträge):** `docs/kaizen/archive/observations_archive.md`

---

## OBS-S090-1 – Vitest ist typ-blind; Typfehler erst im Stryker-Dry-Run sichtbar
- Quelle: Agent
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: frontend-tdd
- Beobachtung: `vitest` (esbuild, transpile-only) prüft **keine** Typen. Echte TS-Fehler (z.B. `ResultAsync` ≠ `Promise`; `errAsync`-`kind`-Widening) blieben bis zum Stryker-typescript-checker-Dry-Run unsichtbar (~1 Zyklus Verzögerung). Kein `tsc --noEmit`-Wrapper auf der Bash-Allow-Liste → der Layer-Implementer konnte Typen nicht isoliert **vor** dem teuren Stryker-Lauf prüfen.
- Entscheidung/Maßnahme: aufgeschoben (NEU) – vor Bewertung sammeln.

---

## OBS-S090-2 – qa-check-Übergabe-Hash erzwingt Extra-Stryker-Lauf bei Re-Stage
- Quelle: Agent (Orchestrator-Beobachtung)
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: implementing-scenario / qa-check
- Beobachtung: Der `qa-check.py`-Übergabe-Hash rechnet über den **gestageten** Zustand. Stagt der Orchestrator nach der Subagent-Hash-Berechnung noch eine freigegebene Test-Änderung, mismatcht `--verify` → ein **erneuter** (teurer) Stryker-Lauf nur, um einen frischen Hash über den finalen Index zu erzeugen. In dieser Session 2× passiert (Frontend Option-A-Restage; variant-c).
- Entscheidung/Maßnahme: aufgeschoben (NEU) – Reihenfolge-Konvention im implementing-scenario-Flow klären; vor Bewertung sammeln.

---

## OBS-S090-3 – Alt-Hooks überprüfen/entschlacken
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Hook/Script
- Beobachtung: Die Hook-Scripte (`check-memory.sh`, `pre-compact.sh`, `session-start.sh`, `session-end.sh`, `task-completed.sh`) stammen aus einer frühen Projektphase mit noch geringem Claude-Code-Verständnis. Mehrere tragen evtl. veraltete Annahmen (z.B. der jetzt korrigierte `/mnt/c`-Hardcode, S090). Ungeprüft, ob einzelne Hooks heute noch ihren Zweck erfüllen, redundant sind oder angepasst/entfernt gehören.
- Entscheidung/Maßnahme: aufgeschoben (NEU) – in der nächsten Retro evaluieren; verwandt mit OBS-S088-1 (Hook-Dispatcher/Reload-Friktion).
- Bezug: OBS-S088-1

## OBS-S090-4 – Subagent-`git add` umgeht den Test-Review-Gate
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: TDD
- Beobachtung: Die Layer-Implementer haben das `Bash`-Tool und die Allow-Liste erlaubt `git add <datei>` → ein Subagent kann (und tat es in S090) Dateien selbst stagen. Der `qa-check`-Übergabe-Hash rechnet über den **gestageten** Zustand, weshalb der Subagent sogar stagen *muss*. Damit ist der dokumentierte Gate „Haupt-Thread reviewt Tests, *dann* staged er" faktisch nicht erzwungen: Ein Subagent könnte ungeprüfte Assertions stagen und trotzdem einen grünen 100%-Hash erzeugen. **Mutation-Score + Hash beweisen „getestet+gemutet", nicht „vom Orchestrator inhaltlich freigegeben".** Kein konkreter Schaden in S090 (Review fand statt) — Integritäts-Risiko, kein Fehlausgang.
- Entscheidung/Maßnahme: aufgeschoben (NEU) – beim Drain entscheiden.
- Bezug: OBS-S090-2 (qa-check-Hash/Staging-Reihenfolge)

## OBS-S090-5 – TD-Grooming-Lücke: Infra-Schuld fällt durchs Raster
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Sonstiges
- Beobachtung: Technische Schuld wird heute nur **opportunistisch** gegroomt (Architektur-Check in `implementing-scenario`: passende TD zum aktuellen Szenario mitnehmen). Schuld ohne Szenario-Bezug — typisch Infrastruktur, z.B. **TD-S083-5** (dirty-Postgres, kein Reset zwischen E2E-Läufen) — mappt auf kein Szenario und wird so **nie** angefasst. Zusätzlich fehlt am Session-Ende ein Check, ob TD unbewusst miterledigt wurde (dann Eintrag schließen).
- Entscheidung/Maßnahme: aufgeschoben (NEU) – Lösung in der nächsten Retro finden (User: „dazu müssen wir eine Lösung finden").
- Bezug: OBS-S087-1 (TD relevanz-filterbar machen)

---

## OBS-S085-2 – Zu verbose Kommunikation (Orchestrator↔Subagenten) verschwendet Token
- Quelle: User
- Status: IN BEOBACHTUNG bis S105
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Kommunikation im implementing-scenario (und ggf. allen Prozessen) ist unnötig verbose.
- Entscheidung/Maßnahme: Aufgeschoben – Spike mit hoher Gefahr (Knappheit ↔ Subagent-Qualität), kein Schnellschuss. Plan: **Phase 1** an einem realen `implementing-scenario`-Lauf messen, *wo* die Tokens hingehen (Orchestrator→Subagent-Prompts vs. Subagent→Orchestrator-Reports vs. Narration); **Phase 2** nur die verbose Richtung straffen, qualitäts-gegated (Tests/Review/Mutation-Score). **Re-Trigger:** erst nach dem geplanten `implementing-scenario`-Umbau (mehrere Szenarien gleichzeitig) – wenn der stabil läuft (~5–10 Sessions); Backstop bis S105.

## OBS-S085-3 – Agenten durchsuchen Tool-Outputs selbst statt unsere gezielten Scripte zu nutzen
- Quelle: User
- Status: IN BEOBACHTUNG bis S099 – S087: A (Wrapper-Audit, kein Change) + C (`--list`/SessionStart-Hinweis „ohne tail/grep") + D (`allowed-commands.log`) umgesetzt, B (tail-Deny) zurückgestellt; **S095 wiederaufgegriffen** nach D-Analyse.
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Mutation-Testing
- Beobachtung: Agenten greppen/`tail`-en Stryker-&-Co-Output, obwohl unsere Scripte gezielt nur das Relevante ausgeben sollen (Deny-Log S086: 81 head/tail-Zeilen).
- Entscheidung/Maßnahme: **A + C + D**; **B zurückgestellt** bis mehr Daten (mittlere Gefahr, könnte legitime Nutzung blocken). C über `--list` + SessionStart-Injection: knappe Script-Anwendungsfälle + Hinweis „normal **ohne** `tail`/Filter nutzen (Output ist optimal); wo nicht → als Beobachtung sammeln". D = erlaubte Befehle loggen.
- **Rezidiv (S090, Quelle: User):** Trotz Gegenmaßnahme C erneut aufgetreten — `grep` mehrfach auf qa-check-Output, `tail` auf playwright-test. Der Session-Hinweis (C) allein verhindert das Verhalten nicht zuverlässig.
- **D-Analyse durchgeführt + Neubewertung (S095):** `allowed-commands.log` ausgewertet (~15+ Filter-Instanzen S90–93). Befund: das Filtern ist **nicht** einheitlich Misuse, sondern zerfällt in drei Klassen — (1) **reines Kürzen** auf bereits kuratiertem Output (`vitest-run|tail`, `eslint-run|tail`) → Disziplin-Thema; (2) **gezieltes Feld-Extrahieren**, weil der Wrapper das Verdikt vergräbt (`qa-check --verify | grep | tail`, `stryker | grep Score/Survived`) → Wrapper sollte das Verdikt klar ausgeben; (3) **legitimer Workaround**, weil der Wrapper die relevante Info gar nicht liefert (`dotnet-test` bei RED ohne Assertion-Details → **OBS-S091-1**). Konsequenz (User-Entscheid): **kein pauschales Deny (B)** — es würde Klasse 2+3 bestrafen. Stattdessen **zuerst die Wrapper fixen** (Klasse 2+3, s. OBS-S091-1/-3), *dann* neu bewerten, ob für Restklasse 1 überhaupt noch eine Maßnahme nötig ist.

## OBS-S085-4 – Kein Language-Server für die Agenten-Programmierung im Einsatz
- Quelle: User
- Status: IN BEOBACHTUNG bis S099 – **Pilot durchgeführt & technisch validiert (2026-06-20):** `typescript-lsp`@claude-plugins-official läuft auf **nativem** Claude-Install 2.1.183 (anthropics/claude-code #20050 hier **nicht** relevant – galt für ältere Versionen); `ENABLE_LSP_TOOL` nicht nötig; `/reload-plugins` statt Neustart genügt. Alle Ops ok (hover, documentSymbol, goToDefinition cross-file, workspaceSymbol, findReferences); **semantisch präziser als grep** (Kommentar-/String-Treffer korrekt ausgeschlossen). **CAVEAT:** erster `findReferences` direkt nach Plugin-Load = kalter/unvollständiger Index → erst nach Warmlauf vollständig (bei verdächtig wenigen Treffern wiederholen). Offene Bewertung: realer Nutzen über laufende Arbeit. C# weiter zurückgestellt (#1359).
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
- Entscheidung/Maßnahme: Aus der S086-Evaluierung **ausgenommen** (deferred Meta-Änderung) – getrennt entscheiden, ggf. gekoppelt an OBS-S085-14 (gemeinsamer Script/History-Touch).

## OBS-S085-12 – Noise-Review skaliert nicht: Archive jede Retro neu zu filtern wird teuer
- Quelle: Agent
- Status: IN BEOBACHTUNG bis S105
- Impact: GERING    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: kaizen-Schritt 0 sah vor, alle Archiv-Dateien jede Retro neu gegen den Filter zu prüfen → Token-Kosten steigen, Grenznutzen gering.
- Entscheidung/Maßnahme: **B gewählt** — Staffel B (nur zuletzt archivierte Periode doppelprüfen) → (kein Rückfall) → A (Archiv-Scan weglassen). Umsetzung: kaizen Schritt 0 (bereits angewandt). Gekoppelt an CM „Noise als LL" (AKTIV + beobachten).

## OBS-S086-5 – Session-Datei-Inhalt: Scope definieren
- Quelle: User
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Unklar/unausgewertet, was in `docs/history/sessions/session_NNN.md` gehört – ist es sinnvoll, alles festzuhalten? Welche Teile können/sollten weg, was fehlt? (Analog zu OBS-S085-9 für `index.md`, aber für die Session-Dateien.)
- Entscheidung/Maßnahme: offen (Retro)

## OBS-S087-1 – Technische Schuld durchsuchbar/relevanz-gefiltert machen
- Quelle: User
- Status: NEU
- Impact: GERING–MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: `docs/tech-debt.md` wird heute per Volltext-grep durchsucht (bei 10 Einträgen ausreichend). Wächst die Datei, wäre es nützlich, wenn der Architektur-Check in `implementing-scenario` (oder ein eigenes Script) die zum bearbeiteten Code-Bereich **potentiell relevante** technische Schuld automatisch identifiziert/auflistet – z.B. über kuratierte Bereichs-Keywords pro Eintrag. Bewusst NICHT jetzt umgesetzt (YAGNI): Keyword-Vokabular sollte **gemeinsam mit dem konsumierenden Script** entworfen werden, sonst spekulative Tags ohne Abnehmer + Drift.
- Entscheidung/Maßnahme: offen (Retro)
- Bezug: OBS-S085-16 (AGENT_MEMORY-Restruktur, in deren Zuge tech-debt.md ausgelagert wurde)

## OBS-S087-2 – Gemeinsame „Tracker-Datei-Konvention" einmal dokumentieren
- Quelle: Agent
- Status: NEU
- Impact: GERING–MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: `observations.md`, `countermeasures.md`, `tech-debt.md`, `open-questions.md` teilen inzwischen dasselbe Muster (Header `wann-lesen/wann-schreiben/Eintrag-Format`, Session-basierte IDs `XX-S<NNN>-<n>`, Fließtext statt Tabelle, `---`-Trenner zwischen Einträgen, Sortierung nach ID aufsteigend). Das Muster ist nirgends zentral beschrieben → beim Anlegen einer neuen Tracker-Datei wird es ad-hoc re-derived (S087: tech-debt.md ~4× überarbeitet, s. LL-S087-1). Eine einmalige Konventions-Beschreibung (z.B. in `process.md` oder einem kurzen Doku-Styleguide) würde das vermeiden.
- Entscheidung/Maßnahme: offen (Retro)
- Bezug: LL-S087-1

## OBS-S088-1 – Hook-Registrierung: ein Dispatcher je Matcher/Event statt Einzeleinträge
- Quelle: User
- Status: NEU
- Impact: GERING–MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Pro Tool-Matcher stehen mehrere Hook-Scripts einzeln in `settings.json` (PreToolUse `Edit|Write`: dependency-allowlist, code-quality-blocking, index-length, e2e-scenario-ref). Ein neuer/entfernter Check erfordert eine `settings.json`-Änderung → **Claude-Code-Reload** nötig, bevor er greift. `check-code-quality-blocking.py` ist bereits ein In-Process-Dispatcher (`CHECKS`-Liste + `checks/`-Package) – Checks dort sind reload-frei. Verallgemeinert man das (ein Dispatcher je Matcher *und* Event, der die Einzel-Checks aufruft), würde künftiges Hinzufügen/Entfernen eines Checks nur den Dispatcher-Inhalt ändern → sofort live, ohne Reload. Designpunkte: Pre (blocking, exit 2) vs. Post (non-blocking) getrennt; uneinheitlicher Input-Vertrag (Fragment-`HookInput` vs. voller Post-Edit-Inhalt + Datei-Reads bei e2e-scenario-ref → Dispatcher gibt rohes JSON, Checks adaptieren); Output-Stil je Dispatcher einheitlich (Bash nutzt JSON-`permissionDecision`); fail-open je Check.
- Entscheidung/Maßnahme: offen (Retro) – als eigener fokussierter Refactor mit eigenen Tests, getrennt vom Szenario-Tracking-Commit
- Bezug: OBS-S085-16 (Reload-Friktion-Familie)

## OBS-S091-2 – Wrapper-Aufrufpfad cwd-relativ, kollidiert mit Projekt-Tooling-cwd
- Quelle: Agent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Die Wrapper liegen im Repo-Root (`.claude/scripts/`) und lösen ihren Root intern via `_util.REPO_ROOT` auf — aber der **Aufrufpfad** `python3 .claude/scripts/foo.py` ist cwd-relativ. Projekt-Tooling (`npm`/`dotnet`/`vite`) zieht die Shell in `Client/`/`Server/`-Subdirs; der nächste Wrapper-Aufruf scheitert dann mit „No such file" (S091: beide Subagenten + Orchestrator betroffen).
- Entscheidung/Maßnahme: offen (Retro)
- Bezug: —

## OBS-S092-1 – Doppelte LL/OBS-Erfassung: implementing-scenario Schritt 6.1 vs. closing-session
- Quelle: User
- Status: NEU
- Impact: GERING    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: implementing-scenario / closing-session
- Beobachtung: `implementing-scenario` Schritt 6.1 („Offene Punkte triagieren") erfasst LLs/OBSs/Tech-Debt, und `closing-session` (Schritt 2/3/5) erfasst dieselbe Klasse von Punkten erneut. Bei direktem Übergang Szenario → Abschluss ist die Vorab-Triage in 6.1 redundant – sie ist nur nötig, wenn die Session **nicht** abgeschlossen wird (Szenario fertig, Session läuft weiter). In dieser Session führte das zu doppeltem Abfragen.
- Entscheidung/Maßnahme: offen – beim Drain entscheiden.

---

## OBS-S092-2 – Dokumentiertes Kommando zum Header-Lesen (statt eigenes Script)
- Quelle: User
- Status: IN BEOBACHTUNG bis S106
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Doku/Hook/Script
- Beobachtung: Viele Doku-Dateien tragen im Header die Meta-Infos inkl. Schema/Format (z.B. lessons_learned, observations, adr, tech-debt). Agenten lesen sie ad-hoc (sed/Read), teils unvollständig. Es genügt ein **dokumentiertes Kommando-Pattern** mit bestehenden Tools (z.B. `sed -n '1,/^-->/p' <datei>` o.ä.), aufgenommen in den Startup-Hinweis bzw. die `--list`-Referenz – **kein eigenes Script** (Wartung) und **nicht** alle Header im Startup injizieren (zu teuer). Ggf. zweigeteilt (Metadaten vs. Schema), aber evtl. besser immer beides gemeinsam, da Schema ohne Metadaten selten nützt.
- Entscheidung/Maßnahme: Aufgeschoben – beim Drain zur Doku-Architektur-/Progressive-Disclosure-Designfrage gewachsen, kein Quick-Edit mehr: (1) welche Dateien brauchen überhaupt einen Header (vs. Name/Index erklärt sich selbst)? (2) was gehört in den Header (Leitfrage: *wann* liest ein Agent die Datei und *welche* Header-Info braucht er dann)? (3) In-Datei-Header vs. **Wiki-Struktur** (eigene Index-/Header-Dateien mit MD-Links). Der kleine Slice (sed-Pattern + Endmarker-Konvention `-->` vs. `---`) ist durch genau diese offenen Fragen blockiert. Re-Trigger: nächster Doku-Struktur-/`review-docs`-Durchgang.

---

## OBS-S092-3 – kaizen-Workshop prüft LL-Metadaten (v.a. Impact) vor dem Retro-Skript
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Review
- Beobachtung: LL-Metadaten (insb. Impact) könnten falsch/inkonsistent gesetzt sein und damit Jenga-/Prioritäts-Matrix verzerren. Idee: Der kaizen-Workshop listet vor dem Retro-Skript potentielle Metadaten-Fehler auf. Nutzen ist empirisch prüfbar: mehrere Subagenten bewerten bestehende Einträge (oder ein Sample) **blind** neu; viele Abweichungen → analysieren und Schlüsse ziehen (echte Fehlklassifikation vs. bloßer Drift / subjektive Streuung).
- Entscheidung/Maßnahme: offen (Retro) – erst Nutzen via Blind-Rebewertung verifizieren, bevor ein Workshop-Schritt eingebaut wird.
- Bezug: OBS-S085-10 (Impact-Vokabular geteilt mit LL-Schwere)

---

## OBS-S093-1 – SonarAnalyzer S125 feuert auf deutsche Kommentare mit Satz-Ende „;"
- Quelle: Agent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Build/Analyzer
- Beobachtung: SonarAnalyzer S125 („Sections of code should not be commented out") interpretiert deutschsprachige Kommentare, die mit „…;" enden, als auskommentierten Code und bricht den Build. In dieser Session musste ein korrekter Erklär-Kommentar nur umformuliert werden, um S125 zu beruhigen – inhaltlich unnötiger Eingriff.
- Entscheidung/Maßnahme: offen (Retro) – Impact gering; vor Config-Änderung Häufigkeit beobachten.

---

## OBS-S095-2 – review-docs: Check auf „Low-Value-Content" (grenzwertiger Mehrwert, Kosten > Nutzen)
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Skills/Docs könnten Selbstverständlichkeiten enthalten — Regeln, gegen die ohnehin nie verstoßen würde, oder Inhalte mit grenzwertigem Mehrwert, deren Token-/Lesekosten den Nutzen nicht rechtfertigen. Offen, ob der `review-docs`-Skill dafür einen expliziten Check hat. Die Skill-Beschreibung nennt „Minimalität", aber das zielt eher auf Redundanz/Länge — „Low-Value-Content" (Regel ist korrekt, aber unnötig, weil der Fehler praktisch nie passiert) ist ein anderer, schärferer Winkel und evtl. nicht abgedeckt.
- Entscheidung/Maßnahme: offen (Retro)
- Bezug: —

---

## OBS-S095-3 – Poka-Yoke-Hook: stabile Datei darf keine volatile ID referenzieren (Referenz-Richtung)
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Das principles.md-Prinzip „Referenzen laufen volatil → stabil, nie umgekehrt" wird nur manuell durchgesetzt (S094: LL-S094-2; S095: 2 weitere Funde in Skills). Ein **syntaktischer** Check ist poka-yoke-bar (kein Ermessen): Beim Edit/Write einer **stabilen** Datei prüfen, ob neuer Inhalt ein **volatiles** ID-Schema (`OBS-`/`OQ-`/`LL-`/`TD-S…`) referenziert. Empirie S095: nur 5 Bestands-Treffer in 3 stabilen Dateien (FP-Risiko niedrig) — **sofern** die kaizen-internen Bookkeeping-Dateien (`observations.md`, `countermeasures.md`, `lessons_learned.md`, `process.md`) aus dem „stabilen" Set ausgeschlossen werden.
- Entscheidung/Maßnahme: offen — Hook gezielt bauen (wird dann CM); Bestand: 2 von 5 Refs in S095 bereinigt, die 3 TS-Guideline-Hits bleiben als dokumentierte Pilot-Ausnahme.
- Bezug: principles.md „Referenzen volatil→stabil"; CM-S086-1 (Referenz-Hygiene/stale Anchors); LL-S094-2

---

## OBS-S095-4 – „Lead-Developer"-Subagent als Eskalations-Instanz für Layer-Implementer
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: AGENT    Kontext: Agent-Prompt
- Beobachtung: Statt anspruchsvolle Schichten komplett auf Opus laufen zu lassen, könnte ein dedizierter „Lead-Developer"-Subagent (stark, z.B. Opus) als Eskalations-Instanz dienen, an den schwächere Implementer (sonnet/haiku) gezielt **Fragen** übergeben — wie in echten Teams, wo Juniors Hilfestellung von Seniors holen. So liefe nur der punktuelle Rat auf dem teuren Modell, nicht die ganze Schicht. Vorausschauende Optimierung der Modell-/Token-Ökonomie; baut auf der S095-Entscheidung „Implementer-Default = sonnet, Opus-Eskalation pro Schicht" auf.
- Entscheidung/Maßnahme: offen (Retro) — eigene Anpassung, vor Umsetzung bewerten.
- Bezug: OBS-S085-8 / OBS-S093-2 (Modellwahl pro Schicht)

---

## OBS-S096-1 – Vor OBS-Erfassung mit bestehenden Einträgen zusammenfassen (parametrisiert/Klasse/Referenz)
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Kaizen
- Beobachtung: Vor dem Festhalten einer neuen OBS prüfen, ob sie mit einem bestehenden Eintrag zusammenfassbar ist – analog parametrisierten Tests: dieselbe Beobachtung an anderer Stelle → bestehendes OBS erweitern statt neu anlegen. Auch nach Problemklassen/anderen Gruppierungen bündeln. Zudem per `Bezug:` mehrere OBS an derselben Stelle gemeinsam lösbar machen (auch bei unterschiedlichen Problemen). Senkt Backlog-Redundanz und Drain-Last.
- Entscheidung/Maßnahme: offen – beim Drain entscheiden.
- Bezug: OBS-S086-2 (Verständnis vor Erfassung); OBS-S086-3 (blockweise)

## OBS-S096-2 – Welche Skill-Schritte deterministisch per Script erledigbar?
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Skill/Script
- Beobachtung: Systematisch prüfen, welche Skill-Schritte deterministisch per Script statt freihändig vom Agenten erledigt werden könnten – inkl. Schritte, die erst Voraussetzungen brauchen (z.B. „zum Parsen muss das Header-/Eintragsformat deterministisch bestimmbar sein"). Senkt Token/Varianz, erhöht Verlässlichkeit.
- Entscheidung/Maßnahme: offen – beim Drain entscheiden.
- Bezug: OBS-S096-3

## OBS-S096-3 – Scripted-Access-Layer für TD/OBS/LL/Doc (Lesen/Schreiben, Metadaten listen/filtern/move)
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Doku/Script
- Beobachtung: Möglichst viel über Script(e) zugänglich machen: Lesen + Schreiben von TD/OBS/LL etc., idealerweise auch Lesen von Doc-Teilen; ein Auflisten aller Inhalts-Header/Metadaten (schneller Überblick + Suche), Filtern nach Metadaten (wie ADRs via `decisions.py`), ggf. Status-Update/Move wo passend. Vorher bewerten, wo es sich (besonders) lohnt. (`obs-drain.py`/`obs-archive.py` sind ein erster Schritt für OBS.)
- Entscheidung/Maßnahme: offen – beim Drain entscheiden.
- Bezug: OBS-S092-2 (Doku-Header lesen, geparkt); OBS-S087-1 (TD durchsuchbar); OBS-S096-2
