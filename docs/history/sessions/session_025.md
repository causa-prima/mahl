# Session 25 – 2026-03-11

**Phase:** SKELETON (Tooling / Qualität)

---

## Implementiertes

### 1. Hook-Erweiterung: `.Should().Contain()` verboten

**Kontext:** Diskussion über Pro/Contra eines `Contain`-Verbots im `test_patterns.py`-Hook.

**Analyse-Ergebnis:**
- Initialer Vorschlag (nur Lambda-Form `Contain(x =>` verbieten) wurde nach User-Nachfrage revidiert
- `body.Should().Contain("text")` auf Response-Bodies ist ebenfalls eine partielle Assertion
- Für Plain-Text-Bodies: `.Should().Be(exactString)` ist die vollständige Assertion
- Für JSON-Bodies: `ReadFromJsonAsync<T>()` + typisierte Assertion

**Änderungen:**
- `checks/test_patterns.py`: `CONTAIN_PATTERN` als separater Check (analog `ExcludingMissingMembers`) mit eigenem Hinweistext
- 3 neue pytest-Tests in `tests/test_test_patterns.py` (gebündelt als Ausnahme, nicht one-at-a-time)
- 13/13 Hook-Tests ✅

### 2. C#-Tests gefixed (TDD)

Die 3 `.Contain()`-Vorkommen in `IngredientsEndpointsTests.cs` ersetzt:

| Test | Alt | Neu |
|------|-----|-----|
| `Create_InvalidInput_Returns422WithMessage` | `body.Should().Contain(expectedMessage)` | `body.Should().Be($"\"{expectedMessage}\"")` |
| `Create_DuplicateName_Returns409WithConflictMessage` (umbenannt) | `body.Should().Contain("Butter")` | `body.Should().Be("\"Eine Zutat mit dem Namen 'Butter' existiert bereits.\"")` |
| `GetById_CorruptIngredient_Returns500WithProblemDetails` | `body.Should().Contain("DB inconsistency...")` | `ReadFromJsonAsync<ProblemDetails>()` → `.Detail.Should().Be(...)` |

### 3. Produktionsbug behoben (durch präzise Assertion aufgedeckt)

**Bug:** `IngredientsEndpoints.cs` L62: `$"... '{ingredient.Name.Value}' ..."` rief `TrimmedString.ToString()` auf → record-struct-Default `"TrimmedString { Value = Butter }"` statt `"Butter"`.

**Fix:** `(string)ingredient.Name` statt `ingredient.Name.Value` in String-Interpolation.

**Root Cause:** `NonEmptyTrimmedString.Value` gibt `TrimmedString` zurück (nicht `string`). In String-Interpolation wird `.ToString()` aufgerufen, nicht der implizite `string`-Operator. `TrimmedString` hat kein `ToString()`-Override.

### 4. TestCase-Werte korrigiert

`[TestCase]`-Attribute in `Create_InvalidInput_Returns422WithMessage`: Fehlermeldungen fehlten Abschluss-Punkte (`"Name darf nicht leer sein"` → `"Name darf nicht leer sein."`). Der `.Contain()`-Test war trotzdem grün, weil `"Name darf nicht leer sein."` den Substring `"Name darf nicht leer sein"` enthält.

---

### 5. `TrimmedString.ToString()` ergänzt (TDD)

**Anlass:** Diskussion nach Bugfix – warum hat `TrimmedString` kein `ToString()`?

**Befund:** Kein Oversight der Uninitialized-Guard-Logik, sondern eine konzeptuelle Inkonsistenz: `(NonEmpty)TrimmedString` repräsentiert konzeptuell einen String und verhält sich via `implicit operator string` in Zuweisung/Rückgabe auch so – aber nicht in String-Interpolation, wo C# `ToString()` aufruft. Da `TrimmedString` ein `readonly record struct` ohne `ToString()`-Override ist, greift der Default (`"TrimmedString { Value = ... }"`).

**Fix:** `public override string ToString() => Value;` in `TrimmedString.cs` (TDD: 1 neuer Test). Cast `(string)ingredient.Name` in `IngredientsEndpoints.cs` anschließend entfernt.

**Ergebnis:** 117 Shared-Tests ✅, 93 Server-Tests ✅.

---

## Ergebnis

- 93 Server-Tests ✅
- 117 Shared-Tests ✅
- 13 Hook-Tests ✅
- 1 Produktionsbug behoben (TrimmedString.ToString)
- 2 verdeckte Test-Qualitätsprobleme behoben (Punkte in TestCase + Contain→Be)

---

### 6. Hook-Regex für Stryker erweitert (TDD)

**Problem:** `check-bash-permission.py` erlaubte nur `mahl && dotnet stryker`, nicht `mahl\Subpfad && dotnet stryker`.

**Analyse:** Kein Bug in Stryker – Usage Error. Stryker erkennt `.sln` im CWD und aktiviert Solution-Mode, der `--project`/`--test-project`-Flags ignoriert → NullReferenceException. Lösung: Stryker aus dem Testprojekt-Unterverzeichnis aufrufen.

**Regex-Änderung:** `mahl\s*&&` → `mahl[^\s&"]*\s*&&` – erlaubt Pfad-Suffix nach `mahl`, verbietet Whitespace/`&`/`"` (keine Shell-Operatoren injizierbar, ungültige Pfadzeichen lassen `cd` einfach fehlschlagen).

**Tests:** 4 neue Fälle in `test-bash-permission.py` (1 allow: Subpfad mit Summary-Script; 3 deny: ohne Summary-Script, Leerzeichen im Pfad, `&` im Pfad, `"` im Pfad).

---

## Offene Punkte

- Stryker Shared-Projekt: Config + Summary-Script für Unterverzeichnisse (TODO nächste Session) – Details in DEV_WORKFLOW.md
- Stryker-Findings aus Session 24 weiterhin offen (RecipesEndpoints Layer-Isolation, WeeklyPoolEndpoints etc.)
- Frontend-Neuimplementierung steht noch aus
