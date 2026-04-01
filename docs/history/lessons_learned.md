# Lessons Learned

<!--
wann-schreiben: Am Ende jeder Session oder jedes Features (Gate 4 der Definition of Done) – Pflicht
wann-lesen: Beim Phasen-Abschluss (alle Einträge auf wiederkehrende Muster prüfen); beim Schreiben eines neuen Eintrags um Duplikate zu vermeiden
kritische-regeln:
  - "Keine Learnings" nur mit expliziter Begründung akzeptabel
  - Dokumentations-Änderungsvorschläge: alle 5 Kern-Dokumente explizit beantworten (auch "Nein")
  - Technische Schuld gehört in AGENT_MEMORY.md, nicht hierher
-->

> **Pflicht:** Jedes Feature und jede Session endet mit einem Eintrag hier.
> "Keine Learnings" ist nur mit expliziter Begründung akzeptabel.
>
> Technische Schuld (nicht sofort behobene ⚠️-Findings) gehört in `docs/AGENT_MEMORY.md`,
> nicht hierher – sie soll aktiv verfolgt und abgebaut werden.

---

## Session 042 – 2026-03-26 – Dokumentations-Großüberarbeitung

### Was lief gut
- Alle 8 geplanten Dokumentations-Tasks vollständig abgeschlossen
- User-Feedback war präzise und führte sofort zu Korrekturen – besonders die Konsistenz-Korrekturen (US-Tag immer am Anfang, "Backend- oder E2E-Test") haben die Docs substanziell verbessert
- domain_visibility.py-Hook: Regex-Bug durch Tests sofort gefunden und behoben (TDD for hooks zahlt sich aus)
- Gherkin-Beispiel-Verbesserung (fachlich lesbar statt HTTP-Details) war ein wichtiger Impuls vom User

### Was war schwierig / Fehler
- **ARCHITECTURE.md Nummerierung**: Mehrere Ablehnungen wegen Missverständnis (0a→0b→0c). Hätte beim ersten Mal direkt fragen sollen: "Soll die neue Sektion 0b oder 0c heißen?" statt anzunehmen
- **domain_visibility.py**: Regex `[/\\]Server[/\\]` erfordert führendes Trennzeichen – schlägt bei Pfaden wie `"Server/Domain/Foo.cs"` ohne führendes `/` fehl. Fix: `(?:^|[/\\])Server[/\\]`. Klassischer Grenzfall-Fehler der durch Tests sofort sichtbar wurde
- **Stryker-Suppression**: Erst nur `Equality` für den default(T)-Guard angenommen – User hat korrekt darauf hingewiesen, dass auch `String` für den "Uninitialized"-String-Literal nötig ist

### Learnings
- **Vor Nummerierung von Sektionen**: explizit fragen wenn die Position in einer bestehenden Nummerierungsfolge unklar ist – nicht raten
- **Regex für Dateipfade**: Immer `(?:^|[/\\])` statt `[/\\]` wenn der Pfad auch ohne führendes Trennzeichen beginnen kann (relative Pfade aus Test-Inputs)
- **Stryker `disable once` Scope**: Statement deckt den ganzen throw ab, aber String-Literals innerhalb des Statements sind separate Mutations – bei Guards immer beide Kategorien prüfen
- **Konsistenz über Ebenen**: Wenn eine Regel auf Ebene A gilt (Tag am Anfang), sofort prüfen ob sie auf Ebene B und C gleich angewendet wird – nicht warten bis der User es bemerkt

### Dokumentations-Änderungen
- `docs/ARCHITECTURE.md`: Sektion 0c (Hexagonal Architecture) + Sektion 4 aktualisiert ✅
- `docs/CODING_GUIDELINE_CSHARP.md`: `internal`-Pflicht + Stryker-Defensive-Guards ✅
- `docs/TDD_PROCESS.md`: Outside-In ATDD-Sektion + US-Tag im Testnamen + Stryker-Kategorien-Tabelle ✅
- `docs/E2E_TESTING.md`: neues Dokument (BDD/Gherkin, ATDD, Quality Gate, Traceability) ✅
- `docs/REVIEW_CHECKLIST.md`: Architecture Layer + Test-Audit Sektionen ✅
- `CLAUDE.md`: E2E_TESTING.md in Navigationstabelle ✅
- `docs/DEV_WORKFLOW.md`: Infrastructure-Projekt-Hinweis ✅
- Skills `implementing-feature`, `tdd-workflow`, `review-code` angepasst ✅
- Hook `domain_visibility.py` + 11 Tests ✅

---

## Session 041 – 2026-03-26 – Architektur-Grundsatzentscheidungen (kein Code)

### Was lief gut
- Debate-Agenten-Format (2× Pro, 2× Contra parallel) lieferte unvoreingenommene Tiefenanalyse – besonders beim Coverage-vs-Spec-Driven-Gate-Vergleich sehr effektiv
- Grill-Me-Ansatz vor Entscheidungen sicherte gemeinsames Verständnis; keine Entscheidung ohne klares Alignment
- User stellte wichtige Korrekturen: Playwright ohne UI ist möglich (RED-State via "Element not found"), ATDD beweist keine Minimalität (nur Code-Test-Kopplung) – gut, dass diese Präzisierungen eingefordert wurden
- Viele komplexe Themen in einer Session strukturiert durchdacht und entschieden

### Was war schwierig / Fehler
- **Falsche Behauptung**: "Playwright-Tests können nicht ohne UI geschrieben werden" – war falsch. Playwright-Tests laufen, scheitern zur Laufzeit. User hat das korrekt herausgefordert
- **Ungenaue Behauptung**: "ATDD beweist, dass Code benötigt wird" – ungenau. ATDD beweist Code-Test-Kopplung, nicht Spec-Test-Kopplung. Das ist Prozess-Disziplin
- Kontext wurde sehr voll ohne Code-Output – Diskussions-Sessions sind kontext-intensiv

### Learnings
- **Bei Behauptungen über Tool-Fähigkeiten**: erst sicher sein, bevor man sie macht. "Playwright kann X nicht" ist eine starke Aussage, die verifiziert sein muss
- **"Beweist" vs. "unterstützt"**: Präzise unterscheiden was ein Mechanismus garantiert vs. was er nur erleichtert. ATDD "unterstützt" Minimalität durch Disziplin, "beweist" sie nicht
- **Debate-Agenten**: Direkt nach den Resultaten synthetisieren und dem User präsentieren – nicht auf Folgefragen warten

### Dokumentations-Änderungen
- `docs/NFR.md`: Mutation-Testing-Ziel ≥90% → 100% korrigiert ✅
- `docs/history/decisions.md`: Alle Architektur-Entscheidungen aus Session 41 dokumentiert ✅
- `docs/history/decisions.md`: Revisionsvermerk zur alten 90%-Entscheidung ✅
- Große Dokumentations-Überarbeitung (ARCHITECTURE.md, neue E2E_TESTING.md, Guidelines, Skills, Hooks): **Nächste Session, Priorität 1**

---

## Session 040 – 2026-03-26 – Branch Coverage + SumType.Unreachable<T>()

### Was lief gut
- Coverlet-Integration war sauber strukturiert: DataCollector via runsettings, korrekte Exclusions, Script-Erweiterung mit line-level Detail — jeder Schritt hat messbaren Mehrwert gebracht
- User-Rückfrage zu Ternary vs. Switch hat einen echten Design-Tradeoff aufgedeckt: Ternary = Coverage-freundlich, Switch = Laufzeit-Schutz. Das wurde sauber durchreflektiert und entschieden
- `SumType.Unreachable<T>()` als Extraktion kam aus User-Beobachtung heraus: das Muster war schon vorhanden (`ValueOrThrowUnreachable`), Analogie war naheliegend
- Agent-Research zur Branch-Level-Suppression war korrekt beauftragt und lieferte belastbare Antwort (kein Tool unterstützt das)

### Was war schwierig
- **Ternary-Refactoring war eine unbedachte Optimierung**: "kürzer = besser" ist kein ausreichendes Argument für eine Design-Änderung, die einen Safety-Property opfert. Der Tradeoff hätte explizit benannt werden müssen, bevor der Code geändert wird
- **Doppeltes Using durch Edit-Fehler**: `mahl.Server.Types` in Quantity.cs doppelt eingefügt — hätte durch Read vor Edit vermieden werden können

### Dokumentations-Änderungen
- `docs/CODING_GUIDELINE_CSHARP.md`: keine Änderung (switch-Muster bleibt dokumentierter Standard)
- `docs/TDD_PROCESS.md`: Branch-Coverage-Ziel 100% ergänzt, Stryker-Ziel präzisiert
- `docs/DEV_WORKFLOW.md`: Timeout-Tabelle korrigiert (max. 2× erwartete Dauer)
- `docs/history/decisions.md`: `SumType.Unreachable<T>()` + `[ExcludeFromCodeCoverage]` auf `Match<T>` dokumentiert

---

## Session 039 – 2026-03-25 – CA1054/CA1056: Uri statt string für SourceUrl

### Was lief gut
- User-Hinweis auf `RecipeSource.FromUrl(Uri)` statt `NonEmptyTrimmedString` war richtig: vereinfacht den Code erheblich und bringt die Semantik auf den Punkt
- Review-Agenten lieferten konkrete, nutzbare Findings; die meisten korrekt — ein Fehlbefund (Round-Trip-Bug) konnte anhand der Architektur-Dokumentation widerlegt werden
- TDD-Hook erzwang sequentielle Test-Splits — das war korrekt und hat Fehler verhindert

### Was war schwierig
- **Review-Agent übernommen ohne kritisches Prüfen**: Der Functional-Agent schlug „silent null" für GetAll mit korrupter URL als „Performance-Tradeoff" vor — ich habe das zu schnell als `decisions.md`-Eintrag formuliert. Erst durch Rückfrage des Users wurde klar, dass das kein akzeptabler Tradeoff ist. **Learning: Vorschläge von Review-Agenten auf semantische Korrektheit prüfen, nicht nur auf technische Umsetzbarkeit.**
- **Dokumentationsbegründung zu unscharf**: Erster Entwurf für `CODING_GUIDELINE_CSHARP.md` schrieb `Guid` und `DateTimeOffset` als BCL-Typen mit Invarianten — was falsch ist. User hat das korrigiert. `Uri` ist der einzige BCL-Typ mit echter Konstruktor-Garantie (kein leerer String möglich).
- **STJ-Serialisierungsverhalten**: Behauptet, aber nicht durch Test verifiziert. Sowohl `OriginalString`-Nutzung als auch 400 vs. 500 bei ungültigem URI-String bleiben unverifiedte Annahmen bis Session 040.

### Learnings
1. Review-Agenten-Findings immer auf semantische Korrektheit prüfen — „Performance-Tradeoff" ist kein Freifahrtschein für falsche API-Semantik
2. Wenn eine Verhaltensannahme über ein Framework (STJ, ASP.NET Core) nicht durch einen Test abgesichert ist, als Tech Debt notieren und in der nächsten Session gezielt prüfen
3. Bei Dokumentationsänderungen: Behauptungen über .NET-Typen genau prüfen — „hat Invarianten durch Konstruktor" ist nicht für alle BCL-Typen wahr

### Dokumentations-Änderungen
- `docs/CODING_GUIDELINE_CSHARP.md`: `Uri`-Ausnahme in Abschnitt "Primitive Obsession" ergänzt
- `docs/history/decisions.md`: 3 neue Einträge (Uri als BCL-Primitive, OriginalString Round-Trip, GetAll 500)
- `docs/REVIEW_CHECKLIST.md`: Prüfpunkt für inkonsistente Fehlerbehandlung bei mehreren Konvertierungspfaden

---

## Session 38 – 2026-03-25 – OneOf implicit cast

### Was lief gut
- Systematische Grep-Analyse aller `FromT*`-Stellen; keine Stelle übersehen
- Guideline-Erweiterung mit Ausnahme-Tabelle ist klar und vollständig
- Stryker-Survivors schnell identifiziert und gezielt gefixt

### Was war schwierig
- **C# Interface-Typ-Falle**: Ursprüngliche Annahme war, dass impliziter Cast für `IResult` funktioniert. Drei Build-Iterationen nötig (implicit fails → explicit cast CS0030 → explizite Typargumente + `FromT1`), bis die korrekte Lösung gefunden war
- **TDD-Hook verletzt**: Beim Stryker-Fix 3 Tests auf einmal geschrieben → Hook geblockt. Auch bei Survivor-Fixes gilt: ein Test pro Zyklus

### Learnings
- **C# user-defined implicit operators gelten nicht für Interface-Typen**: Weder `return someIResult;` noch `(OneOf<T, IResult>) someIResult` kompiliert wenn `IResult` ein Interface ist. `FromT1(...)` ist in diesem Fall zwingend — kein Workaround
- **BindAsync mit Multi-Return-Lambda**: Explizite Typargumente am Methodenaufruf (`.BindAsync<TIn, TOut, TError>(...)`) sind die sauberste Lösung, damit alle `return`-Statements implizit bleiben können
- **TDD gilt auch für Stryker-Fixes**: Wenn ein Survivor gefunden wird, ist das ein fehlender RED-Test. Erst Test schreiben (RED), dann prüfen ob er grün wird. Nicht nachträglich Tests in Batches ergänzen

### Dokumentationsänderungen
- `CODING_GUIDELINE_CSHARP.md`: Abschnitt "OneOf-Instanz erzeugen" mit Ausnahme-Tabelle ergänzt
- `AGENT_MEMORY.md`: Architektur-Entscheidung "OneOf-Instanz erzeugen – Rangfolge" + Test-Pattern `ValueOrThrowUnreachable()` in Unit-Tests ergänzt

---

## Session 37 – 2026-03-24 – AnalysisMode=All

### Was lief gut
- Systematische Kategorisierung der ~250 neuen Warnings (fix vs. suppress vs. tech debt) bevor irgendwas geändert wurde
- Der User-Dialog über jede Regel (Was macht sie? Beispiel? Gegenbeispiel? Warum deaktivieren?) war zeitintensiv aber hat zu substanziell besseren Entscheidungen geführt: CA1054/CA1056 als Tech Debt statt Suppress, CA1848/CA1305 per Pragma statt global, S1905 per explizite Typargumente statt Suppress
- `NonEmptyList<T>` mit `IEquatable<T>` via `SequenceEqual` ist die semantisch korrekte Lösung – besser als Suppress
- `NotFound<T>` zu `readonly record struct` ist eine elegante Vereinfachung

### Was war schwierig
- **editorconfig Glob-Falle (wieder)**: `[Server/**/*.cs]` wurde trotz des bekannten Bugs aus Session 36 erneut falsch verwendet. Drei Build-Runden nötig bis alle Suppressions griffen
- **S1905 False Positive**: Versuch, den `(IResult)`-Cast zu entfernen → `as IResult` (nullable, falsch) → Revert. Erst die Analyse der `MapError`-Signatur hat das echte Problem offenbart (Generic-Type-Inferenz)
- **Hook blockiert partial class Program Pragma**: Code-Quality-Hook erkannte `class` ohne `record` als Verstoß, obwohl es eine Framework-Pflicht war. Lösung via editorconfig statt Pragma

### Learnings
- **editorconfig `/**/*.cs` Falle – endgültig merken**: `[Server/**/*.cs]` matcht NICHT `Server/Helpers.cs`. Selbst wenn der Bug aus Session 36 bekannt ist, muss er beim Schreiben neuer Sektionen aktiv vermieden werden. Checkliste: jede neue `/**/*.cs`-Sektion auf Root-Dateien prüfen und sofort auf `{dir,dir/**}/*.cs` ändern.
- **S1905 in ROP-Ketten nicht entfernen ohne Compile-Check**: Upcasts in Generic-Methoden sind oft nicht redundant – sie steuern Typ-Inferenz. Lösung: explizite Typargumente `MapError<TIn, TErrorIn, TResult>` statt Cast oder Pragma.
- **Regeln-Diskussion lohnt sich**: Wenn der User für jede Suppression eine vollständige Begründung fordert, führt das zu besserem Code. Auch für zukünftige Sessionen: erst erklären, dann supprimieren.

