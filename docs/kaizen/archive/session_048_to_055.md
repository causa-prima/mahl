# Lessons Learned

<!--
Format: Einträge pro Session gruppiert. Ein Bullet pro Erkenntnis.
Pflicht: Jede Session endet mit mindestens einem Eintrag – "Keine Learnings" nur mit expliziter Begründung.
Technische Schuld gehört in AGENT_MEMORY.md, nicht hierher.

Eintrag-Format:
  ## Session NNN – YYYY-MM-DD

  - **[SCHWERE] [KATEGORIE] [KONTEXT] Kurztitel**
    Was: Ein Satz – was ist passiert?
    Warum: Ein Satz – Ursache.
    Regel: Die destillierte Erkenntnis (imperative Form).

Schwere:    KRITISCH | HOCH | MITTEL | GERING
Kategorien: PROZESS | AGENT | QUALITÄT | TOOLING
Kontext:    TDD | C#-Code | TS-Code | Review | Agent-Prompt | Skill-Nutzung |
            Session-Struktur | Tooling | Gherkin | Doku | Sonstiges

Alle drei Tags sind Pflicht. Definitionen und Reaktionsregeln: docs/kaizen/PROCESS.md

Nach der Sitzung prüfen: Gehört ein Eintrag in principles.md oder countermeasures.md?
KRITISCH-Findings werden sofort behandelt (Andon-Cord) – hier trotzdem dokumentieren.
-->

> **Format-Referenz:** `docs/kaizen/PROCESS.md`
> **Archiv (Sessions 001–046, altes Format):** `docs/kaizen/archive/session_001_to_046.md`

---

## Session 054 – 2026-04-12

- **[GERING] [QUALITÄT] [Doku] Linter-Suppression ohne aktiven Linter hinzugefügt**
  Was: `# noqa: E402` in `jenga_score.py` eingefügt, obwohl kein Linter konfiguriert ist.
  Warum: Reflex aus anderen Projekten, ohne zu prüfen ob die Suppression hier sinnvoll ist.
  Regel: Linter-Suppressions nur hinzufügen wenn ein aktiver Linter den Fehler tatsächlich meldet.

- **[GERING] [QUALITÄT] [Doku] Unnötiger Alias beim Extrahieren geteilter Konstanten**
  Was: `DEDUCTIONS = SCHWERE_WEIGHTS` als Zwischenschicht eingeführt statt direkt den kanonischen Namen zu verwenden.
  Warum: Vermeidung von Umbenennungen im bestehenden Code – dabei unnötige Indirektion geschaffen.
  Regel: Beim Extrahieren geteilter Konstanten direkt umbenennen; Aliase erzeugen nur Verwirrung.

- **[MITTEL] [PROZESS] [Gherkin] NFR-Feature-Datei ohne dokumentierte Tag-Klasse erstellt**
  Was: `resilience.feature` mit `@NFR-resilience`-Tags angelegt, obwohl `E2E_TESTING.md` nur `@US-NNN` kannte – CRITICAL-Finding im Review.
  Warum: Beim Anlegen einer neuen Feature-Datei-Kategorie nicht geprüft ob die Tag-Konvention abgedeckt ist.
  Regel: Vor dem Anlegen einer neuen Feature-Datei-Kategorie prüfen ob die Tag-Konvention sie abdeckt; ggf. erst `E2E_TESTING.md` aktualisieren.

- **[MITTEL] [PROZESS] [Gherkin] Querschnittliche Resilience-Fragen fehlten systematisch im gherkin-workshop**
  Was: Schritt 1 des gherkin-workshops fragte nie nach story-spezifischem Resilience-Verhalten oder Draft-Saving-Bedarf.
  Warum: Bei der ursprünglichen Workshop-Konzeption nicht als eigene Dimension erkannt.
  Regel: Resilience und Draft-Saving als Pflicht-Fragen in Schritt 1 führen; Abschluss-Bedingungen erzwingen explizite Entscheidung.

## Session 055 – 2026-04-13

- **[MITTEL] [TOOLING] [TS-Code] react-query + neverthrow: Hook blockiert Standardbrücke**
  Was: `isErr()` + `throw` in der `queryFn` wird vom Code-Quality-Hook blockiert – die übliche Brücke zwischen `ResultAsync` und react-query ist damit
