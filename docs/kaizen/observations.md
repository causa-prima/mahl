# Observations – Beobachtungs-Backlog

<!--
Zweck: Vorausschauende System-Design-Beobachtungen / Optimierungen (proaktiver Track).
       Ergänzt das reaktive lessons_learned.md. Speist den Jenga-Score NICHT.
aufnahmebedingung: Hier steht eine vorausschauende Beobachtung am **Prozess** – wie gearbeitet
       wird (`prozesscode/`, `.claude/**`, `docs/process/`, `docs/kaizen/`). NICHT hierher gehört eine
       Beobachtung am **Produkt**, also am Code samt Build-/Test-Kette: die läuft über
       ADR/TD/OQ ([„Ablage: in welchen Tracker gehört dieser Eintrag?"](../../CLAUDE.md#CLA-ablage)).
       Der Unterschied ist nicht kosmetisch – dieser Pool ist ratenbegrenzt, `tech-debt.md`
       nicht; ein Produkt-Thema hier belegt Drain-Kapazität, die es dort nie gebraucht hätte.
       Abgrenzung zu lessons_learned/countermeasures: [„Wann gehört etwas wohin?"](process.md#KPR-wohin).
       ABER: `obs-drain.py` parst diese Datei (via `obs_parse.py`) für den Drain-Vorschlag → das Eintrags-Format
       unten parse-stabil halten (Feld-Präfixe `- Status:` / `- Impact:` / `- Bezug:` nicht umformatieren).

Eintrag-Format:
  ## OBS-S<NNN>-<n> – Kurztitel
  - Quelle: User | Orchestrator | Subagent   (bei Agent-Quelle möglichst präzise: Subagent vs. Orchestrator)
  - Status: NEU | IN BEOBACHTUNG bis S<NNN> | UMGESETZT (S<NNN>) | VERWORFEN (Grund)
            (IN BEOBACHTUNG: `bis S<NNN>` = Pflicht-Wiedervorlage-Termin; Mechanik: process.md)
  - Impact: KRITISCH | HOCH | MITTEL | GERING    Häufigkeit: gelegentlich | häufig | dauerhaft
            (Score = Impact × Häufigkeit steuert Priorität UND ob der Drain die Session
             beansprucht. Skala und Herleitung: [„Score und Behandlungswürdigkeit"](process.md#KPR-score).
             GERING zählt 0 – die Rubrik definiert es als „keine Folge", nicht als „wenig".)
  - Kategorie: PROZESS | AGENT | QUALITÄT | TOOLING    Kontext: <Kontext-Tag wie in lessons_learned>
  - Beobachtung: <was ist nicht ideal / was fiel auf – Ist-Zustand und Schaden, ohne Ursache/Lösung>
  - Vorprägung: (optional) <was die Bewertung prägen würde: genannte Lösungen, vermutete Ursachen, Analogieschlüsse>
  - Zusammen-erledigen: <OBS-IDs, die sich in einem Zug miterledigen lassen> | keiner   (Pflicht)
            Test: Wenn ich A bearbeite – liegt B dann ohnehin offen vor mir und kostet dadurch
            deutlich weniger? Typisch bei denselben Artefakten oder derselben Sache. NICHT
            gemeint: dasselbe Problem (→ konsolidieren statt clustern), eine Vorfrage (Reihen-
            folge macht nichts billiger), bloße Themen-Ähnlichkeit. Solche Einträge bilden im
            Drain eine Einheit mit summiertem Score – so kommen kleine mit dran, wenn am Thema
            ohnehin gearbeitet wird. Offene Titel zeigt `python3 -m prozesscode.obs
            list-offen`. `keiner` ist Pflicht statt eines weggelassenen Feldes, sonst wäre
            „geprüft, es gibt keine" von „vergessen" nicht unterscheidbar; Freitext blockt
            (er fiele still auf „keine Kante" zurück). `Bezug:` ist dagegen ein freier
            Querverweis und bildet KEINE Einheit.
            **Einseitig genügt** – die Kante wird beim Lesen ungerichtet ausgewertet, eine
            gespiegelte Gegenkante wäre eine zweite Kopie derselben Information und könnte
            nur auseinanderlaufen. `obs.py get` zeigt eingehende Kanten mit an, ein Eintrag
            verrät seine Einheit also von beiden Seiten. Ziele werden beim Schreiben auf
            Existenz geprüft (Vertipper blockt), nicht mehr drainbare meldet der Drain-Satz.
  - Entscheidung/Maßnahme: <bei Erfassung offen; beim Drain: gewählte Lösung + warum statt Alternativen / Verwerf-Grund / Aufschub-Grund + Re-Trigger>; → CM-… falls stehende Leitplanke
            (bei Erfassung mechanisch erzwungen: `prozesscode/hooks/check-obs-capture.py` lässt bei einem NEUEN Eintrag nur
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

## OBS-S101-1 – Flaky-Timeout einzelner Vitest-Tests unter Stryker-Systemlast
- Quelle: Subagent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Mutation-Testing
- Beobachtung: `US904_HappyPath_ReopenDialogAfterCancel_FieldsAreEmpty` lief während eines Stryker-Dry-Runs in einen 5000-ms-Timeout, isoliert (`vitest-run.py --filter`) sofort grün (~900 ms). Ursache vermutlich Systemlast durch viele parallele Checker-/Runner-Prozesse. Kein echter Regress, aber ein solcher Timeout kann einen Übergabe-`qa-check`-Hash fälschlich scheitern lassen (falscher Rot-Alarm).
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: –

## OBS-S085-3 – Agenten durchsuchen Tool-Outputs selbst statt unsere gezielten Scripte zu nutzen
- Quelle: User
- Status: IN BEOBACHTUNG bis S126 – **S115: Filter-Rewrite gebaut (mechanischer Guard), Wirkung offen; Re-Trigger an Wrapper-Läufe statt an eine Session-Nummer gebunden** (s. Entscheidung). S087: A (Wrapper-Audit, kein Change) + C (`--list`/SessionStart-Hinweis „ohne tail/grep") + D (`allowed-commands.log`) umgesetzt, B (Deny) zurückgestellt; **S095 wiederaufgegriffen** nach D-Analyse; **S099 (Drain) erneut aufgeschoben bis S109**; **S109: gemessen + Wrapper-Ausgabe umgebaut, Wirkung offen**.
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Mutation-Testing
- Beobachtung: Agenten greppen/`tail`-en Stryker-&-Co-Output, obwohl unsere Scripte gezielt nur das Relevante ausgeben sollen (Deny-Log S086: 81 head/tail-Zeilen).
- Entscheidung/Maßnahme: **A + C + D**; **B zurückgestellt** bis mehr Daten (mittlere Gefahr, könnte legitime Nutzung blocken). C über `--list` + SessionStart-Injection: knappe Script-Anwendungsfälle + Hinweis „normal **ohne** Filter nutzen (Output ist optimal); wo nicht → als Beobachtung sammeln". D = erlaubte Befehle loggen. — **S115: mechanischer Guard gebaut, als Rewrite statt als Deny.** Erstmals **gemessen statt gerechnet**: `tool-usage.py` um `--since` erweitert (der Zeitstempel stand längst im Log, die Auswertung gruppierte ihn nur auf den Monat und warf den Tag weg – ein Stichtag mitten im Monat war deshalb nicht schneidbar). Ab dem Umbau-Commit (29.07. 00:49) **110 Läufe, 105 gefiltert = 95 %** gegen die Basislinie 83 %. Damit ist das vorab definierte Kriterium erfüllt: drei Soft-Maßnahmen (Hinweis S087, Rezidiv S090, Output-Umbau S109) haben nichts bewegt, das Verhalten ist antrainiert. **Gewählt: Rewrite, nicht Deny** (User-Entscheid) – `strip_wrapper_filter()` entfernt nachgelagerte Filter-Pipes hinter einem Wrapper-Aufruf via `updatedInput`, mit sichtbarem Hinweis auf `--verbose`. Begründung gegen das Deny: Subagenten starten immer frisch und können über Sessions nicht umlernen – ein Deny kostet sie jede Session erneut eine verlorene Runde (105 im Messfenster), der Rewrite keine. Zwei Abgrenzungen tragen die Korrektheit: ein Filter **vor** dem Wrapper filtert dessen Ausgabe nicht und bleibt unberührt, und zwischen Wrapper und erstem Filter bleibt alles erhalten (Argumente, `2>&1`). Analyse-Scripte sind ausgenommen – ihre lange Ausgabe ist zum Zerschneiden gedacht (dieselbe Grenze wie `tool-usage.py` WRAPPERS). **Deny (B) bleibt die Eskalationsstufe** (User-Vorgabe: „ggf. später zum Deny wechseln"). **Re-Trigger: ≥ 100 Wrapper-Läufe nach dem Rewrite-Stichtag 2026-08-08**, dann `python3 -m prozesscode.tool-usage --filter --since 2026-08-08`. Bewusst an Läufe statt an eine Session-Nummer gebunden: Zwischen dem 30.07. und heute fielen in drei Sessions nur **6** Läufe an (Drain-/tech-debt-Sessions führen kaum Wrapper aus) – ein Kalendertermin würde erneut auf Null-Daten urteilen, derselbe Fehler wie im LSP-Pilot. Backstop-Termin S126. **Sinkt die Quote dann nicht deutlich, ist der Rewrite widerlegt und das Deny fällig.**
- **Rezidiv (S090, Quelle: User):** Trotz Gegenmaßnahme C erneut aufgetreten — `grep` mehrfach auf qa-check-Output, `tail` auf playwright-test. Der Session-Hinweis (C) allein verhindert das Verhalten nicht zuverlässig.
- **D-Analyse durchgeführt + Neubewertung (S095):** `allowed-commands.log` ausgewertet (~15+ Filter-Instanzen S90–93). Befund: das Filtern ist **nicht** einheitlich Misuse, sondern zerfällt in drei Klassen — (1) **reines Kürzen** auf bereits kuratiertem Output (`vitest-run|tail`, `eslint-run|tail`) → Disziplin-Thema; (2) **gezieltes Feld-Extrahieren**, weil der Wrapper das Verdikt vergräbt (`qa-check --verify | grep | tail`, `stryker | grep Score/Survived`) → Wrapper sollte das Verdikt klar ausgeben; (3) **legitimer Workaround**, weil der Wrapper die relevante Info gar nicht liefert (`dotnet-test` bei RED ohne Assertion-Details → **OBS-S091-1**). Konsequenz (User-Entscheid): **kein pauschales Deny (B)** — es würde Klasse 2+3 bestrafen. Stattdessen **zuerst die Wrapper fixen** (Klasse 2+3, s. OBS-S091-1/-3), *dann* neu bewerten, ob für Restklasse 1 überhaupt noch eine Maßnahme nötig ist.
- **S099-Drain-Entscheid (erneut aufgeschoben bis S109):** Wrapper-Fixes OBS-S091-1/-3 in S096 erledigt (Blocker weg). User-Korrektur zur Restklasse 1: sie hat **konkreten Schaden** (höherer Token-/Zeitverbrauch, weil der Output anschließend von Hand ausgewertet wird, statt den Tool-Output zu nutzen bzw. eine **Verbesserung am Wrapper** vorzuschlagen) — nicht bloß Disziplin. Da seit S096 kaum Anwendungsgelegenheit bestand, erst ~10 Sessions Post-S096-Daten sammeln, dann Maßnahme neu bewerten (ggf. doch Deny B, ggf. Wrapper-Nachschärfung). Re-Trigger: mehrere Läufe mit realer Wrapper-Nutzung.
- **S109-Messung (`allowed-commands.log`, 17.06.–28.07., nur echte Wrapper-Ausführungen):** **430 von 517 Läufen (83 %) mit nachgelagertem Filter**, Tendenz steigend (Juni 79 % → Juli 85 %). Damit ist die bisherige Einordnung als „Restklasse 1, ~15 Einzelfälle" widerlegt: Filtern ist der Normalfall, nicht die Ausnahme, und die Wrapper-Fixes aus S096 haben daran nichts geändert. Verteilung: vitest-run 96, qa-check 92, dotnet-test 89, playwright-test 60, eslint-run 40, dotnet-stryker 27.
- **S109-Ursachentest (User-Vorschlag, entscheidend):** Die naheliegende Erklärung „der Wrapper-Output ist zu lang, also kürzen die Agenten zu Recht" wurde geprüft, indem in den Session-Transkripten die **Reihenfolge** der Wrapper-Aufrufe je Kontext ausgewertet wurde – filterte ein Kontext erst, *nachdem* er einmal die volle Länge gesehen hatte? Ergebnis: **in 13 von 19 Kontexten (68 %) war schon der allererste Wrapper-Aufruf gefiltert, in 11 davon durchgehend jeder.** Nur 4 Kontexte zeigen das Reaktionsmuster. Der Output kann also nicht der Auslöser sein – er war in diesen Kontexten nie sichtbar. Deutlichster Einzelbeleg: `dotnet-test` gibt im Erfolgsfall **drei Zeilen** aus und wurde trotzdem 89× gefiltert. Das Verhalten ist antrainiert, nicht situativ. *(Limitation: die Transkripte enthalten nur Orchestrator-Kontexte – 211 der 517 Läufe; für die ~306 Subagent-Läufe gilt das Argument aber verschärft, da Subagenten immer frisch starten.)*
- **S109-Maßnahme (unabhängig von der Ursache, User-Vorgabe):** Wrapper-Ausgabe-Politik vereinheitlicht in `_wrapper_output.py`: **im Erfolgsfall nur noch das Verdikt** (ein bis zwei Zeilen), **im Fehlerfall nur das analyse-Relevante**, alles Weitere hinter `--verbose`. Umgesetzt für vitest-run (12 → 2 Zeilen), playwright-test (→ 2), jscpd-run (25 → 6), eslint-run (→ 1 bei sauberem Lauf) und beide Stryker-Wrapper (30 Zeilen Rohoutput im Erfolgsfall entfallen, ~35 → 8). `dotnet-test` blieb unverändert – mit 3 Zeilen bereits optimal. Fail-open-Prinzip: erkennt ein Wrapper sein Muster nicht, gibt er weiter die längere Fassung aus; ein Parser-Fehlgriff darf nie Information verschlucken. Der SessionStart-Hinweis nennt jetzt konkret, dass `tail` das Verdikt **abschneiden** kann, statt nur zu behaupten, der Output sei kuratiert. **Deny (B) weiterhin nicht gebaut** – bei 83 % Quote träfe es zu breit, und die Ursache ist erklärtermaßen nicht Bedarf, sondern Gewohnheit. **Re-Trigger/Bewertung bis S115:** dieselbe Messung wiederholen. Sinkt die Quote trotz Ein-Zeilen-Verdikt nicht, ist die Gewohnheits-These endgültig bestätigt und nur noch ein mechanischer Guard (B) wirksam. **Messwerkzeug (seit S114 regulär statt Wegwerf-Script):** `python3 -m prozesscode.tool-usage --filter`. Die Wrapper-Liste darin **nicht** erweitern – sie ist exakt die der Basislinie, sonst wird die Quote unvergleichbar. **Zwischenstand S114: 636 Läufe, 85 % gefiltert** (Juni 79 %, Juli 86 %) gegenüber der Basislinie 517 / 83 % – also nicht gesunken, eher leicht gestiegen. Die S115-Bewertung selbst steht noch aus.
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
- **S109-Entscheid (User): Empfehlung schärfen, eine Runde verlängern – bis S115.** Das vorab definierte Fehlschlag-Kriterium („kaum genutzt") wäre erfüllt, aber die Nullnutzung ist mehrdeutig: Der Hinweis stand bisher nur in `coding-guideline-typescript.md`, also in einem Dokument, das ein Agent liest *bevor* er arbeitet – nicht dort, wo die Entscheidung „grep oder LSP?" tatsächlich fällt. Zusätzlich ist LSP ein deferred Tool (erst via `ToolSearch select:LSP` ladbar), was eine echte Schwelle darstellt. Beides zusammen macht plausibel, dass „nicht angeboten" statt „nicht nützlich" gemessen wurde. **Maßnahme:** kurzer, konkreter LSP-Block direkt in die Prompts von `frontend-layer-implementer` (schreibt den TS-Code) und `code-quality-auditor` (stellt die „wo wird das noch verwendet?"-Fragen) – inklusive Ladehinweis und Kalt-Index-Caveat. Guideline-Notiz bleibt. **Bewertung S115 mit unveränderten Kriterien; dritte Nullrunde = verwerfen** (dann ist belegt, dass es nicht an der Sichtbarkeit lag). **Messwerkzeug (seit S114 regulär):** `python3 -m prozesscode.tool-usage --lsp` – schlüsselt jetzt nach Session-Art auf, was für dieses Urteil entscheidend ist: Nullnutzung in **implementierung**-Sessions ist ein Urteil über das Werkzeug, Nullnutzung in Drain-/Retro-Sessions nur eines über die Gelegenheit. **Zwischenstand S114: 8 Calls gesamt, unverändert gegenüber S109** – davon 7 im Aktivierungstest (einer tooling-Session zugeordnet) und **genau 1 in 23 implementierung-Sessions**. *Randnotiz:* `backend-layer-implementer` führt `LSP` in seinen `tools`, obwohl für C# kein Server läuft (Blocker #1359) – bewusst nicht angefasst, um das Messsetup nicht mitten in der Bewertung zu ändern.

## OBS-S109-1 – Datei-Lesen ist der mit Abstand größte Token-Posten und wächst mit der Codebasis
- Quelle: User + Orchestrator
- Status: IN BEOBACHTUNG bis S132 – Messung jetzt durchfuehrbar, Datenbasis noch zu duenn
- Impact: HOCH    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Aus der Phase-1-Messung zu OBS-S085-2 (23 Sessions mit Subagent-Einsatz inkl. 112 Subagent-Logs, ~23,5M Zeichen ≈ 5,9M Token-Proxy): **`Read` allein macht 49,5 % des gesamten Volumens aus** – mehr als alles andere zusammen. Bei Subagenten sind es 71,4 % ihres Tool-I/O. 1590 Aufrufe, Ø 7.317 Zeichen (Subagenten Ø 8.373). Zum Vergleich: alle Projekt-Wrapper-Scripts zusammen 8 % des Tool-I/O, Orchestrator↔Subagent-Kommunikation 8,6 % des Gesamtvolumens, Edit 7,9 % des Tool-I/O. Drei Detailbefunde: (1) **Nicht die Anzahl treibt das Volumen, sondern die Größe** – Re-Reads derselben Datei im selben Kontext sind nur 10,1 %; die Top-Dateien sind `Client/e2e/ingredients.spec.ts` (816k gelesen), `docs/kaizen/observations.md` (759k), `Client/src/pages/IngredientsPage.test.tsx` (754k), `docs/guidelines/coding-guideline-csharp.md` (694k), `Server.Tests/IngredientsEndpointsTests.cs` (682k). (2) **86,7 % aller Reads sind vollständig, nur 13,3 % gezielt** (`offset`/`limit`) – und im Fall „Datei wird anschließend editiert" ist der gezielte Read im Schnitt 4,6× kleiner (1.943 vs. 8.971 Zeichen) bei identischem Zweck; der Harness verlangt vor einem Edit einen Read, aber keinen vollständigen (in S109 mehrfach praktisch bestätigt). 17 % des Read-Volumens sind solche vollständigen Vor-Edit-Reads. (3) **Der Posten ist nicht stabil, er wächst mit der Codebasis**: pro Session von Juni auf Juli stieg `Client/`-Lesen von 20k auf 79k Zeichen, `Server/` von 22k auf 48k, während die Pflichtlektüre (`docs/guidelines`) mit 40k→48k nahezu flach blieb. Ergänzend: gezielte Extraktions-Scripte ersetzen die Voll-Reads bisher nicht, sondern kommen hinzu – `decisions.py`-Aufrufe stiegen von 34 auf 87 pro Monat, gleichzeitig stiegen die `adr.md`-Voll-Reads von 1,5k auf 12,3k je Session (die Datei hat 1.263 Zeilen, und wer eine ADR ergänzt, muss sie vorher lesen). Risiko: Der Effekt verschärft sich mit jedem Lauf, weil Test- und Codedateien monoton wachsen und jeder frisch startende Subagent sie vollständig liest.
- Entscheidung/Maßnahme: S124: Die fuer S120 geplante Re-Messung war prinzipiell nicht durchfuehrbar, nicht bloss unterlassen. read-breakdown.py aggregiert ueber alle Sessions; die Wirkung einer Maßnahme verduennt sich darin, bis sie unsichtbar ist. Die S123-Retro hatte das bereits diagnostiziert (CM-S114-2: "read-breakdown.py kennt kein --since") und das Kriterium auf "nach mindestens 3 Implementierungs-Laeufen seit S114" umgestellt, das fehlende Werkzeug aber nicht gebaut. Jetzt gebaut: _session_logs.session_datum liest den Tag aus dem ersten Zeitstempel des Logs - bewusst nicht aus der Datei-mtime, die den letzten Schreibzugriff beschreibt und beim Kopieren neu gesetzt wird; fehlt der Stempel, faellt die Session aus dem Fenster statt hineingeraten zu werden. read-breakdown.py bekommt --since YYYY-MM-DD analog zu tool-usage.py. Erste damit moegliche Messung (ab 2026-08-04) gegen den Gesamtwert aus 24 Implementierungs-Sessions: Anteil gezielter Reads auf Client/ 14 auf 34 Prozent, Server/ 14 auf 17, docs/guidelines 5 auf 22; mittlere Read-Groesse auf Client/ von 7339 auf 3557 Zeichen. Die Richtung stimmt, traegt aber keinen Nachweis: Das Script zaehlt zwar zwei Logs mit implementing-scenario-Signal, laut Session-Index lief S120 jedoch ueber zwei Kalendertage - es ist derselbe Arbeitszusammenhang in zwei Haelften, also EIN Lauf, und auf Client/ beruhen die 34 Prozent auf 15 Reads. Deshalb weiter in Beobachtung. Re-Trigger: erneut messen, sobald drei unterscheidbare Implementierungs-Laeufe seit S114 vorliegen (Kriterium aus CM-S114-2, jetzt erstmals pruefbar); S132 ist nur der Backstop. Nebenbefund fuer die naechste Messung: Die Zaehlung "Sessions" im Script ist die Zahl der Log-Dateien, nicht der Arbeitszusammenhaenge - eine ueber Nacht fortgesetzte Session zaehlt doppelt.
- Bezug: OBS-S085-2 (Messung stammt aus dessen Phase 1); OBS-S096-3 (Scripted-Access-Layer, Re-Trigger jetzt erfüllt)

---

## OBS-S110-1 – „Done"-Erkennung eines Laufs hängt am Test-Kommentar, nicht am grünen Test
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Testing
- Beobachtung: `next_run.py` wertet einen Lauf als erledigt, sobald der `// Szenario: <Titel>`-Kommentar in einer E2E-Spec vorkommt (DONE-Erkennung nach ADR-S041-7 Addendum S088); daraus speist sich auch die Auflösung von `{{NEXT_RUN}}` in `AGENT_MEMORY.md`. Der Kommentar entsteht aber bereits im äußeren Loop von `implementing-scenario`, wenn der E2E-Test absichtlich noch rot ist und kein Produktionscode existiert. In S110 real beobachtet: Nach einem WSL-Absturz mitten in run-9 zeigte `AGENT_MEMORY.md` beim Neustart als nächsten Lauf bereits run-11 an, obwohl von run-9 nur ein roter Test existierte – der tatsächlich laufende Lauf war aus dem Zustandssignal verschwunden. Risiko: Ein Agent, der nach einer Unterbrechung neu startet und dem Zustandsdokument folgt, überspringt einen angefangenen Lauf oder hält ihn für fertig; der Fortschritt wird systematisch überschätzt, weil das Signal an einem Artefakt hängt, das am Anfang statt am Ende des Laufs entsteht.
- Zusammen-erledigen: OBS-S117-1
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

---

## OBS-S112-4 – `eslint-run.py` meldet Fehlschlag bei null Errors
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: dauerhaft
- Kategorie: TOOLING    Kontext: Wrapper-Scripts
- Beobachtung: Auf unverändertem `main` endet `python3 -m prozesscode.eslint-run` mit „✗ ESLint: 3 Problem(e)" bei **0 Errors** und 3 Warnungen. Die Warnungen sind bewusst so eingestuft: `Client/eslint.config.js` setzt `max-params` und `max-lines-per-function` mit ausbuchstabierter Begründung auf `warn` statt `error`. Der Wrapper macht daraus ein Fehlschlag-Verdikt. Damit widersprechen sich Konfiguration und Werkzeug – entweder sind die Warnungen tolerabel, dann ist das ✗ unzutreffend, oder sie sind es nicht, dann steht die Regel-Einstufung falsch. Risiko: Ein Gate, das im sauberen Ausgangszustand rot ist, verliert seine Signalwirkung; ein echtes neues Problem geht im erwarteten Rot unter.
- Bezug: OBS-S112-2
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

---

## OBS-S112-5 – Bash-Allow-Liste hat keinen Weg, eine Dependency-Version zu ändern
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hooks
- Beobachtung: Die Allow-Liste erlaubt `npm run|audit|outdated|update|ci`. Keiner dieser Befehle kann eine Dependency-Version über die deklarierte Semver-Range hinaus verschieben: `update` bleibt innerhalb der Range, `ci` installiert aus dem Lockfile und schreibt es nicht. In S112 war ein Sprung von `react-router` 7 auf 8 nötig, weil die Advisory-behebende Version außerhalb von `^7` lag; er ließ sich ausschließlich über `# --allow-once` durchführen. Dependency-Aktualisierungen sind kein Einzelfall, sondern wiederkehrende Wartung. Risiko: Der Ausnahmemechanismus wird für Routinearbeit verwendet und stumpft dadurch ab.
- Zusammen-erledigen: OBS-S119-1
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

---

## OBS-S113-1 – Kein Ort für beschlossene, noch nicht gebaute OBS
- Quelle: Orchestrator
- Status: IN BEOBACHTUNG bis S136
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: `docs/AGENT_MEMORY.md` führte vier OBS (OBS-S111-1, OBS-S106-1, OBS-S106-2, OBS-S108-2) ausdrücklich als **Gate** vor dem nächsten `gherkin-workshop` – „Gate, nicht nur Priorität". Der Drain-Satz, den `obs-drain.py` am Session-Start ausgibt, sortiert die Wert-Lane rein nach Impact × Häufigkeit; alle vier tragen `× gelegentlich` und fielen deshalb aus der Top-6. Der vorgeschlagene Satz enthielt **keinen** von ihnen, und nichts im Satz wies darauf hin, dass eine externe Vorrangregel existiert. Aufgefallen ist der Konflikt nur, weil in dieser Session beide Quellen nebeneinander gelesen wurden – der Hook injiziert `AGENT_MEMORY.md` und den Drain-Satz zwar gemeinsam, aber unverbunden. Wer dem Drain-Vorschlag folgt, arbeitet einen fachlich korrekt priorisierten Satz ab und lässt das Gate trotzdem stehen; der nächste Workshop liefe dann in genau die Blindstellen, deretwegen das Gate gesetzt wurde. Verallgemeinert: Priorität wird an zwei Orten gebildet – im Script nach einer festen Formel, in `AGENT_MEMORY.md` nach Projektlage –, ohne dass der eine Ort vom anderen weiß.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: AUFGESCHOBEN (S126), erstmals – Datenlage reicht noch nicht. Diagnose praezisiert: Die Beobachtung beschrieb eine zweite Prioritaetsquelle (Gate in AGENT_MEMORY vs. Score im Drain). Die Ursache liegt tiefer – ein OBS hat zwei Lebensabschnitte, und nur der zweite braucht eine Faelligkeit. (1) Erfasste Form: traegt Information, aus der Aktionen abgeleitet werden. Empirie ueber 117 Eintraege (aktiv + Archiv): NULL Faelle, in denen ein offener OBS eine Ereignis-Faelligkeit gebraucht haette und dabei wirklich ein OBS war. Acht Eintraege tragen ueberhaupt einen Ereignis-Ausdruck; davon sind OBS-S101-3 und OBS-S108-5 mit Phase:MVP genau daran gescheitert, dass sie keine Prozess-, sondern Produkt-Themen waren, und zogen nach tech-debt.md um. Die restlichen sechs beschreiben in bereits aufgeloesten Eintraegen die Loesung, nicht eine Faelligkeit. (2) Umzusetzende Form: entschieden, aber nicht direkt gebaut – das ist ein Task, und dafuer gibt es fuer PROZESS-Themen keinen Ort (TD und OQ sind Produkt-Tracker). Genau ein klarer Fall im Bestand: OBS-S121-3 stand als IN BEOBACHTUNG bis S126 mit dem Entscheidungsfeld ENTSCHIEDEN in S125, nur noch zu bauen. Semantisch falsch, praktisch tragfaehig – der Preis ist, dass der Drain so einen Eintrag als faellige Wiedervorlage mit der Frage entscheiden vorlegt, obwohl die Entscheidung steht. VERWORFEN wurden: (d) Faellig-Anker fuer OBS analog TD/OQ – null Anwendungsfaelle, und die zwei mit Bedarf waren TD; (f) eigener Prozess-Task-Tracker – ein Fall in 117, der Preis waeren neue Rangfolge- und Ueberfaelligkeits-Entscheidungen. OFFEN GEHALTEN: (g) ein blosser Status-Wert ENTSCHIEDEN bis S<NNN>, mechanisch wie IN BEOBACHTUNG behandelt, im Drain-Satz aber als umsetzen, nicht entscheiden beschriftet – ein Regex und ein Label, kein neuer Tracker. WIEDERVORLAGE S136, KRITERIUM VORAB: Im Archiv zaehlen, bei wie vielen Eintraegen seit S126 die Entscheidung in einer Session fiel und die Umsetzung in einer spaeteren stattfand. 0 bis 1 weitere Faelle -> verwerfen, der Behelf genuegt. Ab 2 -> (g) bauen. Die Zaehleinheit ist bewusst der Drain und nicht die Session, denn nur im Drain wird eine OBS-Umsetzung beschlossen und damit aufschiebbar; als Mechanik gebaut wird der Zaehler nicht, er braeuchte die Session-Typ-Daten aus den Logs ausserhalb des Repos.

## OBS-S114-2 – Pflichtlektüre ist der zweitgrößte Leseposten und wird nie gefiltert
- Quelle: Orchestrator
- Status: IN BEOBACHTUNG bis S130
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Gemessen über 48 Sessions (`read-breakdown.py`): `docs/guidelines` und `docs/process` machen zusammen 21,4 % des gesamten Read-Volumens aus – in Implementierungs-Sessions sogar 27,9 %, hinter Client/ und Server/ der zweitgrößte Block. Die Einzelwerte sind hoch: Ø 12.234 Zeichen je Read auf `docs/guidelines`, 11.410 auf `docs/process`, und der Anteil gezielter Reads (mit offset/limit) liegt bei 3 % bzw. 7 % – praktisch jeder Aufruf liest das ganze Dokument. Ursache ist die Konstruktion: Die Agenten-Prompts schreiben diese Dateien als Pflichtlektüre vor, und jeder Subagent startet kalt. Anders als bei ADRs (`decisions.py` filtert nach Tags) und seit S114 bei Testdateien (`test-inventory.py` liefert eine Inventur) existiert für Guidelines kein Weg, gezielt nur den relevanten Abschnitt zu holen. Für die Gegenrichtung liegt eine Rechnung vor: Einen ADR in eine Guideline zu überführen kostet das 7- bis 12-Fache, weil eine Guideline von jedem Subagenten gelesen wird (180 Reads im Messzeitraum) statt on demand von den wenigen, die sie brauchen (14). Offen ist die umgekehrte Frage – ob selten gebrauchte Guideline-Abschnitte aus der Pflichtlektüre gelöst und abrufbar gemacht werden können, und woran „selten gebraucht" überhaupt erkennbar wäre. Der Block wächst mit +21 % über fünf Sessions langsamer als der Code, aber er schrumpft nicht.
- Entscheidung/Maßnahme: **Umgesetzt S125 in vier Teilen; Wirkung noch unbewiesen – deshalb IN BEOBACHTUNG statt UMGESETZT.** (1) Werkzeug: prozesscode/doc.py mit get <ANKER> / toc <datei> / audit, Anker-Index aus anchors.py importiert statt kopiert (eigenes Script, weil die Zielgruppe eine andere ist: Retrieval fuer arbeitende Subagenten vs. Integritaetspruefung fuer Autor/Hook). Scope-Regel (User-Entscheid): Ueberschriften-Anker bis zur naechsten gleichrangigen oder hoeherrangigen Ueberschrift inkl. Unterabschnitte; Absatz-Anker nur der zusammenhaengende Block. Die Alternativen sparen im Median ~200 Zeichen und erkaufen das durch stilles Abschneiden. (2) Doku-Umbau: 7 Stellen, an denen fette Absatz-Leads als Abschnitte fungierten, zu echten Ueberschriften gemacht (coding-guideline-csharp, review-workflow, gherkin-workshop, implementing-scenario) - Bestand jetzt 0 mit zurueckgelassenem Text. (3) Absicherung: doc.py audit sichtet alle 344 Anker (Arten fortsetzung/lose/fence/gross, Geschwister-Listenpunkte werden gezaehlt statt still abgezogen), Pflichtschritt in review-docs, Prinzip in principles.md 'Ein Anker ist eine Abrufeinheit'. (4) Wirksamkeit: Implementer-Agenten nennen doc.py konkret, Skills bleiben projektneutral (nur Verweis auf die CLAUDE.md-Navigation, damit sie portabel bleiben - User-Entscheid), neue Sektion 'Gezielt lesen statt Volldatei' in der SessionStart-Injektion (check-bash-permission.py --list). Bewusst NICHT umgestellt: die Review-Auditoren - sie haben kein Bash, und gezieltes Abrufen setzt voraus, dass man weiss wonach man sucht; ein Reviewer weiss das per Definition nicht (begruendet in review-code). **Wiedervorlage-Kriterium:** python3 -m prozesscode.read-breakdown --by-area erneut erheben, aber erst nach mindestens 3 weiteren Implementierungs-Sessions - vorher ist die Datenbasis zu duenn und der Vergleich wertlos (Ausgangswert S125: docs/guidelines 13,9 Prozent bei 6 Prozent gezielten Reads, docs/process 6,5 Prozent bei 9 Prozent, zusammen 20,4 Prozent; Referenz nach oben: docs/history liegt dank decisions.py bei 72 Prozent gezielt). Sind bis S130 keine 3 Implementierungs-Sessions gelaufen, bleibt der Eintrag IN BEOBACHTUNG und bekommt einen neuen Termin, statt auf duenner Basis entschieden zu werden.

## OBS-S116-3 – retro_report.py zeigt je Muster nur zwei Beispiel-Einträge, auch wenn es mehr sind
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Im Report-Abschnitt „Pattern-Kandidaten" sammelt retro_report.py:523 pro Tag-Tripel hoechstens zwei Beispiele, gibt aber die volle Anzahl aus. In der S116-Retro meldete ein Kandidat '3x' und listete zwei Eintraege; der dritte (LL-S114-3) war nur ueber einen eigenen grep auffindbar. Der kaizen-Skill verlangt an derselben Stelle ausdruecklich, vor jedem Vorschlag die konkreten Eintraege zu lesen, weil Cluster Tag-Kombinationen sind und keine semantischen Gruppen - die Kappung entzieht dieser Pflicht gerade bei den groessten und damit wichtigsten Mustern die Grundlage. Wer die Diskrepanz zwischen Zahl und Liste nicht bemerkt, haelt die zwei gezeigten Eintraege fuer das ganze Muster.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: CM-S064-2

## OBS-S117-1 – Geschriebene Szenarien ohne Lauf-Zuordnung haben keinen Weg in die Implementierung
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Gherkin
- Beobachtung: features/interaction.feature (3 Szenarien) und features/resilience.feature (5 Szenarien) enthalten geschriebene, freigegebene Szenarien ohne '# @run-N'-Kommentar. next_run.py behandelt ungetaggte Szenarien als eigenen Einzel-Lauf, erreicht sie aber nie, weil seine Story-Aufloesung ueber den @US-NNN-Feature-Tag laeuft und beide Dateien @CROSS-/@NFR-getaggt sind. Damit existiert kein Mechanismus, der diese Szenarien jemals als 'naechster Lauf' vorlegt. interaction.feature vermerkt 'Implementierungs-Scope: nach MVP' und verlangt vorher einen Workshop-Lauf – ein Plan, den kein Trigger aufruft. Sichtbar wurde es beim Bau des td-due-Moduls in S117: Drei TD-Eintraege ankern per Szenario: auf genau diese Szenarien und brauchen deshalb alle einen Phasen-Backstop, weil ihr eigentlicher Anker strukturell nicht eintreten kann. Die Waisen-TD ist damit nur das Symptom; die Waise ist das Szenario.
- Zusammen-erledigen: OBS-S110-1
- Entscheidung/Maßnahme: Teil-Umsetzung S117: Das Agenda-Modul `ungeplante-szenarien` macht die Szenarien sichtbar (Stub mit Anzahl, Volltext auf Abruf) und weist ihren Status ausdrücklich als *ungeklärt* aus – nicht als fällig. Damit ist die stille Unsichtbarkeit behoben; zusätzlich löst `next-run` nur noch story-gebunden auf, behauptet also keine Arbeit mehr, die die Feature-Datei zurückstellt. OFFEN bleibt der eigentliche Punkt: Es gibt weiterhin keine Regel, WANN querschnittliche Szenarien einen Lauf bekommen (interaction.feature verlangt vorher einen gherkin-workshop-Lauf, den kein Trigger aufruft). Solange das offen ist, brauchen TD-Einträge mit Szenario-Anker einen Phasen-Backstop.

## OBS-S117-2 – Injizierter Kontext erreicht den User nur ueber die Disziplin des Agenten
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Sonstiges
- Beobachtung: Der Session-Start injiziert Bloecke, die fuer den USER bestimmt sind – etwa die faelligen offenen Fragen, die laut Skill draining-observations 'dem User zur Klaerung vorgelegt' werden muessen. Injiziert werden sie aber in den Agenten-Kontext; ob sie beim User ankommen, haengt allein daran, dass der Agent sie weiterreicht. Kein Mechanismus prueft die Uebergabe. Belegt in S117 durch den User selbst ('Mir wurde nichts vorgelegt') und durch den Agenten in derselben Session: OQ-S083-1/-2 und OQ-S094-1 standen im Startblock und wurden nicht vorgelegt. Der Befund ist allgemeiner als offene Fragen – er betrifft jeden Block, dessen Zweck die Weitergabe an den User ist. Nebenbefund zur Wirksamkeit: Die Vorlage funktioniert (die Fragen erscheinen seit S115 jede Session), die Aufloesung nicht. Das ist ein eigener Befund und steht jetzt in OBS-S117-4 – die hier zunaechst notierte Begruendung ('kein Wiedervorlage-Termin') war falsch, ein optionales Faellig-Feld existiert seit S115.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S117-3 – principles.md ist der groesste Session-Start-Block und ungeprueft auf Knappheit
- Quelle: User
- Status: NEU
- Impact: GERING    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: principles.md ist mit 7.417 Bytes der groesste einzelne Block der Session-Start-Injektion – groesser als AGENT_MEMORY, dessen Volumen in S116/S117 als Problem behandelt wurde (OBS-S116-2). Der Block ist ein Immer-Block und wird bewusst nie unterdrueckt: Verhaltensregeln, die nicht geladen sind, fallen lautlos aus. Die Groesse ist damit nicht per Unterdrueckung adressierbar, sondern nur redaktionell. User-Einschaetzung S117: Der Text liesse sich kuerzen, und beim Hineinschreiben muesste rigoroser auf Knappheit ohne Verlust von Vollstaendigkeit geachtet werden. Bewusst nicht in S117 mitgemacht, weil das Kuerzen von Verhaltensregeln inhaltliche Arbeit ist und nicht als Nebenprodukt einer Tooling-Aenderung passieren sollte.
- Zusammen-erledigen: OBS-S123-1
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S119-1 – Deny-Text des Bash-Hooks lenkt in Einmalscripte, statt die Werkzeugfrage zu stellen
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Der Deny-Text von check-bash-permission.py (die Hinweise um `_SMART_DENY_HINTS` und den Standard-Deny-Text) bietet als Ausweg an: 'Für Ad-hoc-Logik: Script nach .claude/tmp/foo.py schreiben, dann python3 .claude/tmp/foo.py.' Der Text setzt damit stillschweigend voraus, dass der geblockte Befehl überhaupt Ad-hoc-Logik war, und bietet den Ausweg an, bevor die Vorfrage gestellt ist: Braucht es hier ein Script? Aufgetreten in S119: Ein zusammenhaengender, vollstaendig gelesener Textblock sollte aus einer Markdown-Datei geloescht werden. Das ist ein Edit-Fall. Ich habe reflexhaft einen Python-Heredoc in Bash versucht, der Hook hat geblockt, und ich bin dem angebotenen Ausweg direkt gefolgt und habe .claude/tmp/drop_oq.py geschrieben – ohne einen Schritt zurueckzugehen. Der Hook hat den Befehl korrekt geblockt und dann in eine zweite, ebenfalls unpassende Loesung gelenkt. Verschaerfend: Das Einmalscript war hier das riskantere Werkzeug. Ein Edit-Mismatch schlaegt fehl, waehrend index() + Slicing blind schneidet, ohne dass sichtbar wird, was rausfliegt. Der Deny-Text nennt kein Kriterium, wann ein Script gegenueber vorhandenen Tools und Scripten ueberhaupt gerechtfertigt ist.
- Vorprägung: Der User hat als Kriterium genannt: ein Script lohnt nur, wenn es effizienter und/oder weniger fehleranfaellig ist als die vorhandenen Tools – nicht deshalb, weil Bash geblockt wurde. Einmalscripte haetten vor allem im Standardprozess nur begrenzt Sinn; primaer sollen vorhandene Tools und Scripte genutzt werden. Naheliegende Richtung waere daher, den Deny-Text um diese Vorfrage zu ergaenzen, statt direkt den tmp-Ausweg anzubieten.
- Zusammen-erledigen: OBS-S112-5
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S120-3 – Der qa-check-Übergabe-Hash erzwingt einen zweiten Stryker-Volllauf, wenn nach dem ersten noch aufgeräumt wird
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Der Übergabe-Hash von qa-check.py bindet unter anderem den Inhalt des Working-Tree-Codes (compute_hash: TREE + Report-Hash + Testdateien + Suppressions). Das ist bewusst so gebaut und richtig – es macht den Hash manipulationsresistent und verhindert, dass ein Subagent nach dem Lauf noch etwas nachschiebt. Die Reibung entsteht am typischen Sessionende: Nach einem grünen Lauf fällt beim Review noch eine Kleinigkeit auf – ein Kommentar, eine Suppressions-Begründung, eine Umbenennung –, und der Hash ist ungültig. Weil der Hash nur aus einem Frisch-Lauf entsteht (--skip-stryker gibt bewusst keinen aus), kostet die Neu-Attestierung den vollen Stryker-Durchgang, in S120 rund zwei Minuten je Schicht, obwohl die Änderung das Mutations-Ergebnis nicht berühren kann. Das Script kann das nicht wissen: Ein inhaltsbasierter Hash unterscheidet semantisch neutrale Edits nicht von echten. Der Anreiz, den die Konstruktion damit setzt, ist der eigentlich unerwünschte – Aufräumarbeiten lieber zu unterlassen oder ungeprüft zu lassen, statt einen zweiten Volllauf zu bezahlen.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S122-1 – Drain-Trigger-Kalibrierung beruht auf einer gerechneten, nicht gemessenen Frequenz
- Quelle: Orchestrator
- Status: IN BEOBACHTUNG bis S132
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Hook/Script
- Beobachtung: Der in S122 eingefuehrte Drain-Trigger (Top-5-Summe >= 9 ODER >= 4 Eintraege aelter als 15 Sessions) entscheidet jede Session darueber, ob der Drain die Session beansprucht. Seine Schwellwerte sind aus Bestandsdaten abgeleitet, aber nie im Betrieb geprueft: Die tragende Groesse - 1,32 behandlungswuerdige Eintraege je Session - stammt aus einer Auswertung von S100 bis S121 und wurde mit der neuen Score-Skala rueckwirkend auf Eintraege angewandt, die unter der alten Skala erfasst und bewertet wurden. Daraus folgt die Erwartung, der Wert-Ausloeser feuere etwa jede dritte Session. Ob das eintritt, haengt an zwei Unbekannten: wie Agenten Impact und Haeufigkeit unter der neuen Skala tatsaechlich vergeben (GERING zaehlt jetzt 0, was die Vergabe veraendern kann), und wie oft Cluster entstehen, seit das Feld Zusammen-erledigen gepflegt wird. Faellt der Trigger zu selten, waechst der Rueckstau wieder; faellt er zu haeufig, ist genau die Verdraengung der Feature-Arbeit zurueck, gegen die er gebaut wurde. Beides zeigt sich erst an mehreren Sessions Betrieb und ist ohne bewusste Wiedervorlage nicht auffaellig, weil ein Trigger, der schweigt, keine Spur hinterlaesst.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: Nicht behandeln, sondern messen - und der Termin muss hinter der Abbauphase liegen: Bei aktuell 12 behandlungswuerdigen Eintraegen und rund 4 bis 5 je Drain-Session feuert der Wert-Ausloeser die naechsten etwa drei Drain-Sessions zwangslaeufig. Eine Messung davor bestaetigte nur den Rueckstau, nicht die Kalibrierung. Ab S132 zu pruefen: In wie vielen der vorangegangenen Sessions hat der Drain beansprucht (erwartet im Gleichgewicht etwa jede dritte), und ist der Backlog dabei gesunken? Weicht die reale Frequenz ab, sind TRIGGER_WERT und TRIGGER_ALT in obs-drain.py nachzuziehen, nicht das Modell. Re-Trigger vor dem Termin: Der Drain beansprucht nach dem Abbau drei Sessions in Folge, oder er schweigt fuenf Sessions am Stueck.

## OBS-S123-1 – Frisch geschriebene Doku wird nie auf Verdichtbarkeit geprueft
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Neu geschriebene Doku enthaelt regelmaessig Text, der ohne Informationsverlust deutlich kuerzer sein koennte - bemerkt wird das nur, wenn der User es ausdruecklich anstoesst. Der User berichtet, dass er diese Durchsicht wiederholt angefordert hat und das Ergebnis jedes Mal dasselbe war: Es liess sich einiges kuerzen. Befund einer solchen Durchsicht in S123: eine Format-Beschreibung dupliziert in genau dem Abschnitt, der einleitend 'hier nicht duplizieren' anordnet; dieselbe Session-Statistik in vier Dokumenten verteilt; CM-Nachtraege zwei- bis zweieinhalbmal so lang wie die bestehenden Nachtraege derselben Maßnahme. Kein Schritt im Session-Abschluss prueft die in der Session geschriebenen Texte auf Verdichtbarkeit. Dem Schreibenden faellt es im Moment des Schreibens strukturell nicht auf: Der Text entsteht aus dem gerade praesenten Kontext, in dem jede Erklaerung noetig scheint, und die Redundanz wird erst sichtbar, wenn man die fertigen Stellen nebeneinander liest. Kosten in zwei Richtungen: Dokumente, die bei jedem Session-Start injiziert werden (principles.md, CLAUDE.md, AGENT_MEMORY), kosten jede ueberfluessige Zeile dauerhaft; und ueberlange Tracker-Eintraege verduennen die Signale, die eine Retro aus ihnen ziehen soll. Verschaerfend: Kuerzen ist selbst fehleranfaellig - in derselben Session wurde beim Verdichten aus einer optionalen Angabe ein scheinbares Verbot (LL-S123-5), was fuer die Ausgestaltung mitbedacht gehoert.
- Vorprägung: User-Vorschlag: Die Durchsicht beim Session-Abschluss ansetzen, vor dem Commit - also wenn alle Dateien geschrieben sind. Moeglicherweise als eigener Skill, moeglicherweise in Teilen geteilt mit review-docs.
- Zusammen-erledigen: OBS-S117-3
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S124-2 – Befundlisten leben nur im Kontext und ueberstehen keinen eingehenden Bericht
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: In S124 lieferten vier Sichter-Subagenten ihre Befundlisten zeitversetzt. Ein bereits verifizierter Befund (process.md Noise-Filter) wurde nicht abgearbeitet, weil waehrend der Bearbeitung der naechste Bericht eintraf und die Arbeit dorthin sprang; der offene Punkt kam nie zurueck. Entdeckt erst zwei Runden spaeter durch eine Nachfrage des Users und eine Transkript-Analyse. Die Liste existierte nur im Gespraechsverlauf - es gab keinen Ort, an dem der Bearbeitungsstand je Befund sichtbar gewesen waere, und keinen Abgleich am Ende. Gilt fuer jede Situation mit mehreren parallel liefernden Subagenten, also auch fuer review-code und review-docs.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S125-2 – Tracker-Scripte koennen Erfassungsfehler nicht korrigieren
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: In S125 wurde eine Beobachtung falsch erfasst: Die Zielvorstellung des Users stand in der Beobachtung statt im Vorpraegungsfeld. Die Korrektur war mit den Scripten nicht moeglich - zwei Luecken traten zusammen auf. (a) obs.py set kennt kein --vorpraegung; das Feld kann nur bei add gesetzt werden. (b) obs.py set --beobachtung erweitert den vorhandenen Text, statt ihn zu ersetzen (Meldung: "Beobachtung erweitert aktualisiert") - fuer einen Nachtrag richtig, fuer eine Korrektur nicht, und die verdoppelte Fassung faellt nur auf, wenn jemand den Eintrag danach liest. Beides zusammen zwang zum Hand-Edit an observations.md, also genau zu dem Weg, den die Schreib-Scripte ersetzen sollen (Vor-Edit-Read der ganzen Datei, keine Formgarantie, kein Freigabe-Dialog mit Vorher/Nachher). Betrifft vermutlich auch lessons.py, td.py und oq.py, das wurde nicht geprueft.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S125-3 – Fuer prozesscode gibt es kein Mutation-Testing, obwohl sie den ganzen Workflow steuern
- Quelle: Orchestrator
- Status: UMGESETZT (S128)
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: TOOLING    Kontext: Mutation-Testing
- Beobachtung: Stryker ist im Projekt C#- und TypeScript-exklusiv (Stryker.NET, stryker-frontend). Fuer die rund 9.800 Zeilen Python unter prozesscode und .claude/hooks gibt es 981 Tests, aber keinen Mutations-Backstop - also nichts, was vakuoese Tests aufdeckt. In S125 wurde das konkret sichtbar: Beim Bau von doc.py wurden drei Mutationen von Hand gesetzt, zwei davon fingen die Tests, die dritte deckte eine Testluecke auf. Anschliessend fanden die Review-Auditoren vier weitere echte Fehler, die keine dieser Handmutationen getroffen hatte - alle an den Nahtstellen zwischen Regeln. Handmutationen treffen das, woran der Autor beim Mutieren denkt; das ist dieselbe Auswahl, die schon beim Testschreiben gewirkt hat. Die Frage ist offen, ob es fuer Python einen tragbaren Mutations-Runner gibt (mutmut, cosmic-ray) und ob sich die Laufzeit fuer eine Suite dieser Groesse rechnet.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: W3 (User, S128): direkt umgesetzt. Der Eintrag fragte nach einem Mutations-Runner; der User hat die Frage umgedeutet - nicht das Werkzeug fehlt, sondern eine Maßgabe fuer Prozess-Code ueberhaupt (keine Szenarien, keine Coverage-Vorgabe, kein Linter, keine Reviews - bisher freie Hand). Ergebnis ist docs/guidelines/coding-guideline-python.md: Sie schneidet Prozess-Code nach seinem FEHLERPROFIL statt nach abgeschwaechten Produktcode-Regeln - Klasse LAUT (Werkzeug crasht, faellt sofort auf, durch 1.000 Tests gedeckt) gegen Klasse STUMM (Guard laeuft fehlerfrei und prueft trotzdem nichts). Was daraus folgte: ruff mit begruendeter Regelauswahl plus PostToolUse-Automatik; Gegenprobe-Pflicht beim Bau jedes Guards; Auslöse-Protokoll (guard_log.py) mit Retro-Sichtung (guard-stats.py); Coverage als Metrik ohne Gate (coverage-run.py, Ist 73 Prozent); jscpd um Python erweitert (0,25 Prozent nach Refactoring). Mutation-Testing selbst wurde BEWUSST zurueckgestuft und steht als solches in der Guideline: Es adressiert Klasse LAUT, die bereits gedeckt ist. Beleg aus derselben Session - der einzige echte Fund war ein zip() ohne strict=, das eine Regression bei ungleich langen Listen still falsch rechnen liess; gefunden hat ihn der billige Linter, keine Mutation, denn der Fehler lag in einer fehlenden Zusicherung und nicht in einer Bedingung. Offen und NICHT Teil dieses Eintrags: das Review-Stufenmodell fuer Prozess-Code und die Einbindung von mutmut (installiert, nicht verdrahtet) - beides gehoert in die naechsten Prioritaeten, nicht in diesen Tracker.

## OBS-S125-4 – Review-Auditoren koennen ihre Findings nicht verifizieren, weil ihnen Bash fehlt
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Review
- Beobachtung: Die Review-Auditoren haben als Tools nur Read, Grep, Glob (+LSP) - kein Bash. Das ist bewusst so: Die Tool-Liste ist der Mechanismus, der garantiert, dass ein Auditor ausschliesslich Findings erzeugt und nichts aendert. Der Preis wurde in S125 dreimal sichtbar. Ein Auditor verbrauchte ein ganzes Finding darauf, dass er doc.py audit nicht ausfuehren konnte und die behaupteten Zahlen daher nicht bestaetigen koenne - Arbeit, die der Orchestrator laengst getan hatte. Zwei Auditoren mussten Aussagen ausdruecklich als unverifiziert kennzeichnen; die Verifikation fiel auf den Orchestrator zurueck. Und ein Auftrag in workflow-auditor.md war schlicht tot: Der Agent sollte decisions.py aufrufen, was er nie konnte (in S125 korrigiert). Das steht in Spannung zum Projektprinzip Empirie vor Behauptung: Wir verlangen von den Auditoren Belege und nehmen ihnen zugleich die Mittel, welche zu erbringen. Der Nutzen waere nicht nur gezieltes Lesen, sondern vor allem, dass ein Auditor die Testsuite laufen lassen und seine Behauptung belegen koennte. Ungeprueft ist die Kernfrage, ob der PreToolUse-Hook den aufrufenden Agenten ueberhaupt unterscheiden kann - davon haengt ab, ob eine engere Allow-Liste je Agent moeglich ist oder ob die Findings-Garantie von einem Mechanismus zu blosser Disziplin wuerde.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S126-1 – Prozessarbeit verdrängt Implementierung, ohne erkennbare Konvergenz
- Quelle: User
- Status: IN BEOBACHTUNG bis S145
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: Rund die Haelfte der Sessions geht an Prozessarbeit statt an Implementierung, und ein Rueckgang ist nicht erkennbar. Gemessen in S126. (a) ZUFLUSS ins OBS-Backlog ueber S111-S125: 7,27 Score je Session, Median der Session-Summe 6,0; je Eintrag Mittel 2,60 und Median 2,0; 67 Prozent der neuen Eintraege sind behandlungswuerdig (Score >= 2), nur 10 Prozent GERING. Die Trigger-Schwelle des Drains liegt bei 9 auf den fuenf staerksten Einheiten - ein Drain, der den Bestand auf ~8 drueckt, ist nach etwa anderthalb Sessions Zufluss wieder ausgeloest. Daraus folgt: Drain in rund 40 Prozent der Sessions, Retro mit ~12 Prozent dazu (Ist-Kadenz 8,3 Sessions; Modell aus dem Jenga-Gewicht 6,6). (b) GEGENCHECK ueber S085-S125: 2,85 Eintraege je Session erfasst gegen 2,44 aufgeloest - der Bestand wuchs um 0,4 je Session, was die heute offenen 17 erklaert. (c) KONVERGENZ: LL-Gewicht je Session ueber vier vollstaendige Perioden 5,9 / 8,3 / 14,7 / 16,4 (steigend); OBS-Score je Session nach der Rubrik-Kalibrierung von S107 6,89 / 7,43 / 6,00 (flach). In keiner der beiden Reihen ein Rueckgang. DREI STOERFAKTOREN, die einen Anstieg auch ohne echte Zunahme erzeugen koennen: die Impact-Rubrik wurde in S107 neu kalibriert und der OBS-Vergleich laeuft quer darueber; die Erfassung wurde ueber die Zeit mechanisiert (mehr erfasste Reibung ist nicht mehr Reibung); und Prozessarbeit erzeugt Prozess-Beobachtungen, also eine Rueckkopplung ueber den Session-Mix. VIERTER, NICHT HERAUSGERECHNETER STOERFAKTOR (User-Hinweis bei der Erfassung): Alle Raten sind je SESSION gemessen, aber Sessions sind unterschiedlich gross. Dieselbe Arbeit auf zwei Sessions verteilt halbiert jede Rate, ohne dass sich etwas geaendert haette. Die Auswertung unterstellt im Mittel gleich grosse Sessions - ueber lange Zeitraeume vertretbar, fuer den Vergleich einzelner Perioden verrauscht. Wer den Trend belastbar entscheiden will, braucht ein Groessenmass je Session (Volumen, Dauer oder Commits) als Normierung. ZU ENTSCHEIDEN ist zweierlei, und beides haengt zusammen: Ist der Prozess-Anteil so gewollt, und konvergiert die Reibung? Konvergierte sie, loeste sich die Verdraengung von selbst - deshalb ein Eintrag und nicht zwei. Kriterium fuer die Konvergenzfrage: Sinkt der OBS-Score-Zufluss ueber drei aufeinanderfolgende Retro-Perioden nach S107? Bisher drei Datenpunkte, flach; in zwei bis drei weiteren Perioden entscheidbar. Hebel fuer den Anteil, falls er nicht gewollt ist: strenger erfassen, TRIGGER_WERT anheben, oder mehr Eintraege je Drain-Session entscheiden.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: K1 (User, S128): weiter beobachten, nicht jetzt entscheiden. Das Konvergenzkriterium des Eintrags - sinkt der OBS-Score-Zufluss ueber drei aufeinanderfolgende Retro-Perioden nach S107 - hat bisher drei Datenpunkte (6,89 / 7,43 / 6,00, flach). Bei der Ist-Retro-Kadenz von 8,3 Sessions sind zwei weitere Perioden um S145 erreicht, dann ist die Konvergenzfrage entscheidbar. Zusatzindiz aus S128, ausdruecklich keine Messung des Session-Anteils: Codevolumen Produkt (C#+TS inkl. Tests) 5.522 Zeilen gegen Prozess-Infrastruktur 37.381 Zeilen (23.944 Python + 13.437 Markdown), Verhaeltnis 6,8:1. Re-Trigger vor Termin: wenn eine Retro-Periode einen deutlichen Rueckgang oder Anstieg des OBS-Score-Zuflusses zeigt. Offen geblieben und Teil der Wiedervorlage: der vierte Stoerfaktor (Raten je Session ohne Groessennormierung) ist nicht behoben - ohne Groessenmass je Session bleibt auch der Befund in S145 verrauscht.

## OBS-S126-2 – Repo-Wurzel wird an drei Stellen verschieden bestimmt
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Die Wurzel des Repos wird in .claude/ auf drei Arten ermittelt, und eine davon kann etwas, das die anderen nicht koennen. (1) _util.REPO_ROOT liest CLAUDE_PROJECT_DIR aus der Umgebung und faellt erst dann auf den Dateipfad zurueck; genutzt von den Toolchain-Wrappern und _session_logs. (2) repo_kontext.repo_root() rechnet ausschliesslich ueber Path(__file__).parents[2] und ignoriert die Umgebungsvariable; daran haengen alle fuenf Erfassungswerkzeuge (obs/lessons/td/oq/adr). (3) Rund zehn Inline-Berechnungen in anchors.py, next_run.py, qa-check.py, check-atdd-gate.py, check-dangling-refs.py, check-ref-direction.py, check-e2e-scenario-ref.py, dotnet-stryker.py, stryker-frontend.py und stryker-parse-survivors.py, teils als parents[2], teils als parent.parent.parent, teils als abgeleitete Konstante. Das ist dasselbe Divergenz-Muster wie CM-S116-1: zwei Implementierungen desselben Begriffs, von denen eine einen Fall kennt und die andere nicht. Aufgefallen ist es in S126 beim Herausloesen von repo_kontext.py aus obs_parse.py; ein Schaden ist bisher NICHT beobachtet - er traete auf, sobald ein Script aus einem anderen Arbeitsverzeichnis oder einem git-Worktree laeuft, wo CLAUDE_PROJECT_DIR und der Dateipfad auseinanderfallen. Zu klaeren ist, ob die Umgebungsvariable ueberhaupt die maszgebliche Quelle sein soll; ist sie es, gehoert eine einzige Implementierung an einen Ort und die uebrigen Stellen ziehen nach. Ist sie es nicht, gehoert sie aus _util entfernt, damit nicht zwei Begriffe unter demselben Namen laufen.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S127-1 – Die vier Maßnahmen der Belegkette sind nach Fehlerform geschnitten, nicht nach Mechanisierbarkeit
- Quelle: User + Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: CM-S064-1, CM-S116-1, CM-S095-2 und CM-S127-1 besetzen je eine Bruchstelle derselben Kette (Frage - Erhebung - Aussage). Der Schnitt ist diagnostisch: er sagt, WO die Kette reisst. Fuer die Maßnahme ist er unergiebig, denn alle vier lauten woertlich "Prinzip in principles.md dokumentiert" - keine hat ein Poka-yoke. Folge: keine kann je BEWAEHRT werden (irgendein Zweig faellt immer zurueck) und keine kann obsolet werden; sie erzeugen in jeder Retro Nachtrags-Ritual ohne Entscheidung. CM-S064-1 wurde seit S064 dreimal verbreitert und wird zum Auffangbecken. Zugleich zerfallen die sieben Rueckfaelle auf CM-S116-1 in zwei Gruppen mit voellig verschiedenen Antworten: solche, die ein Werkzeug fangen koennte (LL-S125-2 zeigt, dass prozesscode/ kein Mutation-Testing hat, obwohl Handmutationen dort nachweislich deckungsgleich mit den vorhandenen Tests waren; LL-S123-7 und LL-S126-7 sind beide "gegen eine Fixture statt gegen das echte Artefakt geprueft"), und solche, die reines Urteil bleiben (LL-S123-5: Kuerzen aendert die Bedeutung eines Textes). Ein Schnitt nach Mechanisierbarkeit statt nach Fehlerform wuerde diese beiden Gruppen trennen und der ersten eine abhakbare Bauliste geben. Zu klaeren ist auch, was mit den Rueckfall-Chroniken der vier bestehenden Eintraege geschieht - sie neu zu verteilen ist Handarbeit, und ein Fehler dabei ist still.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: CM-S064-1, CM-S095-2, CM-S116-1, CM-S127-1

## OBS-S127-2 – Wegwerf-Auswertung über python3-stdin ist geblockt, obwohl der Heredoc-Body als Text gilt
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Bash/Permission
- Beobachtung: In der S127-Retro wurde das Deny-Log für S123-S126 ausgewertet: 144 Einträge, davon 96 gewollt (80 WRITE_ACCESS als vorgesehene Freigabe für Projektdokumente, 14 ONE_TIME, 2 destruktiv/indirekt). Es bleiben 48 vermeidbare Denies in vier Sessions, rund 12 je Session. Die erkennbare Hauptklasse ist die Wegwerf-Auswertung über stdin: python3 - mit Heredoc. Erlaubt ist nur python3 <scratchpad>/<script>.py, also der Umweg über eine Datei. Die Spannung liegt darin, dass die Allow-Liste den Heredoc-Body ausdrücklich als Text und nicht als Befehl behandelt und Heredocs als Zusammensetzung erlaubt – der stdin-Python-Aufruf ist damit nicht offensichtlich derselbe Fall wie eval oder bash -c, die wegen nicht inspizierbarer Herkunft gesperrt sind. Ob hier eine Lücke oder eine bewusste Grenze vorliegt, ist offen und in dieser Session nicht entschieden worden. Dazu kommt read-only-Kleinkram, der nicht auf der Liste steht und je einzeln blockte: git config --get, fold, rev. Zu klären ist auch, ob 12 vermeidbare Denies je Session überhaupt behandlungswürdig sind oder als Preis der Absicherung akzeptiert werden.
- Zusammen-erledigen: OBS-S119-1
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: CM-S078-1

## OBS-S128-1 – test-inventory.py kennt kein Python und sieht damit die groesste Testsuite des Repos nicht
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: In S128 beim Erweitern von test_session_agenda.py aufgefallen. 'test-inventory.py tests/test_session_agenda.py' antwortet 'keine Tests erkannt (unterstuetzt: .cs, .ts/.tsx/.js/.jsx)'. Das Werkzeug steht in der CLAUDE.md-Navigationstabelle als Antwort auf 'Was steht schon in einer Testdatei?' und deckt die 1.021 Python-Tests unter tests nicht ab - also die groesste Testsuite im Repo. Wer es nutzt, faellt auf grep zurueck oder liest die Volldatei, was der Zweck des Werkzeugs gerade vermeiden soll. Die Meldung ist immerhin ehrlich (sie nennt die unterstuetzten Endungen), der Ausfall ist also nicht stumm - deshalb GERING und nicht hoeher. Offen ist, ob sich der Aufwand lohnt: Python-Testnamen sind per 'def test_' trivial zu finden, der Mehrwert gegenueber grep liegt allein im Zeilenbereich je Test.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S129-1 – Pfad-Normalisierung des Bash-Hooks bricht cd, wenn das Arbeitsverzeichnis nicht der Repo-Root ist
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Der PreToolUse-Bash-Hook ersetzt jeden absoluten Repo-Pfad im Befehl durch den relativen (OBS-1, damit Befehle mit absolutem Pfad nicht am Deny fuer 'python3 mit absolutem Pfad' haengenbleiben). Ein nackter Repo-Root wird dabei zu '.' – aus 'x' wird 'cd . && x'. Das ist genau dann falsch, wenn das Arbeitsverzeichnis der Bash-Session nicht der Repo-Root ist: Der Befehl landet dann in irgendeinem Unterverzeichnis statt im Repo-Root, und zwar lautlos – der Hook meldet die Ersetzung nur als additionalContext, der Befehl selbst laeuft mit Exit 0 durch, nur am falschen Ort. In dieser Session trat es beim Aufbau der Hook-Registrierung auf, wo genau diese Konstruktion gebraucht wird.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S129-2 – Der Wrapper-Filter-Strip des Bash-Hooks schneidet in verketteten Befehlen die nachfolgenden Befehle mit ab
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Ruft man einen Projekt-Wrapper mit nachgelagertem Filter auf ('python3 -m prozesscode.ruff-run | tail -5'), entfernt der Hook den Filter und laesst den Wrapper allein laufen – gewollt, weil die Wrapper nur ein Verdikt ausgeben und ein Filter es abschneiden koennte. Der Strip greift aber auf den GANZEN Befehlsstring: Steht hinter dem Filter noch eine weitere Verkettung ('wrapper | tail -5 && python3 -m prozesscode.anchors check'), faellt der zweite Befehl mit weg. Ausgefuehrt wird also weniger als angefordert, und die Rueckmeldung sagt nur, dass ein Filter entfernt wurde – nicht, dass ein Befehl verschwunden ist. Wer die Ausgabe nicht Zeile fuer Zeile mit dem eigenen Befehl vergleicht, haelt den zweiten Schritt fuer erledigt.
- Zusammen-erledigen: OBS-S129-1
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S129-3 – Die Session-ID der Bash-Umgebung weicht von der ab, unter der Background-Tasks ihr Scratchpad anlegen
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Bash/Permission
- Beobachtung: Der Bash-Hook loest das erlaubte Scratchpad-Verzeichnis aus CLAUDE_CODE_SESSION_ID auf. In dieser Session stand dort 3b72d930-..., waehrend Background-Tasks ihre Ausgabe und ihr Scratchpad unter 4cdd1a7e-... ablegten. Ein Script, das im Task-Scratchpad liegt, faellt damit aus dem erlaubten Pfad und wird mit 'python3 mit absolutem Pfad ist nicht erlaubt' geblockt - obwohl es genau der Ort ist, den das Harness selbst fuer diese Ausgabe gewaehlt hat. Umweg war, die Datei stattdessen unter der aelteren Session-ID abzulegen. Die Divergenz trat nach einem Neustart von Claude Code mitten in der Sitzung auf.
- Zusammen-erledigen: OBS-S129-1, OBS-S129-2
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
