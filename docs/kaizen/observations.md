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

## OBS-S111-3 – Stryker-Wrapper meldet Survivors ohne Block-Ende und ohne Coverage-Angabe
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Mutation-Testing
- Beobachtung: `format_mutant_group` in `.claude/scripts/_stryker_report.py` gibt pro Survivor genau drei Felder aus: `location.start.line`, `mutatorName` und `replacement`. Der Stryker-JSON-Report enthält daneben `location.end`, `location.start.column`, `coveredBy`, `killedBy` und `id` – die werden verworfen. Bei zeilenbezogenen Mutatoren (Statement, Equality, String) genügt die Startzeile; bei `Block removal mutation` ist sie strukturell mehrdeutig: Liegt die Zeile in einem `try`/`catch` mit verschachtelten Blöcken, geht aus „Zeile 304 → {}" nicht hervor, welcher der Blöcke entfernt wurde. Ebenso fehlt die Angabe, ob den Mutanten überhaupt ein Test abdeckt (`coveredBy` leer vs. gefüllt) – die Unterscheidung „Test deckt ab, tötet aber nicht" gegen „gar nicht ausgeführt" ist für die Reaktion entscheidend, steht im Report und geht in der Ausgabe verloren. In S111 eingetreten: Der Backend-Fix-Subagent schrieb für genau diese Felder zwei Wegwerf-Scripte unter `.claude/tmp/`; in derselben Session setzte der Orchestrator `jq` auf denselben Report an; und in einer früheren Session existierte bereits ein `.claude/tmp/check_stryker_scope.py` – drei Ad-hoc-Auswertungen desselben Reports über drei Sessions. Für die Wiedervorlage von OBS-S085-3 relevant: Dessen S115-Messung zählt nachgelagerte Filter auf Wrapper-Output (`| grep`, `| tail`) und würde diese Fälle nicht erfassen, weil sie als eigenständige Script-Läufe auftreten.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: OBS-S085-3

## OBS-S111-4 – Bash-Hook blockt erlaubte Befehle, sobald sie verkettet, umgeleitet oder als Heredoc formuliert sind
- Quelle: Subagent + Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: `check-bash-permission.py` dokumentiert „Verknüpfung mit `|`, `||`, `&&`, `;` ist erlaubt – jedes Segment wird einzeln geprüft". In der Praxis scheitern regelmäßig Aufrufe, deren fachlicher Kern erlaubt ist: ein Heredoc (`python3 - <<'EOF'`) wird abgewiesen, ebenso `cat > datei <<'EOF'`, und ein Compound kippt vollständig, sobald ein einzelnes Segment nicht auf der Liste steht – auch wenn dieses Segment read-only ist. In S111 dreimal eingetreten: Der Frontend-Implementierer meldete es unaufgefordert als Reibung (`git stash`, Redirect-Ziele) und wich auf den bereits gelesenen Transcript-Zustand aus; der Backend-Fix-Subagent musste seine Wegwerf-Auswertung über zwei zusätzliche `Write`-Aufrufe umleiten; der fortsetzende Orchestrator lief beim Aufräum-Check (`ls … && git check-ignore …`) in dieselbe Sperre. Die Folge ist keine Blockade, sondern ein Umweg: Agenten bauen Ersatzkonstruktionen, die dasselbe Ergebnis liefern. Damit misst das Deny-Log an dieser Stelle nicht abgewehrte Absichten, sondern Formulierungsvarianten – und die Umwege kosten Tool-Aufrufe, ohne dass ein Sicherheitsgewinn entsteht.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: OBS-S085-3