### Dokumentationsänderungen
- `AGENT_MEMORY.md`: editorconfig Glob-Falle + S1905 in ROP-Ketten als Architektur-Entscheidungen dokumentiert

---

## Session 36 – 2026-03-24 – Analyzer-Cleanup

### Was lief gut
- Build-Output gezielt gefiltert (`grep -oE "(warning|error) [A-Z0-9]+:"`) statt blind durch 72K Output zu scrollen – sehr effizient
- editorconfig-Bug (`/**/*.cs` matchte keine Root-Dateien) durch systematische Analyse diagnostiziert: Warnings gezielt nach Dateiort gefiltert → Hypothese bestätigt
- Hook-Pattern-Fix (`\.Tests[/\\]`) korrekt und sofort mit 57 bestehenden Tests verifiziert
- Kontext-Bewusstsein: Hooks-Review rechtzeitig abgebrochen statt oberflächliche Aussage zu verteidigen

### Was war schwierig
- `Write` statt `Edit` für `ParallelTestLogging.cs` – musste durch User-Feedback korrigiert werden
- Hooks-Review: nur 5 Zeilen je Datei gelesen, dann pauschal "kein Hook redundant" behauptet – zu schnell, zu oberflächlich
- `cmd.exe`-Redirect mit `>` mehrfach durch Hook geblockt, bis korrektes Muster (Variable capturen) angewendet wurde

### Learnings
- **Hooks-Review = vollständige Dateilektüre**: Jede Check-Datei komplett lesen, dann systematisch gegen aktive Analyzer-Regeln abgleichen. Keine Aussage aus 5-Zeilen-Snippets ableiten.
- **`Write` nur für Neudateien oder echte Rewrites**: Bei vorhandenen Dateien mit mehreren Änderungen trotzdem Edit bevorzugen – der User sieht sonst keine diff
- **editorconfig `/**/*.cs` Falle**: Dieses Pattern matchte keine Dateien direkt im Root-Verzeichnis. Fix: `{Dir,Dir/**}/*.cs` Syntax. Diagnose: Warnings nach Dateiort filtern und prüfen ob Root vs. Subdir

### Dokumentationsänderungen
Keine.

---

## Session 35 – 2026-03-24 – Statische Code-Analyse Einrichtung

### Was lief gut
- Das Suppression-Framework (Category 1/2/3) hat sich als sehr nützlich erwiesen: klare Kriterien, wann suppresst wird vs. wann nachgefragt wird vs. wann gefixt wird. Wiederverwendbar für jede zukünftige Analyzer-Einführung.
- Die Diskussion über globale vs. lokale Suppressions (editorconfig vs. pragma) hat zu einer besseren Strukturierung geführt: editorconfig für File-Pattern-Regeln, pragma für einzelne Dateien.
- `eslint-plugin-functional` v9 mit flat config: `projectService: true` statt `project: true` ist die korrekte Lösung für composite TypeScript-Projekte (tsconfig mit `files: []` und `references`).
- Die Frage "ist das eine unbewusste Konvention geworden?" hat echte Probleme aufgedeckt: `_client` als protected Field mit Underscore-Prefix, DTO-Dateien mit mehreren Typen, `List<T>?` statt `IReadOnlyList<T>?` in Test-Buildern.

### Was war schwierig
- Kontext-Erschöpfung: die Kombination aus vielen Dateilesen, Build-Outputs und ausführlichen Analysen hat den Kontext sehr schnell gefüllt. Große Tooling-Sessions sollten wenn möglich in zwei Sitzungen aufgeteilt werden: (1) Evaluation + Entscheidung, (2) Implementierung.
- Anzahl der Implementierungsaufgaben unterschätzt: Analyse ergab ~370 Warnings mit je eigener Behandlung. Nur der editorconfig-Teil wurde fertig; alle Pragmas, Code-Fixes und Refactorings sind für die nächste Session offen.

### Learnings
- **Tooling-Sessions aufteilen:** Evaluation/Entscheidung und Implementierung in separate Sessions. Evaluation generiert viel Kontext-Verbrauch durch Build-Outputs und Diskussionen.
- **S4581 (`== default` vs `== Guid.Empty`):** `default` für uninitialisierten Value-Type-Guard ist bewusst und explizit in `decisions.md` dokumentiert. S4581 ist hier kein Bug-Schutz sondern reine Stilpräferenz.
- **`functional/no-expression-statements` ist für React unbrauchbar:** React-Hooks und Rendering sind inherent side-effectful. Diese Regel muss immer für React-Projekte deaktiviert werden.
- **`no-mixed-types` ist wertvoll:** erzwingt Property-Syntax (`onClick: () => void`) statt Method-Syntax (`onClick(): void`) in Types – verbessert Typ-Safety durch `strictFunctionTypes`.

### Dokumentations-Änderungen
- `decisions.md`: S4581-Entscheidung dokumentiert (`== default` bleibt)
- `CODING_GUIDELINE_CSHARP.md`: kein Update nötig (Guid-Guard-Beispiel bleibt mit `== default`, s. decisions.md)

---

## Zweck

1. Wissen festhalten, das in künftigen Sessions hilft – auch wenn es schwierig zu implementieren war und warum
2. Ableiten, ob Dokumentation angepasst werden muss
3. Muster erkennen, die auf strukturelle Probleme hinweisen

**Periodische Überprüfung:** Am Ende jeder Phase (SKELETON → MVP → V1) alle bisherigen Einträge durchsehen:
- Sind die Learnings noch aktuell / gültig?
- Gibt es wiederkehrende Muster → strukturelles Problem, das grundlegend gelöst werden sollte?
- Kann ein Learning aus der Dokumentation entfernt werden, weil es inzwischen etablierte Praxis ist?

---

### 2026-03-23 – Session 34: Stryker-Survivors, Full State Assertions, Test-Konsolidierungen

**Was lief gut:**
- Parallele Agenten für Test-Review-Analyse sehr effizient (6 Agenten gleichzeitig)
- Systematisches Vorgehen: erst lesen, dann alle Partial Assertions identifizieren, dann beheben
- Stryker-Survivors zügig behoben, 100% direkt wiederhergestellt

**Was schwierig war:**
- TDD-Hook blockiert mehr als 1 neuen `[TestCase]` pro Edit – korrekt für Produktionscode, im reinen Test-Refactoring-Kontext aber bremsend (musste Tab/Newline-Fälle einzeln mit Tests dazwischen einfügen)
- Begründung für Navigation-Property-Ausschlüsse in `BeEquivalentTo` war zunächst unklar formuliert: Der Grund ist nicht „Properties unbekannt", sondern „nicht geladen (kein Include)")

**Learnings:**
- Partial Assertion vs. Full State: Einzelne `.Should().Be(...)` auf Properties sind Partial Assertions – auch wenn mehrere davon hintereinander stehen. Immer `BeEquivalentTo` auf das gesamte Objekt.
- Benannte Parameter für Record-Konstruktoren sind Pflicht in Tests (wurde in `TDD_PROCESS.md` dokumentiert)
- Vor jedem neuen Test prüfen: eigener Test oder `[TestCase]`? Entscheidungskriterien in `TDD_PROCESS.md` ergänzt
- Redundanter zweiter Parameter in `[TestCase]` vermeiden, wenn Input = Expected (direkt `sourceUrl` als Expected verwenden statt `expectedUrl`)

**Dokumentations-Änderungen:**
- `TDD_PROCESS.md`: Benannte-Parameter-Regel + „Test vs. TestCase"-Entscheidungshilfe ergänzt ✅

---

### 2026-03-18 – Session 33: Shared-Projekt aufgelöst, Projektstruktur konsolidiert

**Was lief gut:**
- Migration vollständig und sauber: `Shared/`, `mahl.Shared.Test/`, `mahl.Tests.Shared/`, `mahl.Server.Tests/` alle aufgelöst
- "Erst kopieren (cp), dann anpassen (Edit)" – transparenter Ansatz auf User-Hinweis, ermöglicht gezieltes Review der tatsächlichen Änderungen
- Alle 151 .NET-Tests + 57 Hook-Tests grün nach Migration

**Was schwierig war:**
- Hardcodierte Projektnamen in `test_patterns.py` (`TEST_FILE_PATTERN`) wurden übersehen → Check griff nach Rename nicht mehr → echte funktionale Regression
- Viele beteiligte Dateien (Scripts, Hooks, Hook-Tests, Skills, Docs) – trotz Grep-Vorab-Check einen Treffer verpasst

**Learnings:**
- **Projekt-Rename: Hooks auf hardcodierte Pfade prüfen** – nicht nur Scripts und Docs, sondern auch `.claude/hooks/checks/*.py` auf Projektnamen-Strings durchsuchen. Am einfachsten: `grep -r "mahl\.\|Server\.Tests\|Shared" .claude/hooks/` vor und nach dem Rename.
- **cp + Edit statt Write**: Beim Verschieben von Dateien `cp` (identischer Inhalt) + danach `Edit` (nur gezielte Änderungen) nutzen. Das ist reviewbarer als `Write` mit neuem Inhalt, weil der User den Diff der Anpassungen sehen kann.
- **`--project`-Flag in dotnet-test.py**: War nur bei mehreren Testprojekten sinnvoll – bei einem einzigen Projekt konsequent entfernen statt kommentarlos weiterschleppen.

**Dokumentations-Änderungen:** Scripts, Hooks, Hook-Tests, Skill, DEV_WORKFLOW, TDD_PROCESS, slow-commands – alle auf neuen Projektnamen aktualisiert.

---

### 2026-03-18 – Session 32: Domain-ID-Migration abgeschlossen + Sequence<T>

**Was lief gut:**
- Design-Diskussionen produktiv: `default(T)`-Schutz, Fail-Fast vs. Validation-Semantik, funktionale Varianten für `Sequence<T>`
- Guideline-Lücke (`default(T)` schützen) klar identifiziert und direkt geschlossen
- `Sequence<T>` mit `ImmutableList + Aggregate` – saubere funktionale Lösung ohne Side Effects
- AGENT_MEMORY und Technische Schuld konsequent aktuell gehalten

**Was schwierig war:**
- `RecipeIngredient.Id` GREEN-Phase komplex: Guard brach bestehenden `BeEquivalentTo`-Test (alle Properties werden accessed) → `Create()` + Tuple-Struktur mussten synchron angepasst werden
- Redundanter Test `RecipeIngredient_Create_SetsIdFromParameter` hinzugefügt – erst nach User-Hinweis entfernt (Full-State-Assertion-Test deckte das Verhalten bereits ab)
- Stryker Shared-Projekt: kein JSON-Report generiert → Summary-Script nicht nutzbar → Survivor aus Session unbekannt

**Learnings:**
- **Guard + BeEquivalentTo**: Wenn ein Guard zu einer bestehenden Property hinzugefügt wird, können bestehende `BeEquivalentTo`-Tests brechen (alle Properties inklusive der neuen mit Guard werden accessed). Vor dem GREEN-Schritt prüfen welche Tests das neue Property nutzen.
- **Neue Tests vor Full-State-Assertions prüfen**: Bevor ein neuer Test geschrieben wird, prüfen ob das Verhalten nicht schon in einem bestehenden Full-State-Assertion-Test abgedeckt ist.
- **Sequence<T> ist Übergangslösung**: Fail-Fast-Semantik ist für den aktuellen API-Contract (single string error) korrekt. MVP erfordert Validation-Semantik + strukturierte Mehrfach-Fehler.
- **TDD-Verletzung ≠ Gold-Plating**: Ein Guard, der erwünscht ist aber ohne RED-Test implementiert wurde, ist eine TDD-Verletzung (Prozess-Problem), kein Gold-Plating (unnötiger Code). Terminologie matters.
- **Stryker Shared-Projekt ohne JSON**: Das Summary-Script kann den Shared-Projekt-Report nicht finden (falsches Output-Verzeichnis). Nächste Session: klären warum kein JSON generiert wird.

**Dokumentations-Änderungen:**
- `CODING_GUIDELINE_CSHARP.md` Abschnitt 3: `default(T)`-Schutz + Pflicht-Tests dokumentiert ✅
- `CODING_GUIDELINE_CSHARP.md` Abschnitt 7: Kanonisches Beispiel mit `Guid id` + Guard aktualisiert ✅
- `AGENT_MEMORY.md`: "Gold-Plating" → "TDD-Verletzung", UUID-v7-Status vollständig, Tech-Debt bereinigt, Sequence-MVP-Schuld eingetragen ✅

---

### 2026-03-17 – Session 31: Stryker 100% + Domain-ID-Migration (Ingredient)

**Was lief gut:**
- Stryker 4.14.0 Upgrade löste .NET-10-Compile-Error sofort
- 90.7% → 100% Stryker-Score in einem Durchgang (15 Survivors eliminiert)
- User-Feedback ("Gold-Plating ohne Test") hat Implementierung verbessert – `_id == Guid.Empty` Guard erst nach RED-Test
- Produktive Encapsulation-Diskussion: `IngredientId` als redundantes Property erkannt und entfernt

**Was schwierig war:**
- `// Stryker disable once String Statement` (Leerzeichen) funktioniert **nicht** – Stryker ignoriert alles nach dem ersten Typ. Korrekte Syntax: `String,Statement` (Komma)
- `Results.UnprocessableEntity("text")` serialisiert als JSON-String → `ReadAsStringAsync()` liefert `"\"text\""`, nicht `"text"`. Fix: `ReadFromJsonAsync<string>()`

**Learnings:**
- **Stryker Multi-Mutator-Syntax**: `// Stryker disable once String,Statement` (Komma, kein Leerzeichen). Leerzeichen führt dazu, dass nur die erste Kategorie erkannt wird.
- **JSON-Body bei `Results.UnprocessableEntity(string)`**: ASP.NET Core serialisiert String-Bodies immer als JSON. Für Body-Assertions immer `ReadFromJsonAsync<string>()` verwenden, nie `ReadAsStringAsync()`.
- **Gold-Plating-Check im TDD**: Backing-Field-Guards wie `_id == Guid.Empty ? throw : _id` sind ohne RED-Test Gold-Plating – erst implementieren, wenn ein Test den Guard explizit fordert.
- **`IngredientId` als Convenience-Delegation entfernen**: Wenn ein Property nur auf ein anderes Property eines enthaltenen Objekts delegiert (`=> _ingredient.Id`), ist es redundant. Callers verwenden `Ingredient.Id` direkt.
- **`ToDto(Recipe)` erfordert mehr als `Recipe.Id`**: Auch `RecipeIngredient.Id` (junction table) und `RecipeStep.Id` müssen in Domain-Typen wandern, bevor `RecipeDbType` aus `ToDto` eliminiert werden kann.

**Dokumentations-Änderungen:**
- `CODING_GUIDELINE_CSHARP.md` Abschnitt 8: Multi-Mutator-Komma-Syntax ergänzt ✅
- `docs/history/decisions.md`: `IngredientId`-Property-Entfernung dokumentiert ✅
- `AGENT_MEMORY.md`: Status, Prioritäten, Tech-Debt, Stryker-Score aktualisiert ✅

---

### 2026-03-17 – Session 30: .NET 10 Upgrade + UUID v7 Migration

