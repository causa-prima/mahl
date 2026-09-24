# Autor-Checkliste (Self-Review)

<!--
wann-lesen: Nach jedem TDD-REFACTOR-Schritt, vor dem Aufruf der Review-Agenten ([Gate „Autor-Review"](nfr.md#NFR-gate-autor-review) der Definition of Done)
kritische-regeln:
  - Jeden Punkt explizit durchgehen – nicht überfliegen
  - Findings sofort fixen, bevor Review-Agenten gestartet werden
-->

<a id="RCL-inhalt"></a>
## Inhalt

| Abschnitt | Inhalt | Wann lesen |
|-----------|--------|------------|
| [Allgemeine Prinzipien](#RCL-allgemeine-prinzipien) | KISS, Naming nach Glossar | Immer |
| [Architecture Layer](#RCL-architecture-layer) | Typ-Deklarationen internal, kein InternalsVisibleTo, Testcode greift nur auf Ports zu | Bei neuen Typen, Projektreferenzen oder Tests |
| [Domain Modeling](#RCL-domain-modeling) | Value Types statt Primitives, Factory Methods, keine DTOs in Create(), keine nullable als Zustand | Bei neuen oder geänderten Typen, Endpoints oder Parametern |
| [Komplexität & Refactoring](#RCL-komplexitaet) | Methodenlänge, Verschachtelung, Duplikate | Immer |
| [Tests](#RCL-tests) | Verhalten statt Implementierung, Fehlerpfade, Full State Assertion, kein shared mutable State | Bei neuen oder geänderten Tests |
| [Test-Audit](#RCL-test-audit) | US-Tag im Testnamen, Traceability Spec↔Test, kein Gold-Plating in Tests | Bei jedem neuen Test |
| [Prozess-Code](#RCL-prozess-code) | Wirkung statt Lauffähigkeit: Gegenprobe, Auslösestelle, Meldungsqualität, fail-open | Bei jeder Änderung an Python unter `prozesscode/` – und dann **statt** der Abschnitte darüber |

> **Wann:** Nach jedem TDD-REFACTOR-Schritt, vor dem Aufruf der Review-Agenten.
> Die Checklisten der Review-Agenten stehen in den Agent-Definitionen unter `.claude/agents/`.
>
> **Vollständige Regeln:** `docs/guidelines/coding-guideline-general.md` + `docs/guidelines/coding-guideline-csharp.md` / `docs/guidelines/coding-guideline-typescript.md` / `docs/guidelines/coding-guideline-python.md`. Diese Checkliste ist der retrospektive Review-Modus dazu – sie prüft, ob die Guidelines eingehalten wurden.

Gehe jeden Punkt durch. Findings sofort fixen – erst dann Review-Agenten starten.

---

Alle Punkte sind **Probleme, die gefunden und gefixt werden müssen**. Ein Haken bedeutet: "Geprüft, kein Problem gefunden."

<a id="RCL-endpoints"></a>
## Endpoints

- [ ] Neuer GET-Endpoint? → `ETag`-Header gesetzt + `If-None-Match` → 304 implementiert?
  → Single Resource: xmin (`UseXminAsConcurrencyToken()`). Collection: SHA-256-Hash der Response-Body.
- [ ] Neuer PUT/PATCH/DELETE-Endpoint? → `If-Match`-Prüfung implementiert (fehlend → 428, Mismatch → 412)?
  → Muster: `docs/guidelines/coding-guideline-csharp.md` [Endpoints – ETag-Pflicht](../guidelines/coding-guideline-csharp.md#CGC-endpoints-etag).

<a id="RCL-architecture-layer"></a>
## Architecture Layer (aus [Hexagonal Architecture](../reference/architecture.md#ARC-hexagonal))

- [ ] Neue Typ-Deklarationen (`class`/`record`/`struct`/`interface`/`enum`) in `Server/` sind `internal`? Kein `public` ohne explizite Begründung.
  → Ausnahme: `Infrastructure/`-Typen (`MahlDbContext`, `*DbType`) sind `public`.
  → Das betrifft die Typdeklaration, nicht Member-Sichtbarkeit (`private`/`protected` bleibt unberührt).
- [ ] Kein `InternalsVisibleTo` in `.csproj`-Dateien hinzugefügt?
- [ ] Testcode greift ausschließlich über HTTP-Requests und `MahlDbContext` zu – kein direktes Instantiieren von Domain-Typen?

<a id="RCL-allgemeine-prinzipien"></a>
## Allgemeine Prinzipien (aus `docs/guidelines/coding-guideline-general.md`)

- [ ] KISS eingehalten? Keine Abstraktion für hypothetische Zukunft? Keine clever-überkomplexe Lösung?
- [ ] Naming aus `docs/reference/glossary.md`? Namen selbsterklärend ohne Kommentar?

<a id="RCL-domain-modeling"></a>
## Domain Modeling

- [ ] Neue Properties/Parameter verwenden einen eingebauten Typ (`string`, `int`, `decimal`, ...) obwohl es ungültige Werte gibt?
  → Frage: *Welche Werte wären für dieses Konzept ungültig?* Wenn es solche Werte gibt, braucht das Konzept einen eigenen Typ.
  → C#: `NonEmptyTrimmedString`, `PositiveInt`, etc. (`Server/Types/` als Referenz)
  → TypeScript: Branded Type (`type RecipeId = string & { readonly __brand: 'RecipeId' }`)
  → Gilt auch für Methodenparameter und Props, nicht nur Properties/State.

- [ ] TypeScript: Rohe `string`/`number` als IDs zwischen Komponenten/Services weitergereicht, obwohl verschiedene ID-Konzepte existieren?
  → Verschiedene IDs (RecipeId, IngredientId, WeeklyPoolEntryId) müssen unterschiedliche Branded Types sein – der Compiler soll falsche Zuordnungen verhindern.

- [ ] Neue Domain-Entities werden mit `new` direkt konstruiert statt über eine Factory Method?

- [ ] `Create()`-Parameter sind DTOs oder DbTypes statt Primitives/Domain-Types?
  → Factory Methods nehmen nur Primitives (`string`, `int`, ...) und andere Domain-Typen entgegen.
  → Mapping DTO → Primitives gehört in den Endpoint-Layer, nicht in den Domain-Typ.

- [ ] `ToDto()` ist auf einem DbType definiert statt auf dem Domain-Typ?
  → Read-Pfad: DbType → `ToDomain()` → Domain → `domain.ToDto(...)`. `ToDto()` lebt als file-level Extension Method auf dem Domain-Typ (nicht auf DbType). Siehe `docs/guidelines/coding-guideline-csharp.md` [Systemgrenz-Architektur](../guidelines/coding-guideline-csharp.md#CGC-systemgrenze).

- [ ] `T?` (nullable) als **Property-Typ** eines Domain-Typs verwendet, obwohl null einen semantischen Sonderzustand bedeutet?
  → Ein eigener Typ mit `OneOf<T, Unknown>` intern. `T?` als Domain-Property ist verboten – auch nicht als "pragmatischer Shortcut".
  → Nullable als **Parameter** einer Factory-Methode ist OK (Systemgrenze zu DTO/Primitives).
  → Nullable ist außerdem erlaubt in: DbTypes (`Server/Data/DatabaseTypes/`), DTOs, ASP.NET Options/Settings.

- [ ] Neue `record`-Properties haben `set` statt `init`?

- [ ] Factory-Method-Fehler werden im Endpoint-Layer nicht als HTTP 400 behandelt, oder es gibt einen vorgelagerten Validierungs-Layer?
  → Separate Validierung, die dieselben Regeln wie die Factory Method prüft, ist ein Anti-Pattern (divergiert zwangsläufig).
  → Ausnahme: Cross-Entity-Constraints (z.B. DB-UNIQUE) können nicht im Typ ausgedrückt werden und gehören als expliziter Check ins Endpoint-Layer.

- [ ] Mehrere Endpunkte konvertieren denselben DB-Wert auf unterschiedlichen Pfaden (z.B. ein Helper direkt, ein anderer via `ToDomain()`)?
  → Prüfen: Ist die Fehlerbehandlung konsistent? Ein Pfad, der bei korrupten Daten 500 zurückgibt, ein anderer der still `null` liefert, ist ein Fehler — nicht ein Tradeoff.
  → Wenn das Verhalten bewusst unterschiedlich ist: durch einen Test explizit dokumentieren und in `adr.md` begründen.
  → Beispiel aus Session 039: `GET /api/recipes` nutzte ursprünglich `ToUri()` (silent null), während `GET /api/recipes/{id}` via `ToDomain()` korrekt 500 zurückgab. Behoben durch `ToSummaryDtoOrError()` + `Sequence()`.

<a id="RCL-minimalitaet"></a>
## Minimalität

- [ ] Wurde Mutation Testing auf alle geänderten Dateien ausgeführt und kein Survivor stillschweigend ignoriert?
  → Survivor = entweder Gold-Plating (Code löschen) oder äquivalenter Mutant (begründen + Exclusion).
  → Befehle: `docs/process/dev-workflow.md` – Sektion "[Mutation Testing](dev-workflow.md#DEV-mutation-testing)".

<a id="RCL-komplexitaet"></a>
## Komplexität & Refactoring

- [ ] Eine Methode hat mehr als ~20 Zeilen? → Refactoring-Kandidat
- [ ] Verschachtelung tiefer als 3 Ebenen? → Pattern Matching oder Extraktion erwägen
- [ ] Gibt es Duplikate oder Copy-Paste-Code, der ein gemeinsames Helper verdienen würde?

<a id="RCL-tests"></a>
## Tests

- [ ] Ein Test prüft Implementierungsdetails statt beobachtbares Verhalten (bricht bei harmlosen Refactorings)?
- [ ] Fehlerpfade fehlen (ungültige Eingaben, Not Found, Konflikte)?
- [ ] Testcode ist schwer verständlich – ein anderer Entwickler würde nicht schnell verstehen, was getestet wird?
- [ ] Tests hängen voneinander ab oder teilen mutable State?
- [ ] Gibt es Unit Tests auf Value Types, Domain-Typen oder Service-Klassen die **keine** HTTP-Integrationstests und keine MSW-Komponenten-Tests sind? → **Kritisch prüfen:** Liegt ein Stryker-Survivor-Report vor, der diesen Test erzwingt (Survivor strukturell nicht via HTTP beobachtbar)? Wenn nein → Gold-Plating (Test und ggf. zugehöriger Code löschen). Wenn ja → Begründung im Survivor-Report vollständig und nachvollziehbar?
- [ ] Mutierender Endpoint-Test (POST/PUT/PATCH/DELETE): Wird der DB-Zustand nach der Aktion mit **Full State Assertion** (`GetAllXxx()` + `BeEquivalentTo`) geprüft – nicht nur die HTTP-Response? Damit wird sichergestellt, dass genau die erwarteten Änderungen in der DB gelandet sind und keine unerwarteten Seiteneffekte aufgetreten sind (weder fehlende Änderungen noch ungewollte Mutationen anderer Einträge).
  → Auch Fehlerpfade: Zustand nach einem Fehler muss dem Ausgangszustand entsprechen (`BeEquivalentTo(stateBeforeAction)`).
- [ ] (Frontend) Werden HTTP-Calls in Tests auf falscher Ebene gemockt (`vi.mock` auf Service-Modulen, `vi.stubGlobal('fetch', ...)` o.ä.)? → Ausschließlich MSW verwenden. Service-Funktionen sind Implementierungsdetails – sie werden durch den Komponenten-Test via MSW abgedeckt, nicht direkt getestet. Siehe `docs/guidelines/coding-guideline-typescript.md` [Test-Architektur](../guidelines/coding-guideline-typescript.md#CGT-msw).
- [ ] (Frontend) Hängt eine Folge-Interaktion davon ab, dass ein vorheriger UI-Übergang abgeschlossen ist (Dialog/Overlay geschlossen, Element entfernt/aktiviert)? → Wird dieser Übergang **explizit per Assertion** geprüft (z.B. `await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())`)? `fireEvent.click` prüft keine Actionability – ohne die Assertion bliebe ein Regress, der den Übergang unterlässt, unbemerkt. Siehe `docs/guidelines/coding-guideline-typescript.md` [Test-Architektur](../guidelines/coding-guideline-typescript.md#CGT-dom-matcher).

<a id="RCL-ui-ux"></a>
## UI/UX (aus `docs/guidelines/coding-guideline-ux.md`)

- [ ] Least Surprise: Tut jede Aktion exakt das, was Label, Position und Kontext erwarten lassen?
- [ ] Don't Make Me Think: Braucht ein Element einen Tooltip oder eine Erklärung um verstanden zu werden? → Label oder Struktur überarbeiten bis der Tooltip überflüssig ist.
- [ ] Sichtbares Feedback: Hat jede Aktion ohne direkten UI-Zustandswechsel einen Toast oder Inline-Feedback? Zeigt jede wartende Aktion einen Ladezustand?
- [ ] Fehlermeldungen: Ist jede Fehlermeldung konkret ("Name darf nicht leer sein.") und nah am betroffenen Element platziert?
- [ ] Destructive Actions: Bevorzugt Soft-Delete mit Wiederherstellungsmöglichkeit im UI. Bestätigungsdialog nur wenn Soft-Delete nicht machbar.
- [ ] Terminologie: Verwendet die UI ausschließlich Begriffe aus `docs/reference/glossary.md`? Keine Synonyme in Labels, Buttons, Fehlermeldungen oder leeren Zuständen.
- [ ] Leere Zustände: Erklärt jede potenziell leere Liste (1) warum sie leer ist und (2) was der Nutzer tun kann?
- [ ] Formular-/Dialog-Baseline ([UX-Guideline](../guidelines/coding-guideline-ux.md#CGU-formular-baseline), nur bei Formularen/Dialogen): Pflichtfelder markiert (`required`/`aria-required`, jedes Feld mit Leerwert-Fehler)? Fokus beim Öffnen im visuell ersten Feld (kein CSS-Reorder)? Nach Validierungsfehler Fokus aufs erste fehlerhafte Feld? Enter sendet via echtem `<form>` (kein manueller `keydown→submit`)? Escape/Fokus-Falle/Fokus-Rückkehr durch MUI `Dialog` nicht abgeschaltet?

<a id="RCL-test-audit"></a>
## Test-Audit (aus `docs/process/e2e-testing.md`)

- [ ] Beginnt jeder neue Backend-Integrations-Testname mit US-Tag und ScenarioType (`USxxx_ScenarioType_MethodName_Szenario_ErwartetesErgebnis`, z.B. `US201_HappyPath_Create_ValidData_Returns201`)?
- [ ] Hat jedes neue Gherkin-Szenario mindestens einen grünen E2E-Test?
- [ ] Gibt es Backend- oder E2E-Tests ohne darüberliegendes Gherkin-Szenario? → Outside-In-Verletzung. Prozess: (1) Noch relevant? Nein → löschen. Ja → Szenario schreiben + `@US-NNN`-Tag ergänzen. (2) Befund in `docs/history/adr.md` dokumentieren.
- [ ] Wurden nur Tests angelegt, die das Szenario wirklich fordert? Kein Gold-Plating in Tests (YAGNI gilt auch für Tests).
- [ ] Stimmen bestehende Szenarien noch mit dem implementierten Verhalten überein (kein Silent Drift)?

<a id="RCL-prozess-code"></a>
## Prozess-Code (Python unter `prozesscode/`)

Für Python unter `prozesscode/` gelten **diese Punkte statt der Abschnitte darüber** – jene prüfen
Architektur, Domain-Modellierung und Szenario-Bindung, die es hier alle nicht gibt. Die Maßgaben
und ihr Grund stehen in [`coding-guideline-python.md`](../guidelines/coding-guideline-python.md#CGP-was-gilt);
diese Liste ist der retrospektive Prüfmodus dazu.

Der gemeinsame Nenner aller Punkte: Ein Werkzeug kann fehlerfrei laufen und trotzdem nicht
wirken. Lauffähigkeit prüfen bereits `ruff` und die Werkzeug-Suite automatisch – ungeprüft
bleibt die Wirkung.

- [ ] **Gegenprobe gefahren?** Prüfmechanismus (Hook, Gate, Guard, Wrapper) einmal absichtlich
  gebrochen und beim Anspringen gesehen – nicht nur grüne Tests. → [`CGP-gegenprobe`](../guidelines/coding-guideline-python.md#CGP-gegenprobe)
- [ ] **Gibt es eine Stelle, die den Mechanismus auslöst?** Ein Guard ohne Registrierung, eine
  Ignore-Regel auf einem Pfad, den es nicht gibt, ein Ausgabeblock hinter einem Größen-Cap:
  alle drei laufen fehlerfrei und tun nichts.
- [ ] **Läuft der Test gegen das echte Artefakt?** Aufrufpfad statt nur Funktion, echte Ausgabe
  des fremden Werkzeugs statt erfundener Fixture, Fixture in der Form des Bestands (mehrere
  Einträge, Header). → [`CGP-echtes-artefakt`](../guidelines/coding-guideline-python.md#CGP-echtes-artefakt)
- [ ] **Nennt jede Meldung den Ausweg**, nicht nur den Befund (herstellender Befehl, zu
  ändernde Datei)? → [`CGP-meldungen`](../guidelines/coding-guideline-python.md#CGP-meldungen)
- [ ] **Fail-open, wo ein Nebenzweck scheitern darf?** Protokollierung, Statistik und Parser
  dürfen einen blockierenden Guard nie mitreißen – und ein Parser-Fehlgriff darf nie
  Information verschlucken (er meldet sich, statt still „nichts gefunden" zu liefern).
- [ ] **Wrapper-Ausgabe:** im Erfolgsfall nur das Verdikt, im Fehlerfall nur das
  Analyse-Relevante, alles Weitere hinter `--verbose`?
- [ ] **Prüft der Test die Wirkung oder nur den Aufruf?** Würde er rot, wenn der Mechanismus
  das Fragliche nicht mehr prüft? Sonst deckt er Klasse LAUT doppelt und Klasse STUMM gar nicht.
- [ ] **Trägt jeder Eintrag einer Bestandsliste** (Baseline, Ausnahme, Allow-Liste) seinen
  Grund im Code? Ohne ihn wird sie zur Müllhalde, weil niemand mehr weiß, was raus darf.