## OBS-S111-2 – ADR-Übergabe an Schicht-Subagenten skaliert nicht mehr mit der Zahl der ADRs
- Quelle: User + Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: implementing-scenario
- Beobachtung: `implementing-scenario` (Schritt 0 Punkt 4 und der Message-Block in Schritt 1–3) schreibt vor, die vollständige `--full`-Ausgabe von `decisions.py list --tag scope:cross-cutting` und `--tag story:us-NNN` in **jede** Subagenten-Message zu kopieren. In S111 gemessen: 74.311 Zeichen allein für `scope:cross-cutting` (60 ADRs) plus 22.655 für `resource:ingredients` – bei zwei Schicht-Subagenten pro Full-Stack-Lauf also grob 50k Tokens, von denen der weit überwiegende Teil mit dem Lauf nichts zu tun hat. Die Vorschrift stammt aus einer Zeit mit deutlich weniger ADRs und wächst monoton mit jedem weiteren Eintrag, während der pro Lauf tatsächlich relevante Anteil ungefähr konstant bleibt. In S111 wurde nach Rückfrage bewusst davon abgewichen (kompakte Gesamtliste + gezielt vollständige Auszüge), was den Konflikt zwischen Vorschrift und Praxis offenlegt statt ihn zu lösen.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: OBS-S109-1

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
- **S111-Ergänzung – Messlücke für Klasse 3 (s. OBS-S111-3):** Die S115-Messung zählt Wrapper-Läufe *mit nachgelagertem Filter*. Klasse-3-Fälle (der Wrapper liefert die Information gar nicht) treten aber teils nicht als `| grep` auf, sondern als eigenständiges Ad-hoc-Script auf dem Roh-Report – in S111 dreimal belegt für den Stryker-JSON-Report. Diese Fälle sinken in der Filter-Quote nicht, weil sie nie darin auftauchten; die Quote allein kann die Gewohnheits-These daher nicht bestätigen, solange Klasse 3 ungemessen bleibt.

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

## OBS-S091-2 – Wrapper-Aufrufpfad cwd-relativ, kollidiert mit Projekt-Tooling-cwd
- Quelle: Agent
- Status: IN BEOBACHTUNG bis S115
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Die Wrapper liegen im Repo-Root (`.claude/scripts/`) und lösen ihren Root intern via `_util.REPO_ROOT` auf — aber der **Aufrufpfad** `python3 .claude/scripts/foo.py` ist cwd-relativ. Projekt-Tooling (`npm`/`dotnet`/`vite`) zieht die Shell in `Client/`/`Server/`-Subdirs; der nächste Wrapper-Aufruf scheitert dann mit „No such file" (S091: beide Subagenten + Orchestrator betroffen).
- Entscheidung/Maßnahme: **Aufgeschoben (S109-Drain) bis S115 – die Ursache wurde stattdessen entfernt.** Der mit Abstand häufigste Grund, den Repo-Root zu verlassen, war ein blockiertes `npm --prefix Client run …`, das ein `cd Client` erzwang; `--prefix` ist jetzt erlaubt (s. OBS-S108-4 b), womit der Auslöser wegfällt. Der direkte Fix – der Bash-Hook präfixt Wrapper-Aufrufe via `updatedInput` mit `cd <repo-root> &&` – wurde bewusst **nicht** gebaut: er wäre die Umkehrung der im selben Hook bestehenden Normalisierungsregel (absolute Repo-Pfade → relativ), also zwei gegenläufige Rewrite-Regeln nebeneinander, für ein seit 18 Sessions nie eskaliertes GERING-Problem. Geprüft und verworfen wurde auch der Weg über `$CLAUDE_PROJECT_DIR`: die Variable ist im Bash-Tool leer (nur in Hooks gesetzt), ein Rewrite müsste den Repo-Root literal einsetzen. **Re-Trigger:** ein Wrapper-Aufruf scheitert erneut an falschem cwd, obwohl `--prefix` verfügbar ist – dann ist belegt, dass es noch andere cd-Gründe gibt, und der Hook-Rewrite ist gerechtfertigt.
- Bezug: —

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
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Schritt 4 („Mechanische Verifikation") ist vollständig darauf aufgebaut, dass der Schicht-Subagent in seinem Return einen frischen `=== VERIFIKATIONS-HASH ===`-Block liefert, den der Orchestrator per `qa-check.py --verify` prüft. Der Skill beschreibt keinen Fall, in dem dieser Return ausbleibt, weil der Subagent-Prozess endet, bevor er antworten konnte. In S110 eingetreten: ein WSL-Absturz beendete Orchestrator und Subagent gleichzeitig; nach dem Neustart lagen fertiger Produktionscode und ein durchgeführter Refactor im Working Tree, aber kein Hash und keine Aussage darüber, welche Schritte noch offen waren. Der Zustand ließ sich nur rekonstruieren, weil der Test-Freigabe-Anker als git-Blob außerhalb des Agentenkontexts persistiert war und der Refactor-Diff sich nachträglich dagegen auditieren ließ. Risiko: Ohne beschriebenen Weg improvisiert jeder Orchestrator anders – im schlechteren Fall wird der Subagenten-Stand ungeprüft übernommen oder der ganze Lauf verworfen und neu begonnen. **Zweiter Vorfall (S111), andere Ursache, neuer Schadenstyp:** Diesmal kein Absturz, sondern das Session-Limit – es beendete Orchestrator und **beide** Nachbesserungs-Subagenten innerhalb weniger Minuten. Der Backend-Agent hatte seine Arbeit vollständig abgeschlossen und alle Checks grün, kam aber nicht mehr zum Absenden; der Frontend-Agent stand im laufenden `qa-check`. Neu gegenüber S110 ist die Art des Schadens: Beide Aufträge trugen die Auflage „keine neue ADR anlegen – melde mir im Return, was dokumentiert gehört". Mit dem Return ging diese Meldung verloren, und im Produktionscode blieb ein Kommentar zurück, der auf ein ADR-Addendum verwies, das nie geschrieben wurde. Dieser tote Verweis wäre in den Commit gegangen; der Verifikations-Hash hätte ihn nicht aufgedeckt, weil Code, Tests und Stryker grün waren, und auch `qa-check` Check 6 nicht, weil die referenzierte ADR-ID existiert – nur der Abschnitt darin nicht. Die Rekonstruktion gelang, weil die Subagenten-Logs vollständig persistiert sind, kostete aber rund 15 Aufrufe, bevor überhaupt feststand, welche Arbeit noch offen war. Bemerkenswert: Die Auflage „keine ADR selbst anlegen, stattdessen im Return melden" macht den Return zur einzigen Brücke für eine Doku-Pflicht – fällt er aus, verschwindet die Pflicht spurlos, während der Code den Verweis darauf behält.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

---

## OBS-S112-1 – `tech-debt.md`-Feld „Behebung/Trigger" trägt zwei Bedeutungen in einem
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: tech-debt
- Beobachtung: Die Eintrags-Vorlage im Kopf von `docs/tech-debt.md` definiert das Feld als „<geplante Behebung **oder** auslösende Bedingung>". Ein Eintrag erfüllt die Vorlage damit bereits, wenn er nur beschreibt, *wie* behoben wird – ohne jede Angabe, *wann* das geschehen soll. Beim vollständigen Durchgang durch die Datei in S112 trat das mehrfach auf: Einträge trugen ausformulierte Behebungswege und als Auslöser entweder eine Formulierung, die keinen realen Zeitpunkt benennt („eigene UX-Foundation-Aufgabe", „bei der ersten Härtungs-/Resilience-Aufgabe" – solche Aufgaben stehen in keinem Plan), oder eine, die verfallen war, ohne je gefeuert zu haben („mit run-4", während alle Läufe der Story längst implementiert sind). Im selben Durchgang ist es dem Orchestrator beim Neuschreiben eines Eintrags erneut unterlaufen, obwohl das Muster kurz zuvor besprochen worden war. Risiko: Einträge sehen vollständig aus, obwohl niemand einen Zeitpunkt schuldet; sie bleiben unbegrenzt liegen, ohne dass beim Lesen etwas auffällt.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

