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
            (bei Erfassung mechanisch erzwungen: `.claude/hooks/check-obs-capture.py` lässt bei einem NEUEN Eintrag nur
             genau zwei Werte durch – `offen` oder `offen - beim Drain Kandidaten erstellen und bewerten`, nichts davor
             und nichts dahinter. Weder Kandidat noch offene Frage: beides ankert den bewusst frischen Drain-Agenten,
             und beides gehört ins Feld `- Beobachtung:`. Bestands-Einträge sind frei änderbar – der Drain schreibt hier
             seine Entscheidung hin; bewusster Einzelfall → `obs-ok`-Marker in den Eintrag.)

  Derselbe Hook hält bei NEUEN Einträgen zwei weitere Ausweichwege zu: die Feldliste oben ist abschließend
  (ein erfundenes `- Lösungsidee:`/`- Kandidaten:`-Feld blockt; nur `- Bezug:` ist optional), und explizite
  Lösungs-Ansagen im Eintrags-Text (`Lösungsvorschlag:`, `Idee:`, `Kandidat:`, `Abhilfe:`, `Fix:` …) blocken
  ebenfalls. Ein **Risiko** zu beschreiben („X könnte passieren") ist ausdrücklich erlaubt – gemeint ist nur
  die vorweggenommene Abhilfe. Kandidaten entstehen beim Drain, nicht bei der Erfassung.
  - Bezug: (optional) LL-S<NNN>-<n> / OBS-S<NNN>-<n> / CM-S<NNN>-<n>

  Impact = dieselben vier Werte wie die Impact-Stufe in lessons_learned (geteiltes Vokabular); Impact × Häufigkeit = Prioritäts-Matrix.
  Erfassungs-Regel: sofort & problemlos umsetzbare Einmal-Optimierung → einfach machen, kein Eintrag;
                    aufgeschoben → Eintrag.

Zwei-Brillen-Modell, Erfassungs-Tests, Gefahr/Kandidaten-Bewertung, Evaluierungs-Gate,
Drain-Mechanismus (Wert-/Alters-/Wiedervorlage-Lane), Quer-Bewegung LL↔OBS: docs/kaizen/process.md
-->

> **Mechanismus & Prozess:** `docs/kaizen/process.md`
> **Archiv (aufgelöste Einträge):** `docs/kaizen/archive/observations_archive.md`

---

## OBS-S107-1 – Subagenten nummerieren neue ADRs mit der jüngsten Serie statt der laufenden Session
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: Zwei Backend-Subagenten legten neue ADRs mit der jüngsten bestehenden Serien-Nummer (S105-3/-4) statt der laufenden Session (106) an → nachträgliche Umnummerierung inkl. ~7 Code-/Doku-Referenzen (LL-S106-2). Ein Subagent mitten in der Session hat kein klares Signal für die laufende Session-Nummer (der Index zeigt die letzte ABGESCHLOSSENE) und setzt naiv die höchste bestehende ADR-Serie fort. Bislang 1× beobachtet; die auslösende Klasse (Subagent legt ADR mitten in Session an) wiederholt sich potentiell in jedem Lauf.
- Entscheidung/Maßnahme: Aufgeschoben (S107-Retro) bis zum 2. Vorkommen – 1× liegt unter der 2×-Muster-Schwelle für eine stehende CM. Lösungsrichtung bewusst offen (Drain/Retro entscheidet frisch). Re-Trigger: 2. Auftreten einer mit falscher Session nummerierten ADR-ID.
- Bezug: LL-S106-2

## OBS-S106-1 – Szenario-Clustering (Run-Generierung) modelliert Cross-Run-State-Abhängigkeiten nicht
- Quelle: User + Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: gherkin-workshop / scenario-clustering
- Beobachtung: Beim Einstieg in US-904 run-7 fiel auf, dass die Run-Generierung (gherkin-workshop Schritt 6, `.claude/skills/gherkin-workshop/references/scenario-clustering.md`) Cross-Run-**Zustands-Abhängigkeiten** nicht abbildet. Konkret der Soft-Delete-Lebenszyklus: (1) run-7 S3 „Soft-deleted Zutat erscheint nicht in der Liste" ist ein **Reader** von `DeletedAt`, aber **kein vorausgehender Run schreibt** `DeletedAt` (der DELETE-Writer ist run-8/run-10) → das E2E-Arrangement „existiert und gelöscht wurde" hat keinen echten Vordertür-Weg, erzwingt entweder einen Test-only-Endpoint oder das Vorziehen eines späteren Runs. (2) run-8 Sz.1 fordert „Then ist die Zutaten-Liste leer" nach dem Löschen – das **setzt run-7's GET-Filter voraus**, run-8 kann also nicht vor run-7. Das Clustering ordnet/splittet also einen Zustands-Lebenszyklus so, dass Reader vor Writer landen bzw. eine Reihenfolge entsteht, die eine echte Abhängigkeit verletzt. Kostete diese Session eine mehrrundige Design-Diskussion.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: –

## OBS-S106-2 – Run-Planung flaggt Querschnitts-Policy-Rollout beim ersten Endpoint-Typ nicht vorab
- Quelle: Orchestrator + Subagent
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: gherkin-workshop / scenario-clustering
- Beobachtung: Dass run-10 den **ersten mutierenden Single-Resource-Endpoint** (DELETE) einführt und damit die Querschnitts-Policy ETag/If-Match/Optimistic-Concurrency (ADR-S058-1/-3) auslöst, wurde nicht in der Run-/Szenario-Planung sichtbar, sondern kam erst als PLANUNG-Eskalation des Backend-Subagenten mitten in der Implementierung hoch → mehrrundige Design-Diskussion über Scope (ETag jetzt vs. aufschieben), die vorab hätte eingeplant werden können. Verallgemeinert: Wenn ein Run den ERSTEN Endpoint eines Typs einführt (erster Single-Resource-Mutator; erste zweite Seite → Navigation; …), zieht das eine Querschnitts-Policy nach, die die feature-orientierte Clusterung nicht abbildet.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: OBS-S106-1

## OBS-S105-2 – C#-String-Ops triggern unter `TreatWarningsAsErrors` kulturbezogene Analyzer
- Quelle: Subagent + Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: C#-Code
- Beobachtung: Naive String-Operationen brechen unter `TreatWarningsAsErrors` den Build über kulturbezogene Analyzer – in S105 zweifach getroffen: (1) `.ToLower()` in einem EF-Core-LINQ-Prädikat → CA1304/CA1311/CA1862/MA0011 (Analyzer nehmen Laufzeit-`CurrentCulture` an, obwohl der Ausdruck zu SQL `LOWER()` übersetzt wird → braucht ein gezieltes `#pragma`); (2) `IndexOf(char)` / `==` / im `.env`-Parser → CA1307/MA0006 (hier ist der Nudge berechtigt → `Split`/`StringComparison.Ordinal`/`string.Equals`). Beide Male kostete es einen Trial-and-Error-Zyklus.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: LL-S105-1

## OBS-S103-2 – Stryker 100 % pinnt nicht die Reihenfolge von „erstes-von-N"-Prioritätslogik
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: QUALITÄT    Kontext: Mutation-Testing
- Beobachtung: Bei der Fokus-aufs-erste-Fehlerfeld-Logik (`nameError ? nameRef : unitError ? unitRef : undefined`) töteten die zwei Einzelfeld-Tests alle Stryker-Mutanten (100 %), aber der Mehrfeld-Fall (beide fehlerhaft → Priorität Name) war **nicht** gepinnt: ein menschlicher Prioritäts-Swap (Einheit vor Name) mutiert identisch und bliebe bei 100 % unentdeckt (im Review als FC-F1 gefunden, mit explizitem Mehrfeld-Assert geschlossen). Verallgemeinert: „erstes-von-N"-/Prioritäts-Auswahllogik braucht einen expliziten Mehrfach-Fall-Test; Stryker-100 % über Einzelfälle genügt nicht.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: –

## OBS-S101-1 – Flaky-Timeout einzelner Vitest-Tests unter Stryker-Systemlast
- Quelle: Subagent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Mutation-Testing
- Beobachtung: `US904_HappyPath_ReopenDialogAfterCancel_FieldsAreEmpty` lief während eines Stryker-Dry-Runs in einen 5000-ms-Timeout, isoliert (`vitest-run.py --filter`) sofort grün (~900 ms). Ursache vermutlich Systemlast durch viele parallele Checker-/Runner-Prozesse. Kein echter Regress, aber ein solcher Timeout kann einen Übergabe-`qa-check`-Hash fälschlich scheitern lassen (falscher Rot-Alarm).
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: –

## OBS-S101-3 – useResultMutation: 4er-Positions-Tupel → Objekt-Rückgabe
- Quelle: Subagent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: QUALITÄT    Kontext: TS-Code
- Beobachtung: `useResultMutation` gibt jetzt ein 4-Tupel `[mutate, error, isPending, reset]` zurück – zwei davon Funktionen. Positions-Tupel werden mit wachsender Länge fehleranfällig (Call-Sites müssen exakt in Reihenfolge destrukturieren, `error`/`isPending` leicht verwechselbar). Ein Objekt `{ save, error, isPending, reset }` wäre selbstdokumentierend und reihenfolgeunabhängig.
- Entscheidung/Maßnahme: aufgeschoben – bündeln mit dem nächsten großen Hook-Schritt (volle MutationState-Union, ADR-S083-2), damit die Call-Sites nicht zweimal angefasst werden. Re-Trigger: wenn die volle Union / `matchState` eingeführt wird.
- Bezug: ADR-S083-2

## OBS-S099-1 – Waisen-Infra-TD: Schuld ohne Lauf-Bezug bleibt uncaught
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Sonstiges
- Beobachtung: Die S099-Lösung für OBS-S090-5 (TD-Sichtung in `implementing-scenario` Schritt 0 P5 + TD-Abgleich Schritt 6.1) fängt TD nur, wenn ein Lauf die betroffenen Bereiche real berührt (area-basiert – systematisiert den opportunistischen Fang, wie TD-S083-5 in S098). Infra-/Waisen-TD in Bereichen, die **kein** Lauf je anfasst, bleibt weiter uncaught. Der periodische Voll-Sweep wurde bewusst aus der Kaizen-Retro verbannt (Retro = Prozess, nicht Technik) → ein anderer Träger für einen periodischen TD-Sweep ist offen.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: OBS-S090-5 (TD-Grooming, S099 umgesetzt); OBS-S087-1 (TD relevanz-filterbar)

## OBS-S099-2 – Test-Freigabe-Anker verlangt manuelle Zustandshaltung im Orchestrator
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: implementing-scenario / qa-check
- Beobachtung: Die S099-Lösung für OBS-S090-4 (Blob-Anker-Audit) verlangt vom Orchestrator mehrstufige manuelle Schritte: pro freigegebener Test-Datei `git hash-object -w`, die `pfad=sha`-Paare über den GREEN/REFACTOR-Zyklus hinweg im Kontext halten und in Schritt 4 an `qa-check --verify --approved-tests` durchreichen. Bewusster Trade-off (mechanischer Gate statt „dran denken"), aber die manuelle Zustandshaltung ist selbst vergessbar/fehleranfällig – nur der `--verify`-Abbruch bei geänderten Tests ohne `--approved-tests` fängt das Weglassen.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: OBS-S090-4 (S099 umgesetzt); CM-S070-1

---

## OBS-S085-3 – Agenten durchsuchen Tool-Outputs selbst statt unsere gezielten Scripte zu nutzen
- Quelle: User
- Status: IN BEOBACHTUNG bis S115 – S087: A (Wrapper-Audit, kein Change) + C (`--list`/SessionStart-Hinweis „ohne tail/grep") + D (`allowed-commands.log`) umgesetzt, B (tail-Deny) zurückgestellt; **S095 wiederaufgegriffen** nach D-Analyse; **S099 (Drain) erneut aufgeschoben bis S109**; **S109: gemessen + Wrapper-Ausgabe umgebaut, Wirkung offen** (s. Entscheidung).
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Mutation-Testing
- Beobachtung: Agenten greppen/`tail`-en Stryker-&-Co-Output, obwohl unsere Scripte gezielt nur das Relevante ausgeben sollen (Deny-Log S086: 81 head/tail-Zeilen).
- Entscheidung/Maßnahme: **A + C + D**; **B zurückgestellt** bis mehr Daten (mittlere Gefahr, könnte legitime Nutzung blocken). C über `--list` + SessionStart-Injection: knappe Script-Anwendungsfälle + Hinweis „normal **ohne** `tail`/Filter nutzen (Output ist optimal); wo nicht → als Beobachtung sammeln". D = erlaubte Befehle loggen.
- **Rezidiv (S090, Quelle: User):** Trotz Gegenmaßnahme C erneut aufgetreten — `grep` mehrfach auf qa-check-Output, `tail` auf playwright-test. Der Session-Hinweis (C) allein verhindert das Verhalten nicht zuverlässig.
- **D-Analyse durchgeführt + Neubewertung (S095):** `allowed-commands.log` ausgewertet (~15+ Filter-Instanzen S90–93). Befund: das Filtern ist **nicht** einheitlich Misuse, sondern zerfällt in drei Klassen — (1) **reines Kürzen** auf bereits kuratiertem Output (`vitest-run|tail`, `eslint-run|tail`) → Disziplin-Thema; (2) **gezieltes Feld-Extrahieren**, weil der Wrapper das Verdikt vergräbt (`qa-check --verify | grep | tail`, `stryker | grep Score/Survived`) → Wrapper sollte das Verdikt klar ausgeben; (3) **legitimer Workaround**, weil der Wrapper die relevante Info gar nicht liefert (`dotnet-test` bei RED ohne Assertion-Details → **OBS-S091-1**). Konsequenz (User-Entscheid): **kein pauschales Deny (B)** — es würde Klasse 2+3 bestrafen. Stattdessen **zuerst die Wrapper fixen** (Klasse 2+3, s. OBS-S091-1/-3), *dann* neu bewerten, ob für Restklasse 1 überhaupt noch eine Maßnahme nötig ist.
- **S099-Drain-Entscheid (erneut aufgeschoben bis S109):** Wrapper-Fixes OBS-S091-1/-3 in S096 erledigt (Blocker weg). User-Korrektur zur Restklasse 1: sie hat **konkreten Schaden** (höherer Token-/Zeitverbrauch, weil der Output anschließend von Hand ausgewertet wird, statt den Tool-Output zu nutzen bzw. eine **Verbesserung am Wrapper** vorzuschlagen) — nicht bloß Disziplin. Da seit S096 kaum Anwendungsgelegenheit bestand, erst ~10 Sessions Post-S096-Daten sammeln, dann Maßnahme neu bewerten (ggf. doch Deny B, ggf. Wrapper-Nachschärfung). Re-Trigger: mehrere Läufe mit realer Wrapper-Nutzung.
- **S109-Messung (`allowed-commands.log`, 17.06.–28.07., nur echte Wrapper-Ausführungen):** **430 von 517 Läufen (83 %) mit nachgelagertem Filter**, Tendenz steigend (Juni 79 % → Juli 85 %). Damit ist die bisherige Einordnung als „Restklasse 1, ~15 Einzelfälle" widerlegt: Filtern ist der Normalfall, nicht die Ausnahme, und die Wrapper-Fixes aus S096 haben daran nichts geändert. Verteilung: vitest-run 96, qa-check 92, dotnet-test 89, playwright-test 60, eslint-run 40, dotnet-stryker 27.
- **S109-Ursachentest (User-Vorschlag, entscheidend):** Die naheliegende Erklärung „der Wrapper-Output ist zu lang, also kürzen die Agenten zu Recht" wurde geprüft, indem in den Session-Transkripten die **Reihenfolge** der Wrapper-Aufrufe je Kontext ausgewertet wurde – filterte ein Kontext erst, *nachdem* er einmal die volle Länge gesehen hatte? Ergebnis: **in 13 von 19 Kontexten (68 %) war schon der allererste Wrapper-Aufruf gefiltert, in 11 davon durchgehend jeder.** Nur 4 Kontexte zeigen das Reaktionsmuster. Der Output kann also nicht der Auslöser sein – er war in diesen Kontexten nie sichtbar. Deutlichster Einzelbeleg: `dotnet-test` gibt im Erfolgsfall **drei Zeilen** aus und wurde trotzdem 89× gefiltert. Das Verhalten ist antrainiert, nicht situativ. *(Limitation: die Transkripte enthalten nur Orchestrator-Kontexte – 211 der 517 Läufe; für die ~306 Subagent-Läufe gilt das Argument aber verschärft, da Subagenten immer frisch starten.)*
- **S109-Maßnahme (unabhängig von der Ursache, User-Vorgabe):** Wrapper-Ausgabe-Politik vereinheitlicht in `_wrapper_output.py`: **im Erfolgsfall nur noch das Verdikt** (ein bis zwei Zeilen), **im Fehlerfall nur das analyse-Relevante**, alles Weitere hinter `--verbose`. Umgesetzt für vitest-run (12 → 2 Zeilen), playwright-test (→ 2), jscpd-run (25 → 6), eslint-run (→ 1 bei sauberem Lauf) und beide Stryker-Wrapper (30 Zeilen Rohoutput im Erfolgsfall entfallen, ~35 → 8). `dotnet-test` blieb unverändert – mit 3 Zeilen bereits optimal. Fail-open-Prinzip: erkennt ein Wrapper sein Muster nicht, gibt er weiter die längere Fassung aus; ein Parser-Fehlgriff darf nie Information verschlucken. Der SessionStart-Hinweis nennt jetzt konkret, dass `tail` das Verdikt **abschneiden** kann, statt nur zu behaupten, der Output sei kuratiert. **Deny (B) weiterhin nicht gebaut** – bei 83 % Quote träfe es zu breit, und die Ursache ist erklärtermaßen nicht Bedarf, sondern Gewohnheit. **Re-Trigger/Bewertung bis S115:** dieselbe Messung wiederholen. Sinkt die Quote trotz Ein-Zeilen-Verdikt nicht, ist die Gewohnheits-These endgültig bestätigt und nur noch ein mechanischer Guard (B) wirksam.

## OBS-S085-4 – Kein Language-Server für die Agenten-Programmierung im Einsatz
- Quelle: User
- Status: IN BEOBACHTUNG bis S115 – **S109 (Drain): gemessen, Nutzung nahe null → Empfehlung geschärft statt Pilot beendet** (s. unten). **S099 (Drain) erneut aufgeschoben:** seit Aktivierung (2026-06-20) kaum echte TS-Arbeit, Evidenz-Schwelle (≥ ~3 TS-Sessions) nicht erreicht; Bewertung bleibt an die nächste Kaizen-Retro gebunden (Backstop S105). **Pilot durchgeführt & technisch validiert (2026-06-20):** `typescript-lsp`@claude-plugins-official läuft auf **nativem** Claude-Install 2.1.183 (anthropics/claude-code #20050 hier **nicht** relevant – galt für ältere Versionen); `ENABLE_LSP_TOOL` nicht nötig; `/reload-plugins` statt Neustart genügt. Alle Ops ok (hover, documentSymbol, goToDefinition cross-file, workspaceSymbol, findReferences); **semantisch präziser als grep** (Kommentar-/String-Treffer korrekt ausgeschlossen). **CAVEAT:** erster `findReferences` direkt nach Plugin-Load = kalter/unvollständiger Index → erst nach Warmlauf vollständig (bei verdächtig wenigen Treffern wiederholen). Offene Bewertung: realer Nutzen über laufende Arbeit. C# weiter zurückgestellt (#1359). **S101 – Werkzeug-Zugang korrigiert (kritisch für diese Bewertung):** LSP war nur dem Orchestrator zugeteilt, NICHT den Layer-Implementern (die den Code schreiben) noch den Auditoren – die „≥3 Sessions mit LSP verfügbar"-Evidenz wäre gegen Agenten ohne LSP gesammelt worden (Pilot faktisch nur beim Orchestrator, der kaum Layer-Code schreibt). Fix S101: `LSP` in die `tools` von frontend-/backend-layer-implementer + code-quality-/functional-correctness-/test-quality-/ux-ui-/security-auditor aufgenommen (workflow-auditor bewusst NICHT – auditiert Prozess, nicht Code). Konsequenz: Evidenzfenster für Implementer/Auditor-Nutzung startet effektiv ab S101; Backstop-Bewertung entsprechend nicht auf Vor-S101-Sessions stützen.
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
- **S109-Messung (Frequenz, wie oben unter „Messung (a)" vorgesehen):** 41 Transkripte durchsucht (40 davon mit Subagent-Aktivität). **LSP-Nutzung in 2 Sessions, 8 Calls gesamt – davon 7 im Aktivierungstest am 2026-06-20 und genau 1 danach (2026-07-10).** Seit S101, seit dem Implementer und Auditoren das Tool überhaupt haben, also praktisch keine Nutzung. Operationen: findReferences 3, hover 2, documentSymbol/goToDefinition/workspaceSymbol je 1.
- **S109-Entscheid (User): Empfehlung schärfen, eine Runde verlängern – bis S115.** Das vorab definierte Fehlschlag-Kriterium („kaum genutzt") wäre erfüllt, aber die Nullnutzung ist mehrdeutig: Der Hinweis stand bisher nur in `coding-guideline-typescript.md`, also in einem Dokument, das ein Agent liest *bevor* er arbeitet – nicht dort, wo die Entscheidung „grep oder LSP?" tatsächlich fällt. Zusätzlich ist LSP ein deferred Tool (erst via `ToolSearch select:LSP` ladbar), was eine echte Schwelle darstellt. Beides zusammen macht plausibel, dass „nicht angeboten" statt „nicht nützlich" gemessen wurde. **Maßnahme:** kurzer, konkreter LSP-Block direkt in die Prompts von `frontend-layer-implementer` (schreibt den TS-Code) und `code-quality-auditor` (stellt die „wo wird das noch verwendet?"-Fragen) – inklusive Ladehinweis und Kalt-Index-Caveat. Guideline-Notiz bleibt. **Bewertung S115 mit unveränderten Kriterien; dritte Nullrunde = verwerfen** (dann ist belegt, dass es nicht an der Sichtbarkeit lag). *Randnotiz:* `backend-layer-implementer` führt `LSP` in seinen `tools`, obwohl für C# kein Server läuft (Blocker #1359) – bewusst nicht angefasst, um das Messsetup nicht mitten in der Bewertung zu ändern.

## OBS-S088-1 – Hook-Registrierung: ein Dispatcher je Matcher/Event statt Einzeleinträge
- Quelle: User
- Status: IN BEOBACHTUNG bis S110
- Impact: GERING–MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Pro Tool-Matcher stehen mehrere Hook-Scripts einzeln in `settings.json` (PreToolUse `Edit|Write`: dependency-allowlist, code-quality-blocking, index-length, e2e-scenario-ref). Ein neuer/entfernter Check erfordert eine `settings.json`-Änderung → **Claude-Code-Reload** nötig, bevor er greift. `check-code-quality-blocking.py` ist bereits ein In-Process-Dispatcher (`CHECKS`-Liste + `checks/`-Package) – Checks dort sind reload-frei. Verallgemeinert man das (ein Dispatcher je Matcher *und* Event, der die Einzel-Checks aufruft), würde künftiges Hinzufügen/Entfernen eines Checks nur den Dispatcher-Inhalt ändern → sofort live, ohne Reload. Designpunkte: Pre (blocking, exit 2) vs. Post (non-blocking) getrennt; uneinheitlicher Input-Vertrag (Fragment-`HookInput` vs. voller Post-Edit-Inhalt + Datei-Reads bei e2e-scenario-ref → Dispatcher gibt rohes JSON, Checks adaptieren); Output-Stil je Dispatcher einheitlich (Bash nutzt JSON-`permissionDecision`); fail-open je Check.
- Entscheidung/Maßnahme: aufgeschoben (S102-Drain) bis S110 – **der Enabler-Zug ist entfallen:** OBS-S095-3 wurde als eigenständiges PreToolUse-Script gebaut (nicht in den Dispatcher gehängt), also braucht der Referenz-Hook den Dispatcher-Refactor nicht mehr. Eigenwert laut Fable-Audit (S099) gering (kein Poka-Yoke), und die Reload-Friktion bei Hook-Wartung ist selten (mehrere Sessions). Re-Trigger: nächster realer Bedarf an reload-freiem Check-Management (z.B. mehrere neue Checks gleichzeitig in Sicht); Backstop bis S110.
- Bezug: OBS-S085-16 (Reload-Friktion-Familie)

## OBS-S091-2 – Wrapper-Aufrufpfad cwd-relativ, kollidiert mit Projekt-Tooling-cwd
- Quelle: Agent
- Status: IN BEOBACHTUNG bis S115
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Die Wrapper liegen im Repo-Root (`.claude/scripts/`) und lösen ihren Root intern via `_util.REPO_ROOT` auf — aber der **Aufrufpfad** `python3 .claude/scripts/foo.py` ist cwd-relativ. Projekt-Tooling (`npm`/`dotnet`/`vite`) zieht die Shell in `Client/`/`Server/`-Subdirs; der nächste Wrapper-Aufruf scheitert dann mit „No such file" (S091: beide Subagenten + Orchestrator betroffen).
- Entscheidung/Maßnahme: **Aufgeschoben (S109-Drain) bis S115 – die Ursache wurde stattdessen entfernt.** Der mit Abstand häufigste Grund, den Repo-Root zu verlassen, war ein blockiertes `npm --prefix Client run …`, das ein `cd Client` erzwang; `--prefix` ist jetzt erlaubt (s. OBS-S108-4 b), womit der Auslöser wegfällt. Der direkte Fix – der Bash-Hook präfixt Wrapper-Aufrufe via `updatedInput` mit `cd <repo-root> &&` – wurde bewusst **nicht** gebaut: er wäre die Umkehrung der im selben Hook bestehenden Normalisierungsregel (absolute Repo-Pfade → relativ), also zwei gegenläufige Rewrite-Regeln nebeneinander, für ein seit 18 Sessions nie eskaliertes GERING-Problem. Geprüft und verworfen wurde auch der Weg über `$CLAUDE_PROJECT_DIR`: die Variable ist im Bash-Tool leer (nur in Hooks gesetzt), ein Rewrite müsste den Repo-Root literal einsetzen. **Re-Trigger:** ein Wrapper-Aufruf scheitert erneut an falschem cwd, obwohl `--prefix` verfügbar ist – dann ist belegt, dass es noch andere cd-Gründe gibt, und der Hook-Rewrite ist gerechtfertigt.
- Bezug: —

## OBS-S093-1 – SonarAnalyzer S125 feuert auf deutsche Kommentare mit Satz-Ende „;"
- Quelle: Agent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Build/Analyzer
- Beobachtung: SonarAnalyzer S125 („Sections of code should not be commented out") interpretiert deutschsprachige Kommentare, die mit „…;" enden, als auskommentierten Code und bricht den Build. In dieser Session musste ein korrekter Erklär-Kommentar nur umformuliert werden, um S125 zu beruhigen – inhaltlich unnötiger Eingriff.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

---

## OBS-S096-3 – Scripted-Access-Layer für TD/OBS/LL/Doc (Lesen/Schreiben, Metadaten listen/filtern/move)
- Quelle: User
- Status: NEU – **S109 reaktiviert: Re-Trigger (2) eingetreten** (`observations.md` 264 Zeilen > 250; `adr.md` 1.263 Zeilen), zusätzlich Messdaten vorhanden
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Doku/Script
- Beobachtung: Möglichst viel über Script(e) zugänglich machen: Lesen + Schreiben von TD/OBS/LL etc., idealerweise auch Lesen von Doc-Teilen; ein Auflisten aller Inhalts-Header/Metadaten (schneller Überblick + Suche), Filtern nach Metadaten (wie ADRs via `decisions.py`), ggf. Status-Update/Move wo passend. Vorher bewerten, wo es sich (besonders) lohnt. (`obs-drain.py`/`obs-archive.py` sind ein erster Schritt für OBS.) **Facette (aus OBS-S087-1 konsolidiert, S104):** technische Schuld durchsuchbar/relevanz-gefiltert machen – der Architektur-Check in `implementing-scenario` (oder ein Script) listet die zum bearbeiteten Code-Bereich potentiell relevante TD automatisch auf (kuratierte Bereichs-Keywords pro Eintrag).
- Entscheidung/Maßnahme: **Aufgeschoben (S104-Drain) bis S112.** YAGNI: Access-Layer/Tag-Vokabular ohne konkreten Abnehmer driftet – der **Abnehmer definiert das Schema** (deshalb nicht spekulativ vorbauen; OBS gibt es schon Scripts, TD/LL nicht, TD heute 15 Einträge/123 Zeilen → grep noch tragbar). **Re-Trigger (event-basiert, Backstop S112):** (1) `implementing-scenario` Schritt 0 (TD-Sichtung, area-basiert) reibt real – grep verfehlt Bereichs-Treffer oder ertrinkt in Fehltreffern → konkreter Abnehmer für Bereichs-Keywords, Script+Schema gemeinsam mit *diesem* Schritt entwerfen; (2) eine Tracker-Datei wächst über Schwelle (TD > ~30 Einträge ODER Datei > ~250 Zeilen); (3) ein manueller Schreib-Mehrschritt für TD/LL reibt (Status/Archiv-Workflow, analog `obs-archive.py` für OBS).
- **S109-Reaktivierung (User):** Der beim S104-Aufschub fehlende **konkrete Abnehmer ist jetzt da** – und zwar gemessen statt vermutet. Die Phase-1-Messung (s. OBS-S109-1) zeigt: `docs/kaizen/observations.md` wurde über 23 Sessions mit **759k Zeichen** vollständig gelesen, `docs/history/adr.md` mit 303k, und die `adr.md`-Voll-Reads **steigen** trotz `decisions.py` (1,5k → 12,3k je Session), weil das Script zwar das Suchen abdeckt, nicht aber das Schreiben: Wer eine ADR ergänzt, muss die 1.263-Zeilen-Datei vorher lesen. Damit ist die Schreib-Seite des Access-Layers – beim S104-Aufschub noch als spekulativ eingestuft – als eigener Kostenpunkt belegt. Beide Backstop-Schwellen sind ebenfalls überschritten (`observations.md` 264 Zeilen > ~250). Der Bewertungsauftrag bleibt: **wo lohnt es sich besonders** – die Messung legt Schreib-/Ergänzungs-Operationen auf den großen Tracker-Dateien nahe, weil dort der erzwungene Vor-Edit-Read den eigentlichen Preis ausmacht.
- Bezug: OBS-S092-2 (Doku-Header lesen, geparkt); OBS-S096-2 (Skill-Mechanisierung, umgesetzt S104); OBS-S109-1 (Messung)

---

## OBS-S108-1 – Check 6 (`decisions.py`/`qa-check`) erkennt ADR-Referenzen nur mit `//` unmittelbar davor
- Quelle: Subagent (backend-layer-implementer, run-7)
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Check 6 (`decisions.py check` / `qa-check.py`) erkennt eine `ADR-SXXX-N`-Referenz nur, wenn ein `//` unmittelbar davorsteht (Kommentar am Zeilenanfang) – nicht, wenn zwei ADRs mid-line in einem Fließtext-/Prosa-Kommentar kombiniert werden. In run-7 blieben dadurch zwei in einem Kommentar kombinierte ADR-Referenzen zunächst unerfasst; sichtbar wurde es erst durch den qa-check-Rerun (ein zusätzlicher Lauf, kein Blocker). Risiko: eine real vorhandene ADR-Referenz bleibt unverlinkt/ungeprüft, wenn sie stilistisch in Prosa eingebettet statt als eigene `//`-Zeile geschrieben wird.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: –

---

## OBS-S108-5 – Restore-Endpoint ist als CORS-„Simple Request" ohne Preflight erreichbar
- Quelle: Subagent (security-auditor, Review run-8)
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: QUALITÄT    Kontext: Security
- Beobachtung: `POST /api/ingredients/{id}/restore` verlangt weder Custom-Header noch Request-Body und ist damit ein CORS-„Simple Request": Ein Browser sendet ihn cross-origin **ohne** Preflight, CORS verhindert nur das Auslesen der Antwort, nicht die serverseitige Ausführung. Alle übrigen mutierenden Endpoints sind hier zufällig geschützt – `DELETE` durch den verpflichtenden `If-Match`-Header, `POST /api/ingredients` durch `Content-Type: application/json`; beide erzwingen dadurch eine Preflight, die mangels CORS-Policy scheitert. Der Verzicht auf If-Match beim Restore ist in ADR-S108-2 bewusst und mit Concurrency-Argumenten begründet – dass If-Match nebenbei auch die Preflight erzwungen hätte, ist ein Nebeneffekt, den die ADR nicht betrachtet. Praktische Tragweite im aktuellen Stand begrenzt: Der Angreifer braucht die Ziel-UUIDv7 (~74 nicht erratbare Zufallsbits), wer sie kennt hat über das ungeschützte GET ohnehin direkten API-Zugriff, und der Schaden beschränkt sich auf das Rückgängigmachen eines Soft-Deletes. Relevant wird es, sobald Auth existiert – dann ist es die einzige Stelle, an der ein fremder Browser eine Zustandsänderung auslösen kann. Kein User-Entscheid nötig (kein Business-Impact, technische Härtungsfrage im Sinne der `CLAUDE.md`-Faustregel) – die Abwägung „Preflight erzwingen vs. bewusst tragen" gehört in den Drain, das Ergebnis in eine ADR.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: –

---

## OBS-S108-6 – `open-questions.md` hat keinen Lese-Trigger: Fragen werden abgelegt, nie vorgelegt
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Alle Verweise auf `docs/open-questions.md` in Skills, Hooks und Prozessdocs sind **Schreib**-Verweise („dort eintragen"): `gherkin-workshop` legt nicht lösbare Fragen ab (Schritt ~292), `kaizen` und `closing-session` verweisen aufs Eintragen, `implementing-scenario` ebenso. Kein Prozessschritt liest die Datei, legt Einträge zur Klärung vor oder erzwingt eine Wiedervorlage. Alle anderen Tracker haben einen solchen Trigger: `tech-debt.md` wird in `implementing-scenario` Schritt 0.5 gesichtet und in 6.1 abgeglichen, `observations.md` treibt der Drain-Vorschlag am Session-Start, `lessons_learned.md` die Retro über den Jenga-Score. Folge im Bestand: OQ-S083-1/-2 liegen seit 25 Sessions offen, OQ-S094-1/-2 seit 14. Konkret in dieser Session: OQ-S083-1 fragt „ADR vs. technische Schuld: Taxonomie klären" – genau diese Abgrenzung wurde hier dreimal ad hoc neu verhandelt (ADR-S000-3 löschen statt Superseded; Undo-Toast-Touch-Punkt als TD statt OBS; CORS-Punkt als OBS statt OQ), ohne dass die offene Frage konsultiert wurde. Sichtbar wurde sie nur, weil der User sie beiläufig erwähnte. Anders als bei OBS-Einträgen (Feld `Status: IN BEOBACHTUNG bis S<NNN>`) gibt es im OQ-Format zudem kein Feld für einen Wiedervorlage-Termin.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: –

---

## OBS-S108-2 – gherkin-workshop-Checkliste deckt transiente Feedback-Elemente (Toast/Snackbar) nicht ab
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Gherkin
- Beobachtung: Die Vollständigkeits-Checkliste in `.claude/skills/gherkin-workshop/SKILL.md` (Zeilen ~155-157) fragt „Nach erfolgreicher Aktion", „Abbrechen" und „Feld-Initialisierung" ab – durchgehend dialog- und formularzentriert. Für transiente Feedback-Elemente (Toast/Snackbar) fragt sie nichts: weder Lebensdauer, noch wodurch sie verschwinden, noch was bei mehrfacher Auslösung kurz hintereinander passiert. „Klick außerhalb" kommt vor, aber nur als Abbrechen-Pfad eines Dialogs. In run-8 führte das dazu, dass der Undo-Toast als einzige Wiederherstellungsmöglichkeit im UI (UX-Guideline Prinzip 5) ohne jedes Szenario zu seinem Verhalten implementiert wurde. Erst der Review deckte drei beobachtbare Verhaltensaspekte auf, für die Szenarien fehlten (Klick daneben schließt den Toast; zweiter Toast erbt die Restlaufzeit des ersten und verkürzt das Undo-Fenster; nur der letzte Löschvorgang ist rückgängig). Zwei davon waren bereits implementiertes Verhalten ohne Spec, einer ein realer, im Browser reproduzierter Bug. Die Szenarien wurden nachträglich ergänzt – also in umgekehrter Reihenfolge zum Outside-In-Prinzip (ADR-S041-5). Aufgefallen ist die Lücke dem User, nicht dem Workshop und nicht den Review-Agenten.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: –

---

## OBS-S109-1 – Datei-Lesen ist der mit Abstand größte Token-Posten und wächst mit der Codebasis
- Quelle: User + Orchestrator
- Status: NEU
- Impact: HOCH    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Aus der Phase-1-Messung zu OBS-S085-2 (23 Sessions mit Subagent-Einsatz inkl. 112 Subagent-Logs, ~23,5M Zeichen ≈ 5,9M Token-Proxy): **`Read` allein macht 49,5 % des gesamten Volumens aus** – mehr als alles andere zusammen. Bei Subagenten sind es 71,4 % ihres Tool-I/O. 1590 Aufrufe, Ø 7.317 Zeichen (Subagenten Ø 8.373). Zum Vergleich: alle Projekt-Wrapper-Scripts zusammen 8 % des Tool-I/O, Orchestrator↔Subagent-Kommunikation 8,6 % des Gesamtvolumens, Edit 7,9 % des Tool-I/O. Drei Detailbefunde: (1) **Nicht die Anzahl treibt das Volumen, sondern die Größe** – Re-Reads derselben Datei im selben Kontext sind nur 10,1 %; die Top-Dateien sind `Client/e2e/ingredients.spec.ts` (816k gelesen), `docs/kaizen/observations.md` (759k), `Client/src/pages/IngredientsPage.test.tsx` (754k), `docs/guidelines/coding-guideline-csharp.md` (694k), `Server.Tests/IngredientsEndpointsTests.cs` (682k). (2) **86,7 % aller Reads sind vollständig, nur 13,3 % gezielt** (`offset`/`limit`) – und im Fall „Datei wird anschließend editiert" ist der gezielte Read im Schnitt 4,6× kleiner (1.943 vs. 8.971 Zeichen) bei identischem Zweck; der Harness verlangt vor einem Edit einen Read, aber keinen vollständigen (in S109 mehrfach praktisch bestätigt). 17 % des Read-Volumens sind solche vollständigen Vor-Edit-Reads. (3) **Der Posten ist nicht stabil, er wächst mit der Codebasis**: pro Session von Juni auf Juli stieg `Client/`-Lesen von 20k auf 79k Zeichen, `Server/` von 22k auf 48k, während die Pflichtlektüre (`docs/guidelines`) mit 40k→48k nahezu flach blieb. Ergänzend: gezielte Extraktions-Scripte ersetzen die Voll-Reads bisher nicht, sondern kommen hinzu – `decisions.py`-Aufrufe stiegen von 34 auf 87 pro Monat, gleichzeitig stiegen die `adr.md`-Voll-Reads von 1,5k auf 12,3k je Session (die Datei hat 1.263 Zeilen, und wer eine ADR ergänzt, muss sie vorher lesen). Risiko: Der Effekt verschärft sich mit jedem Lauf, weil Test- und Codedateien monoton wachsen und jeder frisch startende Subagent sie vollständig liest.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: OBS-S085-2 (Messung stammt aus dessen Phase 1); OBS-S096-3 (Scripted-Access-Layer, Re-Trigger jetzt erfüllt)

---

## OBS-S110-1 – „Done"-Erkennung eines Laufs hängt am Test-Kommentar, nicht am grünen Test
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Testing
- Beobachtung: `next_run.py` wertet einen Lauf als erledigt, sobald der `// Szenario: <Titel>`-Kommentar in einer E2E-Spec vorkommt (DONE-Erkennung nach ADR-S041-7 Addendum S088); daraus speist sich auch die Auflösung von `{{NEXT_RUN}}` in `AGENT_MEMORY.md`. Der Kommentar entsteht aber bereits im äußeren Loop von `implementing-scenario`, wenn der E2E-Test absichtlich noch rot ist und kein Produktionscode existiert. In S110 real beobachtet: Nach einem WSL-Absturz mitten in run-9 zeigte `AGENT_MEMORY.md` beim Neustart als nächsten Lauf bereits run-11 an, obwohl von run-9 nur ein roter Test existierte – der tatsächlich laufende Lauf war aus dem Zustandssignal verschwunden. Risiko: Ein Agent, der nach einer Unterbrechung neu startet und dem Zustandsdokument folgt, überspringt einen angefangenen Lauf oder hält ihn für fertig; der Fortschritt wird systematisch überschätzt, weil das Signal an einem Artefakt hängt, das am Anfang statt am Ende des Laufs entsteht.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

---

## OBS-S110-2 – `implementing-scenario` Schritt 4 hat keinen Weg, wenn der Schicht-Subagent nicht zurückkehrt
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Schritt 4 („Mechanische Verifikation") ist vollständig darauf aufgebaut, dass der Schicht-Subagent in seinem Return einen frischen `=== VERIFIKATIONS-HASH ===`-Block liefert, den der Orchestrator per `qa-check.py --verify` prüft. Der Skill beschreibt keinen Fall, in dem dieser Return ausbleibt, weil der Subagent-Prozess endet, bevor er antworten konnte. In S110 eingetreten: ein WSL-Absturz beendete Orchestrator und Subagent gleichzeitig; nach dem Neustart lagen fertiger Produktionscode und ein durchgeführter Refactor im Working Tree, aber kein Hash und keine Aussage darüber, welche Schritte noch offen waren. Der Zustand ließ sich nur rekonstruieren, weil der Test-Freigabe-Anker als git-Blob außerhalb des Agentenkontexts persistiert war und der Refactor-Diff sich nachträglich dagegen auditieren ließ. Risiko: Ohne beschriebenen Weg improvisiert jeder Orchestrator anders – im schlechteren Fall wird der Subagenten-Stand ungeprüft übernommen oder der ganze Lauf verworfen und neu begonnen.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

