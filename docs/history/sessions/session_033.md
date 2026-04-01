# Session 33 – 2026-03-18

## Ziel
Shared-Projekt auflösen: `mahl.Shared`, `mahl.Shared.Test`, `mahl.Tests.Shared` und `mahl.Server.Tests`-Ordner konsolidieren.

## Umgesetzt

### Projektstruktur
- `Shared/` → Typen nach `Server/Types/`, DTOs nach `Server/Dtos/`, `OneOfExtensions` + `Constants` nach `Server/`
- `mahl.Shared.Test/` → nützliche Tests (NonEmptyTrimmedString, TrimmedString, NonEmptyList, OneOfExtensions) nach `Server.Tests/Types/` + Root; Legacy-Tests (ShoppingList, ShoppingListItem, SyncItemId) gelöscht
- `mahl.Tests.Shared/` → `Satisfy<T>` nach `Server.Tests/Helpers/TestHelpers.cs`; `FailWithTypeMismatch` gelöscht (nur in Legacy-Tests verwendet)
- `mahl.Server.Tests/` (Ordner) → `Server.Tests/mahl.Server.Tests.csproj` (Ordner umbenannt, Projektdatei behält `mahl.`-Prefix für Konsistenz mit `mahl.Server`)

### Namespace-Migration
- `mahl.Shared` → `mahl.Server`
- `mahl.Shared.Types` → `mahl.Server.Types`
- `mahl.Shared.Dtos` → `mahl.Server.Dtos`
- Alle using-Statements in `Server/Domain/`, `Server/Endpoints/`, `Server.Tests/` aktualisiert

### Scripts & Tooling
- `dotnet-test.py`: `--project`-Flag entfernt (nur noch ein Testprojekt)
- `dotnet-stryker.py`: `_SUBDIR_FOR_PROJECT`-Logik + `--project mahl.Shared.csproj`-Unterstützung entfernt
- `check-bash-permission.py`, `test-bash-permission.py`: Deny/Allow-Beispiele aktualisiert
- `stryker-summary.py`: Anchor `"Shared/"` + `"mahl.Server.Tests/"` → `"Server.Tests/"`
- `stryker-config.json`: Testprojekt-Pfad aktualisiert
- `tdd-workflow/skill.md`, `DEV_WORKFLOW.md`, `TDD_PROCESS.md`, `slow-commands.md`: Projektnamen aktualisiert

### Bug durch Rename behoben
- `checks/test_patterns.py`: `TEST_FILE_PATTERN` hatte hardcodierte Projektnamen (`mahl.Server.Tests|mahl.Shared.Test|mahl.Tests.Shared`) → nach Rename griff der Check nicht mehr → auf `Server\.Tests` aktualisiert

### `mahl.Server.Tests.csproj`
- `ProjectReference` zu `mahl.Tests.Shared` entfernt
- `<Using Include="FluentAssertions" />` ergänzt (migrierten Tests fehlte das global using aus dem alten Shared-Test-Projekt)

## Ergebnisse
- 151 .NET-Tests ✅ (Reduktion von 224: intentionell gelöschte Legacy-Tests für altes Blazor-Domainmodell)
- 57 Hook-Tests ✅
- Stryker: **98.3%** – 3 neue Survivors durch Migration Shared→Server

## Offene Punkte
- Stryker-Survivors: `OneOfExtensions.cs:41` (Test schreiben), `NonEmptyList.cs:12` (Message-Assertion), `RecipesEndpoints.cs:58` (Ursache untersuchen)