---

## OBS-S112-2 – Das Prioritätsfeld in `tech-debt.md` steuert nichts
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: tech-debt
- Beobachtung: TD-S089-1 trägt seit Session 089 die Priorität „Hoch" samt der Feststellung, dass das Branch-Coverage-Gate aus NFR/DoD dadurch wirkungslos ist. Beim Durchgang in S112 – rund 22 Sessions später – war der Eintrag unverändert und unbearbeitet, und seine technische Beschreibung zeigte auf einen Stack-Stand, den es längst nicht mehr gibt. Dieselbe Form zeigte sich außerhalb der Datei: `npm audit` meldete über mehrere Sessions hinweg Advisories, darunter vier für eine Produktions-Dependency, ohne dass daraus etwas folgte. Gemeinsam ist beiden, dass das Signal korrekt, sichtbar und dauerhaft vorlag – nur folgte keine Handlung. Risiko: Das Feld erzeugt den Eindruck einer Steuerung, die es nicht ausübt; „Hoch" und „Niedrig" unterscheiden sich im Ergebnis nicht.
- Bezug: OBS-S112-1
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

---

## OBS-S112-3 – Kein anerkannter Weg für Infrastruktur-Arbeit ohne treibendes Szenario
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: TDD
- Beobachtung: Der Prozess verlangt für jeden Zweig ein ausübendes Szenario – Begründung ausbuchstabiert in TD-S110-1(c): vorab umgesetzt entstünde ein Zweig, den kein Szenario ausübt → Stryker-Survivor → Suppression außerhalb des treibenden Szenarios, genau die Konstellation, die ADR-S083-2 vermeiden will. Für querschnittliche Infrastruktur existiert jedoch keine Kategorie: Ein globaler Exception-Handler, ein Request-Body-Limit oder ein try/finally in einer Middleware werden von keinem Nutzer-Szenario getrieben. In S112 zeigte sich, dass vier solcher Punkte gemeinsam auf eine Aufgabe warteten, die in keinem Plan existiert. ADR-S106-3 kennt eine verwandte Ausnahme (Querschnitts-Protokoll-/Invarianten-Tests ohne US-Tag), sie deckt aber die Tests ab, nicht die Produktionsarbeit, die sie prüfen würden. Risiko: Infrastruktur-Härtung sammelt sich unbegrenzt an, weil der Prozess sie weder verbietet noch einen gangbaren Weg für sie beschreibt.
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

