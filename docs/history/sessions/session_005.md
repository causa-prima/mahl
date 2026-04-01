# Session 005 – 2026-02-25

## Ziel

TDD-Abschluss für `IngredientsEndpoints` (verbleibende Tests + Restore-Endpoint), ROP-Refactoring
des POST-Endpoints, Guideline-Präzisierung, Code- und Test-Review, PreToolUse-Hook für TDD-Enforcement.

---

## Implementiertes

### 1. PreToolUse-Hook: `check-one-test.sh`

Neue Datei: `.claude/hooks/check-one-test.sh`

Zählt `[Test]`-Attribute (C#) bzw. `it(`/`test(`-Calls (TypeScript) in `new_string` vs. `old_string`
(Edit-Tool) bzw. im Datei-Inhalt (Write-Tool). Blockiert mit Exit 1, wenn mehr als 1 neuer Test
pro Änderung hinzugefügt wird.

Registriert in `.claude/settings.local.json` als `Edit|Write`-Matcher.

### 2. TDD-Zyklen (4 Stück)

Alle Tests zuerst rot, dann minimal grün, dann refactored:

- `Delete_AlreadySoftDeleted_Returns404`
  → Guard `|| ingredient.DeletedAt != null` in DELETE-Handler ergänzt.
- `Restore_SoftDeletedId_Returns200AndReactivates`
  → Restore-Endpoint initial minimal: FindAsync → DeletedAt = null → SaveChangesAsync → Ok.
- `Restore_ActiveIngredient_Returns409`
  → Guard `if (ingredient.DeletedAt == null) return Conflict` ergänzt.
- `Restore_UnknownId_Returns404`
  → Guard `if (ingredient is null) return NotFound` ergänzt.

**Ergebnis:** 23 Tests, alle grün.

### 3. ROP-Refactoring POST-Endpoint

`Shared/OneOfExtensions.cs` um drei Extension-Methods erweitert:
- `Map<TIn, TOut, TError>`: Erfolgsfall transformieren
- `BindAsync<TIn, TOut, TError>`: async Schritt in der Kette
- `MatchAsync<T0, T1, TResult>`: Terminal-Dispatch auf `Task<OneOf<...>>`

`Server/Endpoints/IngredientsEndpoints.cs` POST-Handler umgeschrieben:
- Sync-Validierung via `.MapError()` → `.Bind()` → `.Map()`
- Async DB-Logik via `.BindAsync()`
- Dispatch via `.MatchAsync()`

### 4. Guideline-Aktualisierung

`docs/CODING_GUIDELINE_CSHARP.md` Abschnitt 4 (ROP) um Unterabschnitt "ROP in Minimal-API-Endpoints"
ergänzt: Tabelle mit erlaubten/verbotenen Patterns, Referenz-Beispiel aus IngredientsEndpoints.cs.

### 5. Code- und Test-Review

Zwei Review-Agenten parallel beauftragt. Ergebnisse:

**Code-Review:** 6 ✅ / 9 ⚠️ / 0 ❌
- Wichtigste ⚠️: `SoftDeletedConflict` file record dupliziert `SoftDeletedConflictDto` aus Shared;
  Business-Regeln (Duplikat-Check, Soft-Delete-Konflikt) sollten in Domain Service;
  Error-Message-Strings hardcoded.

**Test-Review:** 17 ✅ / 6 ⚠️ / 2 ❌
- ❌: `GetAllIngredients()` Name irreführend (enthält auch soft-deleted); `HaveCount(1)` in
  `GetAll_ExcludesSoftDeletedIngredients` statt `BeEquivalentTo`.
- ⚠️: `BeEmpty()` → `BeEquivalentTo([])` für Konsistenz; fehlende `stateBeforeAction`-Muster
  an einzelnen Stellen.

---

## Offene Punkte (Technische Schuld)

| # | Problem | Priorität |
|---|---------|-----------|
| 1 | `GetAllIngredients()` umbenennen (irreführend, enthält soft-deleted) | Sofort |
| 2 | `HaveCount(1)` → `BeEquivalentTo` in ExcludesSoftDeleted-Test | Sofort |
| 3 | `SoftDeletedConflict` file record vs. `SoftDeletedConflictDto` aus Shared | Bald |
| 4 | `BeEmpty()` → `BeEquivalentTo([])` in Fehler-Pfad-Tests | Bald |
| 5 | Error-Message-Strings als Konstanten | Bald |
| 6 | Business-Regeln in Domain Service (wenn zweiter Endpoint gleiche Logik braucht) | Zurückstellen |

---

## Probleme / Hindernisse

- **TDD-Verstoß zu Sessionbeginn**: Mehrere Tests + Implementierungen gebündelt → User musste
  unterbrechen → Revert → Diskussion → Hook-Lösung.
- **Hook-Erstellung**: `set -euo pipefail` in WSL nicht unterstützt; CRLF durch Write-Tool →
  Workaround: Bash-Heredoc `cat > file << 'SCRIPT'`.
- **ROP vergessen**: Wurde erst nach User-Hinweis nachgezogen.
- **`MatchAsync` fehlte**: Compile-Error weil `.Match()` auf `Task<OneOf<...>>` nicht direkt
  funktioniert → `MatchAsync`-Extension ergänzt.

---

## Ergebnis

- 23 Ingredients-Tests, alle grün
- Ingredients-Endpoint vollständig (GET all, GET by id, POST, DELETE, Restore)
- ROP-konforme Implementierung
- TDD-Enforcement-Hook aktiv