nicht möglich.
  Warum: Hook prüft generisch auf `isErr()` und `throw`, ohne Kontext ob es sich um eine react-query-Integration handelt.
  Regel: Für react-query `queryFn`-Integrationen plain Promise verwenden; ob das eine Guideline-Anpassung braucht, vor der nächsten Implementierung
klären.

- **[GERING] [QUALITÄT] [TS-Code] Leeres `<ul>` ist für Playwright unsichtbar**
  Was: Ein `<ul>` ohne Kinder hat Höhe 0 – `toBeVisible()` schlägt fehl.
  Warum: Playwright betrachtet Elemente ohne Bounding-Box als hidden.
  Regel: Leere Listen brauchen `minHeight` oder eine Wrapper-Lösung; E2E-Tests mit `toBeVisible()` auf Container-Elemente immer mit sichtbaren Dimensionen
  absichern.

- **[MITTEL] [TOOLING] [Tooling] Backend Stryker schlägt fehl wenn VS-MSBuild und dotnet-SDK-Version auseinanderlaufen**
  Was: Stryker.NET nutzt VS2022-MSBuild, nicht die dotnet CLI – bei .NET 10 Target schlägt der Build fehl wenn VS noch kein .NET 10 Workload hat.
  Warum: Stryker baut die Solution über `MSBuild.exe`, nicht über `dotnet build`.
  Regel: Nach jedem .NET-Major-Update prüfen ob VS2022 auf demselben Stand ist wie das dotnet CLI-SDK.

- **[GERING] [PROZESS] [TDD] "Fake it till you make it" bedeutet auch: keine Typen anlegen, die kein Test erzwingt**
  Was: Diskussion ob `Ingredient`-Typ und `IngredientId` für die leere-Liste-Implementierung nötig sind.
  Warum: Unbewusste Tendenz, bereits "fertige" Typen vorauszugreifen.
  Regel: Kein Typ, kein File, kein Import, das kein aktuell roter Test erzwingt – auch wenn der Typ "offensichtlich" bald gebraucht wird.

---

## Session 053 – 2026-04-10

- **[HOCH] [PROZESS] [TDD] YAGNI bei Entity-Properties und Test-Hilfsmethoden**
  Was: `IngredientDbType` mit 5 Properties angelegt und `EndpointsTestsBase` mit 3 Hilfsmethoden – kein einziger dieser Teile wurde durch den aktuellen Test gefordert.
  Warum: Ich habe die bekannte finale Struktur vorweggenommen statt "Fake it till you make it" konsequent anzuwenden.
  Regel: Bei jedem neuen Property und jeder neuen Methode fragen: "Welcher aktuelle rote Test fordert genau das?" Kein Test → nicht schreiben.

- **[MITTEL] [TOOLING] [Tooling] DEV_WORKFLOW.md-Befehle verwenden, nicht ad-hoc**
  Was: `npx playwright test` direkt verwendet statt `npm run test:e2e` aus DEV_WORKFLOW.md – Hook hat geblockt.
  Warum: Bekannten Befehl durch eigene Variante ersetzt ohne DEV_WORKFLOW.md zu konsultieren.
  Regel: Vor jedem Ausführungsbefehl DEV_WORKFLOW.md prüfen – nicht ad-hoc variieren.

- **[MITTEL] [TOOLING] [Tooling] Regex-Bug in check-bash-permission.py: Backslash-Zählung**
  Was: `mahl\\\\Client` (4 Backslashes im Raw-String = 2 im Regex = matcht 2 Backslashes) statt `mahl\\Client` (2 = 1 Backslash = matcht Windows-Pfad).
  Warum: In Python-Raw-Strings bedeutet `\\` ein literales Backslash im Regex – bei Windows-Pfaden mit einem Backslash also `\\`, nicht `\\\\`.
  Regel: Windows-Pfade in Python-Regex-Raw-Strings brauchen genau 2 Backslashes (`\\`) pro Pfad-Trennzeichen.

