# Session 35 – 2026-03-24

## Phase
SKELETON – Statische Code-Analyse Einrichtung

## Ziel der Session
Statische Code-Analyse-Tools evaluieren, einrichten und erste Suppressions/Fixes durchführen.

## Abgeschlossen

### Evaluierung & Entscheidung
- Ausführliche Analyse: welche Tools für dieses Projekt sinnvoll sind und warum
- Entscheidung für: `Microsoft.CodeAnalysis.NetAnalyzers` (AnalysisMode=Recommended), `SonarAnalyzer.CSharp`, `Meziantou.Analyzer`, `@typescript-eslint/strictTypeChecked`, `eslint-plugin-functional`
- Begründung: schließt zwei offene NFR-Lücken (Cyclomatic Complexity, Duplicate Code); Analyzer sind zuverlässiger als Regex-Hooks wo sie sich überschneiden

### Tooling eingerichtet
- `Directory.Build.props`: `AnalysisMode=Recommended`, `SonarAnalyzer.CSharp 10.21.0.135717`, `Meziantou.Analyzer 3.0.26` (gilt für alle Projekte)
- `Client/eslint.config.js`: auf `tseslint.configs.strictTypeChecked` hochgestuft + `eslint-plugin-functional 9.0.4` (recommended + external TS rules)
- `parserOptions.projectService: true` für composite TypeScript-Projekt (tsconfig.app.json + tsconfig.node.json)
- 3 funktionale React-Regeln deaktiviert (Category-1-Suppressionen): `no-expression-statements`, `no-return-void`, `functional-parameters`
- `no-mixed-types` aktiv gelassen (erzwingt konsistente Property- vs Method-Syntax in Types)

### Findings analysiert und kategorisiert
- Vollständige Auswertung aller ~370 Warnings (Server + Server.Tests) in 3 Kategorien
- Suppressions-Framework: Category 1 (technisch) → sofort, Category 2 (unbewusste Konvention) → evaluieren/fixen, Category 3 → Rücksprache

### .editorconfig ergänzt (pattern-basierte Suppressions)
- `MA0004` (ConfigureAwait) in `Server/**/*.cs` und `Server.Tests/**/*.cs`
- `MA0016` (List<T>) in `Server/Data/DatabaseTypes/*.cs`
- `MA0051`, `MA0048`, `CA1861` in `Server/Migrations/**/*.cs`
- `CA1707` (Unterstriche), `CA1806` (ParameterlessConstructor), `S2187` (abstract base) in `Server.Tests/**/*.cs`

### decisions.md
- S4581: `== default` bleibt erlaubt für uninitialisierten Guid-Guard (bewusste Entscheidung, nicht `Guid.Empty`)

### CODING_GUIDELINE_CSHARP.md
- Guid-Guard-Beispiel: `== default` bleibt dokumentiert (S4581-Entscheidung in decisions.md)

## Offen / Nächste Session

### Pragma-Suppressionen (noch ausstehend)
- `S3060` in `Quantity.cs` und `RecipeSource.cs` (Sum-Type-Match-Pattern)
- `CA1000` in `NonEmptyList.cs` (Factory Method auf Generic)
- `CA1305` + `S1118` in `Program.cs` (Serilog IFormatProvider, Program partial class)
- `S1075` in `SeedDataExtensions.cs` (hardcoded Seed-URLs)
- `S4487` in `Pages/Error.cshtml.cs` (ungenutztes `_logger`-Feld)
- `S4581` in Domain-Typen (4×, `== default` Guid-Guard per Entscheidung)

### Code-Fixes (noch ausstehend)
- `S6966`: `app.Run()` → `await app.RunAsync()` in `Program.cs`
- `CA1805`: `AlwaysInStock = false` entfernen (expliziter Default in `IngredientDbType`)
- `S1905`: 3× unnötiger `(IResult)`-Cast in Endpoint-Dateien
- `S2629`/`CA2254`: String-Konkatenation im Log-Template in `Helpers.cs`
- `CA1848`: `LoggerMessage`-Delegate oder pragma in `Helpers.cs`
- `MA0002`: `Dictionary` ohne `StringComparer.Ordinal` in `Helpers.cs`
- `CA1305` Serilog: `formatProvider: CultureInfo.InvariantCulture` hinzufügen
- Namespace für `ParallelTestLogging.cs` (`ParallelTestLogStore`, `TestIdSink`)
- `CA1852`: `sealed` für `NonEmptyTrimmedStringTests`
- `MA0006` (20×): `StringComparison.Ordinal` in Test-Vergleichen

### Refactorings (noch ausstehend)
- `EndpointsTestsBase`: `_factory`/`_testId` → `private`, `_client` → `protected HttpClient Client { get; }` + alle Verwendungen umbenennen
- `MA0016` in Test-Buildern: `List<T>?` → `IReadOnlyList<T>?` (Parameter + Rückgabetypen)
- DTO-Dateien aufsplitten (Situation A: je 1 Typ pro Datei in `Server/Dtos/`)
- Hooks evaluieren: welche sind durch Analyzer jetzt redundant?

## Testergebnisse
- 155 Tests ✅ (unverändert, nur Build-Konfiguration geändert)
- Build: kompiliert, ~370 Warnings (werden in nächster Session abgebaut)
