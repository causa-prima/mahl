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
- Status: IN BEOBACHTUNG bis S145 – S130: fünfte Runde, mit Abbruchklausel gegen die Selbstblockade
- Impact: MITTEL–HOCH (von GERING revidiert)    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Sonstiges
- Beobachtung: Wir nutzen aktuell **keinen** Language-Server, der Claude Code Code-Intelligence bereitstellt. Recherche (S086): Claude Code v2.1.172 unterstützt LSP (`ENABLE_LSP_TOOL` + Marketplace-Plugin pro Sprache). Nutzen potenziell **hoch** (Auto-Typfehler nach jedem Edit, find-refs, Symbole, Call-Hierarchie → kürzere Edit-Fix-Schleifen) → Impact GERING→MITTEL/HOCH revidiert.
- Entscheidung/Maßnahme: S130-Drain-Entscheid (User): aufgeschoben, obwohl der Eintrag selbst 'vierte Nullrunde = verwerfen, ohne weitere Verlaengerung' festlegt. Grund fuer die Abweichung: Die Klausel zielt auf eine Nullrunde des WERKZEUGS, hier fehlte aber die GELEGENHEIT – seit S125 lief keine einzige Implementierungs-Session, und der Re-Trigger verlangt 3 Sessions mit realem TS-Lauf eines frontend-layer-implementer oder code-quality-auditor. Genau diese Unterscheidung (Urteil ueber das Werkzeug vs. ueber die Gelegenheit) hat der Eintrag in S114 selbst eingefuehrt. Messstand unveraendert gegenueber S114 und S115: 9 Calls gesamt, davon 7 im Aktivierungstest, 1 in 26 implementierung-Sessions (dieser vom 2026-07-10, also vor der Sichtbarkeitsmassnahme), 1 in einer Drain-Session. ABBRUCHKLAUSEL fuer die naechste Runde: Laufen bis S145 drei TS-Sessions mit den beiden Agenten und bleibt die Nutzung null, wird VERWORFEN. Laeuft bis S145 erneut keine solche Session, wird ebenfalls verworfen – dann ist belegt, dass dieser Pilot unter den realen Arbeitsverhaeltnissen nicht bewertbar ist, und ein Pilot, der nie zur Bewertung kommt, ist keine offene Frage mehr, sondern ein Dauerposten. Keine sechste Verlaengerung. Messluecke am Rande (S130): tool-usage --lsp ignoriert die Option --since still, die Zahl 'TS-Sessions seit S115' ist damit nicht direkt erhebbar.
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

## OBS-S114-2 – Pflichtlektüre ist der zweitgrößte Leseposten und wird nie gefiltert
- Quelle: Orchestrator
- Status: IN BEOBACHTUNG bis S142 – S130: der im Eintrag vorgesehene Fall trat ein (0 statt 3 Implementierungs-Sessions)
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Gemessen über 48 Sessions (`read-breakdown.py`): `docs/guidelines` und `docs/process` machen zusammen 21,4 % des gesamten Read-Volumens aus – in Implementierungs-Sessions sogar 27,9 %, hinter Client/ und Server/ der zweitgrößte Block. Die Einzelwerte sind hoch: Ø 12.234 Zeichen je Read auf `docs/guidelines`, 11.410 auf `docs/process`, und der Anteil gezielter Reads (mit offset/limit) liegt bei 3 % bzw. 7 % – praktisch jeder Aufruf liest das ganze Dokument. Ursache ist die Konstruktion: Die Agenten-Prompts schreiben diese Dateien als Pflichtlektüre vor, und jeder Subagent startet kalt. Anders als bei ADRs (`decisions.py` filtert nach Tags) und seit S114 bei Testdateien (`test-inventory.py` liefert eine Inventur) existiert für Guidelines kein Weg, gezielt nur den relevanten Abschnitt zu holen. Für die Gegenrichtung liegt eine Rechnung vor: Einen ADR in eine Guideline zu überführen kostet das 7- bis 12-Fache, weil eine Guideline von jedem Subagenten gelesen wird (180 Reads im Messzeitraum) statt on demand von den wenigen, die sie brauchen (14). Offen ist die umgekehrte Frage – ob selten gebrauchte Guideline-Abschnitte aus der Pflichtlektüre gelöst und abrufbar gemacht werden können, und woran „selten gebraucht" überhaupt erkennbar wäre. Der Block wächst mit +21 % über fünf Sessions langsamer als der Code, aber er schrumpft nicht.
- Entscheidung/Maßnahme: S130-Drain-Entscheid: aufgeschoben nach der Regel, die dieser Eintrag selbst festhaelt – 'Sind bis S130 keine 3 Implementierungs-Sessions gelaufen, bleibt der Eintrag IN BEOBACHTUNG und bekommt einen neuen Termin, statt auf duenner Basis entschieden zu werden.' Genau das ist eingetreten: Seit S125 lief KEINE Implementierungs-Session (S126 Session-Historie, S127 Retro, S128 und S129 Prozess-Code, S130 Drain). Der Vollstaendigkeit halber trotzdem erhoben (read-breakdown --by-area, S130): docs/guidelines 13,8 Prozent bei 6 Prozent gezielten Reads, gegen den S125-Ausgangswert von 13,9 Prozent bei 6 Prozent – also unveraendert. Diese Zahl ist NICHT als Wirkungsurteil zu lesen: Das Lesevolumen entsteht ganz ueberwiegend in Implementierungs-Sessions (69,3 Prozent des Gesamtvolumens), und davon lief seit der Massnahme keine. Gemessen wurde damit erneut die Gelegenheit, nicht die Wirkung. Re-Trigger unveraendert: dieselbe Erhebung nach mindestens 3 Implementierungs-Sessions. Backstop S142.