- **[MITTEL] [PROZESS] [Doku] 5-Punkte-Anfrage vor neuen Paketen – auch bei bekannten**
  Was: `Microsoft.EntityFrameworkCore.InMemory` ohne 5-Punkte-Anfrage eingetragen – User hat es beim nächsten Paket eingefordert.
  Warum: Paket war mir bekannt, Prozess trotzdem übersprungen.
  Regel: DEPENDENCIES.md-Prozess gilt für jedes neue Paket ohne Ausnahme – Bekanntheit ändert nichts am Prozess.

---

## Session 052 – 2026-04-10

- **[MITTEL] [PROZESS] [Doku] Fenced Code Block für copy-paste-kritische Texte**
  Was: Trigger-Text in closing-session mit Backtick-Escaping (`\`kaizen\``) formuliert – wäre literal kopiert worden.
  Warum: In Markdown-Anweisungen an Agenten müssen Texte, die exakt kopiert werden sollen, in Fenced Code Blocks stehen (nicht als Inline-Code mit Escaping), weil der Agent die rohe Markdown-Syntax sieht.
  Regel: Exakt-zu-kopierenden Text immer in ``` einschließen, nie mit Backtick-Escaping in Fließtext.

- **[MITTEL] [PROZESS] [Review] Review-Scope verhaltensbasiert, nicht größenbasiert**
  Was: review-code Scope-Kriterium war Dateianzahl (<3 = KLEIN) – lädt falsche Agenten bei kleinen aber business-kritischen Änderungen.
  Warum: Dateianzahl korreliert nicht mit Risiko. Drei neugeschriebene Dateien mit Domain-Logik sind GROSS.
  Regel: Scope anhand der Art der Änderung bestimmen (Verhaltensänderung? Domain-Layer betroffen?), nicht anhand der Anzahl geänderter Dateien.

## Session 051 – 2026-04-10

- **[MITTEL] [QUALITÄT] [Gherkin] Then-Assertion war trivial wahr – nicht erkannt**
  Was: `And die Liste ist alphabetisch nach Name sortiert` in "Neue Zutat anlegen" prüft mit einem einzigen Listeneintrag nichts Sinnvolles – Assertion ist immer wahr; erst im Review als HIGH entdeckt.
  Warum: Nicht geprüft ob das Then mit dem gewählten Given überhaupt falsifizierbar ist.
  Regel: Für jede Then-Aussage prüfen: Kann das Given einen Gegenfall produzieren? Falls nein, ist die Assertion trivial wahr und testet nichts.

- **[MITTEL] [QUALITÄT] [Gherkin] Given beschrieb nicht vollständig den für Then nötigen Ausgangszustand**
  Was: Then `die Zutaten-Liste ist leer` nach Löschen, obwohl Given nur `"Mehl" existiert` – nicht ausgeschlossen dass weitere Zutaten vorhanden sind; führte zu zwei User-Ablehnungen.
  Warum: Then formuliert ohne zu prüfen ob das Given allein die Vorbedingung vollständig beschreibt.
  Regel: Vor jedem Then prüfen: Beschreibt das Given den Ausgangszustand vollständig genug um diese Aussage zu rechtfertigen?

- **[MITTEL] [PROZESS] [Gherkin] Feature-Scope nicht gegen US-Akzeptanzkriterien abgeglichen**
  Was: Bestehendes Feature-File deckte nur Create+Delete ab; US fordert CRUD+Tags – Abweichung nicht in Schritt 0.B erkannt, erst im Review als HIGH entdeckt.
  Warum: In Schritt 0.B nur bestehende Szenarien gelesen, nicht Feature-Scope aktiv gegen alle Operationen der US-AKs geprüft.
  Regel: In Schritt 0.B des gherkin-workshops: Feature-Scope explizit gegen alle Operationen aus den Akzeptanzkriterien abgleichen; Lücken sofort als Scope-Entscheidung markieren.

- **[GERING] [QUALITÄT] [Gherkin] Logisch widersprüchliche Given-Steps**
  Was: `Given es sind keine Zutaten vorhanden` + `And die Zutat "Mehl" existiert` – logischer Widerspruch, der User hat abgelehnt.
  Warum: Gedacht als "erst leeren, dann hinzufügen" – aber Gherkin-Semantik: alle Given-Schritte gelten gleichzeitig.
  Regel: Given-Schritte in Szenarien auf logische Widersprüche prüfen – sie gelten gleichzeitig, nicht sequentiell.

---

## Session 050 – 2026-04-09

- **[MITTEL] [AGENT] [Review] Fix-Vorschlag formuliert ohne Mechanismus vorab zu prüfen**
  Was: Bei F3 (Runde 6) schlug ich vor "beides hätte ein Archiv hinterlassen müssen" – KRITISCH/HOCH-Findings schreiben aber sofort in countermeasures.md, ohne Retro oder Archiv auszulösen.
  Warum: Die Invariante klang plausibel, wurde aber nicht gegen PROCESS.md verifiziert.
  Regel: Vor einem Fix-Vorschlag der eine Invariante behauptet, die Invariante gegen die tatsächliche Prozessdefinition prüfen.

---

## Session 049 – 2026-04-08

- **[MITTEL] [PROZESS] [Review] Review-Agent-Output vor Umsetzung nicht auf Sachkorrektheit geprüft**
  Was: Mehrere Reviewer-Findings wurden zunächst akzeptiert, die bei näherer Prüfung auf falschen Prämissen basierten (M1: mv ist nicht irreversibel; H3: Eskalationslogik war kein Widerspruch).
  Warum: Findings wurden auf Plausibilität bewertet, nicht auf Verifikation gegen den tatsächlichen Inhalt der Dateien.
  Regel: Vor der Umsetzung jedes Reviewer-Findings den beanstandeten Sachverhalt direkt im Dokument prüfen – nicht nur die Begründung des Reviewers lesen.

- **[MITTEL] [PROZESS] [Doku] Inkonsistenz zwischen zwei Skills nicht beim Schreiben erkannt**
  Was: closing-session schrieb "Score ≤ 0", kaizen erwartete "Jenga-Score ≤ 0" – Match schlug still fehl.
  Warum: Zwei Skills die aufeinander verweisen wurden nie gegeneinander abgeglichen.
  Regel: Wenn ein Skill einen exakten String aus einem anderen Skill matcht, den Quell-Skill lesen und den genauen Text übernehmen.

- **[MITTEL] [PROZESS] [Skill-Nutzung] Nummerierungsfehler beim manuellen Umnummerieren von Schritt-Listen**
  Was: Schritt 5 in kaizen-Skill hatte nach Edit einen Sprung von 2 auf 4.
  Warum: Beim Einfügen eines neuen Schritts nur die neuen Nummern gesetzt, alte Folgeschritte vergessen.
  Regel: Nach dem Einfügen eines Schritts in eine nummerierte Liste die gesamte Sequenz einmal durchlesen.

- **[GERING] [PROZESS] [Doku] principles.md referenzierte nicht-existierenden Hook-Namen**
  Was: Kommentar verwies auf `.claude/hooks/startup.py` – Hook heißt tatsächlich `session-start.sh`.
  Warum: Kommentar wurde beim Erstellen des Hooks nicht synchronisiert.
  Regel: Beim Einrichten eines Hooks den referenzierten Dateinamen in allen Kommentaren/Docs anpassen.

## Session 048 – 2026-04-07

- **[MITTEL] [PROZESS] [Tooling] Edit-Tool ohne vorheriges Read aufgerufen**
  Was: Mehrere Edit-Aufrufe schlugen fehl, weil die Dateien in dieser Konversation nicht vorher gelesen wurden.
  Warum: Parallele Edits vorbereitet ohne Read-Schritt einzuplanen.
  Regel: Vor jedem Edit sicherstellen, dass die Datei in dieser Konversation bereits gelesen wurde.

- **[MITTEL] [PROZESS] [Skill-Nutzung] Skill-Schritt-Reihenfolge nicht auf Abhängigkeiten geprüft**
  Was: closing-session Skill hatte AGENT_MEMORY vor Jenga-Score – musste nach User-Hinweis korrigiert werden.
  Warum: Abhängigkeit (Jenga-Score als Input für AGENT_MEMORY) beim Skill-Design nicht explizit bedacht.
  Regel: Bei Skill-Design mit Task-Reihenfolge Datenflusss-Abhängigkeiten explizit prüfen bevor Reihenfolge festgelegt wird.
