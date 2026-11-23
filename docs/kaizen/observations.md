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

## OBS-S141-2 – Analyzer-Kollisionen und -Grenzen im Backend nicht dokumentiert
- Quelle: Subagent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: QUALITÄT    Kontext: C#-Code
- Beobachtung: Der Backend-Subagent von US-602 run-2 und sein Review-Fix-Nachfolger stießen auf drei Analyzer-Stellen, die keine Guideline erklärt: (1) CA1859 (konkreten Typ statt Interface verwenden) kollidiert mit dem Immutability-Hook, der unveränderliche Schnittstellentypen verlangt; (2) die Grenze von MA0051 (Methode zu lang, 60 Zeilen) steht nirgends, obwohl die Guideline von etwa 20 Zeilen spricht; (3) Sonar S1144 (ungenutztes privates Member) meldet eine Deconstruct-Erweiterung fälschlich als ungenutzt. Jeder Fall kostete Suche, und welche Regel bei (1) gewinnt, ist ungeklärt.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von US-602 run-2 als Beobachtung entschieden; die Auflösung braucht Analyse
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

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
- Beobachtung: Der PostToolUse-Hook check-code-quality-nonblocking fährt nach jedem einzelnen Edit an prozesscode/ oder tests/ die gesamte Werkzeug-Suite (10–45 s) und meldet „Tooling-Tests rot“. Werden mehrere zusammengehörige Edits in einem Zug geschickt (Funktion anlegen, Aufruf umstellen, Import ergänzen), meldet er die Zwischenstände dazwischen als rot – in S143 gut ein Dutzend Mal, jedes Mal Rauschen, das der Agent als solches erkennen und übergehen musste; ruff meldete dabei auch fehlende Imports, die das nächste Edit schon ergänzte. Die Meldung selbst weist auf beabsichtigte RED-Phasen hin, unterscheidet aber nicht zwischen Zwischenstand und Endstand. Weiterer Fall S147 (US-602 run-9): Der ESLint-Teil desselben Hooks meldet bei mehrstufigen Umbauten im Frontend (Hook extrahieren, Aufrufer umstellen) jeden Zwischenstand als Fehler; beide Frontend-Subagenten nannten das in ihrer Rückgabe als Rauschen. Auch beim Orchestrator meldete der Hook in derselben Session ruff F821/F401 zwischen zwei zusammengehörigen Edits (Import und Nutzung in getrennten Edits). Weiterer Fall S153 (US-803 run-3): Der Frontend-Subagent ergänzte einen Test und danach in einem zweiten Edit den Import (`within`); dazwischen meldete der ESLint-Teil 15 Fehler, nach dem zweiten Edit keinen mehr. Er nannte das in seiner Rückgabe als Rauschen.
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

## OBS-S151-1 – implementing-scenario: kein Weg für einen Lauf, dessen E2E-Tests sofort grün sind
- Quelle: Orchestrator
- Status: NEU
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: TDD
- Beobachtung: US-602 run-13 „Formular·nach dem Speichern“ (als Full-Stack geclustert, 6 Szenarien): Alle sechs neuen E2E-Tests waren sofort grün – das Formular ist eine eigene Seite und hängt beim Verlassen aus, das Backend sammelt alle Meldungen ohnehin. Der Skill verlangt im äußeren Loop einen roten E2E-Test und kennt danach nur den Ablauf mit Schicht-Subagenten, Freigabe-Anker und qa-check samt Stryker. Für „sofort grün“ gibt es keinen Pfad: Der Orchestrator musste ad hoc abweichen (Gegenprobe – Verhalten absichtlich brechen, drei der sechs Tests wurden rot; für zwei fand sich kein einfacher Bruch –, User-Bestätigung für einen Charakterisierungs-Lauf ohne Subagenten und ohne Orchestrator-Check, Review nur über den Test-Diff). Offen ist auch, warum der Workshop beim Clustering nicht erkannte, dass das Verhalten schon existiert.
- Zusammen-erledigen: keiner
- Aufschubgrund: User – in der Abschluss-Triage von run-13 entschieden: Einzelfall; ob die Regel in implementing-scenario oder im Workshop-Clustering gehört, braucht den Blick auf weitere Läufe
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

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

## OBS-S153-1 – Langer Befehl eines Subagenten trotz timeout 600000 nach 180 s in den Hintergrund verschoben
- Quelle: Subagent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Beim Frontend-Layer-Implementer (CROSS-navigation run-4, 2026-11-23) wurde der qa-check-Lauf mit Stryker trotz Bash-Parameter timeout: 600000 nach 180 s in den Hintergrund verschoben (Tool-Meldung „moved to the background after running for 180s“, ohne Pipe gestartet). Die Agent-Definition sieht für lange Läufe den Vordergrund mit timeout 600000 vor, damit das Ergebnis im selben Zug vorliegt. Der Subagent wartete daraufhin auf die Benachrichtigung; der Lauf kam durch, kostete aber eine Unterbrechung. Ob der Harness Befehle von Subagenten grundsätzlich nach 180 s verschiebt oder nur unter bestimmten Bedingungen, ist ungeprüft.
- Zusammen-erledigen: keiner
- Aufschubgrund: Recherche – die Ursache verlangt einen eigenen Test des Harness-Verhaltens (Subagent, langer Befehl, verschiedene Timeouts)
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten

## OBS-S153-2 – Primitive-Obsession-Hook warnt bei Guid-Parameter eines Infrastructure-Helfers
- Quelle: Subagent
- Status: NEU
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Beim Schreiben von Infrastructure/PlannedRecipeExtensions.cs (US-803 run-2) meldete der PostToolUse-Hook gegen Primitive Obsession eine Warnung für den Parameter `Guid recipeId` von `PlanRecipeAsync`. Der Bestand nimmt Kennungen am Rand durchgängig als `Guid` entgegen (Endpoints, Route-Constraint `:guid`); der Backend-Subagent wertete die Warnung deshalb als Fehlalarm und ging weiter. Ungeklärt ist, ob der Hook `Guid` als eingebauten Typ zählt und wie oft er an solchen Randstellen anschlägt.
- Zusammen-erledigen: keiner
- Aufschubgrund: Recherche – Hook-Regel lesen und Auslösungen im Bestand zählen, bevor sich Fehlalarm oder berechtigter Hinweis sagen lässt
- Entscheidung/Maßnahme: offen - beim Drain Kandidaten erstellen und bewerten
