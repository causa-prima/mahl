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
  - Beobachtung: <was ist nicht ideal / was fiel auf – Ist-Zustand und Schaden, ohne Ursache/Lösung>
  - Vorprägung: (optional) <was die Bewertung prägen würde: genannte Lösungen, vermutete Ursachen, Analogieschlüsse>
  - Entscheidung/Maßnahme: <bei Erfassung offen; beim Drain: gewählte Lösung + warum statt Alternativen / Verwerf-Grund / Aufschub-Grund + Re-Trigger>; → CM-… falls stehende Leitplanke
            (bei Erfassung mechanisch erzwungen: `.claude/hooks/check-obs-capture.py` lässt bei einem NEUEN Eintrag nur
             genau zwei Werte durch – `offen` oder `offen - beim Drain Kandidaten erstellen und bewerten`, nichts davor
             und nichts dahinter. Weder Kandidat noch offene Frage: beides ankert den bewusst frischen Drain-Agenten.
             Bestands-Einträge sind frei änderbar – der Drain schreibt hier seine Entscheidung hin.)

  Derselbe Hook hält bei NEUEN Einträgen zwei weitere Ausweichwege zu: die Feldliste oben ist abschließend
  (ein erfundenes `- Lösungsidee:`/`- Kandidaten:`-Feld blockt; optional sind nur `- Vorprägung:` und `- Bezug:`),
  und explizite Lösungs-Ansagen im Eintrags-Text (`Lösungsvorschlag:`, `Idee:`, `Kandidat:`, `Abhilfe:`, `Fix:` …)
  blocken ebenfalls. Ein **Risiko** zu beschreiben („X könnte passieren") ist ausdrücklich erlaubt – gemeint ist nur
  die vorweggenommene Abhilfe. Kandidaten entstehen beim Drain, nicht bei der Erfassung.

  **Wohin mit schon genannten Lösungen?** In `- Vorprägung:` (nicht tilgen, nicht in die Beobachtung mischen).
  Trennlinie: Die Beobachtung beschreibt **Ist-Zustand und Schaden** („was passiert ist, wie oft, was es kostet"),
  die Vorprägung alles, was in Richtung **Ursache, Bewertung oder Lösung** zeigt („woran es liegt", „was man tun
  sollte"). Das Feld wird erfasst, aber beim normalen `obs.py get` **nicht mitgelesen** – nur ein Hinweis erscheint,
  Abruf per `--vorprägung`. Grund: Eine Verifikationspflicht *nach* dem Lesen käme zu spät; wer den Volltext gesehen
  hat, ist geprägt. Deshalb gilt im Drain: **erst eigene Kandidaten bilden und vorlegen, dann abrufen.** Der
  Drain-Satz markiert betroffene Einträge mit `+Vorprägung`, damit das Feld nicht in Vergessenheit gerät.
  Der `obs-ok`-Marker bleibt für **echte Einzelfälle** außerhalb dieses Musters (z.B. ein umnummerierter
  Bestands-Eintrag); für genanntes Lösungswissen ist er nicht mehr der Weg – dafür gibt es das Feld.
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
- Entscheidung/Maßnahme: aufgeschoben – bündeln mit dem nächsten großen Hook-Schritt (volle MutationState-Union, TD-S101-1), damit die Call-Sites nicht zweimal angefasst werden. Re-Trigger: wenn die volle Union / `matchState` eingeführt wird.
- Bezug: TD-S101-1

## OBS-S085-3 – Agenten durchsuchen Tool-Outputs selbst statt unsere gezielten Scripte zu nutzen
- Quelle: User
- Status: IN BEOBACHTUNG bis S126 – **S115: Filter-Rewrite gebaut (mechanischer Guard), Wirkung offen; Re-Trigger an Wrapper-Läufe statt an eine Session-Nummer gebunden** (s. Entscheidung). S087: A (Wrapper-Audit, kein Change) + C (`--list`/SessionStart-Hinweis „ohne tail/grep") + D (`allowed-commands.log`) umgesetzt, B (Deny) zurückgestellt; **S095 wiederaufgegriffen** nach D-Analyse; **S099 (Drain) erneut aufgeschoben bis S109**; **S109: gemessen + Wrapper-Ausgabe umgebaut, Wirkung offen**.
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Mutation-Testing
- Beobachtung: Agenten greppen/`tail`-en Stryker-&-Co-Output, obwohl unsere Scripte gezielt nur das Relevante ausgeben sollen (Deny-Log S086: 81 head/tail-Zeilen).
- Entscheidung/Maßnahme: **A + C + D**; **B zurückgestellt** bis mehr Daten (mittlere Gefahr, könnte legitime Nutzung blocken). C über `--list` + SessionStart-Injection: knappe Script-Anwendungsfälle + Hinweis „normal **ohne** Filter nutzen (Output ist optimal); wo nicht → als Beobachtung sammeln". D = erlaubte Befehle loggen. — **S115: mechanischer Guard gebaut, als Rewrite statt als Deny.** Erstmals **gemessen statt gerechnet**: `tool-usage.py` um `--since` erweitert (der Zeitstempel stand längst im Log, die Auswertung gruppierte ihn nur auf den Monat und warf den Tag weg – ein Stichtag mitten im Monat war deshalb nicht schneidbar). Ab dem Umbau-Commit (29.07. 00:49) **110 Läufe, 105 gefiltert = 95 %** gegen die Basislinie 83 %. Damit ist das vorab definierte Kriterium erfüllt: drei Soft-Maßnahmen (Hinweis S087, Rezidiv S090, Output-Umbau S109) haben nichts bewegt, das Verhalten ist antrainiert. **Gewählt: Rewrite, nicht Deny** (User-Entscheid) – `strip_wrapper_filter()` entfernt nachgelagerte Filter-Pipes hinter einem Wrapper-Aufruf via `updatedInput`, mit sichtbarem Hinweis auf `--verbose`. Begründung gegen das Deny: Subagenten starten immer frisch und können über Sessions nicht umlernen – ein Deny kostet sie jede Session erneut eine verlorene Runde (105 im Messfenster), der Rewrite keine. Zwei Abgrenzungen tragen die Korrektheit: ein Filter **vor** dem Wrapper filtert dessen Ausgabe nicht und bleibt unberührt, und zwischen Wrapper und erstem Filter bleibt alles erhalten (Argumente, `2>&1`). Analyse-Scripte sind ausgenommen – ihre lange Ausgabe ist zum Zerschneiden gedacht (dieselbe Grenze wie `tool-usage.py` WRAPPERS). **Deny (B) bleibt die Eskalationsstufe** (User-Vorgabe: „ggf. später zum Deny wechseln"). **Re-Trigger: ≥ 100 Wrapper-Läufe nach dem Rewrite-Stichtag 2026-08-08**, dann `python3 .claude/scripts/tool-usage.py --filter --since 2026-08-08`. Bewusst an Läufe statt an eine Session-Nummer gebunden: Zwischen dem 30.07. und heute fielen in drei Sessions nur **6** Läufe an (Drain-/tech-debt-Sessions führen kaum Wrapper aus) – ein Kalendertermin würde erneut auf Null-Daten urteilen, derselbe Fehler wie im LSP-Pilot. Backstop-Termin S126. **Sinkt die Quote dann nicht deutlich, ist der Rewrite widerlegt und das Deny fällig.**
- **Rezidiv (S090, Quelle: User):** Trotz Gegenmaßnahme C erneut aufgetreten — `grep` mehrfach auf qa-check-Output, `tail` auf playwright-test. Der Session-Hinweis (C) allein verhindert das Verhalten nicht zuverlässig.
- **D-Analyse durchgeführt + Neubewertung (S095):** `allowed-commands.log` ausgewertet (~15+ Filter-Instanzen S90–93). Befund: das Filtern ist **nicht** einheitlich Misuse, sondern zerfällt in drei Klassen — (1) **reines Kürzen** auf bereits kuratiertem Output (`vitest-run|tail`, `eslint-run|tail`) → Disziplin-Thema; (2) **gezieltes Feld-Extrahieren**, weil der Wrapper das Verdikt vergräbt (`qa-check --verify | grep | tail`, `stryker | grep Score/Survived`) → Wrapper sollte das Verdikt klar ausgeben; (3) **legitimer Workaround**, weil der Wrapper die relevante Info gar nicht liefert (`dotnet-test` bei RED ohne Assertion-Details → **OBS-S091-1**). Konsequenz (User-Entscheid): **kein pauschales Deny (B)** — es würde Klasse 2+3 bestrafen. Stattdessen **zuerst die Wrapper fixen** (Klasse 2+3, s. OBS-S091-1/-3), *dann* neu bewerten, ob für Restklasse 1 überhaupt noch eine Maßnahme nötig ist.
- **S099-Drain-Entscheid (erneut aufgeschoben bis S109):** Wrapper-Fixes OBS-S091-1/-3 in S096 erledigt (Blocker weg). User-Korrektur zur Restklasse 1: sie hat **konkreten Schaden** (höherer Token-/Zeitverbrauch, weil der Output anschließend von Hand ausgewertet wird, statt den Tool-Output zu nutzen bzw. eine **Verbesserung am Wrapper** vorzuschlagen) — nicht bloß Disziplin. Da seit S096 kaum Anwendungsgelegenheit bestand, erst ~10 Sessions Post-S096-Daten sammeln, dann Maßnahme neu bewerten (ggf. doch Deny B, ggf. Wrapper-Nachschärfung). Re-Trigger: mehrere Läufe mit realer Wrapper-Nutzung.
- **S109-Messung (`allowed-commands.log`, 17.06.–28.07., nur echte Wrapper-Ausführungen):** **430 von 517 Läufen (83 %) mit nachgelagertem Filter**, Tendenz steigend (Juni 79 % → Juli 85 %). Damit ist die bisherige Einordnung als „Restklasse 1, ~15 Einzelfälle" widerlegt: Filtern ist der Normalfall, nicht die Ausnahme, und die Wrapper-Fixes aus S096 haben daran nichts geändert. Verteilung: vitest-run 96, qa-check 92, dotnet-test 89, playwright-test 60, eslint-run 40, dotnet-stryker 27.
- **S109-Ursachentest (User-Vorschlag, entscheidend):** Die naheliegende Erklärung „der Wrapper-Output ist zu lang, also kürzen die Agenten zu Recht" wurde geprüft, indem in den Session-Transkripten die **Reihenfolge** der Wrapper-Aufrufe je Kontext ausgewertet wurde – filterte ein Kontext erst, *nachdem* er einmal die volle Länge gesehen hatte? Ergebnis: **in 13 von 19 Kontexten (68 %) war schon der allererste Wrapper-Aufruf gefiltert, in 11 davon durchgehend jeder.** Nur 4 Kontexte zeigen das Reaktionsmuster. Der Output kann also nicht der Auslöser sein – er war in diesen Kontexten nie sichtbar. Deutlichster Einzelbeleg: `dotnet-test` gibt im Erfolgsfall **drei Zeilen** aus und wurde trotzdem 89× gefiltert. Das Verhalten ist antrainiert, nicht situativ. *(Limitation: die Transkripte enthalten nur Orchestrator-Kontexte – 211 der 517 Läufe; für die ~306 Subagent-Läufe gilt das Argument aber verschärft, da Subagenten immer frisch starten.)*
- **S109-Maßnahme (unabhängig von der Ursache, User-Vorgabe):** Wrapper-Ausgabe-Politik vereinheitlicht in `_wrapper_output.py`: **im Erfolgsfall nur noch das Verdikt** (ein bis zwei Zeilen), **im Fehlerfall nur das analyse-Relevante**, alles Weitere hinter `--verbose`. Umgesetzt für vitest-run (12 → 2 Zeilen), playwright-test (→ 2), jscpd-run (25 → 6), eslint-run (→ 1 bei sauberem Lauf) und beide Stryker-Wrapper (30 Zeilen Rohoutput im Erfolgsfall entfallen, ~35 → 8). `dotnet-test` blieb unverändert – mit 3 Zeilen bereits optimal. Fail-open-Prinzip: erkennt ein Wrapper sein Muster nicht, gibt er weiter die längere Fassung aus; ein Parser-Fehlgriff darf nie Information verschlucken. Der SessionStart-Hinweis nennt jetzt konkret, dass `tail` das Verdikt **abschneiden** kann, statt nur zu behaupten, der Output sei kuratiert. **Deny (B) weiterhin nicht gebaut** – bei 83 % Quote träfe es zu breit, und die Ursache ist erklärtermaßen nicht Bedarf, sondern Gewohnheit. **Re-Trigger/Bewertung bis S115:** dieselbe Messung wiederholen. Sinkt die Quote trotz Ein-Zeilen-Verdikt nicht, ist die Gewohnheits-These endgültig bestätigt und nur noch ein mechanischer Guard (B) wirksam. **Messwerkzeug (seit S114 regulär statt Wegwerf-Script):** `python3 .claude/scripts/tool-usage.py --filter`. Die Wrapper-Liste darin **nicht** erweitern – sie ist exakt die der Basislinie, sonst wird die Quote unvergleichbar. **Zwischenstand S114: 636 Läufe, 85 % gefiltert** (Juni 79 %, Juli 86 %) gegenüber der Basislinie 517 / 83 % – also nicht gesunken, eher leicht gestiegen. Die S115-Bewertung selbst steht noch aus.
- **S111-Ergänzung – Messlücke für Klasse 3 (s. OBS-S111-3):** Die S115-Messung zählt Wrapper-Läufe *mit nachgelagertem Filter*. Klasse-3-Fälle (der Wrapper liefert die Information gar nicht) treten aber teils nicht als `| grep` auf, sondern als eigenständiges Ad-hoc-Script auf dem Roh-Report – in S111 dreimal belegt für den Stryker-JSON-Report. Diese Fälle sinken in der Filter-Quote nicht, weil sie nie darin auftauchten; die Quote allein kann die Gewohnheits-These daher nicht bestätigen, solange Klasse 3 ungemessen bleibt.

## OBS-S085-4 – Kein Language-Server für die Agenten-Programmierung im Einsatz
- Quelle: User
- Status: IN BEOBACHTUNG bis S126 – **S115 (Drain): vierte Runde, Termin an TS-Sessions gebunden statt an eine Session-Nummer** (s. Entscheidung). **S109 (Drain): gemessen, Nutzung nahe null → Empfehlung geschärft statt Pilot beendet.** **S099 (Drain) erneut aufgeschoben:** seit Aktivierung (2026-06-20) kaum echte TS-Arbeit, Evidenz-Schwelle (≥ ~3 TS-Sessions) nicht erreicht. **Pilot durchgeführt & technisch validiert (2026-06-20):** `typescript-lsp`@claude-plugins-official läuft auf **nativem** Claude-Install 2.1.183 (anthropics/claude-code #20050 hier **nicht** relevant – galt für ältere Versionen); `ENABLE_LSP_TOOL` nicht nötig; `/reload-plugins` statt Neustart genügt. Alle Ops ok (hover, documentSymbol, goToDefinition cross-file, workspaceSymbol, findReferences); **semantisch präziser als grep** (Kommentar-/String-Treffer korrekt ausgeschlossen). **CAVEAT:** erster `findReferences` direkt nach Plugin-Load = kalter/unvollständiger Index → erst nach Warmlauf vollständig (bei verdächtig wenigen Treffern wiederholen). C# weiter zurückgestellt (#1359). **S101 – Werkzeug-Zugang korrigiert:** LSP war nur dem Orchestrator zugeteilt, NICHT den Layer-Implementern noch den Auditoren; Fix S101 nahm `LSP` in die `tools` von frontend-/backend-layer-implementer + code-quality-/functional-correctness-/test-quality-/ux-ui-/security-auditor auf (workflow-auditor bewusst NICHT – auditiert Prozess, nicht Code). Konsequenz: Evidenzfenster für Implementer/Auditor-Nutzung startet effektiv ab S101.
- Impact: MITTEL–HOCH (von GERING revidiert)    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Sonstiges
- Beobachtung: Wir nutzen aktuell **keinen** Language-Server, der Claude Code Code-Intelligence bereitstellt. Recherche (S086): Claude Code v2.1.172 unterstützt LSP (`ENABLE_LSP_TOOL` + Marketplace-Plugin pro Sprache). Nutzen potenziell **hoch** (Auto-Typfehler nach jedem Edit, find-refs, Symbole, Call-Hierarchie → kürzere Edit-Fix-Schleifen) → Impact GERING→MITTEL/HOCH revidiert.
- Entscheidung/Maßnahme: **(a) TS-LSP-Pilot** (`typescript-lsp`-Plugin); **(b) C# zurückgestellt** — offene Showstopper im Claude-Code-LSP-*Client* (claude-plugins-official#1359: 3 server→client-Requests unbeantwortet → csharp-ls-Solution-Loading bricht; claude-code#38683 Roslyn-Kompat). Trigger zum Wiederaufgreifen = #1359 geschlossen. — **S115-Entscheid (vierte Runde, User): Termin an TS-Sessions gebunden statt an eine Session-Nummer.** Die S109-Sichtbarkeitsmaßnahme ist im Bestand **verifiziert** (LSP-Block in `frontend-layer-implementer.md` und `code-quality-auditor.md`, samt Ladehinweis und Kalt-Index-Caveat) – nach ihr liefen aber nur **zwei** TS-Sessions (S110, S111), die vorab definierte Mindest-Evidenz von ≥3 ist also nicht erreicht; ein Urteil darauf wäre das im Eintrag ausdrücklich ausgeschlossene 'Urteil auf Null-Daten'. **S115-Messung:** 9 Calls gesamt, davon **1 in 22 implementierung-Sessions** – und dieser eine vom 2026-07-10, mithin *vor* der Maßnahme; post-S109 somit null. **Re-Trigger: 3 weitere Sessions, in denen ein `frontend-layer-implementer` oder `code-quality-auditor` real auf TS-Code läuft.** Bewusst nicht 'TS-Session': nur diese beiden Agenten tragen den LSP-Block, sonst wird erneut Gelegenheit statt Werkzeug gemessen. Backstop-Termin S126. **Vierte Nullrunde = verwerfen, ohne weitere Verlängerung.**
- **Pilot-Bound & Abschluss-Kriterien:** Bewertung beim **nächsten Kaizen/Retro** (bewertet OBS ohnehin). Mindest-Evidenz: LSP in **≥ ~3 Sessions mit echter TS-Arbeit** verfügbar; sonst Ergebnis = „eine Runde verlängern" (kein Urteil auf Null-Daten).
  - **Erfolg → adoptieren** (alle drei): (1) tatsächlich genutzt (Frequenz, s. Messung); (2) materieller Mehrwert nachweisbar (konkrete HELP-Vorfälle, wo grep+Read schlechter gewesen wäre); (3) keine Zuverlässigkeits-Blocker über die umgehbare Kalt-Index-Caveat hinaus. → permanente Ein-Zeilen-Regel in `coding-guideline-typescript.md`, Pilot-Notiz raus, Status = UMGESETZT.
  - **Fehlschlag → verwerfen/parken** (eines): kaum genutzt / kein Vorteil ggü. grep+Read; oder Kosten > Nutzen (stale/Flakiness/Setup-Fragilität). → Plugin + Pilot-Notiz entfernen, Status = VERWORFEN (Grund).
- **Messung:** (a) **Frequenz objektiv** = beim Retro Session-Transkripte des Pilot-Zeitraums nach LSP-Tool-Calls grepen (Invocations / distinkte Sessions / Operationen; kein neues Tooling). (b) **Nutzen/Zuverlässigkeit qualitativ** = Pilot-Lauf-Log unten. Bewusst keine Pseudo-Metrik für „Nutzen". Bias bekannt: stille Erfolge unterberichtet, Reibung überzeichnet → HELP-Einträge sind eine **Untergrenze** des Nutzens, FAIL-Volumen nicht überbewerten.
- **Pilot-Lauf-Log** (Format `[S<NNN> | Datum] op — HELP|FAIL — Beschreibung`; bei Nicht-Session-Ereignissen Kontext-Label statt Session-Nr.; **Beschreibung ≤ ~100 Zeichen**, länger nur wenn für spätere Nachvollziehbarkeit wirklich nötig; **FAILs immer, HELPs nur bei klarem Counterfactual**; Routine-Calls nicht loggen):
  - [Aktivierungs-Test 2026-06-20] findReferences — FAIL — direkt nach Plugin-Load kalter Index (1 statt 3 Refs); nach Warmlauf korrekt.
  - [Aktivierungs-Test 2026-06-20] findReferences — HELP — schloss Kommentar-/String-Treffer aus, die grep mitzählte (3 statt 4, 12 statt 15).
- **S109-Messung (Frequenz, wie oben unter „Messung (a)" vorgesehen):** 41 Transkripte durchsucht (40 davon mit Subagent-Aktivität). **LSP-Nutzung in 2 Sessions, 8 Calls gesamt – davon 7 im Aktivierungstest am 2026-06-20 und genau 1 danach (2026-07-10).** Seit S101, seit dem Implementer und Auditoren das Tool überhaupt haben, also praktisch keine Nutzung. Operationen: findReferences 3, hover 2, documentSymbol/goToDefinition/workspaceSymbol je 1.
- **S109-Entscheid (User): Empfehlung schärfen, eine Runde verlängern – bis S115.** Das vorab definierte Fehlschlag-Kriterium („kaum genutzt") wäre erfüllt, aber die Nullnutzung ist mehrdeutig: Der Hinweis stand bisher nur in `coding-guideline-typescript.md`, also in einem Dokument, das ein Agent liest *bevor* er arbeitet – nicht dort, wo die Entscheidung „grep oder LSP?" tatsächlich fällt. Zusätzlich ist LSP ein deferred Tool (erst via `ToolSearch select:LSP` ladbar), was eine echte Schwelle darstellt. Beides zusammen macht plausibel, dass „nicht angeboten" statt „nicht nützlich" gemessen wurde. **Maßnahme:** kurzer, konkreter LSP-Block direkt in die Prompts von `frontend-layer-implementer` (schreibt den TS-Code) und `code-quality-auditor` (stellt die „wo wird das noch verwendet?"-Fragen) – inklusive Ladehinweis und Kalt-Index-Caveat. Guideline-Notiz bleibt. **Bewertung S115 mit unveränderten Kriterien; dritte Nullrunde = verwerfen** (dann ist belegt, dass es nicht an der Sichtbarkeit lag). **Messwerkzeug (seit S114 regulär):** `python3 .claude/scripts/tool-usage.py --lsp` – schlüsselt jetzt nach Session-Art auf, was für dieses Urteil entscheidend ist: Nullnutzung in **implementierung**-Sessions ist ein Urteil über das Werkzeug, Nullnutzung in Drain-/Retro-Sessions nur eines über die Gelegenheit. **Zwischenstand S114: 8 Calls gesamt, unverändert gegenüber S109** – davon 7 im Aktivierungstest (einer tooling-Session zugeordnet) und **genau 1 in 23 implementierung-Sessions**. *Randnotiz:* `backend-layer-implementer` führt `LSP` in seinen `tools`, obwohl für C# kein Server läuft (Blocker #1359) – bewusst nicht angefasst, um das Messsetup nicht mitten in der Bewertung zu ändern.

## OBS-S108-5 – Restore-Endpoint ist als CORS-„Simple Request" ohne Preflight erreichbar
- Quelle: Subagent (security-auditor, Review run-8)
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: QUALITÄT    Kontext: Security
- Beobachtung: `POST /api/ingredients/{id}/restore` verlangt weder Custom-Header noch Request-Body und ist damit ein CORS-„Simple Request": Ein Browser sendet ihn cross-origin **ohne** Preflight, CORS verhindert nur das Auslesen der Antwort, nicht die serverseitige Ausführung. Alle übrigen mutierenden Endpoints sind hier zufällig geschützt – `DELETE` durch den verpflichtenden `If-Match`-Header, `POST /api/ingredients` durch `Content-Type: application/json`; beide erzwingen dadurch eine Preflight, die mangels CORS-Policy scheitert. Der Verzicht auf If-Match beim Restore ist in ADR-S108-2 bewusst und mit Concurrency-Argumenten begründet – dass If-Match nebenbei auch die Preflight erzwungen hätte, ist ein Nebeneffekt, den die ADR nicht betrachtet. Praktische Tragweite im aktuellen Stand begrenzt: Der Angreifer braucht die Ziel-UUIDv7 (~74 nicht erratbare Zufallsbits), wer sie kennt hat über das ungeschützte GET ohnehin direkten API-Zugriff, und der Schaden beschränkt sich auf das Rückgängigmachen eines Soft-Deletes. Relevant wird es, sobald Auth existiert – dann ist es die einzige Stelle, an der ein fremder Browser eine Zustandsänderung auslösen kann. Kein User-Entscheid nötig (kein Business-Impact, technische Härtungsfrage im Sinne der `CLAUDE.md`-Faustregel) – die Abwägung „Preflight erzwingen vs. bewusst tragen" gehört in den Drain, das Ergebnis in eine ADR.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: –

---

## OBS-S109-1 – Datei-Lesen ist der mit Abstand größte Token-Posten und wächst mit der Codebasis
- Quelle: User + Orchestrator
- Status: IN BEOBACHTUNG bis S120 – S114: Ursache ergründet und Werkzeuge gebaut, Wirkung offen
- Impact: HOCH    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Aus der Phase-1-Messung zu OBS-S085-2 (23 Sessions mit Subagent-Einsatz inkl. 112 Subagent-Logs, ~23,5M Zeichen ≈ 5,9M Token-Proxy): **`Read` allein macht 49,5 % des gesamten Volumens aus** – mehr als alles andere zusammen. Bei Subagenten sind es 71,4 % ihres Tool-I/O. 1590 Aufrufe, Ø 7.317 Zeichen (Subagenten Ø 8.373). Zum Vergleich: alle Projekt-Wrapper-Scripts zusammen 8 % des Tool-I/O, Orchestrator↔Subagent-Kommunikation 8,6 % des Gesamtvolumens, Edit 7,9 % des Tool-I/O. Drei Detailbefunde: (1) **Nicht die Anzahl treibt das Volumen, sondern die Größe** – Re-Reads derselben Datei im selben Kontext sind nur 10,1 %; die Top-Dateien sind `Client/e2e/ingredients.spec.ts` (816k gelesen), `docs/kaizen/observations.md` (759k), `Client/src/pages/IngredientsPage.test.tsx` (754k), `docs/guidelines/coding-guideline-csharp.md` (694k), `Server.Tests/IngredientsEndpointsTests.cs` (682k). (2) **86,7 % aller Reads sind vollständig, nur 13,3 % gezielt** (`offset`/`limit`) – und im Fall „Datei wird anschließend editiert" ist der gezielte Read im Schnitt 4,6× kleiner (1.943 vs. 8.971 Zeichen) bei identischem Zweck; der Harness verlangt vor einem Edit einen Read, aber keinen vollständigen (in S109 mehrfach praktisch bestätigt). 17 % des Read-Volumens sind solche vollständigen Vor-Edit-Reads. (3) **Der Posten ist nicht stabil, er wächst mit der Codebasis**: pro Session von Juni auf Juli stieg `Client/`-Lesen von 20k auf 79k Zeichen, `Server/` von 22k auf 48k, während die Pflichtlektüre (`docs/guidelines`) mit 40k→48k nahezu flach blieb. Ergänzend: gezielte Extraktions-Scripte ersetzen die Voll-Reads bisher nicht, sondern kommen hinzu – `decisions.py`-Aufrufe stiegen von 34 auf 87 pro Monat, gleichzeitig stiegen die `adr.md`-Voll-Reads von 1,5k auf 12,3k je Session (die Datei hat 1.263 Zeilen, und wer eine ADR ergänzt, muss sie vorher lesen). Risiko: Der Effekt verschärft sich mit jedem Lauf, weil Test- und Codedateien monoton wachsen und jeder frisch startende Subagent sie vollständig liest.
- Entscheidung/Maßnahme: **S114: erst die Ursache gemessen, dann gehandelt.** Die naheliegende Lesart „der Harness erzwingt den Read vor dem Edit" trägt nicht: Auf `Client/` sind nur 31 % der gelesenen Zeichen Vor-Edit-Reads, auf `Server/` 34 % – **zwei Drittel sind Orientierung** (was gibt es schon? welche Konventionen? wo gehört meins hin?), und 86 % davon lesen die ganze Datei. Diese Fragen brauchen Struktur, nicht Volltext. Maßnahmen: (1) `test-inventory.py` liefert Testnamen **mit Zeilenbereich** für C# und TS – gemessen 17,5× bzw. 16,5× kleiner als die Datei, und der Bereich macht den Folge-Read gezielt statt vollständig; (2) beide Layer-Implementer-Prompts angewiesen, die Inventur statt des Voll-Reads zu nehmen, im Frontend zusätzlich `documentSymbol` für Nicht-Test-Dateien. Verworfen: Testdateien nach Bereich aufteilen – das monotone Wachstum ist mit dem Funktionsumfang erwartbar; nicht in Ordnung ist das wiederholte Voll-Lesen, und das löst die Inventur ohne Umbau am Produktionscode. Ebenfalls verworfen: ein reiner Prompt-Appell zum gezielten Lesen – OBS-S085-3 hat für diese Sorte Nudge belegt, dass sie die Quote nicht bewegt. **Re-Messung bis S120:** `python3 .claude/scripts/read-breakdown.py --by-area --type implementierung` – sinkt der Anteil vollständiger Reads auf Client/ und Server/ nicht, war auch das Werkzeug nicht die Antwort. Nebenbefund für die Messgüte: Tool-Ausgaben über ~60 KB werden aus dem Log ausgelagert; die S109-Basislinie untercountet sie, `read-breakdown.py` löst sie jetzt auf. → CM-S114-2
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

## OBS-S112-4 – `eslint-run.py` meldet Fehlschlag bei null Errors
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: dauerhaft
- Kategorie: TOOLING    Kontext: Wrapper-Scripts
- Beobachtung: Auf unverändertem `main` endet `python3 .claude/scripts/eslint-run.py` mit „✗ ESLint: 3 Problem(e)" bei **0 Errors** und 3 Warnungen. Die Warnungen sind bewusst so eingestuft: `Client/eslint.config.js` setzt `max-params` und `max-lines-per-function` mit ausbuchstabierter Begründung auf `warn` statt `error`. Der Wrapper macht daraus ein Fehlschlag-Verdikt. Damit widersprechen sich Konfiguration und Werkzeug – entweder sind die Warnungen tolerabel, dann ist das ✗ unzutreffend, oder sie sind es nicht, dann steht die Regel-Einstufung falsch. Risiko: Ein Gate, das im sauberen Ausgangszustand rot ist, verliert seine Signalwirkung; ein echtes neues Problem geht im erwarteten Rot unter.
- Bezug: OBS-S112-2
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

---

## OBS-S112-5 – Bash-Allow-Liste hat keinen Weg, eine Dependency-Version zu ändern
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hooks
- Beobachtung: Die Allow-Liste erlaubt `npm run|audit|outdated|update|ci`. Keiner dieser Befehle kann eine Dependency-Version über die deklarierte Semver-Range hinaus verschieben: `update` bleibt innerhalb der Range, `ci` installiert aus dem Lockfile und schreibt es nicht. In S112 war ein Sprung von `react-router` 7 auf 8 nötig, weil die Advisory-behebende Version außerhalb von `^7` lag; er ließ sich ausschließlich über `# --allow-once` durchführen. Dependency-Aktualisierungen sind kein Einzelfall, sondern wiederkehrende Wartung. Risiko: Der Ausnahmemechanismus wird für Routinearbeit verwendet und stumpft dadurch ab.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

---

## OBS-S112-7 – Verweise auf Dokument-Abschnitte sind Prosa und damit nicht maschinell prüfbar
- Quelle: User
- Status: IN BEOBACHTUNG bis S120 – **S115: Ziel geschärft, Umfang erhoben, Umsetzung als eigene Session geplant** (User-Entscheid: vollständig migrieren; s. Entscheidung). Erste Ausprägung (fehlende TOC-Einträge) ist erledigt – der TOC von `e2e-testing.md` führt „E2E-Treue" inzwischen. Offen: Verweis-Prüfbarkeit und Nummerierungs-Zwang.
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: TOOLING    Kontext: Doku
- Beobachtung: Verweise zwischen Projektdokumenten stehen als Prosa – „`coding-guideline-typescript.md` §2", „`nfr.md` Sektion Security", „Checkliste in Schritt 1". Kein Werkzeug kann prüfen, ob das Ziel existiert. In S112 trat das in **beiden** Richtungen auf: Zwei neu geschriebene Abschnitte (E2E-Treue in `e2e-testing.md`, §4c in der TypeScript-Guideline) tauchten im jeweiligen Inhaltsverzeichnis nicht auf und waren damit über den vorgesehenen Einstieg unerreichbar – `implementing-scenario` gibt für `e2e-testing.md` ausdrücklich „TOC zuerst" vor; §4b fehlt dort schon länger unbemerkt. Umgekehrt beschrieb die §2-Zeile im Inhaltsverzeichnis nach einer inhaltlichen Guideline-Änderung weiterhin den alten Stand („Factory Function mit Result-Rückgabe"), ohne dass irgendetwas darauf hinwies. Für volatile IDs (OBS-/TD-/LL-/ADR-) existiert die maschinelle Prüfung bereits – `decisions.py check` fängt tote ADR-Referenzen, `check-ref-direction.py` falschgerichtete –, für Dokument-Abschnitte fehlt das Äquivalent vollständig. Risiko: Verweise sterben unbemerkt in beide Richtungen; ein umbenannter Abschnitt hinterlässt tote Verweise, ein entfernter hinterlässt Verweise ins Leere, und beides fällt erst auf, wenn jemand der Referenz tatsächlich folgt. **Zweite Ausprägung derselben Ursache – erzwungene Nummerierung:** Weil Verweise auf Abschnitts*nummern* zeigen („§2", „§4b"), müssen diese Nummern stabil bleiben. Wächst der Inhalt, entstehen daraus Einschübe statt einer Neunummerierung – in S112 kamen so `4b` und `4c` zwischen `4` und `5` zu liegen. Die Nummer ist damit faktisch zur ID geworden, ohne deren Eigenschaften zu haben: Sie kodiert eine Position, die sich nicht mehr ändern darf, und die Gliederung richtet sich nach der Verweisbarkeit statt nach dem Inhalt. <!-- obs-ok: Die folgende Zielvorstellung stammt vom User als Auftraggeber, nicht aus agentenseitiger Vorwegnahme – sie hier zu tilgen hieße, die Entscheidungsgrundlage des Drains zu verlieren. --> Der User hält echte Markdown-Anker statt Prosa-Verweise für den lohnenswerten Weg, zusammen mit einem Hook plus Script, das bei jedem Schreibvorgang tote Anker meldet und zusätzlich **reversgerichtet** arbeitet: Wird ein Anker entfernt, ist zu prüfen, ob noch Verweise darauf zeigen. Anker sollen kurz bleiben, um vom Text nicht abzulenken – analog zur bestehenden ID-Notation (OBS/TD/LL), für Guidelines etwa `CGT`/`CGC`. Damit entfiele zugleich die Notwendigkeit, Abschnitte überhaupt zu nummerieren: Der Anker trägt die Identität, die Reihenfolge bleibt frei. Der Mehraufwand beim Schreiben gilt als vertretbar.
- Entscheidung/Maßnahme: **Aufgeschoben S115 – als eigene Session geplant, Ziel und Umfang jetzt festgelegt.** — **(1) Ziel, vom User in S115 korrigiert:** Es geht ihm um **Navigation zwischen Referenzen** (für Mensch *und* Agent) und darum, **beim Editieren sofort zu merken, wenn eine Referenz ins Leere führt** und woanders nachgezogen werden muss. Das Abschaffen der Nummerierung ist Mittel, nicht Zweck – der ursprüngliche Eintragstext (agentengeschrieben) hat die Zielsetzung verschoben. — **(2) Widerlegte Zwischenannahme:** Der Orchestrator hatte in S115 argumentiert, bei Skill-Ablaufschritten sei die Nummer echte Semantik und Anker daher falsch. Der User hat das entkräftet: Auch dort erzwingt jede Einfügung oder Verschiebung eine Nachnummerierung aller Folgeschritte – genau die Ursache der `4b`/`4c`-Einschübe. Auflösung: **Nummer und Identität trennen** – eine Nummer darf für Ablauf/Fortschritt bleiben, aber *Verweise* zeigen auf den Anker, damit Neunummerieren keine Verweise bricht. IDs wie OBS-/ADR-/TD- bleiben numerisch. — **(3) Umfang, in S115 gemessen.** Nummerierte Überschriften: `docs/guidelines` 23 (ux 9, typescript 9, csharp 2, stryker/rop/sumtypes je 1), `.claude/skills` 40 (kaizen 13, gherkin-workshop 8, design-an-interface 5, review-code 4, draining-observations 4, review-docs 3, write-code 3), `docs/reference` 19 (architecture 14, glossary 5), `docs/process` 0. Verweise: `.claude/skills` 124 Schritt-Verweise, `docs/kaizen` 78 (teils Historie), `docs/history` 107 (**read-only – der Prüfer MUSS sie ausnehmen, sonst über 100 Falschmeldungen**), process+guidelines+agents 1; dazu rund 44 §-/Sektion-Verweise. Etwa die Hälfte aller Verweise nennt die Zieldatei nicht („erst beim vollständigen Lauf in Schritt 4") – ohne eindeutige IDs sind die grundsätzlich nicht auflösbar, für Menschen so wenig wie maschinell. — **(4) Kritischer Befund, der den Umfang bestimmt:** `implementing-scenario/SKILL.md` (356 Zeilen) und `closing-session/SKILL.md` haben **keine Schritt-Überschriften** – nur eine H1. Die 30+ Verweise auf „Schritt N" zeigen dort auf Ziele, die als Struktur überhaupt nicht existieren; wer sie liest, muss die Datei durchsuchen und raten. Die Migration muss dort erst Gliederung schaffen, und zwar in den Skills, die den Arbeitsprozess selbst steuern – ein halb strukturierter Zustand wäre schlechter als der heutige. Zugleich ist das der stärkste Beleg für das Navigationsproblem. — **(5) Empfohlene Reihenfolge:** Anker-Schema als ADR (Schema-Detail → Orchestrator-Entscheidung) → Prüfscript + PostToolUse-Hook auf Edit/Write in Doku, beide Richtungen (toter Verweis; entfernter Anker, auf den noch verwiesen wird), Historie ausgenommen, mit Tests → Gliederung der zwei Prozess-Skills → Überschriften auf Anker → Verweise umstellen → Prüferlauf grün. Der Prüfer zuerst, weil er die Migration selbst absichert.

---

## OBS-S113-1 – Der Drain-Satz kennt keine extern gesetzten Gates und kann sie nicht anzeigen
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: `docs/AGENT_MEMORY.md` führte vier OBS (OBS-S111-1, OBS-S106-1, OBS-S106-2, OBS-S108-2) ausdrücklich als **Gate** vor dem nächsten `gherkin-workshop` – „Gate, nicht nur Priorität". Der Drain-Satz, den `obs-drain.py` am Session-Start ausgibt, sortiert die Wert-Lane rein nach Impact × Häufigkeit; alle vier tragen `× gelegentlich` und fielen deshalb aus der Top-6. Der vorgeschlagene Satz enthielt **keinen** von ihnen, und nichts im Satz wies darauf hin, dass eine externe Vorrangregel existiert. Aufgefallen ist der Konflikt nur, weil in dieser Session beide Quellen nebeneinander gelesen wurden – der Hook injiziert `AGENT_MEMORY.md` und den Drain-Satz zwar gemeinsam, aber unverbunden. Wer dem Drain-Vorschlag folgt, arbeitet einen fachlich korrekt priorisierten Satz ab und lässt das Gate trotzdem stehen; der nächste Workshop liefe dann in genau die Blindstellen, deretwegen das Gate gesetzt wurde. Verallgemeinert: Priorität wird an zwei Orten gebildet – im Script nach einer festen Formel, in `AGENT_MEMORY.md` nach Projektlage –, ohne dass der eine Ort vom anderen weiß.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S114-1 – Zahl der Zugriffs-Scripte wächst, ohne dass fertige Systeme dafür geprüft wurden
- Quelle: User + Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Doku/Script
- Beobachtung: In S114 kamen fünf Zugriffs-/Analyse-Scripte auf einmal dazu: `obs.py` und `lessons.py` (Tracker-Einträge lesen/schreiben), `test-inventory.py` (Testnamen mit Zeilenbereich), `read-breakdown.py` und `tool-usage.py` (Messungen über die Session-Logs). Dazu bestanden bereits `decisions.py`, `obs-drain.py`, `obs-archive.py`, `next_run.py`, `retro_report.py`, `jenga_score.py`. Jedes einzelne Script ist für sich begründet – gemessener Vor-Edit-Read, garantierte Eintragsform, wiederholbare Messung. Die entstehende Menge ist aber selbst eine Architektur-Entscheidung, die nie als solche getroffen wurde: Wir bauen schrittweise eine eigene Zugriffsschicht auf Projektwissen, deren Schema, Konsistenz und Wartung wir vollständig selbst tragen. Der User hat darauf hingewiesen, dass es dafür etablierte (Memory-)Systeme geben könnte, und die Prüfung bewusst auf später vertagt. Ohne Eintrag geht diese Vertagung verloren, weil sie nur im Gesprächsverlauf steht. Risiko: Der Aufwand wächst mit jedem weiteren Script, und je mehr Eigenbau existiert, desto teurer wird ein späterer Wechsel – die Entscheidung wird also mit der Zeit stiller getroffen, nicht bewusster.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S114-2 – Pflichtlektüre ist der zweitgrößte Leseposten und wird nie gefiltert
- Quelle: Orchestrator
- Status: IN BEOBACHTUNG bis S120 – **S115: wartet bewusst auf die Anker aus OBS-S112-7** (User-Entscheid); Messung erneut bestätigt (s. Entscheidung).
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Gemessen über 48 Sessions (`read-breakdown.py`): `docs/guidelines` und `docs/process` machen zusammen 21,4 % des gesamten Read-Volumens aus – in Implementierungs-Sessions sogar 27,9 %, hinter Client/ und Server/ der zweitgrößte Block. Die Einzelwerte sind hoch: Ø 12.234 Zeichen je Read auf `docs/guidelines`, 11.410 auf `docs/process`, und der Anteil gezielter Reads (mit offset/limit) liegt bei 3 % bzw. 7 % – praktisch jeder Aufruf liest das ganze Dokument. Ursache ist die Konstruktion: Die Agenten-Prompts schreiben diese Dateien als Pflichtlektüre vor, und jeder Subagent startet kalt. Anders als bei ADRs (`decisions.py` filtert nach Tags) und seit S114 bei Testdateien (`test-inventory.py` liefert eine Inventur) existiert für Guidelines kein Weg, gezielt nur den relevanten Abschnitt zu holen. Für die Gegenrichtung liegt eine Rechnung vor: Einen ADR in eine Guideline zu überführen kostet das 7- bis 12-Fache, weil eine Guideline von jedem Subagenten gelesen wird (180 Reads im Messzeitraum) statt on demand von den wenigen, die sie brauchen (14). Offen ist die umgekehrte Frage – ob selten gebrauchte Guideline-Abschnitte aus der Pflichtlektüre gelöst und abrufbar gemacht werden können, und woran „selten gebraucht" überhaupt erkennbar wäre. Der Block wächst mit +21 % über fünf Sessions langsamer als der Code, aber er schrumpft nicht.
- Entscheidung/Maßnahme: **Aufgeschoben S115 – gekoppelt an OBS-S112-7.** Der gezielte Abruf soll **anker-basiert** entstehen (`guideline.py get <Anker>`), nicht über eine eigene Zeilennummern-Lösung: ein Werkzeug statt zwei, und keine Zwischenlösung zum Wegwerfen (User-Entscheid). Die naheliegende Baseline – ein `doc-outline.py` analog zum bewährten `test-inventory.py`, das Abschnitte mit Zeilenbereich ausgibt – wurde deshalb ausdrücklich **nicht** gebaut; sie hätte sofort gewirkt, aber ein zweites Werkzeug für dieselbe Aufgabe hinterlassen (der Punkt aus OBS-S114-1). Preis der Kopplung: Die 14 % bleiben unangetastet, bis die Anker-Migration weit genug ist. **Messung S115 erneut bestätigt:** `docs/guidelines` ist mit 14,0 % der zweitgrößte Read-Bereich überhaupt – nur `Client/` liegt mit 23,2 % darüber –, 180 Reads, Ø 12.234 Zeichen, **3 % gezielt**; mit `docs/process` (7,3 %, Ø 11.319, 7 % gezielt) zusammen 21,3 %. Unverändert gegenüber S114, weil seit dem keine Implementierungs-Session lief. **Die offene Frage des Eintrags ist beantwortet:** „Woran wäre 'selten gebraucht' erkennbar?" – beide Pflichtlektüre-Dateien führen im TOC bereits eine **`Wann lesen`-Spalte** (`e2e-testing.md`, `coding-guideline-typescript.md`). Das Metadatum existiert also; es fehlt allein das Werkzeug, das Abschnitt plus Fundstelle ausliefert. Damit ist beim Wiederaufgreifen keine neue Erhebung nötig.

## OBS-S116-1 – Tracker-Schreibscripte machen die vorgenommene Änderung schlechter erkennbar als ein Datei-Edit
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Einträge in observations.md und lessons_learned.md werden seit S114 über obs.py/lessons.py geschrieben statt über Edit/Write. Für den User ist dadurch schwerer nachvollziehbar, was genau erfasst oder geändert wird: Ein Edit/Write zeigt in der Freigabe einen Diff mit Vorher/Nachher im Datei-Kontext; ein Script-Aufruf zeigt eine Kommandozeile mit langen Argumenten und quittiert danach nur mit einer Bestätigungszeile. Bei set-/anhängen-Aufrufen ist zusätzlich der Ausgangszustand unsichtbar, sodass sich aus dem Aufruf allein nicht ablesen lässt, was ersetzt wird. Die Umstellung war beabsichtigt und hat einen belegten Nutzen (CM-S114-2: Tracker-Dateien waren zu 50 Prozent erzwungener Vor-Edit-Read); die Einbusse an Nachvollziehbarkeit fuer den freigebenden User war dabei nicht Teil der Abwaegung. Spannungsfeld: Wer den Diff wiederherstellen will, muss entweder den Vorzustand lesen - womit die Token-Ersparnis entfaellt - oder ihn anders sichtbar machen. Konkreter Schadensfall in S117: Ein `obs.py set --entscheidung "…"`-Aufruf enthielt Backticks im Text; die Shell fuehrte sie als Kommando-Substitution aus, sodass der Modulname aus dem geschriebenen Text verschwand. Das Script quittierte trotzdem mit „✓ aktualisiert" – der Erfolgshinweis bezieht sich auf den Schreibvorgang, nicht auf den Inhalt. Bei einem Edit waere die Luecke im Diff sichtbar gewesen; hier fiel sie nur auf, weil die Shell zufaellig eine Fehlermeldung („command not found") ausgab und danach aktiv nachgelesen wurde. Verschaerft die Beobachtung um eine Dimension: Es geht nicht nur um schlechtere Erkennbarkeit fuer den freigebenden User, sondern um einen stillen Korruptionspfad – Shell-Metazeichen im Argument veraendern den geschriebenen Inhalt, ohne dass Script oder Aufrufer es bemerken.
- Vorprägung: Vom User bei der S116-Retro genannt: Ideal waere, wenn der Script-Aufruf beziehungsweise dessen Freigabe eine Darstellung liefert, an der sich die Aenderung diff-maessig erkennen laesst.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: CM-S114-2

## OBS-S116-3 – retro_report.py zeigt je Muster nur zwei Beispiel-Einträge, auch wenn es mehr sind
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: In Abschnitt 6 (Pattern-Kandidaten) sammelt retro_report.py:523 pro Tag-Tripel hoechstens zwei Beispiele, gibt aber die volle Anzahl aus. In der S116-Retro meldete ein Kandidat '3x' und listete zwei Eintraege; der dritte (LL-S114-3) war nur ueber einen eigenen grep auffindbar. Der kaizen-Skill verlangt an derselben Stelle ausdruecklich, vor jedem Vorschlag die konkreten Eintraege zu lesen, weil Cluster Tag-Kombinationen sind und keine semantischen Gruppen - die Kappung entzieht dieser Pflicht gerade bei den groessten und damit wichtigsten Mustern die Grundlage. Wer die Diskrepanz zwischen Zahl und Liste nicht bemerkt, haelt die zwei gezeigten Eintraege fuer das ganze Muster.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: CM-S064-2

## OBS-S116-4 – Kontext-Tags in lessons_learned werden nirgends gegen die erlaubte Liste geprüft
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Der Noise-Review der S116-Retro fand drei Eintraege mit Kontext-Tags, die es in process.md nie gab: '[Subagenten]' (LL-S108-1) und zweimal '[Kaizen]' (LL-S102-1, LL-S099-1). Sie stammen aus drei verschiedenen Sessions und lagen bis zu 17 Sessions unbemerkt. Die Wirkung ist nicht kosmetisch: retro_report.py clustert auf dem Tripel Impact/Kategorie/Kontext, ein Tag ausserhalb der Liste kann daher mit keinem anderen Eintrag zusammenfallen und faellt aus der Musteranalyse heraus - der Eintrag zaehlt zwar in der Statistik mit, kann aber nie ein Muster bilden. Impact und Kategorie sind durch die argparse-choices von lessons.py abgesichert, --kontext ist als freier String deklariert. Damit ist ausgerechnet die feinste der drei Dimensionen die einzige ungeschuetzte.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: CM-S064-2

## OBS-S116-5 – Kein Mechanismus stellt sicher, dass ein HOCH-Finding einen CM-Anschluss bekommt
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: process.md verlangt fuer jedes KRITISCH- oder HOCH-Finding sofort einen countermeasures-Eintrag. Geprueft wird das nur weich beim closing-session. In der Periode S107-115 entstanden 8 HOCH-Findings bei 2 neuen CMs. Ein Finding blieb ganz ohne Anschluss (LL-S113-3); bei vier weiteren existierte die inhaltlich passende Maßnahme, aber der Nachtrag an ihr fehlte. Die zweite Form ist die unauffaelligere und zugleich schaedlichere: Ohne Nachtrag zaehlt retro_report.py den Rueckfall nicht, die Maßnahme erscheint wirksamer als sie ist, und die naechste Retro bewertet sie auf zu guenstiger Datenlage - genau der Fehler, den LL-S107-2 fuer die BEWAEHRT-Hochstufung beschreibt. Der Punkt war als CM-S078-2 schon einmal offen und wurde in S095 verworfen, weil zwei Perioden ohne Fehlausgang vergingen; die Verwerf-Begruendung nannte ausdruecklich den Fall, der jetzt eingetreten ist. Erschwerend: Der Anschluss ist keine rein syntaktische Eigenschaft - ob eine bestehende CM inhaltlich passt, ist ein Urteil, weshalb ein rein mechanischer Abgleich Impact gegen CM-Existenz Fehlalarme erzeugen wuerde.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: CM-S078-2

## OBS-S117-1 – Geschriebene Szenarien ohne Lauf-Zuordnung haben keinen Weg in die Implementierung
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Gherkin
- Beobachtung: features/interaction.feature (3 Szenarien) und features/resilience.feature (5 Szenarien) enthalten geschriebene, freigegebene Szenarien ohne '# @run-N'-Kommentar. next_run.py behandelt ungetaggte Szenarien als eigenen Einzel-Lauf, erreicht sie aber nie, weil seine Story-Aufloesung ueber den @US-NNN-Feature-Tag laeuft und beide Dateien @CROSS-/@NFR-getaggt sind. Damit existiert kein Mechanismus, der diese Szenarien jemals als 'naechster Lauf' vorlegt. interaction.feature vermerkt 'Implementierungs-Scope: nach MVP' und verlangt vorher einen Workshop-Lauf – ein Plan, den kein Trigger aufruft. Sichtbar wurde es beim Bau des td-due-Moduls in S117: Drei TD-Eintraege ankern per Szenario: auf genau diese Szenarien und brauchen deshalb alle einen Phasen-Backstop, weil ihr eigentlicher Anker strukturell nicht eintreten kann. Die Waisen-TD ist damit nur das Symptom; die Waise ist das Szenario.
- Entscheidung/Maßnahme: Teil-Umsetzung S117: Das Agenda-Modul `ungeplante-szenarien` macht die Szenarien sichtbar (Stub mit Anzahl, Volltext auf Abruf) und weist ihren Status ausdrücklich als *ungeklärt* aus – nicht als fällig. Damit ist die stille Unsichtbarkeit behoben; zusätzlich löst `next-run` nur noch story-gebunden auf, behauptet also keine Arbeit mehr, die die Feature-Datei zurückstellt. OFFEN bleibt der eigentliche Punkt: Es gibt weiterhin keine Regel, WANN querschnittliche Szenarien einen Lauf bekommen (interaction.feature verlangt vorher einen gherkin-workshop-Lauf, den kein Trigger aufruft). Solange das offen ist, brauchen TD-Einträge mit Szenario-Anker einen Phasen-Backstop.

## OBS-S117-2 – Injizierter Kontext erreicht den User nur ueber die Disziplin des Agenten
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Sonstiges
- Beobachtung: Der Session-Start injiziert Bloecke, die fuer den USER bestimmt sind – etwa die faelligen offenen Fragen, die laut Skill draining-observations 'dem User zur Klaerung vorgelegt' werden muessen. Injiziert werden sie aber in den Agenten-Kontext; ob sie beim User ankommen, haengt allein daran, dass der Agent sie weiterreicht. Kein Mechanismus prueft die Uebergabe. Belegt in S117 durch den User selbst ('Mir wurde nichts vorgelegt') und durch den Agenten in derselben Session: OQ-S083-1/-2 und OQ-S094-1 standen im Startblock und wurden nicht vorgelegt. Der Befund ist allgemeiner als offene Fragen – er betrifft jeden Block, dessen Zweck die Weitergabe an den User ist. Nebenbefund zur Wirksamkeit: Die Vorlage funktioniert (die Fragen erscheinen seit S115 jede Session), die Aufloesung nicht. Das ist ein eigener Befund und steht jetzt in OBS-S117-4 – die hier zunaechst notierte Begruendung ('kein Wiedervorlage-Termin') war falsch, ein optionales Faellig-Feld existiert seit S115.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S117-3 – principles.md ist der groesste Session-Start-Block und ungeprueft auf Knappheit
- Quelle: User
- Status: NEU
- Impact: GERING    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: principles.md ist mit 7.417 Bytes der groesste einzelne Block der Session-Start-Injektion – groesser als AGENT_MEMORY, dessen Volumen in S116/S117 als Problem behandelt wurde (OBS-S116-2). Der Block ist ein Immer-Block und wird bewusst nie unterdrueckt: Verhaltensregeln, die nicht geladen sind, fallen lautlos aus. Die Groesse ist damit nicht per Unterdrueckung adressierbar, sondern nur redaktionell. User-Einschaetzung S117: Der Text liesse sich kuerzen, und beim Hineinschreiben muesste rigoroser auf Knappheit ohne Verlust von Vollstaendigkeit geachtet werden. Bewusst nicht in S117 mitgemacht, weil das Kuerzen von Verhaltensregeln inhaltliche Arbeit ist und nicht als Nebenprodukt einer Tooling-Aenderung passieren sollte.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S118-1 – TD-Einträge mit Fälligkeit jetzt werden von Hand in AGENT_MEMORY dupliziert, statt dort erzeugt zu werden
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Ein TD-Eintrag mit '**Fällig:** jetzt' muss zusätzlich als Punkt in docs/AGENT_MEMORY.md unter 'Nächste Prioritäten' stehen. Das ist keine Konvention, sondern Gate: check-td-capture.py:114 blockt das Schreiben von tech-debt.md, wenn die TD-ID dort fehlt. Fuer alle anderen Anker-Arten macht das Startup-Script es dagegen mechanisch - td_due.faellige() liest tech-debt.md und rendert die faellig gewordenen Eintraege in die Session-Agenda, ohne dass irgendwo eine zweite Kopie gepflegt wird. Nur der jetzt-Anker ist davon ausgenommen; td_anchors.faellig_gruende erzeugt fuer ihn bewusst keinen Grund, mit der Begruendung, solche Eintraege stuenden 'bereits in AGENT_MEMORY und werden von dort vorgelegt - hier nochmals zu melden waere die Doppelung, die OBS-S116-2 beanstandet'. Das Argument adressiert doppelte Vorlage und erzeugt dabei doppelte Pflege: Titel und Existenz des Eintrags leben an zwei Orten und koennen driften, und beim Beheben der Schuld muessen zwei Dateien geraeumt werden. Belegt in S118: Beim Anlegen von TD-S118-1 und TD-S118-2 mussten drei Zeilen von Hand nach AGENT_MEMORY geschrieben werden, bevor tech-debt.md ueberhaupt beschreibbar war. Was die AGENT_MEMORY-Zeile heute zusaetzlich traegt und bei einer Loesung nicht verloren gehen darf: (1) die Rangfolge - laut Header der Datei ist die Reihenfolge dort die Auswahl, welcher jetzt-Punkt die 'Naechste Aufgabe' der Session beansprucht, und tech-debt.md kennt keine Ordnung; (2) das Done-Kriterium, das im TD-Eintragsformat (Faellig/Problem/Behebung) kein Feld hat; (3) die Liste mischt TD-Punkte mit Punkten aus anderen Quellen (OBS, ADR, Story) zu einer gemeinsamen Rangfolge.
- Vorprägung: User: 'das doppelt doch nur das TD und koennte mechanisch gemacht werden (wie es fuer die anderen Eintraege auch gemacht wird)'. Orchestrator-Vermutung: Das Anti-Doppelungs-Argument in td_anchors.py ist auf der falschen Ebene angesetzt - es vermeidet doppelte Vorlage, nicht doppelte Pflege. Denkbare Richtungen, ungeprueft: jetzt-TDs vom Script injizieren und AGENT_MEMORY nur noch Rangfolge-Ueberschreibungen tragen lassen; oder das Done-Kriterium als Feld ins TD-Format aufnehmen, damit die Zeile vollstaendig generierbar wird.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: OBS-S116-2

## OBS-S119-1 – Deny-Text des Bash-Hooks lenkt in Einmalscripte, statt die Werkzeugfrage zu stellen
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Der Deny-Text von check-bash-permission.py (Zeile 605 und analog 568) bietet als Ausweg an: 'Für Ad-hoc-Logik: Script nach .claude/tmp/foo.py schreiben, dann python3 .claude/tmp/foo.py.' Der Text setzt damit stillschweigend voraus, dass der geblockte Befehl überhaupt Ad-hoc-Logik war, und bietet den Ausweg an, bevor die Vorfrage gestellt ist: Braucht es hier ein Script? Aufgetreten in S119: Ein zusammenhaengender, vollstaendig gelesener Textblock sollte aus einer Markdown-Datei geloescht werden. Das ist ein Edit-Fall. Ich habe reflexhaft einen Python-Heredoc in Bash versucht, der Hook hat geblockt, und ich bin dem angebotenen Ausweg direkt gefolgt und habe .claude/tmp/drop_oq.py geschrieben – ohne einen Schritt zurueckzugehen. Der Hook hat den Befehl korrekt geblockt und dann in eine zweite, ebenfalls unpassende Loesung gelenkt. Verschaerfend: Das Einmalscript war hier das riskantere Werkzeug. Ein Edit-Mismatch schlaegt fehl, waehrend index() + Slicing blind schneidet, ohne dass sichtbar wird, was rausfliegt. Der Deny-Text nennt kein Kriterium, wann ein Script gegenueber vorhandenen Tools und Scripten ueberhaupt gerechtfertigt ist.
- Vorprägung: Der User hat als Kriterium genannt: ein Script lohnt nur, wenn es effizienter und/oder weniger fehleranfaellig ist als die vorhandenen Tools – nicht deshalb, weil Bash geblockt wurde. Einmalscripte haetten vor allem im Standardprozess nur begrenzt Sinn; primaer sollen vorhandene Tools und Scripte genutzt werden. Naheliegende Richtung waere daher, den Deny-Text um diese Vorfrage zu ergaenzen, statt direkt den tmp-Ausweg anzubieten.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S120-1 – Offene Fragen sind der einzige Tracker ohne Pflege-Werkzeug – Löschen braucht jedes Mal ein Wegwerf-Script
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Doku/Script
- Beobachtung: Um OQ-S119-2 aus docs/open-questions.md zu entfernen, entstand in S120 ein Wegwerf-Script unter .claude/tmp/ – ein fast identisches gab es in einer der vorangegangenen Sessions schon einmal. Der User wertet die Wiederholung als Bedarfsnachweis. Der Befund am Bestand: open_questions.py ist ein reines Import-Modul (parse/due) für session-agenda.py und obs-drain.py und hat gar keine CLI; es gibt also weder get noch add noch remove. Zum Vergleich bietet obs.py get/add/set, lessons.py get/add. Ein Eintrag in open-questions.md ist mehrzeilig mit Pflichtfeldern (Fällig-Anker nach td_anchors-Grammatik, geprüft von check-oq-capture.py) – also genau die Struktur, für die andere Tracker ein Script haben, weil freihändiges Editieren Formfehler produziert und die Datei zum Lesen komplett geöffnet werden muss. Beim Löschen kommt hinzu, dass Fundstellen in anderen Dokumenten hängenbleiben können: In S120 wurde der erste Löschversuch von check-dangling-refs.py geblockt, danach blieb der Eintrag versehentlich stehen, weil nach dem Bereinigen der Fundstellen nicht nachgefasst wurde.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: OBS-S114-1

## OBS-S120-2 – Fünf Eintrags-Tracker, drei verschiedene Pflege-Strategien – gewachsen statt entworfen
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: TOOLING    Kontext: Doku/Script
- Beobachtung: Das Projekt führt inzwischen fünf Dokumente, die strukturierte Einträge mit Pflichtfeldern und IDs tragen: observations.md, lessons_learned.md, adr.md, tech-debt.md, open-questions.md. Wie ein Eintrag entsteht, ist je Datei anders gelöst und die Abdeckung ist ungleich: obs.py kann get/add/set, lessons.py nur get/add, decisions.py ist trotz 463 Zeilen reines Lesen (list/get/check/tags/refs) ohne add, für tech-debt.md existiert überhaupt kein Script (nur die Anker-Helfer td_anchors.py/td_due.py), und open-questions.md hat nicht einmal eine CLI. Parallel dazu bewachen vier Hooks die Form beim Editieren – check-adr-capture, check-obs-capture, check-oq-capture, check-td-capture. Damit koexistieren zwei gegenläufige Strategien für dasselbe Problem: 'Script garantiert die Form beim Schreiben' (OBS, LL) gegen 'Edit von Hand, Hook blockt hinterher' (ADR, TD, OQ). Wer einen Eintrag anlegen will, muss erst wissen, welche der beiden Welten für seine Datei gilt; wer eine Datei ergänzt, dupliziert Parsing, ID-Vergabe, Session-Erkennung und Session-Abschnitts-Logik ein weiteres Mal. Der User schlägt vor zu prüfen, ob ein einziges Werkzeug für alle fünf Dateien den vielen Einzelscripten überlegen wäre. Offen und zu bewerten ist dabei auch, ob die Vereinheitlichung die Trennschärfe der Tracker aufweicht – die Ablage-Taxonomie (CLAUDE.md, process.md) lebt davon, dass die Dateien verschieden sind.
- Vorprägung: Der User nannte als Veranschaulichung eine gemeinsame CLI im Stil 'create-doc-entry ADR --title ...' und wies ausdrücklich darauf hin, dass der Name nur illustrativ ist. Nicht als gesetzte Lösung behandeln: Ebenso denkbar sind ein geteiltes Modul mit weiterhin fünf dünnen Einstiegspunkten, oder nur das Schließen der Abdeckungslücken bei gleichbleibender Struktur.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: OBS-S120-1, OBS-S114-1

## OBS-S120-3 – Der qa-check-Übergabe-Hash erzwingt einen zweiten Stryker-Volllauf, wenn nach dem ersten noch aufgeräumt wird
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Der Übergabe-Hash von qa-check.py bindet unter anderem den Inhalt des Working-Tree-Codes (compute_hash: TREE + Report-Hash + Testdateien + Suppressions). Das ist bewusst so gebaut und richtig – es macht den Hash manipulationsresistent und verhindert, dass ein Subagent nach dem Lauf noch etwas nachschiebt. Die Reibung entsteht am typischen Sessionende: Nach einem grünen Lauf fällt beim Review noch eine Kleinigkeit auf – ein Kommentar, eine Suppressions-Begründung, eine Umbenennung –, und der Hash ist ungültig. Weil der Hash nur aus einem Frisch-Lauf entsteht (--skip-stryker gibt bewusst keinen aus), kostet die Neu-Attestierung den vollen Stryker-Durchgang, in S120 rund zwei Minuten je Schicht, obwohl die Änderung das Mutations-Ergebnis nicht berühren kann. Das Script kann das nicht wissen: Ein inhaltsbasierter Hash unterscheidet semantisch neutrale Edits nicht von echten. Der Anreiz, den die Konstruktion damit setzt, ist der eigentlich unerwünschte – Aufräumarbeiten lieber zu unterlassen oder ungeprüft zu lassen, statt einen zweiten Volllauf zu bezahlen.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S121-1 – Tracker-Schreibscripte pruefen die Eintragsstruktur nach dem Schreiben nicht
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Vorausschauende Haelfte zu LL-S121-1 (dort der eingetretene Schaden). obs.py und lessons.py garantieren die Eintragsform beim ANLEGEN per Konstruktion – aber kein Schreibpfad prueft nach dem AENDERN, ob der Eintrag noch wohlgeformt ist. Genau dort entsteht der Schaden: append_beobachtung haengt an eine Zeile an, und ein einmal verrutschtes Folgefeld macht jeden weiteren Anhang zum Strukturbruch. Ein Nachher-Check waere billig: nach jedem Schreibzugriff pruefen, dass der geaenderte Eintrag jedes Pflichtfeld genau einmal am Zeilenanfang traegt, sonst Abbruch mit unveraenderter Datei. Das meldet den Schaden im Moment seiner Entstehung statt Sessions spaeter beim naechsten Schreibversuch. Offen ist die Reichweite: Der Check koennte je Script sitzen oder gemeinsam in obs_entry/lessons_entry; und er beruehrt dieselbe Frage wie OBS-S120-2 (fuenf Eintrags-Tracker, drei Pflege-Strategien) und OBS-S116-1 (Schreibscripte machen die Aenderung schlechter erkennbar als ein Datei-Edit) – bei einer gemeinsamen Loesung waeren die drei zusammen zu betrachten. Eine Pruefung ueber observations.md, lessons_learned.md und das Archiv ergab genau einen betroffenen Eintrag, das Muster ist also selten, aber stumm und rueckwirkend teuer.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: LL-S121-1

## OBS-S121-2 – Drain-Rate und Backlog-Ziel widersprechen sich - fester Satz gegen variablen Zielwert
- Quelle: User
- Status: NEU
- Impact: HOCH    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: Der OBS-Drain arbeitet je Session einen Satz fester Groesse ab (aktuell 7 Eintraege: Wert-Lane, Alters-Lane, faellige Wiedervorlagen). Der Backlog liegt seit Laengerem weit ueber dem als gesund definierten Wert (Session-Start S121: 29 drainbar bei Ziel <=8) und sinkt langsamer, als neue Eintraege dazukommen - in S121 wurden fuenf aufgeloest und einer neu erfasst, netto minus vier bei 29 Ausgangslage. Der User weist auf einen zweiten, strukturellen Widerspruch hin: Mit dem neuen Startup soll gedraint werden, bis das Backlog unter einem Schwellwert steht (Groessenordnung 12). Ein Skill, der pro Durchlauf eine feste Anzahl Eintraege vorlegt, passt dazu nicht - er endet, waehrend das Backlog noch ueberfuellt ist, und die Rate ist von dem Ziel entkoppelt, das sie erreichen soll. Zu klaeren ist damit nicht nur die Hoehe der Rate, sondern ihre Form: fester Satz je Session, Abarbeiten bis zum Schwellwert, oder eine Rate, die sich aus dem Abstand zum Ziel ergibt. Mitzudenken ist die Gegenkraft - ein Drain-Durchlauf kostet real Kontext und User-Aufmerksamkeit (in S121 fuellte er eine ganze Session fuer fuenf Eintraege), ein reines Hochdrehen der Zahl verlagert das Problem also nur.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S121-3 – Session-Dateien werden zu vier Fuenfteln nie gelesen; ihre Erfassung ist zudem unmechanisiert
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Zwei zusammenhaengende Befunde des Users beim Session-Abschluss. (a) Mechanisierung: Agenten oeffnen beim Abschluss meist die letzte session_NNN.md, nur um die Form abzuschauen, und schreiben danach den index-Eintrag von Hand - beides waere durch ein Erfassungs-Script loesbar, das die Form ueber seine Parameter vorgibt und erklaert und den Index gleich mitschreibt (analog obs.py add / lessons.py add, die genau dieses Muster fuer die anderen Tracker schon aufloesen). (b) Vorgelagert und wichtiger: Der User bezweifelt den Wert der Einzeldateien ueberhaupt - sein Eindruck ist, es handle sich um write-only-Dateien, die Kosten erzeugen ohne nachweisbaren Nutzen. Messung ueber 193 Session-Logs (git-add-Rauschen herausgerechnet) stuetzt das ueberwiegend: von 117 Session-Dateien wurden 91 nie inhaltlich angefasst (78 Prozent); die verbleibenden 26 kommen zusammen auf 59 Zugriffe, davon 19 reines Format-Nachschlagen. Gesamtumfang 455 KB, im Schnitt 4 KB je Datei. Klare Gegenausnahme: index.md wird 109-mal gelesen gegen 53 Schreibzugriffe, ist also nachweislich in Gebrauch - eine Loesung darf ihn nicht mit abraeumen. Zu entscheiden ist damit die Reihenfolge: Erst klaeren, ob und in welcher Tiefe Einzeldateien gebraucht werden (Kandidaten: abschaffen zugunsten eines reicheren Index, radikal kuerzen, unveraendert lassen), denn ein Erfassungs-Script fuer eine Datei, die niemand liest, mechanisiert nur die Kosten.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