## OBS-S122-1 – Drain-Trigger-Kalibrierung beruht auf einer gerechneten, nicht gemessenen Frequenz
- Quelle: Orchestrator
- Status: IN BEOBACHTUNG bis S150 – S138: Re-Trigger erreicht, Stichprobe aber ohne Implementierungs-Läufe
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Hook/Script
- Beobachtung: Der in S122 eingefuehrte Drain-Trigger (Top-5-Summe >= 9 ODER >= 4 Eintraege aelter als 15 Sessions) entscheidet jede Session darueber, ob der Drain die Session beansprucht. Seine Schwellwerte sind aus Bestandsdaten abgeleitet, aber nie im Betrieb geprueft: Die tragende Groesse - 1,32 behandlungswuerdige Eintraege je Session - stammt aus einer Auswertung von S100 bis S121 und wurde mit der neuen Score-Skala rueckwirkend auf Eintraege angewandt, die unter der alten Skala erfasst und bewertet wurden. Daraus folgt die Erwartung, der Wert-Ausloeser feuere etwa jede dritte Session. Ob das eintritt, haengt an zwei Unbekannten: wie Agenten Impact und Haeufigkeit unter der neuen Skala tatsaechlich vergeben (GERING zaehlt jetzt 0, was die Vergabe veraendern kann), und wie oft Cluster entstehen, seit das Feld Zusammen-erledigen gepflegt wird. Faellt der Trigger zu selten, waechst der Rueckstau wieder; faellt er zu haeufig, ist genau die Verdraengung der Feature-Arbeit zurueck, gegen die er gebaut wurde. Beides zeigt sich erst an mehreren Sessions Betrieb und ist ohne bewusste Wiedervorlage nicht auffaellig, weil ein Trigger, der schweigt, keine Spur hinterlaesst.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: S138-Drain (User): weiter beobachten, nicht urteilen. Der Re-Trigger (Drain schweigt fünf Sessions am Stück) ist erreicht, die Stichprobe trägt aber kein Urteil: S132–S137 waren Retro, Tooling, Theme, Workshop und Doku-Review – kein einziger implementing-scenario-Lauf, und gerade Läufe erzeugen vermutlich die meisten und gewichtigsten OBS (unbelegt). BASISLINIE DER NICHT-IMPLEMENTIERUNGSPHASE (rekonstruiert, nicht die damals gezeigte Agenda – heutiger Trigger-Code auf alte Dateistände; der Code änderte sich S128–S131): S128–S131 beansprucht (Top-5 15→10, alt 4→1, Backlog 19→14), S132–S137 sechsmal geschwiegen (Top-5 konstant 6,0, alt 1–2, Backlog 11→16), S138 beansprucht (Top-5 10, Backlog 18). Frequenz damit etwa 1 von 7 statt der in S122 gerechneten 1 von 3; der Zulauf waren fast nur Bagatellen. RE-TRIGGER: nach dem dritten implementing-scenario-Lauf ab US-602 run-1 (gleiches Ereignis wie OBS-S109-1), Backstop S150. METHODE (das S138-Script lag im Scratchpad und ist weg): für jede Session N den Commit mit Trailer „Session-Ende: N-1" suchen (git log --grep "^Session-Ende: N-1$"), daraus docs/kaizen/observations.md holen (git show <commit>:…), mit obs_parse.parse_entries parsen und obs-drain.triggers(eintraege, N) sowie Top-5-Summe (unit_score über wert_einheiten[:TOP_N]) und Alt-Zahl (_alter > ALT_AB) ausgeben. Urteilsfrage dann: Beansprucht der Drain in der Implementierungsphase etwa jede dritte Session, und sinkt dabei der Backlog? Weicht es ab, TRIGGER_WERT/TRIGGER_ALT nachziehen, nicht das Modell.

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