**Was lief gut:**
- Upgrade vollständig in einem Durchgang: Build → Test-Failures diagnostiziert → behoben → alle Tests grün
- UUID v7 Migration systematisch alle Schichten in einem Zug (Domain → DbTypes → DTOs → Endpoints → Tests)
- EF Core 10 TestWebApplicationFactory-Ursache korrekt diagnostiziert (auch wenn mehrere Iterationen nötig waren)

**Was schwierig war:**
- **EF Core 10 TestWebApplicationFactory** brauchte 4 Iterationen:
  - Iteration 1: Nur `DbContextOptions<T>` entfernt → Npgsql-Konflikt beim `EnsureDeletedAsync()` im TearDown
  - Iteration 2: `EnableServiceProviderCaching(false)` → löst Konflikt, bricht aber InMemory-Sharing (jeder Context bekommt eigene interne InMemory-Instanz → `SeedRecipes` schreibt in DB A, Lesen aus leerem DB B)
  - Iteration 3: `IDbContextOptionsConfiguration<T>` zusätzlich entfernen + `EnableServiceProviderCaching(false)` → InMemory-Sharing weiterhin kaputt
  - Iteration 4: `IDbContextOptionsConfiguration<T>` entfernen OHNE `EnableServiceProviderCaching(false)` → ✅
- **Swashbuckle** ist ab .NET 10 inkompatibel (`Method 'GetSwagger' does not have an implementation`)

**Learnings:**
- **EF Core 10 TestWebApplicationFactory**: `AddDbContext(...UseNpgsql(...))` registriert jetzt ZWEI Descriptors: `DbContextOptions<T>` + `IDbContextOptionsConfiguration<T>`. Für Test-Override müssen BEIDE entfernt werden.
- **`EnableServiceProviderCaching(false)` nicht verwenden**: Bricht InMemory-Datenbanksharing – jeder `DbContext` bekommt eine eigene interne InMemory-Instanz. Seeding und Lesen in verschiedenen Scopes sehen unterschiedliche "Datenbanken".
- **Swashbuckle ist ab .NET 10 inkompatibel**: `AddOpenApi()` / `MapOpenApi()` (natives ASP.NET Core) ist der Ersatz. War bereits als `Microsoft.AspNetCore.OpenApi` im Projekt.
- **UUID-Migration ist zweistufig**: DB-Schicht (PKs/FKs, DTOs, Endpoints) ist jetzt erledigt. Domain-Typen brauchen noch eigene `Guid Id`-Properties – das ist der nächste Schritt, der dann `_ingredientId`-Workaround und `ToDto(Recipe, RecipeDbType)` überflüssig macht.

**Dokumentations-Änderungen:**
- AGENT_MEMORY.md: ✅ Letzter Stand, Prioritäten, Architektur-Entscheidungen, Tech-Debt, Stryker-Hinweis aktualisiert
- DEV_WORKFLOW.md: Kein Änderungsbedarf (Fix ist im Code, kein Workflow-Dokument)
- Alle anderen Dokumente: kein Änderungsbedarf

---

### 2026-03-17 – Session 29: Review Session-27-Änderungen, ValueOrThrowUnreachable, Stryker-Scope

**Was lief gut:**
- Review-Agenten (code-quality, functional, test-quality) haben echte Lücken gefunden, die weder Selbst-Review noch Stryker aufgedeckt hatten: falscher Codepfad in `Post_EmptyTitle`, fehlende Quantity-Grenzwert-Tests
- `ValueOrThrowUnreachable()`-Pattern ist sauber entstanden durch iterative Diskussion (User hat Namensgebung und Design verbessert)
- Stryker `disable once` vs. eigenständiges Statement systematisch untersucht und verstanden – altes Verhalten (Timeout-Masking) aus alten Reports erklärt

**Was schwierig war:**
- Stryker `disable once` in Method-Chains funktioniert nicht zuverlässig: Kommentar zwischen verketteten Aufrufen (eigene Zeile) wird nicht als "nächstes Statement" interpretiert. Workaround nötig: Aufruf auf eigenständiges Statement aufteilen.
- Frühere "100%-Stryker"-Einträge in AGENT_MEMORY waren falsch: Mutations haben ge-timed-out statt als `[Ignored]` markiert zu werden – Timeout maskiert den Bug. Erkannt erst durch `--detail`-Flag und Vergleich mit alten Reports.
- Stryker-Scope bei `--mutate`-Läufen schließt andere Dateien aus: `Quantity.cs`-Mutations wurden nie getestet, weil nur `RecipesEndpoints.cs` im Scope war. Die fehlenden Grenzwert-Tests blieben dadurch unentdeckt.

**Learnings:**
- **Stryker `disable once` braucht eigenständiges Statement**: Der Kommentar muss unmittelbar vor einem Statement stehen. Inline in einer Method-Chain (eigene Zeile zwischen zwei Aufrufen) funktioniert NICHT. Aufruf in separate Statement-Zeile aufteilen.
- **Stryker-Reports mit `--detail` auf Timeout-Status prüfen**: `[Timeout]` mit 0 Survivors klingt gut, ist aber trügerisch. Wirklich sicher ist `[Ignored]` für bewusst ausgeschlossene Mutationen.
- **Scoped Stryker-Läufe explizit erweitern**: Wenn Validierungslogik in Datei B liegt (z.B. `Quantity.cs`), aber nur Datei A getestet wird, können Test-Lücken unentdeckt bleiben. Nach jedem Feature-Review auch alle beteiligten Domain-Dateien in den Scope aufnehmen.
- **`ValueOrThrowUnreachable()` als idiomatisches Pattern**: Ersetzt `.Match(r => r, _ => throw new InvalidOperationException("Unreachable."))` in pre-validierten LINQ-Ketten. Kapselt Stryker-Suppression an einem Ort. Zusätzlich `ValueOrThrow(string message)` für Custom-Messages.

**Dokumentations-Änderungen:**
- CODING_GUIDELINE_CSHARP.md: ✅ `ValueOrThrowUnreachable()`-Pattern dokumentiert (vor Abschnitt 5)
- AGENT_MEMORY.md: ✅ Stryker-Tabelle korrigiert, neue Tech-Debt-Einträge, `disable once`-Hinweis aktualisiert
- DEV_WORKFLOW.md: Kein Änderungsbedarf
- TDD_PROCESS.md: Kein Änderungsbedarf
- ARCHITECTURE.md: Kein Änderungsbedarf

---

### 2026-03-16 – Session 28: Hook-Architektur (Wrapper-Scripts statt Regex-Patterns)

**Was lief gut:**
- Diskussion zur Pro/Contra-Analyse der verschiedenen Varianten (Patterns vs. Scripts, Variable vs. Datei vs. direkt) war produktiv und hat zu klaren Entscheidungen geführt
- Iterativer Review-Prozess: User hat jede Änderung einzeln abgenommen und Unklarheiten (Stryker-Script als Wrapper, npm install, `--verbose`-Flag) direkt adressiert
- Hook-Bereinigung sauber durchgeführt: `PRIORITY_ALLOW_PATTERNS` vollständig entfernt inkl. Variable, Kommentar und Schritt 0 in `check_command`
- RED-Tests für neue DENY-Patterns (`dotnet test` direkt, Variable-Capture für test) direkt mitimplementiert – kein nachträglicher Test-Nachtrag nötig

**Was schwierig war:**
- `dotnet test` → DENY war ursprünglich nicht geplant; erst nach User-Rückfrage ("warum ist fall-through okay?") erkannt, dass Enforcement via DENY nötig ist
- `output=$(cmd.exe ...)` Allow-Pattern wurde beim Bereinigen zu weit entfernt – für `dotnet build` war es noch gültig; musste nachträglich wieder ergänzt werden
- Mehrfache Edit-Ablehnungen durch den User (Formulierungen in Fehlermeldungen, `--verbose`-Flag vergessen, Kommentar nach Löschen) → zeigt, dass Änderungen an Fehlermeldungen sehr sorgfältig formuliert werden müssen

**Learnings:**
- Beim Entfernen von Code immer prüfen: Wird dieses Pattern noch an anderer Stelle gebraucht? (Hier: Variable-Capture für build)
- Fehlermeldungen im Hook sind Agent-Dokumentation – gleiche Sorgfalt wie bei Guidelines-Texten
- Wenn Scripts als Ersatz für direkte Befehle eingeführt werden: sofort DENY für den direkten Aufruf ergänzen, sonst bleibt der alte Weg offen

**Dokumentations-Änderungen:**
- DEV_WORKFLOW.md: ✅ aktualisiert (Scripts als primäre Beispiele, Varianten A–D, Stryker-Sektion)
- TDD_PROCESS.md: ✅ aktualisiert (`--files` → `--mutate` + Script)
- Skills (tdd-workflow, review-code): ✅ aktualisiert
- slow-commands.md: ✅ aktualisiert
- AGENT_MEMORY.md: ✅ wird in dieser Session aktualisiert
- CODING_GUIDELINE_CSHARP.md / CODING_GUIDELINE_TYPESCRIPT.md / NFR.md / ARCHITECTURE.md: keine Änderungen nötig

---

### 2026-03-15 – Session 27: Domain-Refactoring + stryker-summary --detail

**Was lief gut:**
- `stryker-summary.py --detail`-Flag sauber implementiert und dokumentiert – kein Ad-hoc-Python mehr nötig
- Architektur-Diskussion zur Domain-Modellierung (`RecipeIngredient` + `Ingredient`, UUID, SourceImagePath, StepNumber) strukturiert geführt – User hat jeden Schritt aktiv mitgedacht und korrekte Designentscheidungen getroffen
- `BeEquivalentTo` mit `WithStrictOrdering()` als elegante Lösung für ID-Reihenfolgen-Assertion entdeckt – ersetzt zirkuläre ID-Referenzen und killt den OrderBy-Mutanten
- Full State Assertion korrekt angewendet: `GetAllStepsFromDb()` als separater Helfer (kein Include in bestehenden Helfern), DB-Direkt-Check statt API-Roundtrip
- 3 von 3 neuen Stryker-Survivors ohne `disable once` gekillt (durch echte Tests)

**Was war schwierig / hat nicht funktioniert – und warum:**
- Hook-Regelung für Bash-Pipes nach cmd.exe war unklar: Der Hook erlaubt Pipes für Stryker, nicht für dotnet test. Lösung: Variante A (output in Variable capturen). Hook-Fehlermeldung wurde in der Session verbessert → jetzt klare Anleitung mit 3 Varianten
- Edit-Tool hat versehentlich eine Lambda-Deklaration doppelt erzeugt (Zeile 35+36 in RecipesEndpoints.cs) – erst beim Test-Run aufgefallen. Ursache: Der alte Lambdakopf war kein Teil des ersetzten Strings. Künftig: Beim Ersetzen größerer Blöcke immer den vollen Kopf in `old_string` einschließen
- Schritt 4–6 (Autor-Review, Review-Agenten, Commit) nicht abgeschlossen – Context wurde knapp

**Learnings:**
- `BeEquivalentTo(expected, opts => opts.WithStrictOrdering())` ist das korrekte Pattern wenn Reihenfolge UND Inhalt geprüft werden sollen – normal ist `BeEquivalentTo` ungeordnet
- Zirkuläre ID-Referenzen (`new StepDto(created.Steps[0].Id, ...)`) sind verbotene Partial Assertions: die erwartete ID kommt aus dem zu testenden Objekt selbst. Immer DB-IDs verwenden
- `stepsInDb[0].Id` nach `GetAllStepsFromDb().OrderBy(s => s.StepNumber)` ist die korrekte Referenz für Step-IDs in POST-Response-Assertions
- Domain-Factory-Methoden (`Create()`) dürfen und sollen Primitives als Parameter nehmen – der Primitive-Obsession-Hook ist in diesem Kontext ein bekanntes Advisory
- UUID v7 ist die richtige Wahl für PKs (time-ordered, index-freundlich, RFC 9562) – in .NET 9+ nativ als `Guid.CreateVersion7()` verfügbar → Migration nach .NET-Upgrade planen

**Dokumentations-Updates (in dieser Session umgesetzt):**
- `docs/DEV_WORKFLOW.md`: `--detail`-Flag für stryker-summary.py dokumentiert ✅
- `docs/DEV_WORKFLOW.md`: Bash-Pipe-Regeln mit 3 Varianten (A/B/C) vollständig beschrieben ✅
- `.claude/hooks/check-bash-permission.py`: Fehlermeldung für Stryker + Pipe-Alternativen verbessert ✅

**Dokumentations-Änderungsvorschläge (zur Genehmigung):**
- `docs/CODING_GUIDELINE_CSHARP.md`: Hinweis ergänzen, dass `BeEquivalentTo` standardmäßig ungeordnet ist und `WithStrictOrdering()` nötig ist, wenn Reihenfolge getestet werden soll
- `docs/ARCHITECTURE.md`: UUID v7 als geplante PK-Strategie dokumentieren (nach .NET 10-Upgrade), mit Begründung (time-ordered, kein DB-Roundtrip für ID)

---

### 2026-03-12 – Session 26: RecipesEndpoints Layer-Isolation + Architektur-Fix

