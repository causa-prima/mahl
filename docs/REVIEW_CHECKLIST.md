# Autor-Checkliste (Self-Review)

<!--
wann-lesen: Nach jedem TDD-REFACTOR-Schritt, vor dem Aufruf der Review-Agenten (Gate 2 der Definition of Done)
kritische-regeln:
  - Jeden Punkt explizit durchgehen – nicht überfliegen
  - Findings sofort fixen, bevor Review-Agenten gestartet werden
-->

## Inhalt

| Abschnitt | Inhalt | Wann lesen |
|-----------|--------|------------|
| Allgemeine Prinzipien | KISS, Naming nach Glossar | Immer |
| Architecture Layer | Typ-Deklarationen internal, kein InternalsVisibleTo, Testcode greift nur auf Ports zu | Bei neuen Typen, Projektreferenzen oder Tests |
| Domain Modeling | Value Types statt Primitives, Factory Methods, keine DTOs in Create(), keine nullable als Zustand | Bei neuen oder geänderten Typen, Endpoints oder Parametern |
| Komplexität & Refactoring | Methodenlänge, Verschachtelung, Duplikate | Immer |
| Tests | Verhalten statt Implementierung, Fehlerpfade, Full State Assertion, kein shared mutable State | Bei neuen oder geänderten Tests |
| Test-Audit | US-Tag im Testnamen, Traceability Spec↔Test, kein Gold-Plating in Tests | Bei jedem neuen Test |

> **Wann:** Nach jedem TDD-REFACTOR-Schritt, vor dem Aufruf der Review-Agenten.
> Die Checklisten der Review-Agenten stehen in `docs/LLM_PROMPT_TEMPLATE.md`.
>
> **Vollständige Regeln:** `docs/CODING_GUIDELINE_GENERAL.md` + `docs/CODING_GUIDELINE_CSHARP.md` / `docs/CODING_GUIDELINE_TYPESCRIPT.md`. Diese Checkliste ist der retrospektive Review-Modus dazu – sie prüft, ob die Guidelines eingehalten wurden.

Gehe jeden Punkt durch. Findings sofort fixen – erst dann Review-Agenten starten.

---

Alle Punkte sind **Probleme, die gefunden und gefixt werden müssen**. Ein Haken bedeutet: "Geprüft, kein Problem gefunden."

## Architecture Layer (aus `ARCHITECTURE.md` Sektion 0c)

- [ ] Neue Typ-Deklarationen (`class`/`record`/`struct`/`interface`/`enum`) in `Server/` sind `internal`? Kein `public` ohne explizite Begründung.
  → Ausnahme: `Infrastructure/`-Typen (`MahlDbContext`, `*DbType`) sind `public`.
  → Das betrifft die Typdeklaration, nicht Member-Sichtbarkeit (`private`/`protected` bleibt unberührt).
- [ ] Kein `InternalsVisibleTo` in `.csproj`-Dateien hinzugefügt?
- [ ] Testcode greift ausschließlich über HTTP-Requests und `MahlDbContext` zu – kein direktes Instantiieren von Domain-Typen?

## Allgemeine Prinzipien (aus `CODING_GUIDELINE_GENERAL.md`)

- [ ] KISS eingehalten? Keine Abstraktion für hypothetische Zukunft? Keine clever-überkomplexe Lösung?
- [ ] Naming aus `docs/GLOSSARY.md`? Namen selbsterklärend ohne Kommentar?

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
  → Read-Pfad: DbType → `ToDomain()` → Domain → `domain.ToDto(...)`. `ToDto()` lebt als file-level Extension Method auf dem Domain-Typ (nicht auf DbType). Siehe `CODING_GUIDELINE_CSHARP.md` Abschnitt 3.

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
  → Wenn das Verhalten bewusst unterschiedlich ist: durch einen Test explizit dokumentieren und in `decisions.md` begründen.
  → Beispiel aus Session 039: `GET /api/recipes` nutzte ursprünglich `ToUri()` (silent null), während `GET /api/recipes/{id}` via `ToDomain()` korrekt 500 zurückgab. Behoben durch `ToSummaryDtoOrError()` + `Sequence()`.

## Minimalität

- [ ] Wurde Mutation Testing auf alle geänderten Dateien ausgeführt und kein Survivor stillschweigend ignoriert?
  → Survivor = entweder Gold-Plating (Code löschen) oder äquivalenter Mutant (begründen + Exclusion).
  → Befehle: `docs/DEV_WORKFLOW.md` – Sektion "Mutation Testing".

## Komplexität & Refactoring

- [ ] Eine Methode hat mehr als ~20 Zeilen? → Refactoring-Kandidat
- [ ] Verschachtelung tiefer als 3 Ebenen? → Pattern Matching oder Extraktion erwägen
- [ ] Gibt es Duplikate oder Copy-Paste-Code, der ein gemeinsames Helper verdienen würde?

## Tests

- [ ] Ein Test prüft Implementierungsdetails statt beobachtbares Verhalten (bricht bei harmlosen Refactorings)?
- [ ] Fehlerpfade fehlen (ungültige Eingaben, Not Found, Konflikte)?
- [ ] Testcode ist schwer verständlich – ein anderer Entwickler würde nicht schnell verstehen, was getestet wird?
- [ ] Tests hängen voneinander ab oder teilen mutable State?
- [ ] Mutierender Endpoint-Test (POST/PUT/PATCH/DELETE): Wird der DB-Zustand nach der Aktion mit **Full State Assertion** (`GetAllXxx()` + `BeEquivalentTo`) geprüft – nicht nur die HTTP-Response? Damit wird sichergestellt, dass genau die erwarteten Änderungen in der DB gelandet sind und keine unerwarteten Seiteneffekte aufgetreten sind (weder fehlende Änderungen noch ungewollte Mutationen anderer Einträge).
  → Auch Fehlerpfade: Zustand nach einem Fehler muss dem Ausgangszustand entsprechen (`BeEquivalentTo(stateBeforeAction)`).

## Test-Audit (aus `E2E_TESTING.md`)

- [ ] Beginnt jeder neue Backend-Integrations-Testname mit US-Tag und ScenarioType (`USxxx_ScenarioType_MethodName_Szenario_ErwartetesErgebnis`, z.B. `US201_HappyPath_Create_ValidData_Returns201`)?
- [ ] Hat jedes neue Gherkin-Szenario mindestens einen grünen E2E-Test?
- [ ] Gibt es Backend- oder E2E-Tests ohne darüberliegendes Gherkin-Szenario? → Outside-In-Verletzung. Prozess: (1) Noch relevant? Nein → löschen. Ja → Szenario schreiben + `@US-NNN`-Tag ergänzen. (2) Befund in `docs/history/decisions.md` dokumentieren.
- [ ] Wurden nur Tests angelegt, die das Szenario wirklich fordert? Kein Gold-Plating in Tests (YAGNI gilt auch für Tests).
- [ ] Stimmen bestehende Szenarien noch mit dem implementierten Verhalten überein (kein Silent Drift)?
