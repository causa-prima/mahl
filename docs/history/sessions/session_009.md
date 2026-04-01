# Session 009 – 2026-02-26: Code-Quality-Hooks

## Kontext

- **Phase:** SKELETON (Backend vollständig, Frontend ausstehend)
- **Schwerpunkt:** Guidelines analysieren, checks/-Package implementieren, Hooks in echtem Claude Code verifizieren

---

## Implementiertes

### CODING_GUIDELINE_CSHARP.md – Aktualisierungen

1. **Abschnitt 1 (Immutability):** Tabelle mit Rollen-Typen (EF-Entity = `class`, DTO = `record`, Value Object = `readonly record struct`); Ausnahme-Pfade explizit dokumentiert
2. **Abschnitt 4 (ROP):** `throw` als seltene Ausnahme mit Pflichtkommentar; `.IsT0`/`.AsT0` global verboten; ROP-Abschnitt auf allgemeinen Produktionscode erweitert
3. **Abschnitt 5 (Sum Types):** Verbotene Muster (bool-Flags, string-Status, nullable als Zustand) mit Gegenbeispielen

### checks/-Package (`.claude/hooks/checks/`)

| Modul | Typ | Prüft |
|-------|-----|-------|
| `immutability_strict.py` | blocking | `class` ohne `record`; `set;` ohne `private/protected/internal` |
| `rop.py` | blocking | `.IsT0`/`.AsT0` (C#); `.isOk()`/`_unsafeUnwrap()` (TS) |
| `throw_check.py` | blocking | `throw new X` außer `InvalidOperationException`; `throw` (TS) |
| `constructors.py` | blocking | nicht-private Konstruktoren in Domain-Code |
| `tdd_one_test.py` | blocking | max. 1 neuer Test pro Edit/Write |
| `immutability.py` | non-blocking | Mutable Collections in Properties/Parametern |
| `primitives.py` | non-blocking | Nackte Built-in-Typen in Properties/Parametern |
| `test_patterns.py` | non-blocking | `HaveCount`/`ContainSingle` statt `BeEquivalentTo` |
| `common.py` | shared | `HookInput`, `parse_input()`, `BLOCKING_DISCUSSION_NOTE`, Regex-Pattern |

### Dispatcher

- `check-code-quality-blocking.py` → `exit 2` + stderr bei Violation
- `check-code-quality-nonblocking.py` → `exit 2` + stderr bei Warning, `exit 0` sonst

### settings.json

Hooks in `settings.json` (projektglobal, committet), nicht mehr in `settings.local.json`:

```json
"PostToolUse": [{
  "matcher": "Edit|Write",
  "hooks": [
    { "type": "command", "command": "bash -c \"python3 $PWD/.claude/hooks/check-code-quality-blocking.py\"" },
    { "type": "command", "command": "bash -c \"python3 $PWD/.claude/hooks/check-code-quality-nonblocking.py\"" }
  ]
}]
```

---

## Bugs gefunden & behoben

| Bug | Ursache | Fix |
|-----|---------|-----|
| `Tests?.cs` matchte `HookTest.cs` | `?` macht `s` optional | `Tests\.cs$` ohne `?` |
| `public set;` nicht erkannt | Regex suchte explizites `public set;` | `\bset\s*;` + Filterung von restricted-setter-Zeilen |
| `$PWD` nicht expandiert | Single quotes in `bash -c '...'` | Double quotes: `bash -c "..."` |
| PostToolUse `exit 1` unsichtbar für Claude | `exit 1` = Terminal-Fehler, nicht Claude-Feedback | `exit 2` + stderr |
| `exit 0` + stderr verworfen | Claude Code ignoriert stderr bei exit 0 | `exit 2` auch für non-blocking |

---

## Ergebnisse

- Alle Hooks im echten Claude Code Betrieb verifiziert (blocking ✅, non-blocking ✅, beides gleichzeitig ✅)
- 52 Tests (unverändert)
- Hook-Konfiguration: `exit 2` + stderr = Claude sieht Meldung als system-reminder

---

## Offene Punkte

- `docs/DEV_WORKFLOW.md`: Abschnitt zu Hook-Entwicklung (exit-Code-Semantik 0/1/2, $PWD, stderr) → User-Approval ausstehend
- `git diff HEAD`-Problem (aus Session 8): Entscheid über `git status --porcelain` ausstehend
- TypeScript ESLint-Regeln: erst relevant bei Frontend-Start
