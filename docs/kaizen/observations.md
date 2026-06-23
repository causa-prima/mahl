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

## OBS-S085-1 – Absolute-Pfad-Retries bei Bash verschwenden Token
- Quelle: User
- Status: UMGESETZT (S087) – `normalize_repo_paths` in `check-bash-permission.py`; `updatedInput`+`additionalContext` live verifiziert.
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Bash/Permission
- Beobachtung: Agenten versuchen wiederholt Bash mit absoluten Pfaden, laufen in den Permission-Deny und verschwenden Token (Deny-Log S086: 113/295 Zeilen mit `/mnt/c/...`, steigender Trend).
- Kandidaten: A) Hook schreibt Befehl auf relativen Pfad um | B) Deny mit gezieltem Hinweis | C) Doku/Allow-Liste schärfen
- Entscheidung/Maßnahme: **Kandidat A** (bei sauberem Scoping geringe Gefahr; spart den Retry-Round-Trip, den B kostet). `check-bash-permission.py` normalisiert als erster Schritt jeden absoluten Repo-Root-Präfix (dynamisch via `CLAUDE_PROJECT_DIR`/Skript-Pfad; ursprünglich der `/mnt/c/...`-Windows-Pfad) → relativ (**breit**, da Einheitlichkeit der Regel der Hauptnutzen ist). [S089: WSL-nativ – die `cmd.exe /c`-Ausnahme (Windows-`C:\…`) entfällt.] `# --allow-once`-Befehle unangetastet (ONE_TIME-Check zuerst). Bei Änderung `updatedInput` (umgeschriebener Befehl) + `additionalContext` (Hinweis an Agent). `defer` verworfen – würde die Hook-eigene Analyse umgehen.

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
- **Rezidiv (S090, Quelle: User):** Trotz Gegenmaßnahme C erneut aufgetreten — `grep` mehrfach auf qa-check-Output, `tail` auf playwright-test. Der Session-Hinweis (C) allein verhindert das Verhalten nicht zuverlässig. Konsequenz: Die geplante **D-Analyse** (`allowed-commands.log` auf Misuse-Patterns auswerten) ist überfällig und sollte in der nächsten Retro erfolgen — Datengrundlage, um über das zurückgestellte B (gezieltes Deny von `tail`/Filter auf Wrapper-CMDs) zu entscheiden.

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
- **Rezidiv + offene Design-Frage (S090, Quelle: User):** In S090 keine bewusste Pro-Spawn-Modellwahl durchgeführt (Layer-Implementer liefen via `inherit` auf Opus 4.8, Auditoren auf Sonnet-Default) — der „reicht der Default?"-Check (Maßnahme A) wurde nicht dokumentiert angewandt. Daraus die noch nicht beantwortete Default-Frage: Ist `inherit` (→ Orchestrator-Modell, hier Opus) der richtige **Implementer**-Default, oder sollte er auf `sonnet` stehen mit gezielter Opus-Eskalation für schwere Schichten? (Orchestrator-Opus gilt als gerechtfertigt — strittig ist nur der Implementer-Default.) In der nächsten Retro entscheiden.

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

## OBS-S091-1 – `dotnet-test.py` zeigt bei RED keine Assertion-Details (MTP-Runner)
- Quelle: Agent
- Status: NEU
- Impact: MITTEL    Häufigkeit: jeder Backend-RED
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: `dotnet-test.py` gibt bei Fehlschlag (Default **und** `--verbose`) nur `Failed: N, Passed: M` + einen Verweis auf eine UTF-16-`.log` aus — **keine** Assertion-Message/Expected-Actual. Empirisch verifiziert (S091, gezielt gebrochene Assertion, voller ungefilterter Output): der MTP-Runner (xunit.v3, TD-S089-1) schreibt Fehlerdetails nur in `TestResults/*.log`, nicht auf stdout im Format, das das `_RELEVANT`-Regex (`Error Message`/`at mahl.`) erwartet. Beim RED-Debugging fehlt damit genau die Info, die man braucht (der Backend-Subagent musste die UTF-16-Datei manuell lesen).
- Kandidaten: — (Retro; u.a.: Wrapper extrahiert die fehlgeschlagene Assertion aus der `.log` vs. MTP auf stdout-Ausgabe konfigurieren)
- Entscheidung/Maßnahme: offen (Retro)
- Bezug: TD-S089-1 (MTP-Migration)

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
- Entscheidung/Maßnahme: offen (Retro)
- Bezug: OBS-S085-3 (Filter-/Output-Familie)

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

## OBS-S093-2 – implementing-scenario Schritt 0: expliziter Modell-Eignungs-Check pro Schicht
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: Die Modellwahl für Schicht-Subagenten (OBS-S085-8: starker Default, `sonnet` nur für klar triviale Schichten) wird aktuell erst unmittelbar **vor dem Spawn** entschieden. Idee: in Schritt 0 (Architektur-Check) bereits pro erwarteter Schicht festhalten, welches Modell voraussichtlich genügt – die Komplexitätseinschätzung liegt dort ohnehin vor (YAGNI-Scope, Domain-Typen). Spart eine spätere Ad-hoc-Entscheidung und macht die Token-/Eignungs-Abwägung nachvollziehbar.
- Kandidaten: A) Schritt-0-Punkt „Modell-Eignung je geplanter Schicht" ergänzen, der beim Spawn nur noch bestätigt wird (gering) | B) Status quo (Entscheidung am Spawn) | C) Heuristik-Tabelle (Schicht-Typ → Modell) in den Skill
- Entscheidung/Maßnahme: offen (Retro) – Kandidat A wahrscheinlich; mit OBS-S085-8 abgleichen, um keine doppelte Regel zu schaffen.
- Bezug: OBS-S085-8 (Modellwahl vor Spawn)

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