## OBS-S112-6 – Verletzungen geltender Regeln werden als aufschiebbare Schuld geführt
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: tech-debt
- Beobachtung: Drei Einträge in `docs/tech-debt.md` beschreiben keine bewusst aufgeschobene Schuld, sondern die Verletzung einer bereits geltenden Regel – und wurden trotzdem wie optionale Posten mit weichem Auslöser geführt. TD-S083-2 verletzt die Accessibility-Anforderung „Touch-Targets ≥ 44×44px" aus `nfr.md` und stand als UX-Politur mit dem Auslöser „eigene UX-Foundation-Aufgabe". TD-S083-4 wich von Guideline §2 ab und war als „kein Szenario, YAGNI" eingeordnet. TD-S089-1 hält fest, dass das Branch-Coverage-Gate aus NFR/DoD wirkungslos ist, und lag mit Priorität „Hoch" rund 22 Sessions unbearbeitet. Eine geltende Regel wartet auf keine Bedingung – sie ist erfüllt oder verletzt, und der einzig sinnvolle Zeitpunkt ist „jetzt". Risiko: Die Datei mischt zwei Sorten von Einträgen, deren Dringlichkeit sich grundsätzlich unterscheidet; die dringendere Sorte erbt dabei die Unverbindlichkeit der anderen und wird über viele Sessions mitgeschleppt, während die Anwendung die Regel weiter verletzt.
- Bezug: OBS-S112-1
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

---