## OBS-S128-1 – test-inventory.py kennt kein Python und sieht damit die groesste Testsuite des Repos nicht
- Quelle: Orchestrator
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: In S128 beim Erweitern von test_session_agenda.py aufgefallen. 'test-inventory.py tests/test_session_agenda.py' antwortet 'keine Tests erkannt (unterstuetzt: .cs, .ts/.tsx/.js/.jsx)'. Das Werkzeug steht in der AGENTS.md-Navigationstabelle als Antwort auf 'Was steht schon in einer Testdatei?' und deckt die 1.021 Python-Tests unter tests nicht ab - also die groesste Testsuite im Repo. Wer es nutzt, faellt auf grep zurueck oder liest die Volldatei, was der Zweck des Werkzeugs gerade vermeiden soll. Die Meldung ist immerhin ehrlich (sie nennt die unterstuetzten Endungen), der Ausfall ist also nicht stumm - deshalb GERING und nicht hoeher. Offen ist, ob sich der Aufwand lohnt: Python-Testnamen sind per 'def test_' trivial zu finden, der Mehrwert gegenueber grep liegt allein im Zeilenbereich je Test.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S133-1 – Die Logik in main() der Prozess-Werkzeuge ist nur an der Verdrahtung getestet
- Quelle: User + Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: QUALITÄT    Kontext: Testing
- Beobachtung: Seit S133 erzwingt tests/test_aufrufpfad.py für jedes der 51 Werkzeuge einen Test über den echten Aufrufpfad (main bzw. check). Die Mutationssichtung zeigt aber, dass diese Tests die Argument-Verdrahtung halten, nicht die Logik in main dahinter. Gesichtet wurden drei Werkzeuge: vitest-run (34 überlebende main-Mutanten), lessons (56) und check-atdd-gate (12). Darunter waren fünf echte Lücken, die ein Fehlurteil still durchgelassen hätten: ein ignorierter Titel-Filter im ATDD-Gate, ein ungetesteter get-Unterbefehl, ein grünes Verdikt bei rotem Exit-Code. Diese fünf sind in S133 geschlossen. Die übrigen 48 Werkzeuge sind nicht gesichtet; wahrscheinlich, aber nicht belegt, gibt es dort dieselbe Klasse: ungetestete Unterbefehle und Aufrufformen, Verdikt-Bedingungen ohne Test. Ein großer Teil der Überlebenden sind argparse-Hilfetexte und Meldungstexte ohne Aussagekraft; wie groß der Anteil echter Lücken ist, hängt je Werkzeug davon ab, wie viel Logik in main statt im Kern liegt.
- Zusammen-erledigen: keiner
- Aufschubgrund: Umfang – 48 Werkzeuge je mit Mutationslauf (1–2 min) und Sichtung der Überlebenden; sprengt die Retro-Session
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
- Bezug: CM-S133-1, LL-S128-1

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
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Der Wrapper-Filter in check-bash-permission erkennt diese Formen bewusst nicht, weil keine davon im protokollierten Bestand (8.567 erlaubte Befehle) vorkommt: Here-String auf Wrapper-Ausgabe (tail <<< "$(wrapper)"), Kürzung per printf '%.300s', Filter hinter einem Kommentar mit --allow-once, maskierter Befehlsname (dotnet\-test), Filter mit anschließendem Kontrollfluss (wrapper | tail && x), einzelnes & als Trenner, | in Kommentaren, $(…) innerhalb einer Filterstufe. Daneben: Die Liste der filterbaren Wrapper existiert doppelt (Hook und tool-usage.py); ruff-run, coverage-run und mutmut-run geben ebenfalls nur ein Verdikt aus, stehen aber nicht in _FILTERABLE_WRAPPERS – ob sie hinein gehören, ist nicht entschieden. Der Hook hat fünf eigene Quote-Scanner, die je eigene Lücken haben können. Der Eintrag dient als Gedächtnis, falls eine der Formen doch auftritt.
- Vorprägung: Ein gemeinsamer Quote-Scanner statt fünf eigener würde mehrere der Lücken zugleich schließen.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – Vorgabe des Users: Fälle, die nie vorkommen, werden nicht behandelt, wenn das den Code komplexer oder schwerer wartbar macht.
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S138-2 – argparse ergänzt in den Prozess-Werkzeugen Optionspräfixe still
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: argparse nimmt standardmäßig jedes eindeutige Präfix einer Option an (allow_abbrev=True). In S138 lief dadurch obs set --beobachtung unbemerkt als --beobachtung-anhängen – der Aufruf hängte Text an, statt ihn zu ersetzen, ohne jede Fehlermeldung; aufgefallen nur, weil ein neuer Test mit Exit 1 statt 2 endete. obs set ist seither mit allow_abbrev=False gebaut, alle übrigen CLIs unter prozesscode/ nicht. Kommt dort eine Option hinzu, deren Name Präfix einer bestehenden ist, oder vertippt man sich zu einem Präfix, wird der Aufruf still umgedeutet statt abgewiesen; bei den schreibenden Tracker-Werkzeugen landet das in den Tracker-Dateien. Häufigkeit geschätzt, nicht gemessen.
- Zusammen-erledigen: OBS-S133-1
- Aufschubgrund: Umfang – über 50 Werkzeuge, je zu prüfen, ob Abkürzungen bewusst genutzt werden (etwa per Meta-Test über alle Parser)
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

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