**Was lief gut:**
- Layer-Isolation erfolgreich: `ToDomain()` → `OneOf<Recipe, Error<string>>`, GET /{id} mit `Results.Problem()` statt throw – sauber in einem TDD-Zyklus
- Architektur-Relic entdeckt und behoben: `ToDto()` war auf `RecipeDbType` definiert (Verletzung der Coding-Guideline „Read-Pfad: DbType → Domain → DTO"). Durch Umstellung auf `ToDto(this Recipe domain, RecipeDbType db)` wurde gleichzeitig der OrderBy-Stryker-Survivor gekillt – Domain ist jetzt autoritativ für Step-Reihenfolge
- Stryker `disable once`-Verhalten tiefgehend untersucht und verstanden (Statement-Scope, nicht Zeilen-Scope). Irrtum mit zwei überlagernden Kommentaren erkannt und korrekt behoben
- Alle 3 echten Survivors mit echten Tests gekillt (CorruptRecipe 500, Fehlermeldung, Location-Header); 0 Survivors, 100% Mutation Score für RecipesEndpoints
- NTFS-Read-Problem als behoben bestätigt → Memory-Eintrag entfernt

**Was war schwierig / hat nicht funktioniert – und warum:**
- `// Stryker disable once String` Scope-Verhalten war unklar: Kommentar vor `"/"` innerhalb der Argumentliste deaktiviert trotzdem alle String-Mutations des gesamten Statements (weil das ganze `MapPost(...)` ein syntaktisches Statement ist). Erst durch Analyse zweier überlagernder Kommentare und gezieltem Stryker-Re-Run wurde das Verhalten verstanden
- Ad-hoc-Python-Skripte zur JSON-Report-Analyse wurden mehrfach genutzt – erfordern jedes Mal manuelles Abnicken vom User und sind gefährlich wenn das „automatisch" abgehakt wird. Lösung steht aus (Task für nächste Session): `stryker-summary.py` um `--detail`-Flag erweitern
- Stryker crashte zweimal mit Race Condition – Retry hat jeweils geholfen

**Learnings:**
- `// Stryker disable once MutatorType` gilt für das **nächste syntaktische Konstrukt (Statement)**, nicht für die nächste Zeile. Bei Multi-Argument-Lambdas (wie `MapPost(route, lambda)`) wird die gesamte Invocation als ein Statement betrachtet. Lösung: Kommentar muss direkt vor dem Ziel-String-Literal stehen UND es darf kein zweiter Kommentar auf Statement-Ebene davor stehen
- `ToDto(this Recipe domain, RecipeDbType db)` ist besser als `ToDto(this RecipeDbType db)`, aber noch nicht ideal: das DB-Objekt wird noch für Step-IDs, RecipeIngredient-IDs und Ingredient-Namen benötigt. Step-Nummern könnten aus Listenposition (idx+1) abgeleitet werden. Technische Schuld – nächste Session
- Gold-Plating-Code vor RED: nicht nur Test schreiben und grün sehen, sondern zuerst die Implementierung reduzieren (z.B. Location-URL auf `null`), dann RED bestätigen, dann GREEN

**Dokumentations-Updates (in dieser Session umgesetzt):**
- `REVIEW_CHECKLIST.md`: Eintrag „ToDto auf DbType statt Domain-Typ" ergänzt ✅
- `docs/DEV_WORKFLOW.md` (Stryker-Sektion): `disable once`-Scope-Verhalten mit Erklärung und korrektem Beispiel dokumentiert ✅

---

### 2026-03-11 – Session 23: Retrospektive + Skill-Verbesserungen

**Was lief gut:**
- Parallele Sub-Agenten (Prozess-Auditor, Qualitäts-Analyst, Velocity-Tracker) lieferten unabhängig konsistente Befunde – alle drei identifizierten Guideline-Internalisierung als Kernproblem
- Nutzerfeedback korrigierte Fehlinterpretation: Stryker war kein Velocity-Killer, sondern Symptom-Detektor für Prinzipienverstöße – wichtige Klarstellung für das Selbstbild des Projekts
- Drei konkrete Skill-Verbesserungen konnten direkt umgesetzt werden

**Was war schwierig / hat nicht funktioniert – und warum:**
- `Read`-Tool und `cat` scheiterten für `.claude/skills/`-Dateien mit NTFS-Permissions-Bug (WSL2 `statx()` schlägt fehl). Umweg via `cmd.exe /c type ...` nötig. Das Edit-Tool gab ENOENT zurück, schrieb die Datei aber trotzdem – inkonsistentes Verhalten, das schwer zu debuggen war.
- Zwei der drei Edits (`write-code`, `tdd-workflow`) schlugen mit ENOENT fehl, haben aber dennoch geschrieben – der Zustand nach dem Edit war korrekt, aber die Fehlerrückmeldung war irreführend.

**Learnings:**
- Bei `.claude/skills/`-Dateien sofort `cmd.exe /c type` nutzen – Read/cat schlägt fehl (NTFS-Problem). Kein dreifacher Fehlversuch mehr.
- Edit-Tool kann bei NTFS-Dateien ENOENT melden und trotzdem schreiben – nach fehlgeschlagenem Edit via `cmd.exe type` verifizieren ob die Änderung trotzdem ankam.
- Die Retro-Methode mit 3 parallelen Analyse-Agenten ist effektiv: Unabhängige Befunde aus verschiedenen Blickwinkeln konvergieren zuverlässig auf die echten Probleme.
- Der eigentliche Root Cause fast aller Qualitätsprobleme war ein einziger: Guidelines werden gelesen aber nicht internalisiert. Alle anderen Probleme (Stryker-Findings, Rework, Hooks) sind Konsequenzen daraus.

**Dokumentations-Änderungsvorschläge:**
- docs/ARCHITECTURE.md: Nein
- docs/GLOSSARY.md: Nein
- docs/REVIEW_CHECKLIST.md: Nein
- docs/NFR.md: Nein
- Phasen-Spec: Nein
- CLAUDE.md: **Vorschlag:** Hinweis ergänzen, dass `.claude/skills/`-Dateien per `cmd.exe /c type` gelesen werden müssen (NTFS-Bug). → Bitte um Bestätigung vor Umsetzung.

---

### 2026-03-11 – Session 24: Stryker L37+L52 + Schema-Änderung Unit NULL + Quantity.Create-Refactoring

**Was lief gut:**
- L37 (AND→OR) sauber durchgezogen: delete → RED → GREEN → Stryker 0 Survivors
- L52 (string.Empty → null) führte zu einer produktiven Designdiskussion, die zu einer besseren Lösung führte (NULL statt leerer String, Option B Quantity.Create)
- Diskussion über API-Vertragsklarheit (`string?` vs `string`) war wertvoll und führte zu einer klaren Entscheidungsregel

**Was war schwierig / hat nicht funktioniert – und warum:**
- `--no-build` lieferte false GREEN: nach Codeänderungen muss immer neu gebaut werden → `dotnet test` ohne `--no-build`
- Die Kaskade der Schema-Änderung (Unit → string?) zog sich durch 7 Dateien und dauerte länger als erwartet
- Mehrere Designdiskussionen (null vs `""`, Option A vs B, `string?`-Signalsemantik) verlängerten die Session erheblich – nicht schlecht, aber zeitintensiv
- `??string.Empty`-Ablehnung vs. Akzeptanz: Kontext entscheidend – als Normalisierung intern OK, als "null wegschummeln" nicht OK

**Learnings:**
- **`string?` als Signatur-Entscheidung**: `string?` signalisiert "null ist erwarteter Input". Wenn null ein Fehler ist, `string` nehmen + Aufrufer schützt sich. Wenn null und leer dasselbe bedeuten, `?? string.Empty` als interne Normalisierung OK.
- **Schema-Änderungen ohne Migration**: Solange keine Produktionsinstanz existiert, können Schema-Änderungen direkt gemacht werden. Seed-Daten prüfen ob Anpassung nötig.
- **`--no-build` niemals nach Codeänderungen**: Immer `dotnet test` (mit Build) nach Änderungen an Produktionscode.
- **Quantity.Create(NonEmptyTrimmedString)**: Wenn ein Factory-Parameter bereits als Domain-Typ vorliegen kann, ist das die sauberere Signatur gegenüber `string`.

**Dokumentations-Änderungsvorschläge:**
- `docs/ARCHITECTURE.md`: Nein
- `docs/GLOSSARY.md`: Nein
- `docs/CODING_GUIDELINE_CSHARP.md`: **Ja** – Entscheidungsregel für `string` vs `string?` als Factory-Parameter ergänzen: "`string?` nur wenn null ein erwarteter, verarbeitbarer Input ist. Wenn null ein Fehler ist → `string` + Null-Guard beim Aufrufer." Außerdem: `?? string.Empty` als interne Normalisierung (nicht als Gold-Plating) explizit erlauben wenn null und leer semantisch identisch sind.
- `docs/REVIEW_CHECKLIST.md`: Nein
- `docs/NFR.md`: Nein
- Phasen-Spec: Nein

---

## Eintrag-Format

```markdown
### [Datum] – [US-XXX / Session N]: [Kurztitel]

**Was lief gut:**
- ...

**Was war schwierig / hat nicht funktioniert – und warum:**
- [Problem] → [Ursache] → [Lösung / Workaround]
- (z. B. "Die Generierung der Einkaufsliste war schwierig, weil die Mengenaggregierung Edge Cases hat, die nicht im Spec standen.")

**Learnings (was würde ich beim nächsten Mal anders machen?):**
- ...

**Dokumentations-Änderungsvorschläge (PFLICHT – jeden Punkt explizit beantworten; Änderungen erst nach User-Approval durchführen):**
- docs/ARCHITECTURE.md:      [Anpassung nötig? Was? / Nein]
- docs/GLOSSARY.md:          [Anpassung nötig? Was? / Nein]
- docs/REVIEW_CHECKLIST.md:  [Anpassung nötig? Was? / Nein]
- docs/NFR.md:               [Anpassung nötig? Was? / Nein]
- Phasen-Spec:               [Anpassung nötig? Was? / Nein]
```

---

### 2026-03-09 – Session 22: Stryker-Findings / Layer-Isolation / Proper Error Handling

**Was lief gut:**
- TDD-Zyklus für `IngredientsEndpoints` konsequent durchgezogen: RED → GREEN → Stryker → weitere Survivor aufgedeckt → nächster RED-Zyklus
- Layer-Isolation-Prinzip klar verstanden und umgesetzt: `ToDomain()` gibt jetzt `OneOf<Ingredient, Error<string>>` zurück statt zu werfen
- `Results.Problem()` liefert strukturiertes `application/problem+json` – testbar und informativ für Clients

**Was war schwierig / hat nicht funktioniert – und warum:**
- Anfangs falsche Denkweise: Tests wurden als "Mittel zum Toten von Mutanten" gesehen statt als "Dokumentation fehlenden Verhaltens" → Stryker-Bezüge in Kommentaren und zu starker Fokus auf die Mutation statt auf die Anwendungslogik
- `dotnet test --no-build` mit veralteten Binaries: mehrfach Build vergessen → falsche Testergebnisse (200 statt 500 Status). Ursache: MSBUILD-Lock-Fehler beim kombinierten Build+Test verhinderte Rebuild
- `Write` statt `Edit` führte zu breitem Hook-Delta und False-Positive-Warnungen für Primitive Obsession (bereits vorhandene Zeilen als "neu" behandelt)

**Learnings:**
- **Stryker survivor = fehlende Verhaltens-Assertion**: Die Frage ist immer "Welches Verhalten fehlt?", nie "Welche Mutation muss getötet werden?". Stryker-Bezüge gehören nicht in Kommentare oder Test-Beschreibungen.
- **Layer-Isolation ist keine Option**: Die DB-Schicht kann korrupt sein (manuelle Eingriffe, Migrations-Fehler). Jeder Layer muss Daten aus anderen Layern via `Domain.Create()` validieren. Der Read-Pfad in Endpoints muss daher `ToDomain()` aufrufen, das `OneOf<Domain, Error<string>>` zurückgibt – und Fehler als `Results.Problem()` zurückgeben.
- **`throw` vs. `Results.Problem()`**: `throw` führt zu einem ungeordneten 500 (HTML/plain-text, nicht testbar auf Inhalt). `Results.Problem(detail, statusCode: 500)` gibt strukturiertes JSON (`application/problem+json`) zurück – testbar per `ContentType` und Body-Assertion.
- **Stryker disable**: Ausschließlich für echte äquivalente Mutanten (z.B. `"/"` vs. `""` als Route-Sub-Path in ASP.NET Core = identisches Routing-Verhalten). Jede Suppression in `decisions.md` begründen.
- **Phasen**: SKELETON, MVP, V1, V2, V2+ (keine NFR-Phase). TraceId in Fehlerantworten → frühestens MVP/V1, nicht SKELETON.
- **Ein Test nach dem anderen**: Auch wenn mehrere Findings offen sind, immer einen vollständigen RED→GREEN→Stryker-Zyklus abschließen bevor der nächste Test kommt.

**Dokumentations-Änderungsvorschläge (PFLICHT):**
- `docs/CODING_GUIDELINE_CSHARP.md`: **Ja** – Abschnitt 7 (Domain-Typen / Read-Pfad) sollte explizit machen, dass `ToDomain()` `OneOf<Domain, Error<string>>` zurückgibt (kein throw) und Endpoints `Results.Problem()` statt unbehandelter Exception nutzen. Außerdem: Layer-Isolation-Prinzip ("Die Domäne vertraut weder Request-Daten noch DB-Daten") im Read-Pfad explizit machen.
- `docs/ARCHITECTURE.md`: **Ja** – Layer-Isolation-Prinzip als expliziten Architektur-Grundsatz ergänzen: "Jeder Layer schützt sich aktiv gegen fehlerhafte Daten aus benachbarten Layern."
- `docs/TDD_PROCESS.md`: **Ja** – Abschnitt über Stryker-Survivor-Behandlung: "Survivor = fehlende Test-Assertion für echtes Verhalten, nie Stryker-Disable als Erstreaktion."
- `docs/GLOSSARY.md`: Nein
- `docs/REVIEW_CHECKLIST.md`: Nein
- `docs/NFR.md`: Nein
- Phasen-Spec: Nein

---

### 2026-03-09 – Session 21: Hook-Architektur-Fixes

**Was lief gut:**
- `$CLAUDE_PROJECT_DIR` vs `$PWD` schnell identifiziert (Subagent-Research) und sofort getestet
- Schrittweise Verifikation: erst einen Hook ändern + testen, dann den Rest – kein Massenumbau blind
- `bash -c`-Wrapper sicher entfernt (mit Test nach jeder Änderung verifiziert)
- `Error<string>`-False-Positive präzise analysiert: nicht generell alle Generics filtern, sondern gezielt `Error<string>` – Begründung diskutiert und dokumentiert

**Was war schwierig / hat nicht funktioniert – und warum:**
- `$PWD` in Hooks ist fragil: nach `cd .claude/hooks` im Bash-Tool brach die gesamte Hook-Chain → Session-Neustart nötig
  - Ursache: Claude Code persistiert CWD zwischen Bash-Tool-Calls; Hooks erben dieses CWD via `$PWD`
  - Lösung: `$CLAUDE_PROJECT_DIR` (stabiler Projekt-Root, unabhängig vom CWD)
- Full-Test-Suite konnte in derselben Session nicht mehr ausgeführt werden, weil der CWD-Bruch alle Bash-Befehle blockierte

**Learnings (was würde ich beim nächsten Mal anders machen?):**
- **Niemals `cd` in Unterverzeichnis** ohne sofortiges `cd $CLAUDE_PROJECT_DIR` danach – persistierter CWD bricht alle hook-internen `$PWD`-Referenzen
- **DENY-Hook-Tests**: Nur Commands wählen, die auch bei versehentlichem Durchlaufen nichts zerstören (z.B. `dotnet stryker` = DENY + harmlos). `git push --force` ist kein guter Testkandidat – bei Hook-Ausfall wäre der Befehl ausgeführt worden
- **Schrittweise testen bei Hook-Infrastruktur**: Erst einen Hook ändern und testen, dann den Rest – nicht alle auf einmal

**Dokumentations-Änderungsvorschläge (PFLICHT – jeden Punkt explizit beantworten; Änderungen erst nach User-Approval durchführen):**
- docs/ARCHITECTURE.md: Nein
- docs/GLOSSARY.md: Nein
- docs/CODING_GUIDELINE_CSHARP.md: Nein
- docs/CODING_GUIDELINE_TYPESCRIPT.md: Nein
- docs/DEV_WORKFLOW.md: **Ja** – Hinweis ergänzen: Hook-Commands müssen `$CLAUDE_PROJECT_DIR` statt `$PWD` verwenden; `cd` in Unterverzeichnisse im Bash-Tool bricht Hook-Chain bis zum nächsten Session-Neustart

---

### 2026-03-09 – Session 20: Quantity Sum-Type + Stryker-Disable-Syntax

**Was lief gut:**
- Stryker-Disable-Bug systematisch debuggt: JSON-Inspektion des Reports führte direkt zur Ursache.
- Architektur-Diskussion zu `Measurement` → `Quantity` Sum-Type war produktiv: Domänenfragen (Prise, optionale Menge, Einheit ohne Zahl) sauber durchdacht, Ergebnis klar und begründet.
- „Fake it till you make it" konsequent angewandt: `value == 0`-Check als minimale Implementierung erzwang im nächsten Zyklus den generalisierten `<= 0`-Check.
- Stryker nach jedem GREEN-Schritt: Minimality-Nachweis pro Zyklus, keine Gold-Plating-Überraschungen am Ende.

**Was war schwierig / hat nicht funktioniert – und warum:**
- `// Stryker disable once StringMutation` → falsche Syntax. Korrekt: `// Stryker disable once String : Begründung` (Kategorie-Name ohne „Mutation", Beschreibungstext nach Doppelpunkt). Stryker-Docs beschreiben das nur implizit.
- Refactoring (`Measurement` → `Quantity`) erzeugt unvermeidlich Gold-Plating-Alarm: Consumer-Abhängigkeiten erzwingen die vollständige Implementierung vor dem ersten Test. Das ist in reinen Refactoring-Schritten akzeptabel, sollte aber explizit kommuniziert werden.
- Neuer Stryker-Survivor (L52 RecipesEndpoints) durch die neue Mapping-Zeile entdeckt – Regressions-Survivor durch Refactoring ist ein Warnsignal, das der Full-Stryker-Lauf am Ende der Session fängt.

**Learnings:**
- Stryker-Disable-Kommentar immer mit `// Stryker disable once <Kategorie> : <Begründung>` schreiben. Kategorien: `String`, `Equality`, `Logical`, `Linq`, `Statement`, `Conditional` – nicht die C#-Klassen-Namen.
- Beim Umbenennen eines Typs (Refactoring) zuerst alle Consumer identifizieren, dann Typ + Tests + Consumer in einem Schritt kompilierbar machen, danach TDD für neue Verhalten.
- „Ist das Verhalten Teil des Vertrags?" konsequent für Stryker-Survivors prüfen. Fehler-Nachrichten, die über API-Responses propagieren, sind Vertragsbestandteil.

**Dokumentations-Änderungsvorschläge:**
- `docs/CODING_GUIDELINE_CSHARP.md`: Stryker-Disable-Syntax (Abschnitt 8) ergänzt. ✅
- `docs/DEV_WORKFLOW.md`: Stryker-Disable-Syntax-Beispiel in Mutation-Testing-Sektion ergänzt. ✅
- `docs/GLOSSARY.md`: `Quantity`-Eintrag ergänzt. ✅
- `docs/ARCHITECTURE.md`: Nein.
- `docs/REVIEW_CHECKLIST.md`: Nein.
- `docs/NFR.md`: Nein.
- Phasen-Spec: Nein.

---

### 2026-03-06 – Session 19: PreToolUse-Hook für Bash-Permissions

**Was lief gut:**
- Permission-System-Problem vollständig verstanden und sauber gelöst: Statt fragiler `permissions.allow`-Glob-Liste jetzt ein Python-Hook mit klarer Entscheidungskette (Priority-Allow → Deny → Compound-Split → Allow → explizites `ask`).
- Compound-Command-Splitting mit Quote-Awareness sauber implementiert und mit 96 Tests abgesichert.
- Stryker-Sonderregel elegant als Priority-Allow-Pattern gelöst: Stryker nur mit Python-Summary-Script erlaubt, sonst deny.
- Output-Redirect-Erkennung (unquoted `>`, `>>`) mit sicherem Zielverzeichnis `.claude/tmp/` funktioniert korrekt.
- Toten `Bash(git commit*)` Hook-Eintrag identifiziert und mit Skript entfernt.

**Was war schwierig / hat nicht funktioniert – und warum:**
- `fall-through` (exit 0, kein JSON) war nicht ausreichend: Claude Code kann Befehle trotzdem auto-approven (Session-State). Fix: explizites `permissionDecision: "ask"` erzwingt immer einen Prompt.
- `Bash(git commit*)` Matcher feuert nie – Claude Code matcht Hooks anhand des Tool-Namens (`"Bash"`), nicht des Kommandoinhalts. Dieses Verhalten ist in der Doku nicht klar beschrieben.
- Live-Test mit `whoami` ohne Prompt bestätigte das `fall-through`-Problem erst nach dem ersten Versuch.

**Learnings:**
- PreToolUse-Hook mit `permissionDecision: "ask"` ist der robustere Mechanismus gegenüber `permissions.allow`. `permissions.allow` soll laut Doku keine Compound-Commands matchen (Sicherheitsdesign).
- Hook-Matcher (`"Bash"`, `"Bash(git commit*)"`) matchen auf dem Tool-Namen, nicht auf dem Kommando-Inhalt. Für Command-spezifische Logik muss der Hook selbst das Kommando parsen.
- Immer explizite `permissionDecision` zurückgeben – nie auf `fall-through` vertrauen wenn kontrolliertes Verhalten gewünscht ist.

**Dokumentations-Änderungsvorschläge:**
- docs/ARCHITECTURE.md: Nein
- docs/GLOSSARY.md: Nein
- docs/REVIEW_CHECKLIST.md: Nein
- docs/NFR.md: Nein
- Phasen-Spec (SKELETON_SPEC.md): Nein

---

### 2026-03-06 – Session 18: Sum-Type-Guidelines, RecipeSource-Refactoring, Permission-System-Analyse

**Was lief gut:**
- Sum-Type-Design in einer langen Diskussion vollständig durchdacht und fundiert entschieden: private Subtypen (Variante A + B), `Match<T>` intern statt direktem switch, `implicit`/`explicit`-Konvention, `Match<T>` public vs. internal. Alles in CODING_GUIDELINE_CSHARP.md, decisions.md und AGENT_MEMORY.md dokumentiert.
- RecipeSource-Refactoring sauber via TDD: `NoSource` als RED-Test, GREEN mit minimalen Änderungen, REFACTOR mit Privatisierung und Factory-Methoden. Gleichzeitig Quantity-Compilation-Blocker (vorhandener RED-Test) mit minimalen Stubs aufgelöst.
- Stryker-Disable-Kommentar-Format entdeckt und korrekt dokumentiert: `// Stryker disable once String` (nicht `StringMutation`).
- Permission-System durch systematisches Testen verstanden: `autoAllowBashIfSandboxed: true` war die eigentliche Ursache für das "alles läuft durch"-Verhalten.

**Was war schwierig / hat nicht funktioniert – und warum:**
- `run_in_background: true` bei Bash-Befehlen hat Stryker ohne Genehmigung ausgeführt – vermutlich weil background commands einen anderen Permission-Code-Pfad nehmen. Noch nicht vollständig geklärt.
- `autoAllowBashIfSandboxed: false` + Allow-Regeln: `Bash(ls*)` matcht `ls /projekt/...` (kein Prompt), aber `ls ~/.claude/` (Prompt) und `python3 -c "..."` (Prompt) obwohl beide Patterns in der Allow-Liste stehen. Ursache unklar – undokumentiertes Verhalten oder Bug.
- GREEN-Schritt bei RecipeSource: beim ersten Edit wurde der `explicit operator string?` versehentlich mitentfernt, was einen Build-Fehler in `RecipesEndpoints.cs` verursachte. Ursache: zu großer Edit-Scope.

**Learnings:**
- `run_in_background: true` bei Bash nie nutzen ohne zu wissen, ob es die Permission-Prüfung umgeht – zunächst weiter untersuchen.
- Allow-Listen-Patterns in `settings.json` sind bei aktivierter Sandbox ohne Wirkung (`autoAllowBashIfSandboxed: true` überschreibt alles). Erst mit `autoAllowBashIfSandboxed: false` tritt das eigentliche Matching in Kraft – und verhält sich dann nicht vollständig dokumentationskonform.
- Im GREEN-Schritt: Edits so klein wie möglich halten. Nur die Zeilen ändern, die der rote Test erzwingt. Nie ganze Blöcke ersetzen wenn ein Detail geändert wird.
- Stryker inline disable: Korrekter Mutatorname ist `String` (nicht `StringMutation`). Gilt als Muster für alle `_ => throw new InvalidOperationException("Unreachable.")` in Sum-Type-Match-Methoden.

**Dokumentations-Änderungsvorschläge:**
- docs/ARCHITECTURE.md: Nein
- docs/GLOSSARY.md: Nein
- docs/REVIEW_CHECKLIST.md: Nein
- docs/NFR.md: Nein
- docs/DEV_WORKFLOW.md: Ergänzung sinnvoll: Permission-System-Verhalten dokumentieren (autoAllowBashIfSandboxed, run_in_background-Vorsicht, Stryker-Disable-Format). Bitte um Approval.

---

### 2026-03-03 – Session 16: Dokumentations-Scanbarkeit (Header + Inhalt-Tabellen)

**Ziel / Motivation:**
Agenten lesen typischerweise nur die ersten ~100 Zeilen einer Datei, um Relevanz einzuschätzen. Wichtige Guidelines wurden dadurch systematisch nicht vollständig gelesen und in der Folge nicht eingehalten. Ziel der Überarbeitung: Jede Dokumentationsdatei enthält am Anfang einen maschinenlesbaren HTML-Kommentar-Header (`wann-lesen`, `kritische-regeln`) und eine Inhalt-Tabelle, die einem Agenten beim initialen Scan ermöglicht, die Relevanz und Struktur sofort zu erfassen und gezielt in die richtigen Abschnitte zu navigieren – ohne die gesamte Datei lesen zu müssen.

**Was lief gut:**
- Systematisches Durcharbeiten aller Docs-Dateien mit klarem Pattern (HTML-Kommentar-Header + Inhalt-Tabelle)
- Split-Entscheidungen waren eindeutig: TDD_PROCESS.md war der einzige sinnvolle Split
- Verbesserungen, die nebenbei entdeckt wurden, konnten direkt behoben werden (ExcludingMissingMembers in Skill falsch beschrieben, readonly struct vs. record struct Inkonsistenz, LLM_PROMPT_TEMPLATE veraltet)

**Was war schwierig / hat nicht funktioniert – und warum:**
- Edit-Tool schlägt fehl bei Strings mit typografischen Anführungszeichen (curly quotes) – Lösung: sed via Bash für zeilenbasierte Entfernung
- `wann-lesen` als Framing passt nicht für Dateien, die primär beschrieben werden (lessons_learned.md) → `wann-schreiben` + `wann-lesen` getrennt

**Learnings:**
- Das "Verbotene Muster"-Kurzreferenz-Pattern (Tabelle vor den ausführlichen Abschnitten) ist generell nützlich für Guidelines mit Anti-Patterns
- Vollständige Referenz-Verweise (z.B. `docs/TDD_PROCESS.md`) sollten immer am Anfang eines Skills stehen, nicht am Ende
- Vor Inhalt-Anpassungen in Docs: immer den tatsächlichen Code als Ground Truth prüfen (statt MEMORY.md zu vertrauen)

**Dokumentations-Änderungsvorschläge (PFLICHT):**
- docs/ARCHITECTURE.md:      Nein (bereits in dieser Session aktualisiert)
- docs/GLOSSARY.md:          Nein (bereits in dieser Session aktualisiert)
- docs/REVIEW_CHECKLIST.md:  Nein (bereits in dieser Session aktualisiert)
- docs/NFR.md:               Nein (bereits in dieser Session aktualisiert)
- Phasen-Spec:               Nein

---

### 2026-03-03 – Session 14: RecipeSource + Recipe.Create-Refactoring + Success<>-Removal

**Was lief gut:**
- `RecipeSource` Sum-Type erfolgreich implementiert (TDD: Red→Green): `UrlSource(NonEmptyTrimmedString Url)` + expliziter `string?`-Operator
- `Recipe.Create` auf Primitives umgestellt (Dependency Rule erfüllt) – sauber ohne neue Tests nötig
- `NonEmptyTrimmedString.Create` von `Success<T>`-Wrapper befreit (Tech Debt Session 7 behoben): alle Caller `n.Value` → `n` vereinfacht
- Test-Stil-Refactoring begonnen: `IsT0/AsT0` → `BeOfType<T>().Which` + zweizeilige Error-Assertions

**Was war schwierig / hat nicht funktioniert – und warum:**
- **TDD-Minimalität RecipeSource**: Mehrfache Ablehnungen weil `NoSource`, nullable `Source` und `default!` über das Minimum hinausgingen. Kernproblem: bestehende Tests ohne Null-URL zwingen technisch zur Entscheidung über den Null-Fall, obwohl kein Test diesen Pfad testet. Lösung: `default!` (null) als bewusste technische Schuld bis zum nächsten RED-Zyklus.
- **`Satisfy<T>()` nicht verfügbar**: FluentAssertions 7.2 hat `Satisfy` nicht auf `ObjectAssertions`. Session-Ende ohne funktionierende Multi-Property-Assertion. Nächste Session muss Alternative finden (z.B. `Match<T>` mit Expression, zwei Statements, oder Custom-Extension).
- **`BeEquivalentTo` als Tautologie**: `result.Value.Should().BeOfType<T>().Which.Should().BeEquivalentTo(T.Create(same inputs).AsT0)` – testet nicht ob Werte in Properties gelandet sind, sondern ob Create dasselbe zurückgibt wie Create. Daher abgelehnt.

**Learnings:**
- **`default!` als bewusster Platzhalter**: Wenn kein Test einen Pfad abdeckt und der Typ kein `null` unterstützen will, ist `default!` + Kommentar die minimalste ehrliche Lösung bis zum nächsten RED-Zyklus. Wichtig: Kommentar mit Verweis auf offenen RED-Zyklus.
- **FluentAssertions Multi-Property ohne Variable**: `Satisfy` existiert nicht auf `ObjectAssertions`. Geprüfte Alternativen: zwei separate Statements (je `BeOfType().Which.Prop`), `Match<T>(Expression)`, oder Variable. In der nächsten Session klären.
- **`BeEquivalentTo` nur für echte Zustandsvergleiche**: Nicht `T.Create(same inputs)` als Expected verwenden – das ist zirkulär und testet nichts.

**Dokumentations-Änderungsvorschläge:**
- docs/ARCHITECTURE.md: Test-Patterns-Sektion ergänzen: "Kein `Satisfy` in FA 7.2; stattdessen zwei Statements oder `Match<T>`" – **Vorschlag, erst nach User-Approval**
- docs/CODING_GUIDELINE_CSHARP.md: `NonEmptyTrimmedString.Create` gibt jetzt `OneOf<NonEmptyTrimmedString, Error<string>>` zurück (kein `Success<T>`-Wrapper) – im Beispielcode prüfen ob noch aktuell
- docs/GLOSSARY.md: Nein
- docs/REVIEW_CHECKLIST.md: Nein
- docs/NFR.md: Nein
- Phasen-Spec: Nein

---

### 2026-03-03 – Session 15: Satisfy-Custom-Extension, Stryker-Findings, ExcludingMissingMembers-Verbot

**Was lief gut:**
- `Satisfy<T>`-Extension in `mahl.Tests.Shared/Helpers.cs` – elegante Lösung ohne FA-Upgrade, identische Syntax wie das gewünschte FA-Pattern
- Stryker-Findings (Hoch-Priorität) systematisch abgearbeitet: `All()→Any()` für Ingredients + Steps, `BoughtAt`-Equality – alle drei Mutanten getötet, Score 79.63% → 82.10%
- `ExcludingMissingMembers`-Diskussion führte zu klarer Regel: DB-State → `Excluding(x => x.Id)`, API-Response → ID aus DB + vollständiger Vergleich
- Hook für `ExcludingMissingMembers` per TDD ergänzt (5 neue Tests, 52 gesamt grün)
- Stryker `--mutate`-Pfad-Problem analysiert und korrekt dokumentiert (projektrelativ, nicht solution-relativ)
- Zeiten in DEV_WORKFLOW.md korrigiert: vollständiger Lauf ~2–3 min (nicht 10–30), gezielt ~1 min

**Was war schwierig / hat nicht funktioniert – und warum:**
- **Stryker `--mutate` mit falschem Pfad**: `Server/Domain/Recipe.cs` matched nicht – Stryker erwartet projektrelativen Pfad `Domain/Recipe.cs`. Ursache: Pfad-Konvention war nicht dokumentiert. Behoben in DEV_WORKFLOW.md.
- **Gold-Plating-Alarm bei `All()→Any()`-Tests**: Tests gingen sofort grün – weil der Produktionscode bereits korrekt war und nur der Mutant fehlte. Korrekte Interpretation: Test ist nicht redundant, er tötet einen Stryker-Mutanten. Verifikation via vollem Stryker-Lauf nötig.
- **`ExcludingMissingMembers` in ShoppingList-Test**: Direkt nach Einführung des Hooks noch einmal verwendet – Diskussion über Sinnhaftigkeit führte zur klären Regel. Hook-Warnung hat sich bewährt.
- **Zirkuläre ID-Assertion**: `var id = GetAllXFromDb()[0].Id; GetAllXFromDb().Should().BeEquivalentTo([new { Id = id }])` – DB gegen DB ist sinnlos. Korrekte Unterscheidung: API-Response vs. DB-State.

**Learnings:**
- **`Satisfy<T>` als Custom-Extension**: Wenn FA eine Methode nicht hat, eigene schreiben – 5 Zeilen in Helpers.cs, identische Syntax. Kein FA-Upgrade nötig.
- **Stryker-Pfade sind projektrelativ**: `--mutate Domain/Recipe.cs` (nicht `Server/Domain/Recipe.cs`). Report-Tabelle zeigt die korrekten Pfade.
- **Sofort-grüner Test ≠ Gold-Plating**: Wenn ein Stryker-Mutant der Anlass ist, ist ein sofort-grüner Test korrekt – er beschreibt Verhalten, das der Mutant verändert hätte. Stryker-Verifikation zeigt ob er tötet.
- **`ExcludingMissingMembers` vs. `Excluding(x => x.Id)`**: Ersteres ist "stille Ignoranz", Letzteres ist explizite Absicht. Faustregel: Wenn man erklären muss warum eine Property irrelevant ist, sollte man sie explizit ausschließen.
- **API-Response vs. DB-State bei ID-Assertions**: API-Response → ID aus DB (nicht zirkulär, testet Korrektheit der ID). DB-State → `Excluding(x => x.Id)` (DB gegen DB wäre zirkulär).

**Dokumentations-Änderungsvorschläge:**
- docs/ARCHITECTURE.md: Test-Patterns bereits aktualisiert (Satisfy-Custom-Extension, ExcludingMissingMembers-Verbot, API-Response vs. DB-State) ✅
- docs/DEV_WORKFLOW.md: Stryker-Zeiten + `--mutate`-Pfad-Konvention bereits aktualisiert ✅
- docs/GLOSSARY.md: Nein
- docs/REVIEW_CHECKLIST.md: Nein
- docs/NFR.md: Nein
- Phasen-Spec: Nein

---

### 2026-03-02 – Session 13: Hook-Tests + readonly record struct

**Was lief gut:**
- pytest-Tests für alle 8 Code-Quality-Checks auf einmal: sauber strukturiert, 47 Tests, alle grün
- `constructors.py` TDD-konform erweitert: 3 Red-Tests → Implementierung → 47/47 grün
- Domain-Typen-Umstellung (`readonly struct` → `readonly record struct`): mechanisch und sicher durch streng eingehaltenen Red→Green-Zyklus pro Typ
- Subshell-Pattern `(cd ... && cmd)` als saubere Lösung für persistentes CWD-Problem gefunden

**Was war schwierig / hat nicht funktioniert – und warum:**
- **CWD-Problem**: `cd .claude/hooks` im Bash-Tool ändert den CWD dauerhaft → Hooks laufen dann mit falschem `$PWD` → doppelter Pfad in Hook-Aufrufen. Lösung: immer `(cd ... && cmd)` Subshell statt nacktem `cd`.
- **pytest auf NTFS**: `FileNotFoundError` auf Tempfiles ohne `-p no:cacheprovider -s`. Workaround dokumentiert in DEV_WORKFLOW.md.
- **TDD-Verletzung bei Measurement**: Produktionscode vor Test geschrieben → User musste eingreifen. Konsequenz: ab jetzt immer Test ERST schreiben, auch bei rein mechanischen Umstellungen.
- **"Minimaler Code"-Verletzung bei RecipeSource**: Zu viel auf einmal geplant (URL-Validierung, ImageSource, NoSource) statt nur den minimalen Code für den roten Test. Session musste geschlossen werden.

**Learnings:**
- **TDD ist auch bei Refactorings Pflicht**: Auch rein mechanische Umstellungen (struct → record struct) benötigen den Test zuerst. Kein "das ist ja offensichtlich".
- **Minimaler Code für Green**: Nur so viel implementieren, dass der rote Test grün wird. Nicht mehr – auch wenn die vollständige Lösung schon klar ist.
- **CWD-Hygiene**: Nie `cd` ohne Subshell verwenden, wenn danach Edits kommen. Merksatz: `(cd dir && cmd)` statt `cd dir && cmd`.
- **pytest aus NTFS-Verzeichnis**: Immer mit `-p no:cacheprovider -s` und aus `.claude/hooks/` starten.

**Dokumentations-Änderungsvorschläge:**
- docs/DEV_WORKFLOW.md: ✅ Bereits aktualisiert (pytest-Befehl, Subshell-Hinweis)
- docs/ARCHITECTURE.md: Nein
- docs/GLOSSARY.md: Nein
- docs/REVIEW_CHECKLIST.md: Nein
- docs/NFR.md: Nein
- Phasen-Spec: Nein

---

### 2026-03-02 – Session 12: DDD-Domain-Typen + Stryker

**Was lief gut:**
- Architektur-Diskussionen (From() raus, RecipeSource, Recipe.Create-Primitives, record-struct) produktiv: User hatte klare Entscheide, keine endlosen Schleifen.
- Hook-Feedback war wertvoll: Constructor-Verletzung sofort erkannt → `readonly struct` statt `readonly record struct` als Workaround.
- Stryker-JSON-Auswertung via Python lieferte vollständige Übersicht aller überlebenden Mutanten mit Zeilen und Typen.

**Was war schwierig / hat nicht funktioniert – und warum:**
- **CS8958 (Stryker/MSBuild)**: Stryker nutzt MSBuild von VS2022, das `langversion:latest` als C# 10 interpretiert → `private` parameterloser Ctor auf struct verboten.
  → Workaround: Expliziten Ctor entfernt, `_items == null`-Guard reicht. Eigentliche Lösung: Hook erweitern + `readonly record struct` nutzen.
- **Gecachter Build maskierte fehlende `using`-Direktiven**: `dotnet test` nutzte beim ersten Lauf alte DLL-Artefakte; nach Cache-Invalidierung zeigten sich in allen Domain-Dateien fehlende `using mahl.Shared;`. → Learning: Immer nach größeren Refactorings ein explizites `dotnet build` ohne `--no-build` durchführen.
- **`TrimmedString` ≠ `string` in FluentAssertions**: `NonEmptyTrimmedString.Value` gibt `TrimmedString` zurück. `Should().Be("Wert")` schlägt fehl, weil FluentAssertions Typen vergleicht.
  → Fix: Immer `((string)domain.Name).Should().Be(...)` oder `(string)domain.Name.Value` in Tests.
- **`Recipe.Create(dto)` war ein Planfehler**: Das ursprüngliche Design nahm ein DTO im Domain-Typ entgegen – verletzt die Dependency Rule, die wir gerade für `From()` durchgesetzt hatten. Erst auf Nachfrage erkannt.
  → Learning: Bei jedem neuen `Create()`-Parameter automatisch fragen: "Ist das ein Primitive oder ein Infrastruktur-Typ?"

**Learnings:**
- `NonEmptyTrimmedString.Value` → `TrimmedString`. In Tests immer `(string)domain.Field` (implicit operator) statt `.Value.Should().Be(...)`.
- Nach Cache-Invalidierung (Datei in referenziertem Projekt geändert) explizit `dotnet build` ausführen, nicht `--no-build`.
- Dependency-Rule-Check: Domain-Types dürfen nur Primitives und andere Domain-Types als Parameter entgegennehmen – nicht DTOs, nicht DbTypes. Wenn `Create()` ein DTO nimmt, ist das ein Smell.
- Stryker fällt auf VS MSBuild zurück wenn `dotnet build` fehlschlägt – deshalb Build-Fehler immer VOR Stryker beheben.

**Dokumentations-Änderungsvorschläge:**
- `docs/CODING_GUIDELINE_CSHARP.md`: ✅ Abschnitt 7 bereits in dieser Session hinzugefügt (Domain-Typen).
- `docs/ARCHITECTURE.md`: Hinweis ergänzen: Domain-Typen `Create()` nehmen nur Primitives/andere Domain-Types – kein DTO, kein DbType. → **Vorschlag an User, noch nicht durchgeführt.**
- `docs/GLOSSARY.md`: Nein
- `docs/REVIEW_CHECKLIST.md`: Punkt ergänzen: "Nimmt `Create()` nur Primitives/Domain-Types? (kein DTO, kein DbType)" → **Vorschlag an User, noch nicht durchgeführt.**
- `docs/NFR.md`: Nein
- Phasen-Spec: Nein

---

### 2026-02-27 – Session 11: .claude-Struktur auf Skills-Standard gebracht

**Was lief gut:**
- Analyse war vollständig: Explore-Agent lieferte alle Dateipfade und Inhalte in einem Durchgang.
- Commands → Skills-Migration verlief ohne Probleme; YAML-Frontmatter-Format war klar.
- Hook-Konsolidierung (`IMMUTABILITY_EXCLUDED`) sauber: beide Dateien importieren jetzt aus `common.py`, keine inhaltliche Verhaltensänderung.
- `implementing-feature` konnte um ~60% gekürzt werden, weil die Duplikate (TDD-Regeln, Review-Tabelle) jetzt in den dedizierten Skills leben.

**Was war schwierig / hat nicht funktioniert – und warum:**
- **`rm` auf NTFS-Pfaden aus WSL schlägt fehl** mit "Read-only file system": Die `.claude/commands/`-Dateien liegen auf dem Windows-NTFS-Laufwerk (`/mnt/c/...`). WSL2 kann Dateien auf NTFS lesen und schreiben, aber `rm` auf bestimmten Pfaden wird geblockt.
  → Fix: `cmd.exe /c "del /f ..."` als Windows-nativer Delete-Befehl funktioniert.

**Learnings:**
- `rm` auf `/mnt/c/...`-Pfaden kann scheitern. Alternative: `cmd.exe /c "del /f <windows-pfad>"`.
- Skills mit `user-invocable: false` und einer guten Description in der YAML-Frontmatter triggern automatisch – der User muss sich keinen Command merken.
- Die `commands/`-Grenze vs. `skills/`-Grenze ist jetzt klar: Commands = Legacy. Skills = Standard ab Feb 2026.

**Dokumentations-Änderungsvorschläge:**
- `docs/ARCHITECTURE.md`: Nein
- `docs/GLOSSARY.md`: Nein
- `docs/REVIEW_CHECKLIST.md`: Nein
- `docs/NFR.md`: Nein
- `docs/DEV_WORKFLOW.md`: Hinweis ergänzen, dass `rm` auf `/mnt/c/...` scheitern kann und `cmd.exe /c "del /f ..."` der korrekte Workaround ist. → **Vorschlag an User, noch nicht durchgeführt.**
- `CLAUDE.md`: Die Navigationstabelle referenziert noch "Commands" als Konzept – ggf. auf "Skills" aktualisieren. → **Vorschlag an User, noch nicht durchgeführt.**

---

### 2026-02-27 – Session 10: Skills & Guidelines-Architektur

**Was lief gut:**
- Die Diskussion über Duplikation vs. Trennung der Rollen (Guidelines = präskriptiv, Checklist = retrospektiv) war produktiv und führte zu einer klaren Entscheidung.
- Das Iterieren des Plans (mehrere Planmode-Runden) hat geholfen, Widersprüche frühzeitig zu erkennen (z.B. der Widerspruch zwischen "Different Mode"-Argument und Domain-Modeling-Block-Entfernung).
- Neue Skill-Struktur (write-code, review-code) ist lean und enthält keinen duplizierten Guideline-Inhalt.

**Was war schwierig / hat nicht funktioniert – und warum:**
- Der Plan musste mehrfach angepasst werden, weil die Konsequenzen der "Different Mode"-Argumentation zunächst nicht konsequent zu Ende gedacht wurden: Zuerst sollte der Domain-Modeling-Block ersetzt werden, dann wurde erkannt, dass das Argument ihn gerade rechtfertigt. → Lösung: Im nächsten Schritt zuerst die Konsequenz einer Argumentation vollständig durchdenken, bevor der Plan finalisiert wird.

**Learnings:**
- Bevor ein Argument als Pro oder Contra eingesetzt wird, prüfen: Gilt es nicht auch für das Gegenteil? (Symmetriecheck)
- Skill-Dateien sollten keine Guideline-Inhalte duplizieren – nur Verweise. Das ist wartbarer und wurde hier konsequent umgesetzt.
- Eine sprachunabhängige Guideline (`CODING_GUIDELINE_GENERAL.md`) macht Drift zwischen C#- und TS-Guidelines strukturell unmöglich.

**Dokumentations-Änderungsvorschläge:**
- docs/ARCHITECTURE.md:      Nein
- docs/GLOSSARY.md:          Nein
- docs/REVIEW_CHECKLIST.md:  Bereits in dieser Session angepasst
- docs/NFR.md:               Nein
- Phasen-Spec:               Nein

---

## Beispiel-Einträge (zur Orientierung)

### Beispiel A – Umgebungs-Problem

**Was war schwierig:**
- `dotnet` Befehle schlagen in WSL fehl, weil .NET nur auf dem Windows-Host installiert ist.
  → Ursache: WSL hat keinen eigenen dotnet-Pfad.
  → Lösung: `cmd.exe /c "cd /d C:\...\mahl && dotnet <command>"` als Wrapper verwenden.

**Learnings:**
- Diesen Wrapper immer als erstes dokumentieren, wenn ein neuer Entwickler/Agent startet.

**Dokumentations-Check:**
- docs/ARCHITECTURE.md: Nein (kein Pattern-Problem)
- CLAUDE.md: ✅ Bereits dokumentiert (KRITISCH-Sektion)

---

### Beispiel B – Prozess-Problem (TDD)

**Was lief nicht gut:**
- Tests wurden erst nach der Implementierung geschrieben. Dadurch wurde der Refactoring-Schritt übersprungen.
  → Ursache: Kein expliziter Stopping-Point nach dem ersten Test.
  → Konsequenz: Tests prüfen Implementierung statt Verhalten; bei Refactoring brechen viele Tests.

**Learnings:**
- TDD funktioniert nur mit bewusstem Stop nach dem Schreiben des Tests und Verifikation des Fehlschlags.
- Wenn der Test "von alleine grün" ist, wurde etwas Falsches getestet.

**Dokumentations-Check:**
- docs/ARCHITECTURE.md: ✅ TDD-Sektion um Pflicht-Outputs ergänzt.
- docs/NFR.md: ✅ Definition of Done um explizite Verifikationsschritte erweitert.

---

### Beispiel C – Qualitäts-Finding (Domain Modeling)

**Was lief nicht gut:**
- Review-Agent hat festgestellt: `Recipe.Title` war als `string` deklariert statt `NonEmptyTrimmedString`.
  → Ursache: Beim Schreiben des Endpoints wurde der Typ aus dem DTO unreflektiert übernommen.

**Learnings:**
- Bei jedem neuen Property automatisch fragen: "Was wäre ein ungültiger Wert?" – nicht erst im Review.
- DTOs dürfen primitive Typen haben (sie kommen aus der Außenwelt). Domain-Entities dürfen das nicht.

**Dokumentations-Check:**
- docs/REVIEW_CHECKLIST.md: ✅ Explizite Frage zur primitiven Typisierung ergänzt.

---

## Einträge

### 2026-02-26 – Session 9: Code-Quality-Hooks (checks/-Package, blocking/non-blocking, exit 2)

**Was lief gut:**
- Alle Guidelines aus `CODING_GUIDELINE_CSHARP.md` systematisch auf Automatisierbarkeit bewertet.
- `checks/`-Package mit isolierten Modulen und zwei Dispatcher-Skripten (`blocking.py` / `nonblocking.py`) sauber umgesetzt – kein globaler State, jedes Modul eigenständig testbar.
- Bugfix-Kaskade vollständig durchlaufen: drei unabhängige Bugs gefunden und behoben.
- Korrekte Hook-Konfiguration (`exit 2` + stderr) empirisch ermittelt – kein Raten, Beleg durch tatsächliche Claude-Code-Ausgabe.

**Was war schwierig / hat nicht funktioniert – und warum:**
- **`Tests?.cs` matchte `HookTest.cs`**: Regex `Tests?\.cs` matcht auch `Test.cs` (s ist optional) → `HookTest.cs` endete auf `Test.cs` und wurde fälschlich als Testdatei excluded.
  → Fix: `Tests\.cs$` ohne `?`.
- **`public set;` Regex zu eng**: `\bpublic\s+set\s*;` matcht nur explizites `public set;`, nicht das übliche C# `{ get; set; }` (implizit public).
  → Fix: `\bset\s*;` kombiniert mit Filterung von Zeilen, die `private/protected/internal set;` enthalten.
- **Single quotes verhindern `$PWD`-Expansion**: `bash -c 'python3 $PWD/...'` – single quotes blockieren Shell-Variablen.
  → Fix: `bash -c "python3 $PWD/..."` mit escaped double quotes in JSON.
- **PostToolUse mit `exit 1` ist nicht blocking**: `exit 1` zeigt Fehler dem User im Terminal, nicht Claude. Claude sieht die Meldung nicht.
  → Fix: `exit 2` + stderr → Claude Code zeigt Meldung als system-reminder, Claude reagiert darauf.
- **`exit 0` + stderr ist unsichtbar**: Non-blocking Warnungen mit `exit 0` + stderr werden von Claude Code still verworfen.
  → Fix: `exit 2` auch für non-blocking (Ton des Textes unterscheidet `⛔` von `⚠`).
- **`settings.json` wird erst beim Session-Start geladen**: Änderungen während einer laufenden Session haben keine Wirkung → Neustart nötig. Drei Neustarts waren notwendig.

**Learnings:**
- **Claude Code PostToolUse Hook-Semantik**: `exit 0` = ok, `exit 1` = Fehler (nur Terminal/User), `exit 2` = Feedback an Claude (system-reminder). Immer `exit 2` + stderr für Checks die Claude sehen soll.
- **`$PWD` in settings.json**: Nur mit double quotes (`bash -c "..."`) expandiert. Single quotes: nie für Hook-Commands in JSON.
- **Python-Package statt einzelne Scripts**: `checks/`-Package mit `__init__.py` und Dispatcher-Pattern ist wartbarer als N isolierte `.sh`/`.py`-Skripte.
- **Regex testen mit echter Datei vor Commit**: Alle drei Bugs wären durch einen einzigen End-to-End-Test mit `HookTest.cs` vor dem Commit aufgefallen.

**Dokumentations-Änderungsvorschläge:**
- `docs/DEV_WORKFLOW.md`: Abschnitt zu Hook-Entwicklung ergänzen: exit-Code-Semantik (0/1/2), $PWD-Expansion, stderr vs. stdout. → **Vorschlag an User, noch nicht durchgeführt.**
- `docs/ARCHITECTURE.md`: Nein
- `docs/GLOSSARY.md`: Nein
- `docs/REVIEW_CHECKLIST.md`: Nein
- `docs/NFR.md`: Nein
- Phasen-Spec: Nein

### 2026-02-26 – Session 8: ShoppingListEndpoints, WeeklyPool-Duplikat-Fix, Workflow-Verbesserungen

**Was lief gut:**
- WeeklyPool POST Duplikat-Verbot via TDD (1 Zyklus): Entscheidung → Test → 409-Implementierung.
- DELETE-Test korrigiert (kein Doppel-Seed mehr, Testname angepasst).
- `ShoppingListEndpoints` vollständig via TDD (7 Tests): POST generate, GET, PUT check/uncheck inkl. 404-Fälle.
- `ExcludingMissingMembers`-Review: Alle 9 Usages analysiert, alle korrekt für anonyme Partial-Assertions – kein Handlungsbedarf.
- Workflow-Verbesserungen: Hook auf Python umgestellt (kein jq-Problem mehr), DEV_WORKFLOW.md um Pipe-Regeln + Tool-Failure-Analyse erweitert, ARCHITECTURE.md um "Fake it till you make it" ergänzt, Skills-System eingerichtet.

**Was war schwierig / hat nicht funktioniert – und warum:**
- **`ExecuteDeleteAsync` in Tests nicht verwendbar**: Im GREEN-Refactoring-Versuch schlug `ExecuteDeleteAsync` mit 500 fehl (InMemory-Provider). Zurück zu `RemoveRange`.
- **`git checkout -- Server/Program.cs` beim Hook-Test**: `git checkout` auf eine tracked-Datei im Working Tree stellte die alte HEAD-Version (MariaDB) statt der neuen PostgreSQL-Version wieder her – weil HEAD nur den initialen Commit enthält. Die korrekte Version musste manuell rekonstruiert werden.
- **`git diff HEAD` im Hook-Test schlägt fehl**: Im Repo gibt es eine Datei namens `HEAD` (wahrscheinlich ein verwaistes git-Objekt oder worktree-Datei), die git-Ambiguität verursacht → `fatal: ambiguous argument 'HEAD'`. Hooks, die `git diff HEAD` nutzen, funktionieren daher in dieser Umgebung nicht wie erwartet.
- **check-lessons.sh / check-pre-commit.sh können nicht vollständig getestet werden**: Da `git diff HEAD --name-only` fehlschlägt, ist deren Kernlogik in dieser WSL/Windows-Kombination defekt. Hook-Prüfprotokoll wurde dadurch unterbrochen.
- **GREEN-Schritt noch zu komplex**: Bei `GET /api/shopping-list` wurde direkt die vollständige DB-Logik implementiert statt zuerst `return Results.Ok(new ShoppingListResponseDto([], []))`. Im REFACTOR erkannt, aber nicht rückgängig gemacht (nächste Tests waren bereits alle grün).

**Learnings:**
- `git diff HEAD` ist in dieser Umgebung nicht zuverlässig. Hooks die darauf basieren müssen mit `git status --short` oder `git diff --cached` refactored werden. → Offener Punkt.
- Beim Hook-Test niemals `git checkout -- <file>` auf tracked Dateien, die noch nicht committed sind (im initialen Commit fehlt die neue Version). Stattdessen Testdatei in `/tmp/` anlegen.
- "Fake it till you make it" greift auch für bekannte Patterns: Selbst wenn man "weiß wie's geht", muss der erste Test die minimale Implementierung erzwingen – hardcodierter Return-Wert zuerst.

**Dokumentations-Änderungsvorschläge:**
- `docs/DEV_WORKFLOW.md`: ✅ Bereits ergänzt (Pipe-Regeln, Tool-Failure-Analyse)
- `docs/ARCHITECTURE.md`: ✅ Bereits ergänzt (Fake it, REFACTOR-Minimalität)
- `.claude/commands/feature.md`: ✅ Bereits ergänzt
- **Hooks mit `git diff HEAD`**: Die Hooks `check-lessons.sh`, `pre-compact.sh`, `session-end.sh`, `task-completed.sh` und `check-pre-commit.sh` nutzen alle `git diff HEAD --name-only`. Da das in dieser Umgebung fehlschlägt, sollten sie auf `git status --porcelain` umgestellt werden. **→ Vorschlag an User, noch nicht durchgeführt.**

### 2026-03-11 – Session 25: `.Should().Contain()` verboten, Hook-Erweiterung, Produktionsbug entdeckt

**Was lief gut:**
- Analyse-Diskussion über Vor-/Nachteile des `Contain`-Verbots war produktiv: der User hat die Schwäche meiner initialen Argumentation (String-Assertions seien legitim) korrekt herausgefordert.
- Der Hook-Fix selbst war minimal und konsistent mit dem bestehenden `ExcludingMissingMembers`-Muster.
- Das Präzisieren der Test-Assertions hat **zwei echte Bugs aufgedeckt**, die `.Contain()` vorher verborgen hatte:
  1. Produktionsbug: `ingredient.Name.Value` in String-Interpolation rief `TrimmedString.ToString()` auf (record-struct-Default `"TrimmedString { Value = Butter }"`), statt den eigentlichen String zu liefern. Fix: `(string)ingredient.Name`.
  2. Test-Mismatch: `[TestCase]`-Werte fehlte jeweils der Abschluss-Punkt, der in den Domain-Fehlermeldungen vorhanden ist.

**Was war schwierig / hat nicht funktioniert – und warum:**
- Initialer Fehler: Ich habe `body.Should().Contain()` auf Response-Bodies als "legitim und unersetzbar" eingestuft. Der User hat zu Recht nachgehakt – für Plain-Text-Bodies ist `.Be()` die vollständige Assertion, für JSON `ReadFromJsonAsync<T>()`.
- TDD-Verstoß: Ich habe drei pytest-Tests gleichzeitig geschrieben, statt einen nach dem anderen. Vom User toleriert, aber korrekt gerügt.

**Learnings:**
- **`.Contain()` ist immer eine partielle Assertion** – auch auf Strings. Die Frage ist nie "geht `.Be()` nicht?", sondern "warum will ich partielle Kenntnis?". Für Response-Bodies gilt: Plain-Text → `.Be()`, JSON → deserialisieren.
- **Partielle Assertions verbergen Bugs**: Der `TrimmedString.ToString()`-Bug hätte ohne das `.Contain()`-Verbot ewig unentdeckt bleiben können. Genau das ist der Grund für Full-State-Assertions.
- **`TrimmedString` in String-Interpolation**: `record struct` ohne `ToString()`-Override gibt `"TrimmedName { Value = ... }"` aus – nie `.Value` (vom Typ `TrimmedString`) in `$"..."` einbetten, sondern explizit casten: `(string)domainProp`.

**Weitere Learnings (Nachtrag):**
- **Stryker + Solution-Mode**: `dotnet stryker --project X --test-project Y` aus dem Solution-Root schlägt mit NullReferenceException fehl, weil Stryker Solution-Mode aktiviert und die Flags ignoriert. Korrekt: aus dem Testprojekt-Unterverzeichnis aufrufen (`cd mahl.Shared.Test && dotnet stryker --project mahl.Shared.csproj`).
- **Hook-Regex präzise begründen**: `[^\s&"]*` statt `\S*` – nicht "beliebig nicht-Whitespace", sondern explizit die Injection-relevanten Zeichen ausschließen. Die Frage "was ist gültig?" und "was ist sicherheitskritisch?" separat beantworten.
- **TDD auch für Hook-Änderungen**: Regex-Änderung erst testen (RED), dann implementieren – auch wenn es "nur" ein einzeiliges Pattern ist.

**Dokumentations-Änderungsvorschläge:**
- `docs/TDD_PROCESS.md`: `.Contain()` in Full-State-Assertion-Sektion ergänzt. ✅
- `docs/DEV_WORKFLOW.md`: Stryker Shared-Projekt + offene TODOs ergänzt. ✅
- Alle anderen Kern-Dokumente: Nein.

### 2026-02-25 – Session 7: RecipesEndpoints POST + WeeklyPoolEndpoints, Test-Qualität, Docs

**Was lief gut:**
- `DELETE /api/recipes/{id}` via TDD fertig (2 Zyklen: NonExistingId, AlreadySoftDeleted).
- `POST /api/recipes` vollständig: 5 TDD-Zyklen (EmptyTitle, EmptyIngredients, EmptySteps, UnknownIngredientId, HappyPath).
- `WeeklyPoolEndpoints` vollständig: 6 TDD-Zyklen (GET empty, GET with entries, POST valid/invalid/soft-deleted, DELETE bulk).
- Gold-Plating in `GetAll_ReturnsExistingEntries` (WeeklyPool) korrekt erkannt und rückgängig gemacht – `e.Recipe.Title` war Gold-Plating für den leeren-Liste-Test.
- `ACreateRecipeDto(ingredientId, ...)` Builder extrahiert nach REFACTOR-Checkliste.
- Guideline ergänzt: REFACTOR gilt auch für Tests (Tests = Spezifikation, gleichwertig mit Produktionscode).
- Frontend-Neuimplementierungspflicht an drei Stellen dokumentiert (SKELETON_SPEC.md, AGENT_MEMORY.md).

**Was war schwierig / hat nicht funktioniert – und warum:**
- **`Success<T>`-Wrapper in ROP-Kette**: `NonEmptyTrimmedString.Create` gibt `OneOf<Success<NonEmptyTrimmedString>, Error<string>>` zurück, nicht direkt `NonEmptyTrimmedString`. Im `Bind`-Lambda muss daher `OneOf<Success<NonEmptyTrimmedString>, IResult>` als Typ angegeben werden – sehr laut. Technische Schuld.
- **Duplikat-Test durch abgebrochenes Edit**: `Post_EmptySteps_Returns422` erschien doppelt, weil ein abgebrochenes Tool-Edit doch teilweise geschrieben hatte. Manuell bereinigt.
- **Design-Frage unbeantwortet**: WeeklyPool DELETE-Semantik (by entryId vs. by recipeId, mit/ohne Duplikatverhinderung) wurde am Session-Ende aufgeworfen – noch offen.
- **`ExcludingMissingMembers`-Kritik**: User identifizierte potentiell unsicheres Blanket-Pattern. Analyse durchgeführt (13/15 Usages mit ExcludingMissingMembers), Session aber vor der Klärung geschlossen.

**Learnings:**
- Gold-Plating in GET-Endpoints (z.B. `e.Recipe.Title`) ist schwerer zu erkennen als in POST/DELETE, weil es nicht direkt als zusätzliche Schreiboperation auffällt. Den PFLICHT-CHECK strikt anwenden: „Erzwingt der leere-Liste-Test den Join?"
- `NonEmptyTrimmedString.Create` gibt `Success<T>` zurück – beim nächsten ROP-Endpoint darauf achten; in der REFACTOR-Phase erwägen, ob `.Value` im Lambda eleganter ist.
- Builder für Request-DTOs (`ACreateRecipeDto`) lohnt sich ab dem Moment, wo der Happy-Path-Test die Defaults definiert – daher erst nach dem Happy-Path-Test extrahieren.

**Dokumentations-Änderungsvorschläge (PFLICHT):**
- docs/ARCHITECTURE.md: Sektion zur `ExcludingMissingMembers`-Nutzung ergänzen (wann angemessen, wann gefährlich) → **Vorschlag an User, noch nicht durchgeführt**
- docs/SKELETON_SPEC.md: ✅ Status und Frontend-Hinweis bereits aktualisiert (diese Session)
- docs/GLOSSARY.md: Nein
- docs/REVIEW_CHECKLIST.md: Nein
- docs/NFR.md: Nein
- Phasen-Spec: Nein

### 2026-02-25 – Session 6: RecipesEndpoints GET+DELETE via TDD, Docs-Fixes, Phase-Korrektur

**Was lief gut:**
- 3 Sofort-Fixes aus Review sauber abgearbeitet (Rename, BeEquivalentTo, SoftDeletedConflict-Dedup).
- TDD-Zyklen für `GET /api/recipes` und `GET /api/recipes/{id}` ohne Abweichungen.
- Gold-Plating wurde 2× rechtzeitig erkannt und rückgängig gemacht (DeletedAt-Filter, NotFound-Guard).
- Zyklische Referenz in `GetAllRecipesFromDb()` früh entdeckt und durch Entfernen der Includes gelöst.

**Was war schwierig / hat nicht funktioniert – und warum:**
- **MSB3492 / DLL-Sperr-Fehler**: WSL schreibt Dateien, Windows-`dotnet` liest Cache gleichzeitig → regelmäßige Build-Fehler.
  → Gelöst: `dotnet build Server`, dann separat `dotnet build mahl.Server.Tests`, dann `--no-build`. Mit `ping -n 15` als Warte-Mechanismus.
  → Workaround in `docs/slow-commands.md` dokumentiert.
- **Sofort-grüner Test durch Gold-Plating in vorherigem Zyklus**: `r.DeletedAt == null`-Filter und `Results.NotFound()` wurden je einen Zyklus zu früh geschrieben.
  → TDD-Enforcement greift hier nicht mechanisch – der Agent muss den Pflicht-Check vor dem Speichern diszipliniert anwenden.
- **Zyklische Referenz**: `GetAllRecipesFromDb()` mit Include-Ketten erzeugt `Recipe.Ingredients[0].Recipe`-Zyklen die FluentAssertions nicht vergleichen kann.
  → Lösung: State-Assertion-Methoden (`GetAllXxxFromDb`) laden KEINE Navigations-Properties.

**Learnings:**
- `GetAllXxxFromDb()` für State-Assertions: niemals `Include()` – nur Toplevel-Felder. Navigations-Properties nur im Endpoint via EF laden.
- Den PFLICHT-CHECK vor dem Speichern (Phase 2) konsequent Zeile für Zeile durchführen – nicht "offensichtlich nötige" Guards hinzufügen.
- `ping -n N 127.0.0.1 >nul` als Warte-Mechanismus zwischen Server-Build und Test-Build auf WSL/Windows.

**Dokumentations-Änderungsvorschläge (PFLICHT):**
- docs/ARCHITECTURE.md: Regel ergänzen: "`GetAllXxxFromDb()` in Tests lädt keine Navigations-Properties (kein `Include`)." → Vorschlag an User.
- docs/GLOSSARY.md: Nein
- docs/REVIEW_CHECKLIST.md: Nein (bereits in dieser Session angepasst)
- docs/NFR.md: Nein
- Phasen-Spec: Nein

### 2026-02-25 – Session 5: TDD-Abschluss Ingredients + ROP-Refactoring + PreToolUse-Hook

**Was lief gut:**
- Vier verbleibende TDD-Zyklen (Delete_AlreadySoftDeleted, Restore 3×) wurden sauber durchgeführt.
- Minimality-Enforcement funktionierte: Beim Restore-Endpoint wurde Gold-Plating in der GREEN-Phase sofort erkannt und zurückgerollt.
- ROP-Refactoring des POST-Endpoints verlief reibungslos; `Map`, `BindAsync`, `MatchAsync` in `OneOfExtensions.cs` korrekt ergänzt.
- Guideline für ROP in Minimal-API-Endpoints wurde in `CODING_GUIDELINE_CSHARP.md` präzisiert (Tabelle + Referenz-Pattern).
- Code-Review + Test-Review als parallele Agenten: effizient, klare Findings.

**Was war schwierig / hat nicht funktioniert – und warum:**
- **TDD-Verstoß zu Sessionbeginn**: Agent wechselte sofort in "Implementierungsmodus" und bündelte mehrere Tests + Implementierungen.
  → Ursache: Die Formulierung "Implementiere folgenden Plan" triggerte Implementation-Mode ohne TDD-Ablauf.
  → Gelöst: PreToolUse-Hook `check-one-test.sh` zählt neue `[Test]`/`it(`-Vorkommen; blockiert bei > 1.
- **Hook-Erstellung schlug fehl**: `set -euo pipefail` nicht in WSL unterstützt; CRLF-Problem durch Write-Tool auf NTFS.
  → Gelöst: Hook via `cat > file << 'SCRIPT'` im Bash-Tool geschrieben (Unix-Zeilenenden).
- **ROP vergessen**: POST-Endpoint wurde ohne ROP implementiert, obwohl Guideline existierte.
  → Ursache: Guideline war vorhanden, aber kein Zeitpunkt im TDD-Workflow erzwingt den Guideline-Check für Endpoint-Implementierungen.
  → Offen: Eine mechanische Lösung (z. B. REFACTOR-Checkliste mit "ROP genutzt?") fehlt noch.
- **`SoftDeletedConflict`-Duplikat**: `file record` im Endpoint und `SoftDeletedConflictDto` im Shared sind nahezu identisch.
  → Technische Schuld, noch nicht behoben.

**Learnings:**
- Selbst wenn Docs und Guidelines vorhanden sind, umgeht der Agent sie in "Implementierungsmodus". Mechanische Enforcement-Hooks sind notwendig.
- Shell-Scripts auf NTFS immer via `cat << 'SCRIPT'`-Bash-Heredoc erstellen, nie via Write-Tool.
- Das REFACTOR-Schritt eignet sich als Checkpoint für Guideline-Compliance (ROP, Typen etc.) – explizit als Pflicht aufnehmen.
- `MatchAsync` ist nötig wenn `BindAsync` eine `Task<OneOf<...>>` zurückgibt – nicht `.Match()` direkt auf dem Task aufrufen.

**Dokumentations-Änderungsvorschläge (PFLICHT):**
- docs/ARCHITECTURE.md: Prüfen ob REFACTOR-Phase eine Checkliste für Guideline-Compliance enthält (ROP, Typen) – Vorschlag an User.
- docs/GLOSSARY.md: Nein
- docs/REVIEW_CHECKLIST.md: Persistenz-Check-Punkt aus Session 4 noch offen – prüfen und ggf. ergänzen. Vorschlag an User.
- docs/NFR.md: Nein
- Phasen-Spec: Nein

### 2026-02-24 – Session 4: TDD-Neustart IngredientsEndpoints + Test-Qualitäts-Guidelines

**Was lief gut:**
- Strikte RED→GREEN→REFACTOR-Zyklen mit expliziten PFLICHT-OUTPUTs haben funktioniert.
- Sofort-grüne Tests wurden korrekt als Gold-Plating identifiziert und rückgängig gemacht (Location-Header-Test).
- Parametrisierte Tests (`[TestCase]`) für Validierungsfälle haben die Testanzahl erhöht ohne Testlogik zu duplizieren.
- Test-Data-Builder (`AnIngredient(...)`) macht Tests schema-robust und lesbarer.
- Business-Entscheidung (409 bei Soft-Delete-Namenskonflikt) wurde nach Rückfrage korrekt getroffen und dokumentiert.

**Was war schwierig / hat nicht funktioniert – und warum:**
- **Gold-Plating wurde zu spät erkannt** (beim nächsten sofort-grünen Test statt beim Schreiben): Der GREEN-Schritt hatte keinen expliziten Minimalitäts-Check.
  → Gelöst: ARCHITECTURE.md Phase 2 um "PFLICHT-CHECK vor dem Speichern" erweitert; Phase 3 (REFACTOR) um Minimalitäts-Checklisten-Punkt ergänzt.
- **Full State Assertion** wurde anfangs als `ContainSingle` / `HaveCount` statt `BeEquivalentTo` umgesetzt.
  → Ursache: Guideline beschrieb das Prinzip, nannte aber `BeEquivalentTo` nicht als Standard-Methode.
  → Gelöst: Guideline präzisiert mit expliziter Hierarchie (BeEquivalentTo = Standard, HaveCount etc. = nur unterstützend).
- **Implizite Business-Entscheidung** (Soft-Delete-Verhalten bei Namenskonflikt) wurde kodiert ohne zu flaggen.
  → Ursache: TDD RED-Phase hatte keinen Checkpoint für Business-Entscheidungen.
  → Gelöst: Hinweis in Phase 1 (RED) ergänzt, der auf CLAUDE.md-Entscheidungsregel verweist.
- **Persistenz-Check fehlte** in Create-Tests: Nur Response wurde geprüft, nicht ob SaveChangesAsync wirklich aufgerufen wurde.
  → Gelöst: Neue Pflicht-Regel "Full State Assertion bei mutierenden Operationen" in ARCHITECTURE.md.

**Learnings:**
- `BeEquivalentTo(stateBeforeAction)` ist das stärkste Muster für "Zustand unverändert"-Tests.
- `AnIngredient(...)` Builder in Base-Klasse ist orthogonal zur Parametrisierung und löst das Schemaänderungs-Problem sauberer.
- Parametrisierung passt für gleichartige Validierungsfälle; erzwingt man sie für komplexe Setup-Logik, wird der Test unlesbar.
- `file record` für endpoint-interne Response-Typen (wie `SoftDeletedConflict`) hält den Namespace sauber.

**Dokumentations-Änderungsvorschläge (PFLICHT):**
- docs/ARCHITECTURE.md: ✅ Bereits in dieser Session aktualisiert (TDD-Phasen, Full State Assertion, Builder-Pattern, Parametrisierung)
- docs/GLOSSARY.md: Nein
- docs/REVIEW_CHECKLIST.md: Prüfen ob ein Punkt zu "Persistenz-Check in mutierenden Tests" fehlt – noch nicht geprüft
- docs/NFR.md: Nein
- Phasen-Spec: Nein

### 2026-02-24 – Session 3: Coding Guidelines eingeführt (fDDD / ROP / Type-Driven)

**Was lief gut:**
- Konzeptionelle Fragen (Übertragbarkeit auf TypeScript, Test-Code, Dokumentations-Integration) wurden direkt beantwortet ohne unnötige Exploration.
- Alle vier Integrationsschritte (neue Guideline-Datei, CLAUDE.md, ARCHITECTURE.md, Agent-Dateien) konnten in einer Runde konsistent umgesetzt werden.

**Was war schwierig / hat nicht funktioniert – und warum:**
- Kein technisches Problem. Reine Dokumentations-Session.

**Learnings:**
- Coding-Richtlinien wirken nur, wenn sie an allen Einstiegspunkten verlinkt sind: CLAUDE.md (Navigation), feature.md (Pflichtlektüre), Agent-Prompts (Kontext-Abschnitt). Ein einzelnes Dokument, das nicht verlinkt wird, wird ignoriert.
- TypeScript-spezifische Äquivalente (Branded Types, `neverthrow`, Discriminated Unions) sind ausdrucksstärker als ihre C#-Pendants bei Sum Types – das sollte im Review explizit genutzt werden.

**Dokumentations-Änderungsvorschläge (PFLICHT):**
- docs/ARCHITECTURE.md:     ✅ Bereits in dieser Session aktualisiert (neue Sektion 0 "Design Philosophy")
- docs/GLOSSARY.md:         Nein
- docs/REVIEW_CHECKLIST.md: Prüfen, ob ein Punkt zu "Branded Types in TypeScript" fehlt – kein dringender Bedarf erkannt
- docs/NFR.md:              Nein
- Phasen-Spec:              Nein

### 2026-02-20 – Session 2: Hook-Scripts mit falschen Zeilenenden

**Was war schwierig / hat nicht funktioniert – und warum:**
- Alle Shell-Scripts hatten CRLF-Zeilenenden, weil das Write-Tool Dateien auf dem NTFS-Laufwerk (via WSL) mit Windows-Zeilenenden schreibt.
- Das check-pre-commit.sh blockierte zusätzlich jeden weiteren Bash-Aufruf, weil der PreToolUse-Hook auf alle Bash-Befehle feuert – auch auf den Versuch, das Script selbst zu fixen.

**Learnings:**
- Shell-Scripts auf NTFS (WSL) niemals mit dem Write-Tool erstellen. Immer `cat > file << 'EOF' ... EOF` via Bash-Tool verwenden – das schreibt Unix-Zeilenenden.
- Bei PreToolUse-Hooks auf Bash aufpassen: Ein kaputtes Script blockiert sich selbst und alle weiteren Bash-Aufrufe. Im Zweifel den Hook temporär deaktivieren (exit 0) bevor man ihn repariert.

**Dokumentations-Änderungsvorschläge:**
- docs/DEV_WORKFLOW.md: Hinweis ergänzen, dass Shell-Scripts via `cat << 'EOF'` erstellt werden müssen, nicht via Write-Tool. → Vorschlag an User.
// lesson
### 2026-03-04 – Session 17: Quantity Sum-Type, Tooling-Verbesserungen, TDD-Disziplin

**Was lief gut:**
- Dokumentations-Inkonsistenz (`T?` in Domain-Typen) schnell erkannt und in REVIEW_CHECKLIST, CODING_GUIDELINE_CSHARP und decisions.md konsistent behoben.
- Stryker-Workflow erheblich verbessert: cleartext+json Reporter, Summary-Script, kombinierter Aufruf mit `tail -60 && python3 stryker-summary.py`, Permissions in settings.json überführt.
- TDD-Disziplin beim `abstract record`-Pivot: Sauberer Neustart statt Weiterbauen auf falscher Grundlage.

**Was war schwierig / hat nicht funktioniert – und warum:**
- **7 Stryker-Aufrufe für einen Lauf:** Ursache 1: DLL-Sperre nach vorherigem `dotnet test`. Ursache 2: grep auf ANSI-kodierten Output – DEV_WORKFLOW.md war bereits korrekt dokumentiert, wurde aber nicht gelesen. Problem-Typ: Disziplin, nicht Dokumentation.
- **`IsT0` im Domain-Typ:** Hook hat korrekt geblockt. Zeigt, dass "fake it" manchmal Überlegung braucht, welche Struktur das Minimum erzwingt.
- **Sum-Type-Design-Diskussion:** Erster Ansatz (`OneOf<decimal, None>` intern, `IsSpecified` als bool) war kein richtiger Sum-Type aus Caller-Sicht – erzwingt kein exhaustives Handling, kapselt zwar intern, bietet aber schlechte Ergonomie (Exception beim Zugriff auf uninitialisierten Wert).

**Learnings für die nächste Session:**
- DEV_WORKFLOW.md VOR jedem langen Befehl lesen – nicht nach dem ersten Fehler.
- Für `readonly record struct` Domain-Typen: **erster TDD-Zyklus ist immer `ParameterlessConstructor_Throws`** – dieser Typ braucht immer einen werfenden public Ctor.
- `abstract record` Sum-Types testen über `Match()`, nicht über `BeOfType<SubType>()` – testet Verhalten, nicht interne Struktur.

**Offene Designfrage für nächste Session:**
Wann `abstract record` (ADT) vs. `OneOf<A,B>` intern vs. `OneOf<A,B>` direkt exponiert?
- Bisher kommuniziert: `abstract record` bevorzugt wenn Subtypen bedeutsam unterschiedliche Struktur haben und Caller exhaustives Handling benötigen.
- `OneOf` direkt exponiert: wenn der Typ nur ein dünner Wrapper wäre (Frage: lohnt dann ein eigener Typ überhaupt?).
- Noch nicht geklärt: Gilt die `readonly record struct`-Regel auch für `abstract record`-Sum-Types (nein, da abstract = Referenztyp)? Und: Sollen `SpecifiedQuantity`/`UnspecifiedQuantity` public oder private (nested) sein? Diskussion in Session 17 endete mit Empfehlung für private Subtypen + `Match`, aber nicht abschließend entschieden.

**Dokumentations-Änderungsvorschläge:**
- `docs/ARCHITECTURE.md`: Abschnitt "Bestehende Typen" sollte `abstract record` Sum-Type vs. `OneOf`-intern vs. `OneOf`-exponiert mit Entscheidungskriterien ergänzen. **Vorschlag an User – nicht eigenständig geändert.**
- `docs/CODING_GUIDELINE_CSHARP.md`: Abschnitt 5 (Sum Types) sollte explizit sagen wann `abstract record` gegenüber `OneOf` bevorzugt wird. **Vorschlag an User.**
- `docs/REVIEW_CHECKLIST.md`: ✅ Minimalitäts-Abschnitt ergänzt (Mutation Testing sprachunabhängig).
- `docs/NFR.md`: Nein.
- Phasen-Spec: Nein.