## OBS-S112-7 – Verweise auf Dokument-Abschnitte sind Prosa und damit nicht maschinell prüfbar
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: TOOLING    Kontext: Doku
- Beobachtung: Verweise zwischen Projektdokumenten stehen als Prosa – „`coding-guideline-typescript.md` §2", „`nfr.md` Sektion Security", „Checkliste in Schritt 1". Kein Werkzeug kann prüfen, ob das Ziel existiert. In S112 trat das in **beiden** Richtungen auf: Zwei neu geschriebene Abschnitte (E2E-Treue in `e2e-testing.md`, §4c in der TypeScript-Guideline) tauchten im jeweiligen Inhaltsverzeichnis nicht auf und waren damit über den vorgesehenen Einstieg unerreichbar – `implementing-scenario` gibt für `e2e-testing.md` ausdrücklich „TOC zuerst" vor; §4b fehlt dort schon länger unbemerkt. Umgekehrt beschrieb die §2-Zeile im Inhaltsverzeichnis nach einer inhaltlichen Guideline-Änderung weiterhin den alten Stand („Factory Function mit Result-Rückgabe"), ohne dass irgendetwas darauf hinwies. Für volatile IDs (OBS-/TD-/LL-/ADR-) existiert die maschinelle Prüfung bereits – `decisions.py check` fängt tote ADR-Referenzen, `check-ref-direction.py` falschgerichtete –, für Dokument-Abschnitte fehlt das Äquivalent vollständig. Risiko: Verweise sterben unbemerkt in beide Richtungen; ein umbenannter Abschnitt hinterlässt tote Verweise, ein entfernter hinterlässt Verweise ins Leere, und beides fällt erst auf, wenn jemand der Referenz tatsächlich folgt. **Zweite Ausprägung derselben Ursache – erzwungene Nummerierung:** Weil Verweise auf Abschnitts*nummern* zeigen („§2", „§4b"), müssen diese Nummern stabil bleiben. Wächst der Inhalt, entstehen daraus Einschübe statt einer Neunummerierung – in S112 kamen so `4b` und `4c` zwischen `4` und `5` zu liegen. Die Nummer ist damit faktisch zur ID geworden, ohne deren Eigenschaften zu haben: Sie kodiert eine Position, die sich nicht mehr ändern darf, und die Gliederung richtet sich nach der Verweisbarkeit statt nach dem Inhalt. <!-- obs-ok: Die folgende Zielvorstellung stammt vom User als Auftraggeber, nicht aus agentenseitiger Vorwegnahme – sie hier zu tilgen hieße, die Entscheidungsgrundlage des Drains zu verlieren. --> Der User hält echte Markdown-Anker statt Prosa-Verweise für den lohnenswerten Weg, zusammen mit einem Hook plus Script, das bei jedem Schreibvorgang tote Anker meldet und zusätzlich **reversgerichtet** arbeitet: Wird ein Anker entfernt, ist zu prüfen, ob noch Verweise darauf zeigen. Anker sollen kurz bleiben, um vom Text nicht abzulenken – analog zur bestehenden ID-Notation (OBS/TD/LL), für Guidelines etwa `CGT`/`CGC`. Damit entfiele zugleich die Notwendigkeit, Abschnitte überhaupt zu nummerieren: Der Anker trägt die Identität, die Reihenfolge bleibt frei. Der Mehraufwand beim Schreiben gilt als vertretbar.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

---

## OBS-S113-1 – Der Drain-Satz kennt keine extern gesetzten Gates und kann sie nicht anzeigen
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: `docs/AGENT_MEMORY.md` führte vier OBS (OBS-S111-1, OBS-S106-1, OBS-S106-2, OBS-S108-2) ausdrücklich als **Gate** vor dem nächsten `gherkin-workshop` – „Gate, nicht nur Priorität". Der Drain-Satz, den `obs-drain.py` am Session-Start ausgibt, sortiert die Wert-Lane rein nach Impact × Häufigkeit; alle vier tragen `× gelegentlich` und fielen deshalb aus der Top-6. Der vorgeschlagene Satz enthielt **keinen** von ihnen, und nichts im Satz wies darauf hin, dass eine externe Vorrangregel existiert. Aufgefallen ist der Konflikt nur, weil in dieser Session beide Quellen nebeneinander gelesen wurden – der Hook injiziert `AGENT_MEMORY.md` und den Drain-Satz zwar gemeinsam, aber unverbunden. Wer dem Drain-Vorschlag folgt, arbeitet einen fachlich korrekt priorisierten Satz ab und lässt das Gate trotzdem stehen; der nächste Workshop liefe dann in genau die Blindstellen, deretwegen das Gate gesetzt wurde. Verallgemeinert: Priorität wird an zwei Orten gebildet – im Script nach einer festen Formel, in `AGENT_MEMORY.md` nach Projektlage –, ohne dass der eine Ort vom anderen weiß.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S112-8 – Lösungsfreie OBS-Erfassung erzwingen kostet mehr, als das eigentliche Ziel verlangt
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Hook/Script
- Beobachtung: Die Erfassungsregel für neue OBS verbietet jede Lösungsangabe und wird von `check-obs-capture.py` mechanisch durchgesetzt (nur zwei erlaubte Werte im Feld `Entscheidung/Maßnahme`, abschließende Feldliste, Blockade bei Lösungs-Ansagen im Text). Das eigentliche Ziel ist aber enger als die Regel: Beim **Drain** sollen die möglichen Maßnahmen möglichst vollständig und möglichst unvoreingenommen erzeugt und bewertet werden. Die Regel setzt dafür an der Erfassung an – und trifft damit auch Fälle, in denen die Beobachtung vom User kommt und bereits eine konkrete Maßnahme benennt. Dann bleiben nur zwei Wege: die Angabe tilgen (Informationsverlust, die Begründung ist beim späteren Drain nicht mehr rekonstruierbar) oder den `obs-ok`-Marker setzen (Ausnahme wird zur Routine). In S112 trat genau das innerhalb einer Session zweimal auf – bei OBS-S112-7 und bei diesem Eintrag selbst, der die Regel beschreibt, an der er scheitern würde. Risiko: Eine Regel, deren Ausnahme regelmäßig gezogen werden muss, verliert ihre Bindungskraft, und der Marker wird zur Formalie statt zur bewussten Einzelfallentscheidung. <!-- obs-ok: Die folgende Zielrichtung stammt vom User als Auftraggeber, nicht aus agentenseitiger Vorwegnahme – und ihre Tilgung wäre genau der Informationsverlust, den dieser Eintrag beschreibt. --> Der User weist darauf hin, dass die Unvoreingenommenheit des Drains auch anders gesichert werden könnte als über die Erfassung, etwa indem der bewertende Schritt in einem Subagenten läuft, der ausschließlich die dafür nötigen Informationen erhält.
- Bezug: OBS-S112-7
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

