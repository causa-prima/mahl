# Observations – Beobachtungs-Backlog

<!--
Zweck: Vorausschauende System-Design-Beobachtungen / Optimierungen (proaktiver Track).
       Ergänzt das reaktive lessons_learned.md. Speist den Jenga-Score NICHT.
aufnahmebedingung: Hier steht eine vorausschauende Beobachtung am **Prozess** – wie gearbeitet
       wird (`prozesscode/`, `.claude/**`, `docs/process/`, `docs/kaizen/`). NICHT hierher gehört eine
       Beobachtung am **Produkt**, also am Code samt Build-/Test-Kette: die läuft über
       ADR/TD/OQ ([„Ablage: in welchen Tracker gehört dieser Eintrag?"](../../AGENTS.md#CLA-ablage)).
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
  - Aufschubgrund: User | Umfang | Recherche – <warum erfasst statt sofort behoben>   (Pflicht
            für neue Einträge seit S133; trifft keiner zu, wird behoben statt erfasst. Bedeutung
            der Werte: `prozesscode/eintrag_felder.py`)
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

## OBS-S085-4 – Kein Language-Server für die Agenten-Programmierung im Einsatz
- Quelle: User
- Status: IN BEOBACHTUNG bis S152 – S146: sechste Runde mit korrigiertem Hinweis
- Impact: MITTEL–HOCH (von GERING revidiert)    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Sonstiges
- Beobachtung: Wir nutzen aktuell **keinen** Language-Server, der Claude Code Code-Intelligence bereitstellt. Recherche (S086): Claude Code v2.1.172 unterstützt LSP (`ENABLE_LSP_TOOL` + Marketplace-Plugin pro Sprache). Nutzen potenziell **hoch** (Auto-Typfehler nach jedem Edit, find-refs, Symbole, Call-Hierarchie → kürzere Edit-Fix-Schleifen) → Impact GERING→MITTEL/HOCH revidiert.
- Entscheidung/Maßnahme: S146 (User): Ursache geklärt, eine Runde mit deutlicherem Hinweis. Befund S146: (1) Subagenten-Logs seit S130 – 20 frontend-layer-implementer, 32 code-quality-auditor: null ToolSearch-, null LSP-Aufrufe, aber 262 grep-Suchen über Client/, davon 86 mit -r/-w (ein Teil echte Referenzsuchen, z.B. grep -rn seedIngredientViaApi). (2) Harness-Test mit einem frontend-layer-implementer: LSP steht DIREKT in seiner Tool-Liste, ToolSearch fehlt. Die Prompt-Anweisung 'deferred: einmal ToolSearch select:LSP laden' war also falsch und konnte ein Agent als 'nicht ladbar' lesen; documentSymbol und findReferences liefen auf Anhieb. Damit Ursache (a): Gewohnheit/Schwelle, nicht Unerreichbarkeit; über den Mehrwert sagt die Nullnutzung nichts. Maßnahme: ToolSearch-Hinweis in frontend-layer-implementer, code-quality-auditor und coding-guideline-typescript entfernt; Regel an den Entscheidungspunkt gelegt ('bevor du per grep nach dem NAMEN eines TS-Symbols suchst → LSP findReferences/workspaceSymbol; grep für Textmuster'); Implementer meldet beim Return eine Zeile 'LSP: genutzt für … / nicht genutzt, weil …'. Bewertung: nach 3 Sessions mit TS-Implementierung oder TS-Review (Messung tool-usage --lsp plus die Return-Zeilen). Bleibt die Nutzung null → VERWORFEN samt Aufräumen (Plugin, LSP in den tools der Agenten, Pilot-Blöcke), ohne weitere Verlängerung. Backstop S152.
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
- Status: IN BEOBACHTUNG bis S150 – S138: Messbedingung weiter unerfüllt, Re-Trigger an Ereignis gebunden
- Impact: HOCH    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Aus der Phase-1-Messung zu OBS-S085-2 (23 Sessions mit Subagent-Einsatz inkl. 112 Subagent-Logs, ~23,5M Zeichen ≈ 5,9M Token-Proxy): **`Read` allein macht 49,5 % des gesamten Volumens aus** – mehr als alles andere zusammen. Bei Subagenten sind es 71,4 % ihres Tool-I/O. 1590 Aufrufe, Ø 7.317 Zeichen (Subagenten Ø 8.373). Zum Vergleich: alle Projekt-Wrapper-Scripts zusammen 8 % des Tool-I/O, Orchestrator↔Subagent-Kommunikation 8,6 % des Gesamtvolumens, Edit 7,9 % des Tool-I/O. Drei Detailbefunde: (1) **Nicht die Anzahl treibt das Volumen, sondern die Größe** – Re-Reads derselben Datei im selben Kontext sind nur 10,1 %; die Top-Dateien sind `Client/e2e/ingredients.spec.ts` (816k gelesen), `docs/kaizen/observations.md` (759k), `Client/src/pages/IngredientsPage.test.tsx` (754k), `docs/guidelines/coding-guideline-csharp.md` (694k), `Server.Tests/IngredientsEndpointsTests.cs` (682k). (2) **86,7 % aller Reads sind vollständig, nur 13,3 % gezielt** (`offset`/`limit`) – und im Fall „Datei wird anschließend editiert" ist der gezielte Read im Schnitt 4,6× kleiner (1.943 vs. 8.971 Zeichen) bei identischem Zweck; der Harness verlangt vor einem Edit einen Read, aber keinen vollständigen (in S109 mehrfach praktisch bestätigt). 17 % des Read-Volumens sind solche vollständigen Vor-Edit-Reads. (3) **Der Posten ist nicht stabil, er wächst mit der Codebasis**: pro Session von Juni auf Juli stieg `Client/`-Lesen von 20k auf 79k Zeichen, `Server/` von 22k auf 48k, während die Pflichtlektüre (`docs/guidelines`) mit 40k→48k nahezu flach blieb. Ergänzend: gezielte Extraktions-Scripte ersetzen die Voll-Reads bisher nicht, sondern kommen hinzu – `decisions.py`-Aufrufe stiegen von 34 auf 87 pro Monat, gleichzeitig stiegen die `adr.md`-Voll-Reads von 1,5k auf 12,3k je Session (die Datei hat 1.263 Zeilen, und wer eine ADR ergänzt, muss sie vorher lesen). Risiko: Der Effekt verschärft sich mit jedem Lauf, weil Test- und Codedateien monoton wachsen und jeder frisch startende Subagent sie vollständig liest.
- Entscheidung/Maßnahme: S138-Drain-Entscheid (User): erneut aufgeschoben, jetzt an ein Ereignis gebunden statt an eine Session-Nummer. Grund: Seit S120 lief kein einziger implementing-scenario-Lauf; die Bedingung (drei unterscheidbare Implementierungs-Läufe seit S114) ist deshalb nicht erfüllt, und jede Session-Nummer als Termin liefe wieder leer (S120, S132 bereits verstrichen). Re-Trigger: nach dem dritten implementing-scenario-Lauf ab US-602 run-1 messen mit python3 -m prozesscode.read-breakdown --since <Datum von run-1> --by-area; Backstop S150. VOR der Messung das Werkzeug korrigieren (S138 gefunden): _session_logs.py ordnet write-code und review-code der Art implementierung zu – beide laufen aber auch bei Prozess-Code (diese Drain-Session S138 zählt als implementierung; seit 2026-08-04 gelten 11 Sessions als Implementierung, bei praktisch keinem echten Lauf). Nur implementing-scenario darf implementierung ergeben, sonst misst die Quote Tooling-Sessions mit.
- Bezug: OBS-S085-2 (Messung stammt aus dessen Phase 1); OBS-S096-3 (Scripted-Access-Layer, Re-Trigger jetzt erfüllt)

---

## OBS-S114-2 – Pflichtlektüre: ob jeder Abschnitt seinen Lesepreis wert ist, ist nicht messbar
- Quelle: Orchestrator
- Status: IN BEOBACHTUNG bis S152 – S146: Messung wird aufgebaut
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Gemessen über 48 Sessions (`read-breakdown.py`): `docs/guidelines` und `docs/process` machen zusammen 21,4 % des gesamten Read-Volumens aus – in Implementierungs-Sessions sogar 27,9 %, hinter Client/ und Server/ der zweitgrößte Block. Die Einzelwerte sind hoch: Ø 12.234 Zeichen je Read auf `docs/guidelines`, 11.410 auf `docs/process`, und der Anteil gezielter Reads (mit offset/limit) liegt bei 3 % bzw. 7 % – praktisch jeder Aufruf liest das ganze Dokument. Ursache ist die Konstruktion: Die Agenten-Prompts schreiben diese Dateien als Pflichtlektüre vor, und jeder Subagent startet kalt. Anders als bei ADRs (`decisions.py` filtert nach Tags) und seit S114 bei Testdateien (`test-inventory.py` liefert eine Inventur) existiert für Guidelines kein Weg, gezielt nur den relevanten Abschnitt zu holen. Für die Gegenrichtung liegt eine Rechnung vor: Einen ADR in eine Guideline zu überführen kostet das 7- bis 12-Fache, weil eine Guideline von jedem Subagenten gelesen wird (180 Reads im Messzeitraum) statt on demand von den wenigen, die sie brauchen (14). Offen ist die umgekehrte Frage – ob selten gebrauchte Guideline-Abschnitte aus der Pflichtlektüre gelöst und abrufbar gemacht werden können, und woran „selten gebraucht" überhaupt erkennbar wäre. Der Block wächst mit +21 % über fünf Sessions langsamer als der Code, aber er schrumpft nicht.
- Entscheidung/Maßnahme: S146 (User): K2 – aufschieben, aber erst messbar machen. ZIEL (User): Jeder Agent liest gezielt nur das Nötige, ohne Wichtiges wegzulassen; entstehen durch zu wenig Information Fehler (Mehrarbeit, schlechterer Code), ist das Ziel ebenso verfehlt. BEFUND S146 (Logs seit 2026-09-10, Reads auf docs/guidelines + docs/process je Agententyp): Auditoren 6,4 Mio. Zeichen (test-quality 3,17 Mio., code-quality 2,11 Mio., ux 0,70 Mio., functional 0,32 Mio., security 0,12 Mio.), Implementer zusammen ~20k Zeichen bei 70 doc.py-get-Abrufen, Hauptsession 269 doc.py-get. Auditoren lesen laut review-code absichtlich vollständig. Das ist der AKTUELLE Stand – früher lasen womöglich auch andere Agenten vollständig; die Aufteilung kann sich wieder verschieben. Von 157 Ankern in den beiden Ordnern wurden in Agenten-Texten nur 26 je zitiert, von Auditoren fast nie: 'gebraucht' ist heute nicht messbar. MASSNAHMEN: M1 (S146 umgesetzt): Jedes Finding nennt den Anker der verletzten Regel ('Regel: <ANKER>' bzw. 'Regel: keine'), in review-code und allen fünf Auditor-Definitionen. M2 (zur Auswertung bauen): read-breakdown-Option für Lesevolumen je Agententyp und Datei sowie Zitate/Abrufe je Anker (Vorlage: Erhebungsscript S146). M3 (zur Auswertung): Fehlerspur – je Finding mit Anker prüfen, ob der Implementer des Laufs den Abschnitt vorher abgerufen hatte bzw. im Prompt hatte; 'nicht abgerufen' = Mehrarbeit durch nicht gelesene Doku. Auswertung nach 3 Implementierungs-Sessions mit Review-Loop, Backstop S152: Kandidaten zum Auslagern sind Abschnitte, die in N Reviews nie eine Regel lieferten (Vorbehalt: ohne Finding kann ein Abschnitt trotzdem geprüft und nötig gewesen sein); Gegenmaß ist die Fehlerspur aus M3.

## OBS-S122-1 – Drain-Trigger-Kalibrierung beruht auf einer gerechneten, nicht gemessenen Frequenz
- Quelle: Orchestrator
- Status: IN BEOBACHTUNG bis S150 – S138: Re-Trigger erreicht, Stichprobe aber ohne Implementierungs-Läufe
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Hook/Script
- Beobachtung: Der in S122 eingefuehrte Drain-Trigger (Top-5-Summe >= 9 ODER >= 4 Eintraege aelter als 15 Sessions) entscheidet jede Session darueber, ob der Drain die Session beansprucht. Seine Schwellwerte sind aus Bestandsdaten abgeleitet, aber nie im Betrieb geprueft: Die tragende Groesse - 1,32 behandlungswuerdige Eintraege je Session - stammt aus einer Auswertung von S100 bis S121 und wurde mit der neuen Score-Skala rueckwirkend auf Eintraege angewandt, die unter der alten Skala erfasst und bewertet wurden. Daraus folgt die Erwartung, der Wert-Ausloeser feuere etwa jede dritte Session. Ob das eintritt, haengt an zwei Unbekannten: wie Agenten Impact und Haeufigkeit unter der neuen Skala tatsaechlich vergeben (GERING zaehlt jetzt 0, was die Vergabe veraendern kann), und wie oft Cluster entstehen, seit das Feld Zusammen-erledigen gepflegt wird. Faellt der Trigger zu selten, waechst der Rueckstau wieder; faellt er zu haeufig, ist genau die Verdraengung der Feature-Arbeit zurueck, gegen die er gebaut wurde. Beides zeigt sich erst an mehreren Sessions Betrieb und ist ohne bewusste Wiedervorlage nicht auffaellig, weil ein Trigger, der schweigt, keine Spur hinterlaesst.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: S138-Drain (User): weiter beobachten, nicht urteilen. Der Re-Trigger (Drain schweigt fünf Sessions am Stück) ist erreicht, die Stichprobe trägt aber kein Urteil: S132–S137 waren Retro, Tooling, Theme, Workshop und Doku-Review – kein einziger implementing-scenario-Lauf, und gerade Läufe erzeugen vermutlich die meisten und gewichtigsten OBS (unbelegt). BASISLINIE DER NICHT-IMPLEMENTIERUNGSPHASE (rekonstruiert, nicht die damals gezeigte Agenda – heutiger Trigger-Code auf alte Dateistände; der Code änderte sich S128–S131): S128–S131 beansprucht (Top-5 15→10, alt 4→1, Backlog 19→14), S132–S137 sechsmal geschwiegen (Top-5 konstant 6,0, alt 1–2, Backlog 11→16), S138 beansprucht (Top-5 10, Backlog 18). Frequenz damit etwa 1 von 7 statt der in S122 gerechneten 1 von 3; der Zulauf waren fast nur Bagatellen. RE-TRIGGER: nach dem dritten implementing-scenario-Lauf ab US-602 run-1 (gleiches Ereignis wie OBS-S109-1), Backstop S150. METHODE (das S138-Script lag im Scratchpad und ist weg): für jede Session N den Commit mit Trailer „Session-Ende: N-1" suchen (git log --grep "^Session-Ende: N-1$"), daraus docs/kaizen/observations.md holen (git show <commit>:…), mit obs_parse.parse_entries parsen und obs-drain.triggers(eintraege, N) sowie Top-5-Summe (unit_score über wert_einheiten[:TOP_N]) und Alt-Zahl (_alter > ALT_AB) ausgeben. Urteilsfrage dann: Beansprucht der Drain in der Implementierungsphase etwa jede dritte Session, und sinkt dabei der Backlog? Weicht es ab, TRIGGER_WERT/TRIGGER_ALT nachziehen, nicht das Modell.

## OBS-S133-2 – qa-check nummeriert seine Prüfungen als CHECK 1 bis 6
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Die Ausgabe von qa-check gliedert ihre Prüfungen als „CHECK 1“ bis „CHECK 6“ (geänderte Testdateien, Suppressionen, Testmuster, ESLint, Given/When/Then, ADR-Referenzen). Das sind selbst vergebene Ordnungszahlen – genau die Zweitadresse, die das Prinzip „Namen statt Nummern“ verbietet, weil sie bei jedem Umsortieren oder Einfügen still falsch wird. Verweise darauf existieren bereits: Commit cc660d5 nennt „Check-6 ADR-Referenz-Erkennung“; ob Skills, Doku oder Tests die Nummern ebenfalls zitieren, ist nicht gesichtet. check-ordinale sieht Ausgabetexte in Python-Strings nicht als Gliederung und schlägt deshalb nicht an. Aufgefallen in S133, als der User fragen musste, was „CHECK 6“ ist – die Nummer trug keine Bedeutung.
- Zusammen-erledigen: keiner
- Aufschubgrund: Umfang – vor dem Umbenennen müssen alle Verweise repo-weit gesucht werden (LL-S124-1: Umbenennung ohne Verweissuche); die Session wird gerade abgeschlossen
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: LL-S124-1

## OBS-S135-1 – Arbeitsnotizen eines Gherkin-Workshops überstehen eine lange Session nicht
- Quelle: User
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Gherkin
- Beobachtung: Im US-602-Workshop lagen die Entscheidungen der Regelentdeckung in einer Notizdatei im Scratchpad (us602-entscheidungen.md). Der Workshop lief über mehrere Tage, mit mehreren Kompaktierungen und einem Neustart des Rechners dazwischen; beim Fortsetzen war die Datei weg. Die ADRs nach der Freigabe musste ich aus dem Kopf der Feature-Datei rekonstruieren – das ging nur, weil der Kopf ausführlich war; Entscheidungen, die nicht dort landeten (z. B. verworfene Alternativen, Begründungen aus dem Dialog), sind nur noch im Session-Log. Laut User war die Länge vorher nicht absehbar, ein Gherkin-Workshop ist aber vermutlich generell öfter eine größere Sache, bei der das vorkommen kann. Der Skill sagt nicht, wo Zwischenstände (Story-Kern, Dialog-Antworten verbatim, Tiefe je Regel, Entscheidungen für ADRs) liegen sollen, damit sie Kompaktierung und Neustart überstehen.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – im Session-Abschluss zur Erfassung entschieden, Lösung über den Drain
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S136-1 – Zwei aktive Maßnahmen beruhen auf überholtem Subagenten-Verhalten
- Quelle: User + Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Ein Harness-Test am 2026-10-09 (Claude Code 2.1.295, CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1) hat zwei Annahmen widerlegt, auf denen aktive Maßnahmen beruhen: (1) Berechtigungsabfragen von Hintergrund-Subagenten erscheinen beim User und werden nicht automatisch abgelehnt – zwei Abfragen mit eindeutiger Marke kamen beim User an, seine Ablehnungstexte wörtlich beim Subagenten zurück. (2) Der Abschlusstext eines Subagenten-Laufs kommt automatisch beim Orchestrator an, auch bei Agenten mit tools-Liste ohne SendMessage; Rückfragen funktionieren, indem der Subagent seinen Lauf mit der Frage beendet und der Orchestrator per SendMessage antwortet. Damit fehlt CM-S070-6 (Hintergrund-Subagenten scheitern an automatisch abgelehnten Berechtigungen) und dem Fallback-Teil von CM-S102-3 (Berichte gehen als plain text verloren) die Grundlage. implementing-scenario, review-code und review-workflow sind bereits angepasst; offen ist nur der Status der beiden Maßnahmen.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – CM-Status ändert die Retro im Maßnahmen-Review, nicht der Doku-Review; mit dem User so abgestimmt
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: CM-S070-6, CM-S102-3

## OBS-S136-2 – Maßnahmen haben als einziger Tracker kein eigenes Werkzeug mit list und get
- Quelle: User + Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: docs/kaizen/countermeasures.md (über 110 KB, 39 aktive Maßnahmen) hat als einziger Tracker kein Abruf-Werkzeug – obs, lessons, td, oq und decisions haben je eines mit list/get, und prozesscode.tracker führt die Maßnahmen nicht. Wer beim Erfassen eines KRITISCH- oder HOCH-Learnings den Pflichtbezug --cm-bezug braucht, liest die Datei ganz oder nutzt den grep-Sonderweg, den closing-session dafür beschreibt (Titel per grep listen, Kandidaten per Read mit offset lesen). Der Sonderweg ist nur dort dokumentiert und weicht von der Bedienung aller anderen Tracker ab. Ein Parser für die Einträge existiert bereits (retro_report.load_cm). Nachtrag S136 (Doc-Review): Die Datei überschreitet inzwischen die Read-Grenze – 56k Tokens, ein Read zeigt nur die ersten 100 von 266 Zeilen (Grenze 25k). Der Retro-Schritt im kaizen-Skill sagt aber „Lies docs/kaizen/countermeasures.md"; wer ihn wörtlich befolgt, sieht nur die ersten rund 13 AKTIV-Einträge und keinen BEWÄHRT-Eintrag (die liegen dort, um Rückfälle zu erkennen). Belegt in der letzten Retro (Log 859f846e, 2026-09-29): Volltext-Read, dann ein Read mit Offset, der an der Größengrenze scheiterte, dann mit limit. Ursache der Größe: einzelne Einträge sammeln vollständige Rückfall-Chroniken (CM-S116-1 rund 10.000, CM-S124-3 rund 10.100 Zeichen). Damit hat die Lücke eine Qualitätsfolge für das Maßnahmen-Review, Impact von GERING auf MITTEL angehoben.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – entschieden, es gesondert umzusetzen; bis dahin gilt der grep-Weg in closing-session
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S136-3 – Text aus den Tracker-Werkzeugen umgeht die Edit-Hooks
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Die Doku-Hooks (Gliederungsnummern, Anker-Verweise, Verweisrichtung) laufen als PreToolUse auf Edit/Write. Text, den obs/lessons/td/oq per Bash in die Tracker-Dateien schreiben, sehen sie nicht. In S136 kam so über 'obs set --beobachtung-anhängen' eine Zeilenangabe in OBS-S136-2, die der Gliederungsnummern-Hook bei einem Edit geblockt hätte; aufgefallen ist sie erst beim Bestandslauf 'python3 -m prozesscode.ordinale'. Dieselbe Lücke gilt vermutlich für die übrigen Edit-Prüfungen – nicht geprüft.
- Zusammen-erledigen: keiner
- Aufschubgrund: Umfang – betrifft alle schreibenden Tracker-Werkzeuge, und erst ist zu entscheiden, welche Edit-Prüfungen für Tracker-Text gelten sollen; mit Tests und Gegenprobe je Werkzeug sprengt das den Session-Abschluss
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S137-2 – Bash-Hook: bekannte Lücken im Wrapper-Filter ohne Vorkommen im Bestand
- Quelle: Orchestrator
- Status: UMGESETZT (S151)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Der Wrapper-Filter in check-bash-permission erkennt diese Formen bewusst nicht, weil keine davon im protokollierten Bestand (8.567 erlaubte Befehle) vorkommt: Here-String auf Wrapper-Ausgabe (tail <<< "$(wrapper)"), Kürzung per printf '%.300s', Filter hinter einem Kommentar mit --allow-once, maskierter Befehlsname (dotnet\-test), Filter mit anschließendem Kontrollfluss (wrapper | tail && x), einzelnes & als Trenner, | in Kommentaren, $(…) innerhalb einer Filterstufe. Daneben: Die Liste der filterbaren Wrapper existiert doppelt (Hook und tool-usage.py); ruff-run, coverage-run und mutmut-run geben ebenfalls nur ein Verdikt aus, stehen aber nicht in _FILTERABLE_WRAPPERS – ob sie hinein gehören, ist nicht entschieden. Der Hook hat fünf eigene Quote-Scanner, die je eigene Lücken haben können. Der Eintrag dient als Gedächtnis, falls eine der Formen doch auftritt.
- Vorprägung: Ein gemeinsamer Quote-Scanner statt fünf eigener würde mehrere der Lücken zugleich schließen.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – Vorgabe des Users: Fälle, die nie vorkommen, werden nicht behandelt, wenn das den Code komplexer oder schwerer wartbar macht.
- Entscheidung/Maßnahme: Erledigt durch die Vereinfachung des Wrapper-Filters: Umgeschrieben wird nur ein Filter in der eigenen Pipeline eines Wrappers, jeder Umweg bleibt erlaubt und unverändert (Schutzziel Versehen statt Absicht, docs/process/dev-workflow.md#DEV-schutzziel). Damit sind die aufgezählten nicht erkannten Formen kein Mangel mehr, sondern gewollt. Die Liste in tool-usage.py ist kein Duplikat: Sie ist für die Vergleichbarkeit der Messreihe eingefroren (dort kommentiert, im Hook jetzt auch). ruff-run gibt nur ein Verdikt aus und steht jetzt in _FILTERABLE_WRAPPERS; coverage-run und mutmut-run nicht, ihre Ausgabe ist zum Lesen da. Die fünf Quote-Scanner bleiben: Ein gemeinsamer Scanner lohnt nur gegen gezielte Umgehung.

## OBS-S139-1 – Ein nacktes cd bleibt trotz Regel ungehindert und wiederholte sich in derselben Session
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: AGENT    Kontext: Bash/Permission
- Beobachtung: In S139 lief zweimal ein Bash-Aufruf mit nacktem cd in ein Unterverzeichnis (cd Client, später cd prozesscode/hooks); jedes Mal blieb das Arbeitsverzeichnis für die folgenden Aufrufe gesetzt, beim zweiten Mal wenige Stunden nach Erfassen von LL-S139-2. Der Bash-Guard lässt 'cd <dir>' als Allow-Muster durch und verhindert es nur vor npm (cd_npm_conflict). Die Regel von LL-S139-2 nennt für eine Wiederholung selbst den Anlass für einen Hook. Der User hat die Frage in S139 bewusst zurückgestellt.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – Hook gegen nacktes cd in S139 bewusst zurückgestellt
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: LL-S139-2

## OBS-S141-1 – Bash-Hook blockt Heredoc, sed -i und cat >> bei Layer-Subagenten
- Quelle: Subagent
- Status: UMGESETZT (S151)
- Impact: GERING    Häufigkeit: häufig
- Kategorie: AGENT    Kontext: Bash/Permission
- Beobachtung: In S141 meldeten drei Layer-Subagenten (Frontend run-2, Backend run-2, Frontend Review-Fixes) unabhängig, dass der Bash-Hook python3-Heredocs, sed -i, cat >> (Redirect) und einen Heredoc-Edit mit anschließendem Wrapper-Aufruf im selben Befehl blockt. Alle wichen ohne Folgen auf Edit aus, verloren dabei aber je einen oder mehrere Versuche und meldeten den Punkt als Prozess-Auffälligkeit im Return. Offen ist, ob die Agent-Definitionen den Weg (Dateien per Edit/Write ändern) so klar nennen, dass der erste Versuch schon richtig ist. Erneut in S143 (US-602 run-6): Drei der vier Layer-Subagenten meldeten in ihrem Prozessverbesserungs-Abschnitt Fehlversuche an Heredoc-Skripten mit Wrapper-Aufruf, sed -i und npx eslint bzw. npm run lint, bevor sie auf Edit und eslint-run wechselten. Erneut in S144 (US-602 run-8): Vier von sechs Layer-Subagenten meldeten Fehlversuche an python3-Heredocs, sed -i oder Redirects auf Repo-Dateien, bevor sie auf Edit/Write wechselten; auch der Orchestrator lief einmal in die Sperre (Heredoc-Anhängen an eine Spec-Datei). Erneut in S148 (US-602 run-11): Fünf von sechs Layer-Subagenten meldeten Fehlversuche an python3-Heredocs bzw. sed -i (einer auch an einem Filter hinter dem Wrapper), bevor sie auf Edit wechselten; der Orchestrator lief einmal in die Sperre (Heredoc-Anhängen an die E2E-Spec).
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-2 als Beobachtung entschieden
- Entscheidung/Maßnahme: Zwei Stellen: (a) Die Redirect-Ablehnung nennt jetzt zuerst den Weg zum Ziel – 'Datei anlegen, ändern oder anhängen: Write- bzw. Edit-Tool' – statt 'Output in Variable capturen' mit dotnet-build-Beispiel. (b) Beide Layer-Implementer-Definitionen nennen sed -i, Heredoc (cat > datei <<'EOF') und Python-Skript ausdrücklich als abgelehnt; der Frontend-Definition fehlte die Regel ganz, die Backend-Begründung ('Hook blockt Wrapper mit Heredoc oder Filter') stimmt seit dem vereinfachten Wrapper-Filter nicht mehr. Ob die Fehlversuche damit seltener werden, zeigen die Prozessverbesserungs-Abschnitte der nächsten Läufe.

## OBS-S141-2 – Analyzer-Kollisionen und -Grenzen im Backend nicht dokumentiert
- Quelle: Subagent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: QUALITÄT    Kontext: C#-Code
- Beobachtung: Der Backend-Subagent von US-602 run-2 und sein Review-Fix-Nachfolger stießen auf drei Analyzer-Stellen, die keine Guideline erklärt: (1) CA1859 (konkreten Typ statt Interface verwenden) kollidiert mit dem Immutability-Hook, der unveränderliche Schnittstellentypen verlangt; (2) die Grenze von MA0051 (Methode zu lang, 60 Zeilen) steht nirgends, obwohl die Guideline von etwa 20 Zeilen spricht; (3) Sonar S1144 (ungenutztes privates Member) meldet eine Deconstruct-Erweiterung fälschlich als ungenutzt. Jeder Fall kostete Suche, und welche Regel bei (1) gewinnt, ist ungeklärt.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-2 als Beobachtung entschieden; die Auflösung braucht Analyse
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S141-4 – qa-check Check 1 übersieht geänderte Test-Hilfsdateien
- Quelle: Orchestrator
- Status: UMGESETZT (S147)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Mutation-Testing
- Beobachtung: In S141 war Server.Tests/Helpers/EndpointsTestsBase.cs laut git geändert (neue Test-Data-Builder) und per --approved-tests freigegeben, erschien aber nicht unter „CHECK 1: GEÄNDERTE TEST-DATEIEN“. Der Test-Freigabe-Audit meldete nur „freigegeben, taucht aber nicht unter den geänderten Test-Dateien auf (committet/zurückgesetzt?)“ – eine irreführende Vermutung. Eine Änderung an einer Hilfsdatei, die alle Integrationstests trägt, läuft so am Audit vorbei.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-2 als Beobachtung entschieden
- Entscheidung/Maßnahme: _is_test_file in qa-check.py erkennt Testdateien jetzt auch über ihr Verzeichnis (Server.Tests/, Client/src/test/, Client/src/mocks/); Helfer wie EndpointsTestsBase.cs und RecipeRequests.cs laufen damit durch den Freigabe-Audit. Die Endung Tests.cs/Test.cs entfiel als toter Code (mutmut zeigte sie als überlebend). Test: test_is_test_file_recognizes_test_helpers_by_directory. Zweiter Fall war US-602 run-9 (S147).

## OBS-S143-1 – Stryker-Timeouts können Survivors verdecken
- Quelle: Orchestrator
- Status: UMGESETZT (S147)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Mutation-Testing
- Beobachtung: In US-602 run-5 meldete der erste qa-check-Lauf des Frontends 100 % bei 43 Timeouts (Timeouts zählen als detected). Ein späterer Lauf ohne Änderung an der betroffenen Datei meldete 17 Timeouts und einen Survivor in Client/src/pages/RecipeDetailPage.tsx:24 (StringLiteral im Query-Key), der seit run-3/run-4 besteht und dort nie aufgefallen war; ein dritter Lauf mit 10 Timeouts zeigte ihn ebenfalls. Ein Score von 100 % mit vielen Timeouts ist damit kein verlässlicher Beleg dafür, dass jeder Mutant von einem Test getötet wird – und der Verifikations-Hash bestätigt nur Frische, nicht Stabilität des Ergebnisses. qa-check weist Timeouts aus („können Timing-Artefakte sein – mit --verbose prüfen"), gated aber nicht darauf. Zweiter Fall in US-602 run-6 (S143): Ein Survivor im Layout-Wert sx={{ justifyContent: 'flex-end' }} von FormActions (CreateRecipePage.tsx) stand in den ersten qa-check-Läufen hinter 68 Timeouts bei „100 %“ und fiel erst im Volllauf eines Subagenten auf; zwischen zwei Läufen wechselte er dabei zwischen den Mutatoren ObjectLiteral und StringLiteral. Dritter Fall in US-602 run-8 (S144): qa-check meldete 100 % bei 101 Timeouts von 240 Mutanten. Ein gezielter Lauf auf CreateRecipePage.tsx mit timeoutMS 60000 ergab 0 Timeouts und 13 Survivors – darunter Mutanten, die keine Schleife erzeugen können (error={…} → false). Ursache geprüft: der Stryker-Default timeoutMS 5000 reicht für die user-event-Komponententests je Mutant nicht. timeoutMS 60000 ist seitdem gesetzt (ADR-S144-4); der Gesamtlauf deckte dabei noch einen seit run-3/run-4 verdeckten Survivor in RecipeDetailPage.tsx (Query-Key ohne Id) auf. Offen bleibt die Hälfte von qa-check: Timeouts zählen dort weiter still als erkannt, ein künftiger Timeout fiele wieder nicht auf.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-5 als Beobachtung entschieden
- Entscheidung/Maßnahme: qa-check listet Timeouts in geänderten Dateien gesondert (Datei:Zeile, Mutant) und gibt ohne Einordnung kein gültiges Verdikt (Exit 1); die Layer-Implementer ordnen jeden solchen Timeout in ihrer Rückgabe ein, der Orchestrator prüft die Einordnung. Gewählt statt eines harten Timeout-Verbots, weil echte Endlosschleifen-Mutanten legitim als Timeout enden – entscheiden kann das nur ein Blick auf den Mutanten. Den Grundfall (Stryker-Default timeoutMS zu knapp) behebt seit run-8 ADR-S144-4.

## OBS-S143-2 – Edit-Tool löst \uXXXX in String-Literalen zu rohen unsichtbaren Zeichen auf
- Quelle: Subagent + Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Sonstiges
- Beobachtung: In US-602 run-6 (S143) schrieben ein Layer-Subagent und der Orchestrator unabhängig voneinander Escape-Sequenzen wie \u200B, \u00AD, \u2060 und \uFEFF über das Edit-Tool in TypeScript-String-Literale (Komponententests, E2E-Spec). In der Datei landeten jeweils die rohen, unsichtbaren Zeichen. Im Quelltext sah ein Leser leere oder scheinbar gleiche Strings; aufgefallen ist es nur durch Zufall im Test-Review und dann per grep -P auf die Codepunkte. Die Schreibweise \u{200B} blieb erhalten. Kein Check im Repo meldet rohe unsichtbare Zeichen in Quelltext.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-6 als Beobachtung entschieden
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S143-3 – Review-Loop konvergiert nicht: frische Auditoren kehren Entscheidungen früherer Runden um
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Review
- Beobachtung: US-602 run-6 (S143) brauchte vier Review-Runden; jede fand bei 0 ❌ zwischen 6 und 15 ⚠️. Ab Runde 3 widersprachen Funde direkt früheren Runden: Ein Test-Helfer wurde in Runde 3 verlangt und in Runde 4 als „verbirgt Arrange und Act“ wieder beanstandet; eine explizite Existenz-Assertion wurde in Runde 1 verlangt und in Runde 4 als redundant gemeldet; die Unterscheidung toHaveCount(0) gegenüber toBeHidden() wurde in Runde 2 als begründet gelobt und in Runde 4 als Streuung beanstandet. Die Regel „Auditoren ohne Iterations-Vorwissen“ verhindert gedämpfte Kritik, lässt aber jede Runde neue Politur finden; das Rundenlimit (max. 3) stoppte den Loop, die Fortsetzung entschied der User. Jede Runde kostete vier bis fünf Agentenläufe plus einen Fix-Subagenten und einen qa-check. Weiterer Fall S147 (US-602 run-9): Auch hier drei Runden ohne Konvergenz. Frische Auditoren kehrten in Runde 3 zwei Empfehlungen aus Runde 2 um (Titel-Konstante im E2E-Test, Default eines Test-Data-Builders), und jede Runde brachte neue kosmetische ⚠️. Der User beendete den Loop nach Runde 3 und hängte die inhaltlichen Punkte an einen TD für run-13. Weiterer Fall S148 (US-602 run-11): Runde 1 verlangte, die Meldungsliste im Frontend-Test nicht seitenweit zu suchen; Runde 2 band sie über aria-describedby ans Feld; Runde 3 beanstandete genau diese Bindung als Kopplung und die seitenweite Gegenprobe als fragil. Dazu kam eine in Runde 1 vom User verworfene Szenario-Bindung in Runde 3 wieder. Wegen Fixes durch Schicht-Subagenten waren alle drei Runden nötig (R1 und R2 je fünf Auditoren, R3 zwei); erst Runde 3 endete mit nur trivialen Fixes.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-6 als Beobachtung entschieden
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S143-4 – mutmut-Baseline speichert keine Mutanten – ein Tausch von Überlebenden bleibt unsichtbar
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Mutation-Testing
- Beobachtung: In S143 riss die Sperrklinke für prozesscode.hooks.check-bash-permission zweimal (98,1 % → 98,1 % VERSCHLECHTERT), obwohl die Änderung nur Modulkonstanten betraf, die mutmut nicht mutiert. Beide Läufe hatten 22 Überlebende wie die Baseline (1171 beurteilbar, 1149 getötet); gesunken war nur der Nenner, weil mehr Mutanten in _maskiere_strings im Timeout endeten und Timeouts als „ohne Aussage“ aus dem Bruch fallen. Dass es dieselben 22 Überlebenden sind, ließ sich nicht prüfen: mutation-baseline.json hält je Modul nur zwei Zahlen. Der Riss wurde auf User-Entscheid als Rauschen hingenommen, die Baseline nicht nachgezogen. Verwandt mit OBS-S143-1 (Stryker), aber ein anderes Werkzeug. Vorlauf: Dieselbe Klasse trat in S139 auf (Commit 4672f72): Timeouts in main verschoben den Nenner, damals mit Exit -24 als getötet gezählt; behoben durch höheres timeout_constant, der Nenner sank von 1228 auf 1170 bei denselben 22 Überlebenden. S143 zeigt, dass Timeouts den Bruch auch danach noch um einzelne Mutanten verschieben.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – im Session-Abschluss S143 entschieden: als Rauschen hinnehmen und beobachten
- Entscheidung/Maßnahme: S146: Teil 'Klinke reißt durch schwankende Timeouts' behoben – Rückschritt gilt seit S146 nur noch, wenn der Bruch sinkt UND die offenen Befunde (überlebt + ohne deckenden Test) steigen; ein neutraler Stand wird fortgeschrieben (mutmut-run.ratchet, Tests in test_mutmut_ratchet). In S146 trat die Klasse erneut auf: x_expand_segment__mutmut_43 kippte je nach Testreihenfolge zwischen getötet (Fehlschlag) und timeout (Endlosschleife), die Schleife ist inzwischen durch einen Ausdruck ersetzt. OFFEN bleibt der zweite Teil: mutation-baseline.json hält je Modul nur zwei Zahlen, sodass 'dieselben 22 Überlebenden' nicht prüfbar ist und ein Tausch (ein Mutant neu getötet, ein anderer neu überlebend) bei gleicher Zahl unbemerkt bleibt – das war vor S146 ebenso. Beim Drain Kandidaten bilden.
- Bezug: OBS-S143-1

## OBS-S143-5 – Post-Edit-Suite meldet Zwischenstände von Edit-Bündeln als rot
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Der PostToolUse-Hook check-code-quality-nonblocking fährt nach jedem einzelnen Edit an prozesscode/ oder tests/ die gesamte Werkzeug-Suite (10–45 s) und meldet „Tooling-Tests rot“. Werden mehrere zusammengehörige Edits in einem Zug geschickt (Funktion anlegen, Aufruf umstellen, Import ergänzen), meldet er die Zwischenstände dazwischen als rot – in S143 gut ein Dutzend Mal, jedes Mal Rauschen, das der Agent als solches erkennen und übergehen musste; ruff meldete dabei auch fehlende Imports, die das nächste Edit schon ergänzte. Die Meldung selbst weist auf beabsichtigte RED-Phasen hin, unterscheidet aber nicht zwischen Zwischenstand und Endstand. Weiterer Fall S147 (US-602 run-9): Der ESLint-Teil desselben Hooks meldet bei mehrstufigen Umbauten im Frontend (Hook extrahieren, Aufrufer umstellen) jeden Zwischenstand als Fehler; beide Frontend-Subagenten nannten das in ihrer Rückgabe als Rauschen. Auch beim Orchestrator meldete der Hook in derselben Session ruff F821/F401 zwischen zwei zusammengehörigen Edits (Import und Nutzung in getrennten Edits).
- Zusammen-erledigen: keiner
- Aufschubgrund: User – im Session-Abschluss S143 als Beobachtung entschieden
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S144-2 – Test-Wrapper verschweigen Filter-Fehlgriffe und Testausgaben
- Quelle: Subagent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Testing
- Beobachtung: In S144 (US-602 run-8): dotnet-test mit --filter 'FullyQualifiedName~…' lief als „Zero tests“ (Exit 8) ohne Hinweis, dass --filter ein Substring des vollqualifizierten Namens ist – das steht nur in --help. vitest-run verschluckt console.log aus Tests; ein Subagent musste für eine Layout-Messung ein throw new Error(...) nutzen. Beides kostete je einen Umweg.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-8 entschieden
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S144-4 – Hintergrund-Lauf weckt den Layer-Subagenten nach seinem Ende nicht
- Quelle: Orchestrator + Subagent
- Status: IN BEOBACHTUNG bis S151
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: AGENT    Kontext: Agent-Prompt
- Beobachtung: In S144 (US-602 run-8) meldeten zwei Frontend-Subagenten „Warte auf qa-check (Hintergrund)“ und beendeten ihren Zug. Beide Male war der Lauf Minuten später fertig (einmal Exit 1 an ESLint, einmal Score 99,6 % nach 5 Minuten), ohne dass der Subagent sich meldete; erst der User bemerkte, dass nichts mehr lief, nach rund 10 bzw. 20 Minuten Stillstand. Ein Subagent sagte im Nachgang, der Wake-up sei erst nach einer Nachricht des Orchestrators gekommen. implementing-scenario (Innerer Loop, „Arbeitende Subagenten nicht pollen“) stützt sich auf einen Harness-Test vom 2026-10-29 (Claude Code 2.1.312), nach dem das Laufende den Subagenten selbst weckt – die Beobachtung widerspricht dem. Auch die ausdrückliche Anweisung im Spawn-Prompt, qa-check im Vordergrund laufen zu lassen, wurde einmal nicht befolgt. Der Orchestrator hat qa-check beide Male selbst gefahren. Rückfall S147 (CROSS-text/run-1, Claude Code 2.1.318): Der Backend-Subagent startete qa-check mit run_in_background, wurde durch eine Orchestrator-Nachricht geweckt, beendete seinen Zug; der Lauf endete 2 min später, die Task-Notification wurde in die Warteschlange der Haupt-Session eingereiht (queue-operation enqueue, kein remove) und kam im Subagent-Log nie an. Ursache (geprüft: Session-Logs der letzten 40 Sessions, Analyse-Script über queue-operation und Subagent-Logs): Betroffen sind benannte Subagenten (meta.json taskKind in_process_teammate – implementing-scenario vergibt immer einen Namen), die beim Laufende idle sind: 3 von 3 Fällen nie bzw. erst nach der nächsten Orchestrator-Nachricht zugestellt (e7e1f0f1/2.1.309 nie, 99223889/2.1.312 nach 18 min direkt nach einer Teammate-Nachricht, 9fd1a54c/2.1.318 nie). Zugestellt wurde sofort, wenn der Subagent beim Laufende noch im Zug war (9fd1a54c, 0,2 s) oder unbenannt war (taskKind plain). Der Harness-Test S146 (65f02267, 2.1.318) nutzte einen unbenannten Subagenten und konnte den Fall deshalb nicht nachstellen. Nicht geprüft: welchen Subagenten der Harness-Test vom 2026-10-29 nutzte; die interne Zustellung in Claude Code ist eine Deutung der Logs, nicht dokumentiert. Rückfall S148 (US-602 run-7, Claude Code 2.1.323): Der Backend-Subagent setzte run_in_background selbst (Log: zwei qa-check-Aufrufe mit run_in_background:true), sein Lauf endete nach rund 1½ Minuten, geweckt wurde er nicht; rund 30 Minuten Stillstand, bis der User fragte. Die Übergangsregel aus S147 (Vordergrund-Vorgabe im Spawn-Prompt) fehlte im ersten Spawn (LL-S148-5); die Agent-Definitionen schrieben zu dem Zeitpunkt sogar ausdrücklich run_in_background vor. Zweiter Weg in den Hintergrund, belegt in mindestens drei früheren Logs (auch Subagenten): Ohne explizites timeout verschiebt der Harness einen Vordergrund-Aufruf nach 120 s selbst („Command did not complete within its 120s timeout and was moved to the background“) – ein Hook gegen run_in_background fängt das nicht. Harness-Test S148 (benannter Subagent, 2.1.323): python3 -m prozesscode.stryker-frontend im Vordergrund mit timeout 600000 lief 273 s ohne Verschiebung durch; der frühere Befund „ab 180 s auch mit timeout“ (2.1.312) trat nicht auf – eine Messung, n=1. Einordnung des Users: Die eigentliche Ursache ist die fehlende Zustellung an untätige benannte Subagenten; Vordergrund+timeout verhindert nur, dass der Fall bei Läufen unter 10 Minuten entsteht. Korrektur zu S147: „Maßnahme vom User gewählt“ war die Annahme meiner Empfehlung „Erfassen, später bauen“, kein durchdachter Beschluss für den Hook. Datenpunkt S148 (US-602 run-10), nach der Maßnahme: Kein Schicht-Subagent meldete einen Hintergrund-Lauf; beide lieferten qa-check-Hash und Bericht ohne Nachfrage, je 4–5 Minuten nach der Test-Freigabe (GREEN, REFACTOR, qa-check zusammen). Nicht geprüft: ob ein Lauf über 120 s dauerte und ob die Subagenten timeout 600000 tatsächlich setzten – der Datenpunkt belegt also nur, dass der Fehlerfall nicht auftrat.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – S148: Vordergrund-Vorgabe jetzt in den Agent-Definitionen, Hook nur als Kandidat; die Ursache liegt im Harness
- Entscheidung/Maßnahme: User, S148: Agent-Definitionen (backend-/frontend-layer-implementer) verlangen lange Läufe im Vordergrund mit timeout 600000, nie run_in_background; implementing-scenario („Arbeitende Subagenten nicht pollen“) korrigiert – meldet ein Subagent trotzdem Hintergrund, fährt der Orchestrator den Lauf selbst. Kandidaten für den Drain, nicht beschlossen: Hook, der für qa-check/Stryker/mutmut run_in_background blockt und timeout 600000 verlangt; Behebung der Zustellung im Harness (Ursache, außerhalb des Projekts).

## OBS-S147-1 – Beispielzeilen eines Grundrisses werden nicht gegen die Testfälle abgeglichen
- Quelle: Subagent + Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Hook/Script
- Beobachtung: Die Zeilen einer Gherkin-Beispieltabelle stehen dreifach von Hand: im Feature-File, in der Testdaten-Liste des Backend-Tests und in der des E2E-Tests (S147: text-input.feature, Grundriss „Ein nach der Normalisierung gleicher Name gilt als Duplikat“ mit 9 Zeilen; die Reihenfolge weicht im C#-Test schon ab). Ein Test mit `// Beispiel: alle` besteht den Spec-Verweis-Hook, ohne dass geprüft wird, ob jede Zeile einen Testfall hat (laut Hook-Beschreibung check-test-spec-ref.py, nicht nachgestellt). Kommt eine Zeile hinzu und eine Testliste wird vergessen, wird nichts rot – die zeilengenaue Rückverfolgbarkeit Spec ↔ Test hängt am Review. Bald konkret: US-602 run-12 hat einen Grundriss mit 6 Zeilen. Gemeldet vom test-quality-auditor (Review-Runde 3, CROSS-text/run-1).
- Zusammen-erledigen: keiner
- Aufschubgrund: User – S147 entschieden: als OBS für den Drain, ein Check braucht einen Entwurf (Anzeigenamen im Backend, Titelzusatz im E2E, „Beispiel: alle“)
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S147-2 – mutmut-Sperrklinke meldet ohne --frisch einen Schein-Rückschritt
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Mutation-Testing
- Beobachtung: In US-602 run-9 (S147) meldete mutmut-run --ratchet für prozesscode.qa-check ohne --frisch einen Rückschritt (90,1 % → 90,0 %), obwohl gerade Tests hinzugekommen waren. Derselbe Stand mit --frisch ergab 90,6 % und hielt die Sperrklinke. Der Test, der die neue Meldung prüfte, war dem betroffenen Mutanten im Lauf ohne --frisch nicht zugeordnet. Ungeprüft ist, ob die Zuordnung Test → Mutant aus einem früheren Lauf im Verzeichnis mutants/ wiederverwendet wurde. Folge: Ein roter Ratchet-Lauf ohne --frisch ist kein verlässlicher Befund, und wer das nicht weiß, sucht eine Lücke, die es nicht gibt. Zweiter Fall S151, prozesscode.hooks.check-bash-permission: ohne --frisch 98,2 % → 94,6 % mit Zuordnungen „no tests“, derselbe Stand mit --frisch 96,6 %. Dritter Fall S151, diesmal MIT --frisch: prozesscode.playwright-test auf unverändertem Stand einmal 83,3 % (43 überlebt, Sperrklinke gerissen), direkt danach 84,4 % (gehalten); ohne --frisch zuvor 83,7 %. Ein Mutant springt also auch bei frischem Baum um – die Annahme, nur die wiederverwendete Zuordnung in mutants/ sei schuld, trägt damit nicht allein. Welcher Mutant springt, ist ungeprüft (der erste Lauf wurde vom nächsten --frisch weggeräumt); Weg dorthin: mutmut-run --tests-for <mutant>.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-9 als Beobachtung entschieden
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: OBS-S143-4

## OBS-S147-3 – Mengenangaben-Hinweis schlägt in Testkommentaren mit lokal definierter Menge an
- Quelle: Subagent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: In US-602 run-9 (S147) meldete der nicht-blockierende Mengenangaben-Check (prozesscode/hooks/checks/mengenangaben.py) beim Frontend-Review-Fix-Subagenten „Alle drei Felder“ in einem Testkommentar von RecipesPage.test.tsx. Die Menge ist dort im selben Test festgelegt (drei Felder des Formulars, die der Test selbst befüllt) und kann nicht still veralten – die Klasse, gegen die der Check gebaut ist (eine anderswo definierte, wachsende Menge), liegt nicht vor. Der Subagent erkannte das und änderte nichts; der Hinweis kostete nur Aufmerksamkeit. Die Sichtung S133 kannte nur Prosa in Doku-Dateien (2 echte von 20 Treffern); ob Code-Kommentare in Testdateien ein eigenes Fehlalarm-Profil haben, ist nicht erhoben.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-9 als Beobachtung entschieden
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S147-4 – Zwischenmeldungen benannter Subagenten kommen beim Orchestrator abgeschnitten an
- Quelle: Orchestrator
- Status: IN BEOBACHTUNG bis S151
- Impact: GERING    Häufigkeit: häufig
- Kategorie: AGENT    Kontext: Agent-Prompt
- Beobachtung: In US-602 run-9 (S147) kam die PLANUNG beider Schicht-Subagenten beim Orchestrator gekürzt an (Hinweis des Harness: „result truncated — ask the agent for the rest“): beim Frontend ab Punkt P6, beim Backend ab P5. Gerade die Rückfragen an den Orchestrator standen hinter dem Schnitt; je Subagent kostete das einen zusätzlichen Nachrichtenwechsel. Die Layer-Implementer-Definitionen ordnen für den Abschlussbericht schon an, das Unverzichtbare vorn zu bringen („Ein zu langer Bericht kommt … am Ende abgeschnitten an“), für die PLANUNG gibt es keine solche Reihenfolge. Ab welcher Länge gekürzt wird, ist nicht gemessen. Rückfall S148 (US-602 run-7): Diesmal traf es das TEST-REVIEW-Signal des Subagenten backend-tests-2 (Hinweis „result truncated“), abgeschnitten mitten in der Begründung eines Typ-Umzugs. Der Orchestrator las den Rest aus dem Diff, statt nachzufragen. Betroffen ist also jede längere Zwischenmeldung, nicht nur die PLANUNG. Datenpunkt S148 (US-602 run-10), nach der Maßnahme: PLANUNG und TEST-REVIEW beider Schicht-Subagenten kamen vollständig an. Gekürzt wurde nur der Abschlussbericht des Backend-Subagenten, hinten im letzten Punkt der Prozessverbesserung; Hash, Survivors und Dateiliste standen davor und kamen an. Den Rest lieferte eine Nachfrage.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-9 als Beobachtung entschieden
- Entscheidung/Maßnahme: User, S148: direkt umgesetzt – backend-/frontend-layer-implementer.md verlangen jetzt auch für Zwischenmeldungen (PLANUNG, TEST-REVIEW) Signal und Rückfragen zuerst, Begründung knapp, keine Nacherzählung des Diffs. Reine Anweisung, nicht mechanisch; ob sie reicht, zeigen die nächsten Läufe.

## OBS-S148-1 – Hinweis „Primitive Obsession“ löst an der API-Grenze bei jedem Edit aus
- Quelle: Subagent + Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: In S148 (US-602 run-7) meldete check-code-quality-nonblocking nach praktisch jedem Edit an Server/Endpoints/RecipesEndpoints.cs „Primitive-Obsession-Hinweis: Nackte Built-in-Typen als Parameter in Domain-Code erkannt“ – gut ein Dutzend Mal in der Session, beim Orchestrator und bei Subagenten. Auslöser sind Parameter wie ParseLine(string line) oder IngredientIdByName(…, string name). Die Datei ist kein Domain-Code, sondern die API-Grenze, an der der rohe Text aus dem Request zerlegt wird; der Hinweistext nennt aber „Domain-Code“. Ein Subagent führte den Hinweis als Störung in seinem Prozessverbesserungs-Abschnitt auf. Offen ist, ob der Hinweis dort sachlich falsch ist: Die Review-Checkliste (RCL-domain-modeling) wendet die Regel ausdrücklich auch auf Methodenparameter an. Wiederholt sich derselbe nicht blockierende Hinweis bei jedem Edit, wird er erfahrungsgemäß überlesen – auch dort, wo er träfe. Datenpunkt S148 (US-602 run-10): Der Hinweis löste auch an QuantityAmount.Create(string word) in Server/Domain aus – einer Factory-Methode, die laut Review-Checkliste (RCL-domain-modeling) ausdrücklich Primitive annehmen darf. Der Backend-Subagent führte ihn als Rauschen in seiner Prozessverbesserung auf; der Hinweistext nennt die Ausnahme selbst, erkennt sie aber nicht.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-7 als Beobachtung entschieden; ob die Regel an der API-Grenze gilt, ist eine Regelfrage
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S148-2 – ESLint meldet auf unverändertem Code zufällig einen Typfehler
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: In S148 meldete python3 -m prozesscode.eslint-run zweimal auf unverändertem Code den Fehler Client/e2e/api/recipesApi.ts:29:78 functional/prefer-immutable-types „Parameter should have an immutability of at least ReadonlyDeep (actual: ReadonlyShallow)“ für den Parameter recipe: RecipeCommand. Die Datei war in der Session nie geändert (git diff leer), RecipeCommand ist durchgehend readonly. Reproduziert: Fünf Läufe direkt hintereinander, nur der erste meldete den Fehler, die vier folgenden nicht. Über die Session waren es 2 von etwa 9 Läufen, jeweils der erste nach einer Pause oder einer Änderung an anderen Dateien. eslint-run ruft „npm run lint“ = „eslint .“ ohne --cache auf, ein veralteter Cache scheidet aus. Die Regel arbeitet typbasiert. In früheren Session-Logs fand sich die Stelle nicht (grep auf ReadonlyShallow + recipesApi.ts). Ungeprüft: ob der Fehler auch ohne die Änderungen dieses Laufs auftritt (dazu hätte der Arbeitsbaum gestasht werden müssen) und ob der Edit-Hook (eslint_lint, nur die geänderte Datei) betroffen sein kann. Folge, wenn es qa-check trifft: ein falsches Rot ohne Codeursache, das einen Subagenten in eine Fehlersuche schickt. Erneut in S151 (US-602 run-14): derselbe Fehler an derselben Stelle (recipesApi.ts:29:78, ReadonlyShallow) im ersten eslint-run nach mehreren Edits an anderen Dateien (RecipesPage.test.tsx, recipes.spec.ts); ein zweiter Lauf rund zwei Minuten später war sauber, der qa-check dazwischen meldete ESLint OK (geprüft). Datei, Typ und eslint.config.js im Lauf unverändert (geprüft: git status, git diff). Der Edit-Hook lief kurz vorher auf den geänderten Dateien; ob er gleichzeitig lief, ist ungeprüft.
- Vorprägung: Vermutung ohne Beleg: Typ-Immutabilität wird in eslint-plugin-functional/is-immutable-type über Dateien hinweg zwischengespeichert, das Ergebnis könnte von der Lint-Reihenfolge abhängen.
- Zusammen-erledigen: keiner
- Aufschubgrund: Recherche – Ursache unklar, braucht Läufe mit gestashtem Arbeitsbaum und isolierter Regel
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S148-3 – Auditoren sollen Tests fahren, der Nur-Lese-Hook blockt die Test-Wrapper
- Quelle: Subagent
- Status: NEU
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Review
- Beobachtung: review-code verlangt, dass Auditoren jedes Finding am Stand belegen, auch durch Testläufe, und der Orchestrator-Prompt nannte python3 -m prozesscode.dotnet-test bzw. vitest-run. In US-602 run-11 meldeten mehrere Auditoren (functional-correctness R1 und R2, test-quality R2, code-quality R1), der Hook habe dotnet-test geblockt, laut eigener Angabe auch ohne Pipe oder Redirect; vitest-run lief bei einem. Folge: Befunde kamen als „offene Prüfung" statt belegt, und die Gegenproben musste der Orchestrator bzw. ein Schicht-Subagent nachholen. Nicht nachgestellt: ob der Hook dotnet-test für Auditoren absichtlich sperrt (der Build schreibt bin/obj) oder ob nur der Aufruf mit Filter/Pipe scheiterte. Zu klären: Wrapper für Auditoren freigeben (ggf. im Nur-Lese-Modus ohne Build) oder den Auftrag im Prompt und in review-code auf das ändern, was erlaubt ist. Weiterer Fall S150 (SPA-Auslieferung, ADR-S150-2): In Runde 1 meldeten drei von vier Auditoren (code-quality, functional-correctness, test-quality), der Hook habe python3 -m prozesscode.dotnet-test --filter SpaHosting geblockt, auch ohne Pipe und Redirect; ab Runde 2 stand im Prompt, dass Auditoren keine Tests fahren können. Laufzeitfragen (405 unter /api, POST und HEAD auf Client-Pfade, Groß-/Kleinschreibung, Pfade mit Endung) kamen deshalb nur als offene Prüfung; belegt hat sie erst der RED-Lauf eines Fix-Subagenten, und zwei Annahmen erwiesen sich dabei als falsch: POST auf einen Client-Pfad liefert 405 statt 404, und der erste Fallback überdeckte die 405 unter /api. S151: playwright-test ist für Auditoren freigegeben, mit einem Lauf-Lock, der einen zweiten gleichzeitigen E2E-Lauf vor dem Bauen abbricht (Exit 99); vitest-run war es schon. dotnet-test bleibt gesperrt (gemeinsame Build-Ausgabe paralleler Auditoren) – dafür bleibt die Beobachtung offen; der Lauf-Lock wäre auch dort ein Weg.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-11 als Beobachtung entschieden; Ursache erst beim Drain nachstellen
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S148-4 – Sonar-Regeln, auf die sich Code-Kommentare berufen, sind im Build nicht prüfbar
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Sonstiges
- Beobachtung: Mehrere Backend-Stellen begründen eine Form mit einer Sonar-Regel („Sonar S8949 verlangt die explizite Wahl" des CancellationToken). In US-602 run-11 wurden alle Aufrufe auf eine zentrale Konstante Cancellation.None umgestellt; ob S8949 das als explizite Wahl akzeptiert, ließ sich nicht prüfen: Der Build (TreatWarningsAsErrors) bindet keinen Sonar-Analyzer ein, die Regel läuft nur in der IDE-Analyse des Users. Damit sind Kommentare, die sich auf Sonar berufen, und Umbauten, die sie berühren, für Agenten unprüfbar. Zu klären: SonarAnalyzer.CSharp in den Build aufnehmen (Kosten, Lärm), einen Wrapper für eine Sonar-Analyse anbieten, oder Sonar-Begründungen im Code als ungeprüft kennzeichnen.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-11 als Beobachtung entschieden (statt in der IDE zu prüfen oder zurückzudrehen)
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S148-5 – Line-Coverage zählte eine const-decimal-Zeile als nicht ausgeführt
- Quelle: Subagent
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Testing
- Beobachtung: In US-602 run-11 brach die Line-Coverage (Gate 100 %) an einer unveränderten Zeile in Server/Domain/QuantityAmount.cs: private const decimal ThousandthsPerUnit = 1000m; meldete 0 Treffer (Line 99,80 %), zweimal reproduziert, obwohl der Wert in jedem Mengen-Test verwendet wird. Ein const decimal ist in C# kein IL-Literal, sondern ein Feld mit DecimalConstantAttribute; warum die Zeile vor dem Umbau gezählt wurde und danach nicht, ist ungeklärt (vermutet, nicht gemessen: Zeitpunkt der Typinitialisierung). Umgangen durch const int und Umrechnung an der Verwendungsstelle. Andere const decimal im Code könnten das Gate genauso flackern lassen; zu klären: Ursache nachstellen, ggf. Guideline-Hinweis oder Coverage-Ausschluss für solche Deklarationen.
- Zusammen-erledigen: keiner
- Aufschubgrund: Recherche – die Ursache nachzustellen braucht mehrere Coverage-Läufe mit Varianten (Tiering, Typinitialisierung); im Lauf per int umgangen
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S148-6 – Das von EF erzeugte SQL ist über den dotnet-test-Wrapper nicht einsehbar
- Quelle: Subagent
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Testing
- Beobachtung: Um zu belegen, dass EF eine Abfrage mit lower() auf beiden Seiten nach SQL übersetzt (ADR-S135-2, Addendum S148 – kein Test trennt das), musste der Backend-Subagent in US-602 run-11 vorübergehend Code ändern: ein LogTo in die Datei im Scratchpad in TestWebApplicationFactory und einen Logging-Eintrag in appsettings.json, beides danach zurückgebaut; das kostete rund drei Zyklen. Der Wrapper zeigt keine Logs des Test-Hosts, auch nicht mit --verbose (MTP/xUnit schluckt die Konsolenausgabe), und Umgebungsvariablen als Präfix blockt der Bash-Hook. Vorschlag des Subagenten: ein Schalter am Wrapper (z. B. --sql-log), der das EF-Command-Logging per Umgebung in eine Scratchpad-Datei lenkt.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-11 als Beobachtung entschieden
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S148-7 – jscpd meldet ein Duplikat zwischen tests/test_qa_check.py und tests/test_qa_check_git.py
- Quelle: Subagent
- Status: NEU
- Impact: GERING    Häufigkeit: dauerhaft
- Kategorie: QUALITÄT    Kontext: Hook/Script
- Beobachtung: Beim REFACTOR von US-602 run-11 meldete python3 -m prozesscode.jscpd-run einen Fund, den dieser Lauf nicht erzeugt hat: tests/test_qa_check.py Zeilen 142–157 gleichen tests/test_qa_check_git.py Zeilen 19–34. Beide Dateien hat der Lauf nicht angefasst. Wahrscheinlich eine gemeinsame Fixture bzw. Hilfsfunktion, die beim Aufteilen der qa-check-Tests doppelt blieb; nicht geprüft, seit wann.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-11 als Beobachtung entschieden; außerhalb des Laufs
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S148-8 – td add vergibt die ID eines in derselben Session entfernten Eintrags erneut
- Quelle: Orchestrator
- Status: NEU
- Impact: HOCH    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: In S148 entfernte td remove den Eintrag TD-S148-1 („Zutatensuche faltet anders als der Unique-Index", behoben in US-602 run-11); das folgende td add vergab für einen neuen, anderen Eintrag wieder TD-S148-1. Die alte ID steht aber schon in der Historie (Commit 3e4d7b0, tech-debt.md von HEAD): git log --grep und jeder Verweis in einer Commit-Nachricht träfen danach zwei verschiedene Einträge. Ursache vermutet, nicht im Code gelesen: Die ID-Vergabe zählt nur die aktuell in der Datei stehenden IDs der laufenden Session. Behelf diesmal: ID per Edit auf TD-S148-2 geändert (User-Freigabe). Vermutlich gleiche Logik in oq.py und weiteren Trackern. Behebung: die nächste freie Nummer gegen die git-Historie (alle je vergebenen IDs der Session) bestimmen.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-11 entschieden: diesmal einmalig per Edit umbenannt, Werkzeug-Fix später
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S151-1 – implementing-scenario: kein Weg für einen Lauf, dessen E2E-Tests sofort grün sind
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: TDD
- Beobachtung: US-602 run-13 „Formular·nach dem Speichern“ (als Full-Stack geclustert, 6 Szenarien): Alle sechs neuen E2E-Tests waren sofort grün – das Formular ist eine eigene Seite und hängt beim Verlassen aus, das Backend sammelt alle Meldungen ohnehin. Der Skill verlangt im äußeren Loop einen roten E2E-Test und kennt danach nur den Ablauf mit Schicht-Subagenten, Freigabe-Anker und qa-check samt Stryker. Für „sofort grün“ gibt es keinen Pfad: Der Orchestrator musste ad hoc abweichen (Gegenprobe – Verhalten absichtlich brechen, drei der sechs Tests wurden rot; für zwei fand sich kein einfacher Bruch –, User-Bestätigung für einen Charakterisierungs-Lauf ohne Subagenten und ohne Orchestrator-Check, Review nur über den Test-Diff). Offen ist auch, warum der Workshop beim Clustering nicht erkannte, dass das Verhalten schon existiert.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von run-13 entschieden: Einzelfall; ob die Regel in implementing-scenario oder im Workshop-Clustering gehört, braucht den Blick auf weitere Läufe
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S151-2 – Bash-Hook: Ablehnung einer Befehlskette nennt nicht das gescheiterte Glied
- Quelle: Subagent
- Status: UMGESETZT (S151)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: US-602 run-13: Ein test-quality-auditor schickte `python3 -m prozesscode.decisions list … ; sed -n 325,360p datei` als eine Kette. prozesscode/hooks/check-bash-permission.py lehnte die ganze Kette ab, weil das unquotierte sed damals nicht auf der Auditor-Liste stand (geprüft: Hook mit Auditor-Kontext aufgerufen). Die Meldung beschreibt nur allgemein, was erlaubt ist, und nennt nicht, welches Glied scheiterte. Der Auditor hielt deshalb `decisions list --tag resource:recipes` für gesperrt, berichtete das so und ließ die ADR-Prüfung zu diesem Tag aus. Ein stiller Prüfungsausfall, entstanden aus einer harmlosen Ablehnung. Dieselbe Meldungsform erhält auch die Hauptsession.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von run-13 entschieden: der sed-Anlass ist behoben, die Meldungsform kommt in den Drain
- Entscheidung/Maßnahme: Die Ablehnung einer Kette beginnt mit 'Abgelehnt wurde dieses Glied: <befehl>' und sagt, dass die Glieder davor erlaubt sind – auch für Auditoren, deren Meldung sonst den Grund ersetzt. Gilt bei mehreren Segmenten und bei Gliedern in einer Substitution, nicht beim Einzelbefehl. Tests in tests/test_bash_permission_hookausgabe.py.

## OBS-S151-3 – mutmut-Lauf stößt an die eigene Speichergrenze, Bedarf je Worker unklar
- Quelle: User + Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Am 18.11.2026 brachte mutmut mit 20 Workern (Default os.cpu_count()) die WSL-VM in den OOM; die Distro wurde dreimal beendet. Ein Windows-Kollege hat einzelne mutmut-Prozesse mit bis zu 3,3 GB RSS gesehen (ungeprüft durch mich). Seit S151 begrenzt mutmut-run die Worker auf 4 und startet den Lauf in einer eigenen Speichergruppe (MemoryHigh=10G, MemoryMax=12G). Beim Ratchet-Lauf für check-bash-permission habe ich eine Spitze von rund 1,9 GB gemessen (geprüft: Momentaufnahmen der Gruppe). Nach dem Ratchet-Lauf für prozesscode.mutmut-run zählte app.slice aber 340.509 'high'-Ereignisse (geprüft: memory.events unter user@1000.service/app.slice). Mindestens ein Lauf ist also an MemoryHigh=10G gestoßen und wurde gedrosselt; einen OOM-Kill gab es in user.slice nicht. Welcher Lauf und welcher Test den Speicher braucht, ist offen: Fixtures, Testdaten, ein Leck oder einfach 4 x pytest über die ganze Werkzeug-Suite. Folge der Drosselung: lange Laufzeit (über 10 Minuten), und bei mehr Bedarf droht der Kill bei 12G mit einem Verdikt ohne Aussage.
- Zusammen-erledigen: keiner
- Aufschubgrund: Recherche – den Bedarf je Worker zu messen braucht mehrere volle mutmut-Läufe mit Speicherprotokoll, je über 10 Minuten
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S151-4 – Layer-Implementer bemerkt Lint-Verbote und Schreibweg erst durch Ablehnung
- Quelle: Subagent + Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: AGENT    Kontext: Hook/Script
- Beobachtung: In S151 (US-602 run-14) meldete der Frontend-Subagent zwei Umwege. (a) Dass das Projekt-ESLint if-Anweisungen (functional/no-conditional-statements) und das Schreiben in Refs (functional/immutable-data) verbietet, bemerkte er erst über die Meldung des Edit-Hooks nach dem Schreiben; nach eigener Aussage hatte er den Abschnitt CGT-verbotene-muster der TS-Guideline nicht gelesen. (b) Er versuchte einmal, eine Datei per Heredoc (cat > Datei <<EOF) zu schreiben; der Bash-Hook lehnte ab. Dieses Verbot steht seit derselben Session ausdrücklich in .claude/agents/frontend-layer-implementer.md (Maßnahme zu OBS-S141-1, dort UMGESETZT). Ein Fall, n=1: Ob die neue Regel übersehen oder nicht befolgt wurde, ist ungeklärt. Beide Umwege kosteten je einen Tool-Aufruf, Folgen am Ergebnis gab es keine.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von run-14 entschieden; Ursache unklar, ein Fall reicht für eine Maßnahme nicht
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: OBS-S141-1
